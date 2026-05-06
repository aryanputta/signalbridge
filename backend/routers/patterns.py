import json
from collections import defaultdict
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from database import get_session
from models import SignalLog, PatternSummary

router = APIRouter(prefix="/patterns", tags=["patterns"])


@router.get("/{patient_id}/summary")
def get_pattern_summary(patient_id: int, session: Session = Depends(get_session)):
    patterns = session.exec(
        select(PatternSummary)
        .where(PatternSummary.patient_id == patient_id)
        .order_by(PatternSummary.count.desc())
    ).all()

    logs = session.exec(
        select(SignalLog).where(SignalLog.patient_id == patient_id)
    ).all()

    total_interactions = len(logs)
    correct = sum(1 for l in logs if l.feedback == "correct")
    incorrect = sum(1 for l in logs if l.feedback == "incorrect")
    low_confidence = sum(1 for l in logs if l.confidence is not None and l.confidence < 0.35)
    urgent_events = sum(1 for l in logs if l.urgency == "high")

    accuracy = round(correct / total_interactions, 3) if total_interactions > 0 else 0.0

    time_buckets: dict[str, int] = defaultdict(int)
    for log in logs:
        if log.timestamp:
            hour = log.timestamp.hour
            if 5 <= hour < 12:
                time_buckets["morning"] += 1
            elif 12 <= hour < 17:
                time_buckets["afternoon"] += 1
            elif 17 <= hour < 21:
                time_buckets["evening"] += 1
            else:
                time_buckets["night"] += 1

    top_signals: dict[str, int] = defaultdict(int)
    for log in logs:
        top_signals[log.signal] += 1

    top_needs: dict[str, int] = defaultdict(int)
    for log in logs:
        if log.confirmed_intent:
            top_needs[log.confirmed_intent] += 1

    return {
        "patient_id": patient_id,
        "total_interactions": total_interactions,
        "top_1_accuracy": accuracy,
        "correct_count": correct,
        "incorrect_count": incorrect,
        "low_confidence_count": low_confidence,
        "urgent_events": urgent_events,
        "top_signals": sorted(top_signals.items(), key=lambda x: x[1], reverse=True)[:8],
        "top_confirmed_needs": sorted(top_needs.items(), key=lambda x: x[1], reverse=True)[:8],
        "time_of_day_distribution": dict(time_buckets),
        "patterns": [
            {
                "signal": p.signal,
                "confirmed_intent": p.confirmed_intent,
                "count": p.count,
                "last_seen": p.last_seen.isoformat(),
                "time_buckets": json.loads(p.time_buckets or "{}"),
            }
            for p in patterns
        ],
    }


@router.get("/{patient_id}/export")
def export_summary(patient_id: int, session: Session = Depends(get_session)):
    summary = get_pattern_summary(patient_id, session)
    # Only fetch logs that have a caregiver note — avoids re-scanning all logs
    note_logs = session.exec(
        select(SignalLog)
        .where(
            SignalLog.patient_id == patient_id,
            SignalLog.caregiver_note.is_not(None),
        )
        .order_by(SignalLog.timestamp.desc())
        .limit(100)
    ).all()

    lines = [
        f"# SignalBridge Session Export",
        f"**Patient ID:** {patient_id}",
        f"**Generated:** {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Stats",
        f"- Total interactions: {summary['total_interactions']}",
        f"- Top-1 accuracy: {summary['top_1_accuracy']}",
        f"- Urgent events: {summary['urgent_events']}",
        f"- Low confidence fallbacks: {summary['low_confidence_count']}",
        "",
        "## Most Frequent Signals",
    ]
    for signal, count in summary["top_signals"]:
        lines.append(f"- {signal}: {count}")

    lines += ["", "## Most Confirmed Needs"]
    for need, count in summary["top_confirmed_needs"]:
        lines.append(f"- {need}: {count}")

    lines += ["", "## Time of Day Distribution"]
    for bucket, count in summary["time_of_day_distribution"].items():
        lines.append(f"- {bucket}: {count}")

    lines += ["", "## Personalized Patterns"]
    for p in summary["patterns"]:
        lines.append(
            f"- '{p['signal']}' → '{p['confirmed_intent']}' confirmed {p['count']}x "
            f"(last: {p['last_seen'][:10]})"
        )

    lines += ["", "## Recent Caregiver Notes"]
    for log in note_logs:
        if log.caregiver_note:
            ts = log.timestamp.isoformat()[:16] if log.timestamp else "unknown"
            lines.append(f"- [{ts}] {log.signal}: {log.caregiver_note}")

    lines += [
        "",
        "---",
        "*This export is for caregiver handoff only. Not a medical record.*",
    ]

    return {"markdown": "\n".join(lines), "json": summary}
