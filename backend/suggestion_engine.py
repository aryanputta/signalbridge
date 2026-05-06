import json
from datetime import datetime
from typing import Optional
from sqlmodel import Session, select, func

from models import SignalLog, PatternSummary


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

    if context.get("hours_since_meal", 99) > 4:
        modified["food"] = modified.get("food", 0) * 1.3
        modified["water"] = modified.get("water", 0) * 1.2

    if context.get("hours_since_medication", 99) > 6:
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


def _build_explanation(
    top_intent: str,
    signal: str,
    time_bucket: str,
    context: dict,
    history_counts: dict[str, int],
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

    if context.get("pain_visible") and top_intent == "pain":
        parts.append("Visible pain signs were noted.")
    if context.get("hours_since_meal", 99) > 4 and top_intent in ("food", "water"):
        parts.append(f"It has been over {int(context['hours_since_meal'])} hours since the last meal.")
    if context.get("hours_since_medication", 99) > 6 and top_intent == "medication":
        parts.append("Medication timing may be due.")
    if context.get("low_sleep") and top_intent == "tired":
        parts.append("Low sleep quality was noted.")
    if context.get("no_movement") and top_intent == "reposition":
        parts.append("No movement was noted recently.")

    return " ".join(parts)


FALLBACK_MESSAGE = (
    "The system is not confident enough to suggest a specific intent. "
    "Please check directly with the person. Consider: pain, water, bathroom, comfort, medication."
)
CONFIDENCE_THRESHOLD = 0.35


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

    time_mods = TIME_MODIFIERS.get(time_bucket, {})
    for intent, mult in time_mods.items():
        if intent in priors:
            priors[intent] *= mult

    priors = _apply_context_modifiers(priors, context)
    priors, history_counts = _apply_history(priors, signal, patient_id, time_bucket, session)

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
        }

    explanation = _build_explanation(top_intent, signal, time_bucket, context, history_counts)

    predictions = []
    for intent, score in ranked[:3]:
        is_top = intent == top_intent
        predictions.append({
            "intent": intent,
            "confidence": round(score, 3),
            "urgency": "high" if intent in URGENT_INTENTS else ("medium" if score > 0.5 else "low"),
            "explanation": explanation if is_top else "",
        })

    return {
        "predictions": predictions,
        "fallback": False,
        "fallback_message": None,
        "urgency": urgency,
        "time_bucket": time_bucket,
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
        pattern = PatternSummary(
            patient_id=patient_id,
            signal=signal,
            confirmed_intent=confirmed_intent,
            count=1,
            last_seen=datetime.utcnow(),
            time_buckets=json.dumps({time_bucket: 1}),
        )
        session.add(pattern)

    session.commit()
