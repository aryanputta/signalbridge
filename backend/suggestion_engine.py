"""
Suggestion engine — three-stage pipeline:

  Stage 0 (<20 confirmed): rule-based priors + time modifiers + context modifiers
  Stage 1 (20-49 confirmed): Stage 0 output Bayes-updated with confirmed history
  Stage 2 (>=50 confirmed): Transformer output blended with Stage 1

The blend weight at Stage 2 starts at 0.3 (trust the rule engine more early on)
and scales toward 0.7 (trust the model more) as confirmed count grows toward 200.
This gives a smooth, monotonic transition rather than a hard cutover.
"""

import json
from datetime import datetime
from typing import Optional

from sqlmodel import Session, select

from models import SignalLog, PatternSummary

# Transformer layer — imported lazily so the engine still works without torch
try:
    from personal_model import get_personal_model
    from mini_transformer import _time_bucket as _tb_from_transformer
    TRANSFORMER_AVAILABLE = True
except ImportError:
    TRANSFORMER_AVAILABLE = False

URGENT_INTENTS = {"pain", "help", "breathing", "medication", "bathroom_urgent"}

SIGNAL_PRIORS: dict[str, dict[str, float]] = {
    "pain":         {"pain": 0.70, "uncomfortable": 0.15, "help": 0.10, "reposition": 0.05},
    "water":        {"water": 0.75, "food": 0.10, "medication": 0.10, "tired": 0.05},
    "food":         {"food": 0.70, "water": 0.15, "medication": 0.10, "tired": 0.05},
    "bathroom":     {"bathroom": 0.75, "reposition": 0.10, "uncomfortable": 0.10, "pain": 0.05},
    "tired":        {"tired": 0.60, "pain": 0.20, "uncomfortable": 0.15, "reposition": 0.05},
    "uncomfortable":{"uncomfortable": 0.50, "reposition": 0.20, "pain": 0.20, "temperature": 0.10},
    "yes":          {"yes": 0.80, "help": 0.10, "okay": 0.10},
    "no":           {"no": 0.80, "uncomfortable": 0.10, "pain": 0.10},
    "help":         {"help": 0.65, "pain": 0.20, "anxiety": 0.10, "bathroom": 0.05},
    "reposition":   {"reposition": 0.70, "uncomfortable": 0.15, "pain": 0.10, "tired": 0.05},
    "medication":   {"medication": 0.75, "pain": 0.15, "water": 0.10},
    "temperature":  {"temperature": 0.60, "cold": 0.20, "hot": 0.15, "uncomfortable": 0.05},
    "cold":         {"cold": 0.70, "temperature": 0.20, "uncomfortable": 0.10},
    "hot":          {"hot": 0.70, "temperature": 0.20, "uncomfortable": 0.10},
    "anxiety":      {"anxiety": 0.60, "help": 0.20, "pain": 0.10, "confused": 0.10},
    "confused":     {"confused": 0.60, "anxiety": 0.20, "help": 0.15, "medication": 0.05},
}

TIME_MODIFIERS: dict[str, dict[str, float]] = {
    "morning":   {"medication": 1.4, "food": 1.3, "water": 1.2, "pain": 1.1},
    "afternoon": {"water": 1.3, "tired": 1.2, "food": 1.1},
    "evening":   {"food": 1.3, "tired": 1.2, "medication": 1.2, "pain": 1.1},
    "night":     {"pain": 1.4, "bathroom": 1.3, "uncomfortable": 1.2, "tired": 1.1},
}

FALLBACK_MESSAGE = (
    "The system is not confident enough to suggest a specific intent. "
    "Please check directly with the person. Consider: pain, water, bathroom, comfort, medication."
)
CONFIDENCE_THRESHOLD = 0.35


def _time_bucket(dt: datetime) -> str:
    hour = dt.hour
    if 5 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "afternoon"
    if 17 <= hour < 21:
        return "evening"
    return "night"


def _apply_context_modifiers(scores: dict[str, float], context: dict) -> dict[str, float]:
    modified = dict(scores)

    if context.get("pain_visible"):
        modified["pain"] = modified.get("pain", 0) * 1.5
        modified["help"] = modified.get("help", 0) * 1.2

    hours_meal = context.get("hours_since_meal")
    if hours_meal is not None and hours_meal > 4:
        modified["food"] = modified.get("food", 0) * 1.3
        modified["water"] = modified.get("water", 0) * 1.2

    hours_meds = context.get("hours_since_medication")
    if hours_meds is not None and hours_meds > 6:
        modified["medication"] = modified.get("medication", 0) * 1.4

    if context.get("low_sleep"):
        modified["tired"] = modified.get("tired", 0) * 1.4
        modified["pain"] = modified.get("pain", 0) * 1.2

    if context.get("no_movement", False):
        modified["reposition"] = modified.get("reposition", 0) * 1.5
        modified["uncomfortable"] = modified.get("uncomfortable", 0) * 1.2

    room_temp = context.get("room_temp", "")
    if room_temp == "cold":
        modified["cold"] = modified.get("cold", 0) * 1.5
        modified["temperature"] = modified.get("temperature", 0) * 1.2
    elif room_temp == "hot":
        modified["hot"] = modified.get("hot", 0) * 1.5
        modified["temperature"] = modified.get("temperature", 0) * 1.2

    return modified


