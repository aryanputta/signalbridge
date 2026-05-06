"""
SignalBridge suggestion engine benchmark.

Measures:
  - suggestion latency (p50, p95, p99)
  - top-1 accuracy before and after personalization
  - top-3 match rate
  - low-confidence fallback rate
  - personalization delta (accuracy improvement after feedback)

Usage:
    cd signalbridge/backend
    python ../benchmarks/bench_suggestions.py
"""

import sys
import time
import random
import statistics
from datetime import datetime, timedelta
from unittest.mock import MagicMock

sys.path.insert(0, ".")

from suggestion_engine import suggest, record_feedback, _time_bucket
from models import SignalLog, PatternSummary, PatientProfile
from sqlmodel import SQLModel, create_engine, Session

SEED = 42
random.seed(SEED)

PATIENT_ID = 999

GROUND_TRUTH = {
    "pain":        "pain",
    "water":       "water",
    "food":        "food",
    "bathroom":    "bathroom",
    "tired":       "tired",
    "uncomfortable": "uncomfortable",
    "yes":         "yes",
    "no":          "no",
    "help":        "help",
    "reposition":  "reposition",
    "medication":  "medication",
    "temperature": "temperature",
    "cold":        "cold",
    "hot":         "hot",
    "anxiety":     "anxiety",
    "confused":    "confused",
}

NOISE_RATE = 0.15


def make_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    session = Session(engine)
    patient = PatientProfile(id=PATIENT_ID, name="Benchmark Patient")
    session.add(patient)
    session.commit()
    return session


def sample_context() -> dict:
    return {
        "pain_visible": random.random() < 0.2,
        "hours_since_meal": random.uniform(0, 8) if random.random() < 0.6 else None,
        "hours_since_medication": random.uniform(0, 12) if random.random() < 0.5 else None,
        "low_sleep": random.random() < 0.3,
        "no_movement": random.random() < 0.2,
        "room_temp": random.choice([None, None, "cold", "hot"]),
    }


def noisy_signal(true_signal: str) -> str:
    if random.random() < NOISE_RATE:
        return random.choice(list(GROUND_TRUTH.keys()))
    return true_signal


def run_window(
    session: Session,
    signals: list[str],
    n: int,
    with_feedback: bool,
    time_offset_hours: int = 0,
) -> tuple[float, float, float, float]:
    correct = 0
    top3 = 0
    fallbacks = 0
    latencies = []

    for i in range(n):
        true_signal = signals[i % len(signals)]
        obs_signal = noisy_signal(true_signal)
        context = sample_context()
        now = datetime.utcnow() + timedelta(hours=time_offset_hours + i * 0.5)

        t0 = time.perf_counter()
        result = suggest(obs_signal, PATIENT_ID, context, session, now)
        latencies.append((time.perf_counter() - t0) * 1000)

        if result["fallback"]:
            fallbacks += 1
            continue

        true_intent = GROUND_TRUTH[true_signal]
        top_intent = result["predictions"][0]["intent"] if result["predictions"] else ""
        top3_intents = [p["intent"] for p in result["predictions"][:3]]

        if top_intent == true_intent:
            correct += 1
        if true_intent in top3_intents:
            top3 += 1

        if with_feedback and result["predictions"]:
            tb = _time_bucket(now)
            feedback = "correct" if top_intent == true_intent else "incorrect"
            log_id = -(i + 1)
            log = SignalLog(
                id=log_id,
                patient_id=PATIENT_ID,
                signal=obs_signal,
                timestamp=now,
            )
            session.add(log)
            session.commit()
            record_feedback(log_id, true_intent, feedback, PATIENT_ID, obs_signal, tb, session)

    total = n - fallbacks
    acc = correct / total if total > 0 else 0.0
    top3_rate = top3 / total if total > 0 else 0.0
    fallback_rate = fallbacks / n
    return acc, top3_rate, fallback_rate, latencies


def percentile(data: list[float], p: float) -> float:
    sorted_data = sorted(data)
    idx = int(len(sorted_data) * p / 100)
    return sorted_data[min(idx, len(sorted_data) - 1)]


def main():
    print("=" * 60)
    print("SignalBridge Suggestion Engine Benchmark")
    print("=" * 60)

    session = make_session()
    signals = list(GROUND_TRUTH.keys())

    print("\n[Phase 1] Baseline accuracy (no personalization, n=50)")
    acc0, top3_0, fb0, lat0 = run_window(session, signals, 50, with_feedback=False)
    print(f"  Top-1 accuracy:   {acc0:.1%}")
    print(f"  Top-3 match rate: {top3_0:.1%}")
    print(f"  Fallback rate:    {fb0:.1%}")
    print(f"  Latency p50:      {percentile(lat0, 50):.2f}ms")
    print(f"  Latency p95:      {percentile(lat0, 95):.2f}ms")
    print(f"  Latency p99:      {percentile(lat0, 99):.2f}ms")

    print("\n[Phase 2] Feedback training (n=100, with caregiver corrections)")
    run_window(session, signals, 100, with_feedback=True)
    print("  Feedback loop complete.")

    print("\n[Phase 3] Post-personalization accuracy (n=50)")
    acc1, top3_1, fb1, lat1 = run_window(session, signals, 50, with_feedback=False, time_offset_hours=200)
    print(f"  Top-1 accuracy:   {acc1:.1%}")
    print(f"  Top-3 match rate: {top3_1:.1%}")
    print(f"  Fallback rate:    {fb1:.1%}")
    print(f"  Latency p50:      {percentile(lat1, 50):.2f}ms")
    print(f"  Latency p95:      {percentile(lat1, 95):.2f}ms")
    print(f"  Latency p99:      {percentile(lat1, 99):.2f}ms")

    delta = acc1 - acc0
    print("\n[Result] Personalization Delta")
    print(f"  Accuracy improvement: {delta:+.1%}")
    print(f"  Top-3 improvement:    {top3_1 - top3_0:+.1%}")
    print(f"  Fallback reduction:   {fb0 - fb1:+.1%}")

    targets_met = []
    targets_failed = []

    if acc0 >= 0.40:
        targets_met.append(f"Baseline top-1 >= 40%: {acc0:.1%}")
    else:
        targets_failed.append(f"Baseline top-1 < 40%: {acc0:.1%}")

    if acc1 >= 0.60:
        targets_met.append(f"Post-training top-1 >= 60%: {acc1:.1%}")
    else:
        targets_failed.append(f"Post-training top-1 < 60%: {acc1:.1%}")

    if top3_0 >= 0.75:
        targets_met.append(f"Baseline top-3 >= 75%: {top3_0:.1%}")
    else:
        targets_failed.append(f"Baseline top-3 < 75%: {top3_0:.1%}")

    if delta >= 0.10:
        targets_met.append(f"Personalization delta >= 10pp: {delta:+.1%}")
    else:
        targets_failed.append(f"Personalization delta < 10pp: {delta:+.1%}")

    if percentile(lat0, 99) < 50:
        targets_met.append(f"p99 latency < 50ms: {percentile(lat0, 99):.1f}ms")
    else:
        targets_failed.append(f"p99 latency >= 50ms: {percentile(lat0, 99):.1f}ms")

    print("\n[Targets]")
    for t in targets_met:
        print(f"  PASS  {t}")
    for t in targets_failed:
        print(f"  FAIL  {t}")

    session.close()
    print("\n" + "=" * 60)
    if not targets_failed:
        print("All targets met.")
    else:
        print(f"{len(targets_failed)} target(s) failed.")
    print("=" * 60)


if __name__ == "__main__":
    main()