def _apply_history(
    scores: dict[str, float],
    signal: str,
    patient_id: int,
    time_bucket: str,
    session: Session,
) -> tuple[dict[str, float], dict[str, int]]:
    patterns = session.exec(
        select(PatternSummary).where(
            PatternSummary.patient_id == patient_id,
            PatternSummary.signal == signal,
        )
    ).all()

    history_counts: dict[str, int] = {}
    total_confirmed = sum(p.count for p in patterns)

    for p in patterns:
        history_counts[p.confirmed_intent] = p.count
        if total_confirmed > 0:
            likelihood = p.count / total_confirmed
            prior = scores.get(p.confirmed_intent, 0.01)
            scores[p.confirmed_intent] = prior * (1 + likelihood * 2)

            time_buckets = json.loads(p.time_buckets or "{}")
            bucket_count = time_buckets.get(time_bucket, 0)
            if bucket_count > 0 and p.count > 0:
                time_weight = bucket_count / p.count
                scores[p.confirmed_intent] *= 1 + time_weight * 0.5

    return scores, history_counts


def _blend_with_transformer(
    bayes_scores: dict[str, float],
    model_probs: dict[str, float],
    confirmed_count: int,
) -> dict[str, float]:
    """
    Linearly blend Bayesian engine scores with Transformer probabilities.
    Blend weight ramps from 0.3 to 0.7 as confirmed_count grows 50→200.
    """
    alpha = min(0.7, 0.3 + (confirmed_count - 50) / 150 * 0.4)

    all_intents = set(bayes_scores) | set(model_probs)
    total_bayes = sum(bayes_scores.values()) or 1.0
    bayes_norm = {k: v / total_bayes for k, v in bayes_scores.items()}

    blended = {}
    for intent in all_intents:
        b = bayes_norm.get(intent, 0.0)
        m = model_probs.get(intent, 0.0)
        blended[intent] = (1 - alpha) * b + alpha * m

    return blended


def _build_explanation(
    top_intent: str,
    signal: str,
    time_bucket: str,
    context: dict,
    history_counts: dict[str, int],
    used_transformer: bool = False,
) -> str:
    parts = []
    count = history_counts.get(top_intent, 0)

    if count >= 3:
        parts.append(f"This signal was confirmed as '{top_intent}' {count} times before")
        parts.append(f"and often appears in the {time_bucket}.")
    elif count > 0:
        parts.append(f"This signal was confirmed as '{top_intent}' {count} time before.")
    else:
        parts.append(f"Based on typical patterns, '{signal}' signals most commonly indicate '{top_intent}'.")

    if used_transformer:
        parts.append("Personalised model active.")

    if context.get("pain_visible") and top_intent == "pain":
        parts.append("Visible pain signs were noted.")

    hours_meal = context.get("hours_since_meal")
    if hours_meal is not None and hours_meal > 4 and top_intent in ("food", "water"):
        parts.append(f"It has been over {int(hours_meal)} hours since the last meal.")

    hours_meds = context.get("hours_since_medication")
    if hours_meds is not None and hours_meds > 6 and top_intent == "medication":
        parts.append("Medication timing may be due.")

    if context.get("low_sleep") and top_intent == "tired":
        parts.append("Low sleep quality was noted.")
    if context.get("no_movement") and top_intent == "reposition":
        parts.append("No movement was noted recently.")

    return " ".join(parts)


def _fetch_recent_history(patient_id: int, session: Session, limit: int = 8) -> list[dict]:
    logs = session.exec(
        select(SignalLog)
        .where(SignalLog.patient_id == patient_id, SignalLog.confirmed_intent.is_not(None))
        .order_by(SignalLog.timestamp.desc())
        .limit(limit)
    ).all()
    result = []
    for log in reversed(logs):
        ctx = json.loads(log.context_json or "{}")
        result.append({
            "signal": log.signal,
            "time_bucket": _time_bucket(log.timestamp) if log.timestamp else "morning",
            "context": ctx,
            "confirmed_intent": log.confirmed_intent,
        })
    return result


def suggest(
    signal: str,
    patient_id: int,
    context: dict,
    session: Session,
    now: Optional[datetime] = None,
) -> dict:
    if now is None:
        now = datetime.utcnow()

    priors = dict(SIGNAL_PRIORS.get(signal, {"unknown": 1.0}))
    time_bucket = _time_bucket(now)

    for intent, mult in TIME_MODIFIERS.get(time_bucket, {}).items():
        if intent in priors:
            priors[intent] *= mult

    priors = _apply_context_modifiers(priors, context)
    priors, history_counts = _apply_history(priors, signal, patient_id, time_bucket, session)

    used_transformer = False
    confirmed_count = sum(history_counts.values())

    if TRANSFORMER_AVAILABLE and confirmed_count >= 50:
        try:
            personal = get_personal_model(patient_id)
            if personal.stage == 2:
                history = _fetch_recent_history(patient_id, session)
                model_probs = personal.predict(signal, time_bucket, context, history)
                if model_probs:
                    priors = _blend_with_transformer(priors, model_probs, confirmed_count)
                    used_transformer = True
        except Exception:
            pass  # never let the model layer break the rule engine

    total = sum(priors.values()) or 1.0
    normalized = {k: v / total for k, v in priors.items()}
    ranked = sorted(normalized.items(), key=lambda x: x[1], reverse=True)

    top_intent, top_score = ranked[0]
    is_urgent = top_intent in URGENT_INTENTS
    urgency = "high" if is_urgent else ("medium" if top_score > 0.5 else "low")

    if top_score < CONFIDENCE_THRESHOLD:
        return {
            "predictions": [
                {"intent": intent, "confidence": round(score, 3), "urgency": urgency, "explanation": ""}
                for intent, score in ranked[:3]
            ],
            "fallback": True,
            "fallback_message": FALLBACK_MESSAGE,
            "urgency": "unknown",
            "time_bucket": time_bucket,
            "stage": 0 if confirmed_count < 20 else (1 if confirmed_count < 50 else 2),
        }

    explanation = _build_explanation(
        top_intent, signal, time_bucket, context, history_counts, used_transformer
    )

    predictions = []
    for intent, score in ranked[:3]:
        predictions.append({
            "intent": intent,
            "confidence": round(score, 3),
            "urgency": "high" if intent in URGENT_INTENTS else ("medium" if score > 0.5 else "low"),
            "explanation": explanation if intent == top_intent else "",
        })

    return {
        "predictions": predictions,
        "fallback": False,
        "fallback_message": None,
        "urgency": urgency,
        "time_bucket": time_bucket,
        "stage": 0 if confirmed_count < 20 else (1 if confirmed_count < 50 else 2),
    }


def record_feedback(
    log_id: int,
    confirmed_intent: str,
    feedback: str,
    patient_id: int,
    signal: str,
    time_bucket: str,
    session: Session,
) -> None:
    log = session.get(SignalLog, log_id)
    if log:
        log.confirmed_intent = confirmed_intent
        log.feedback = feedback
        session.add(log)

    existing = session.exec(
        select(PatternSummary).where(
            PatternSummary.patient_id == patient_id,
            PatternSummary.signal == signal,
            PatternSummary.confirmed_intent == confirmed_intent,
        )
    ).first()

    if existing:
        existing.count += 1
        existing.last_seen = datetime.utcnow()
        buckets = json.loads(existing.time_buckets or "{}")
        buckets[time_bucket] = buckets.get(time_bucket, 0) + 1
        existing.time_buckets = json.dumps(buckets)
        session.add(existing)
    else:
        from models import PatternSummary as PS
        pattern = PS(
            patient_id=patient_id,
            signal=signal,
            confirmed_intent=confirmed_intent,
            count=1,
            last_seen=datetime.utcnow(),
            time_buckets=json.dumps({time_bucket: 1}),
        )
        session.add(pattern)

    session.commit()

    # Train the personal model asynchronously (blocking but fast: <80ms on CPU)
    if TRANSFORMER_AVAILABLE:
        try:
            personal = get_personal_model(patient_id)
            context = json.loads(log.context_json or "{}") if log else {}
            history = _fetch_recent_history(patient_id, session)
            suggested = log.suggested_intent or "unknown" if log else "unknown"
            personal.add_and_train(
                signal=signal,
                time_bucket=time_bucket,
                context=context,
                confirmed_intent=confirmed_intent,
                feedback=feedback,
                suggested_intent=suggested,
                history=history,
            )
        except Exception:
            pass  # never break the feedback loop
