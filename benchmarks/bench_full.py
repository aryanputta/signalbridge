"""
SignalBridge full benchmark suite.

Measures and plots:
  1. Accuracy convergence: top-1 accuracy vs number of caregiver feedback rounds
     across all three engine stages (rule / Bayesian / Transformer)
  2. Latency distribution: p50/p95/p99 at each stage (violin + percentile bars)
  3. Transformer parameter count and training throughput
  4. Soft-label vs hard-label loss comparison (motivation for the novel contribution)
  5. Confidence calibration: predicted confidence vs actual correctness

Saves plots to benchmarks/plots/ and a JSON results file.

Usage:
    cd signalbridge/backend
    python ../benchmarks/bench_full.py
"""

import sys
import json
import math
import time
import random
import statistics
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, ".")

import numpy as np
from sqlmodel import SQLModel, create_engine, Session

from suggestion_engine import suggest, record_feedback, _time_bucket
from models import SignalLog, PatternSummary, PatientProfile
from mini_transformer import (
    _init_params, _init_adam_state, forward, backward, adam_step,
    predict as tf_predict, make_soft_label, soft_cross_entropy,
    N_INTENTS, INTENTS, N_SIGNALS,
)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

SEED = 42
random.seed(SEED)
np.random.seed(SEED)

PATIENT_ID = 1
PLOTS_DIR = Path(__file__).parent / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

GROUND_TRUTH: dict[str, str] = {
    "pain": "pain", "water": "water", "food": "food", "bathroom": "bathroom",
    "tired": "tired", "uncomfortable": "uncomfortable", "yes": "yes", "no": "no",
    "help": "help", "reposition": "reposition", "medication": "medication",
    "temperature": "temperature", "cold": "cold", "hot": "hot",
    "anxiety": "anxiety", "confused": "confused",
}
SIGNALS = list(GROUND_TRUTH.keys())

PALETTE = {
    "rule":        "#64748b",
    "bayes":       "#0ea5e9",
    "transformer": "#10b981",
    "accent":      "#f59e0b",
}


# ── Utilities ─────────────────────────────────────────────────────────────────

def make_db() -> Session:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    s = Session(engine)
    s.add(PatientProfile(id=PATIENT_ID, name="Bench Patient"))
    s.commit()
    return s


def sample_context() -> dict:
    return {
        "pain_visible": random.random() < 0.15,
        "hours_since_meal": random.uniform(0, 8) if random.random() < 0.6 else None,
        "hours_since_medication": random.uniform(0, 12) if random.random() < 0.5 else None,
        "low_sleep": random.random() < 0.25,
        "no_movement": random.random() < 0.2,
        "room_temp": random.choice([None, None, None, "cold", "hot"]),
    }


def pct(p: float, data: list[float]) -> float:
    s = sorted(data)
    idx = int(len(s) * p)
    return s[min(idx, len(s) - 1)]


def bar(label: str, val: float, width: int = 40) -> str:
    filled = int(val * width)
    return f"{label:<26} {'█' * filled}{'░' * (width - filled)} {val:.1%}"


def hbar(label: str, val_ms: float, max_ms: float = 10.0, width: int = 30) -> str:
    filled = int(min(val_ms / max_ms, 1.0) * width)
    return f"{label:<20} {'█' * filled}{'░' * (width - filled)} {val_ms:.2f}ms"


# ── Benchmark 1: Accuracy Convergence ────────────────────────────────────────

def bench_accuracy_convergence() -> dict:
    """
    Simulate a caregiver session: 200 interactions with feedback.
    Every 10 feedback rounds, evaluate top-1 accuracy on 30 held-out queries.
    Tracks rule-only, Bayesian (after N feedback), and returns series.
    """
    print("\n[1/5] Accuracy Convergence")

    session = make_db()
    checkpoints = list(range(0, 201, 10))
    rule_acc: list[float] = []
    bayes_acc: list[float] = []
    latencies_by_stage: dict[str, list[float]] = {"rule": [], "bayes": []}

    total_feedback = 0

    for cp in checkpoints:
        # Give feedback up to this checkpoint
        while total_feedback < cp:
            sig = random.choice(SIGNALS)
            ctx = sample_context()
            now = datetime.now(timezone.utc) + timedelta(hours=total_feedback * 0.3)
            result = suggest(sig, PATIENT_ID, ctx, session, now)
            true_intent = GROUND_TRUTH[sig]
            if result["predictions"]:
                tb = _time_bucket(now)
                top = result["predictions"][0]["intent"]
                fb = "correct" if top == true_intent else "incorrect"
                log_id = -(total_feedback + 1)
                log = SignalLog(id=log_id, patient_id=PATIENT_ID, signal=sig, timestamp=now)
                session.add(log)
                session.commit()
                record_feedback(log_id, true_intent, fb, PATIENT_ID, sig, tb, session)
            total_feedback += 1

        # Evaluate on 30 held-out probes
        correct_r = correct_b = 0
        for _ in range(30):
            sig = random.choice(SIGNALS)
            ctx = sample_context()
            now = datetime.now(timezone.utc) + timedelta(hours=total_feedback * 0.3 + 1000)
            t0 = time.perf_counter()
            result = suggest(sig, PATIENT_ID, ctx, session, now)
            lat = (time.perf_counter() - t0) * 1000
            true_intent = GROUND_TRUTH[sig]
            if not result["fallback"] and result["predictions"]:
                top = result["predictions"][0]["intent"]
                if cp == 0:
                    correct_r += int(top == true_intent)
                    latencies_by_stage["rule"].append(lat)
                else:
                    correct_b += int(top == true_intent)
                    latencies_by_stage["bayes"].append(lat)
            elif cp == 0:
                correct_r += 0
            else:
                correct_b += 0

        if cp == 0:
            rule_acc.append(correct_r / 30)
            bayes_acc.append(correct_r / 30)
        else:
            bayes_acc.append(correct_b / 30)
            if len(rule_acc) < len(bayes_acc):
                rule_acc.append(rule_acc[0])

    session.close()

    result = {
        "checkpoints": checkpoints,
        "rule_acc": rule_acc,
        "bayes_acc": bayes_acc,
    }

    # ASCII chart
    print(f"  Feedback rounds → Accuracy (rule baseline: {rule_acc[0]:.1%})")
    for i, cp in enumerate(checkpoints[::2]):
        idx = i * 2
        b = bayes_acc[idx] if idx < len(bayes_acc) else bayes_acc[-1]
        print(f"  n={cp:>3}  {bar('Bayesian', b, 30)}")

    return result


# ── Benchmark 2: Latency Distribution ────────────────────────────────────────

def bench_latency() -> dict:
    """Measure p50/p95/p99 for rule engine, Bayesian, and transformer predict."""
    print("\n[2/5] Latency Distribution")

    # Rule engine latency (fresh DB, no history)
    session_r = make_db()
    rule_lat = []
    for _ in range(200):
        sig = random.choice(SIGNALS)
        ctx = sample_context()
        t0 = time.perf_counter()
        suggest(sig, PATIENT_ID, ctx, session_r, datetime.now(timezone.utc))
        rule_lat.append((time.perf_counter() - t0) * 1000)
    session_r.close()

    # Bayesian latency (with 80 feedback rounds)
    session_b = make_db()
    for i in range(80):
        sig = random.choice(SIGNALS)
        ctx = sample_context()
        now = datetime.now(timezone.utc) + timedelta(hours=i * 0.5)
        result = suggest(sig, PATIENT_ID, ctx, session_b, now)
        true_intent = GROUND_TRUTH[sig]
        if result["predictions"]:
            tb = _time_bucket(now)
            top = result["predictions"][0]["intent"]
            fb = "correct" if top == true_intent else "incorrect"
            log_id = -(i + 1)
            log = SignalLog(id=log_id, patient_id=PATIENT_ID, signal=sig, timestamp=now)
            session_b.add(log)
            session_b.commit()
            record_feedback(log_id, true_intent, fb, PATIENT_ID, sig, tb, session_b)
    bayes_lat = []
    for _ in range(200):
        sig = random.choice(SIGNALS)
        ctx = sample_context()
        t0 = time.perf_counter()
        suggest(sig, PATIENT_ID, ctx, session_b, datetime.now(timezone.utc))
        bayes_lat.append((time.perf_counter() - t0) * 1000)
    session_b.close()

    # Transformer forward pass latency (standalone, no SQLite overhead)
    params = _init_params()
    history = [
        {"signal": random.choice(SIGNALS), "time_bucket": "morning",
         "context": {}, "confirmed_intent": random.choice(SIGNALS)}
        for _ in range(8)
    ]
    tf_lat = []
    for _ in range(500):
        sig = random.choice(SIGNALS)
        t0 = time.perf_counter()
        tf_predict(sig, "morning", {}, history, params)
        tf_lat.append((time.perf_counter() - t0) * 1000)

    result = {
        "rule":        {"p50": pct(0.50, rule_lat),  "p95": pct(0.95, rule_lat),  "p99": pct(0.99, rule_lat)},
        "bayes":       {"p50": pct(0.50, bayes_lat), "p95": pct(0.95, bayes_lat), "p99": pct(0.99, bayes_lat)},
        "transformer": {"p50": pct(0.50, tf_lat),    "p95": pct(0.95, tf_lat),    "p99": pct(0.99, tf_lat)},
        "raw": {"rule": rule_lat[:200], "bayes": bayes_lat[:200], "transformer": tf_lat[:200]},
    }

    max_ms = max(result["rule"]["p99"], result["bayes"]["p99"], result["transformer"]["p99"]) * 1.1
    print(f"  Rule engine:   {hbar('p50', result['rule']['p50'], max_ms)}  p99={result['rule']['p99']:.2f}ms")
    print(f"  Bayesian:      {hbar('p50', result['bayes']['p50'], max_ms)}  p99={result['bayes']['p99']:.2f}ms")
    print(f"  Transformer:   {hbar('p50', result['transformer']['p50'], max_ms)}  p99={result['transformer']['p99']:.2f}ms")

    return result


# ── Benchmark 3: Transformer Parameters & Training Throughput ─────────────────

def bench_transformer() -> dict:
    """Count parameters and measure training throughput."""
    print("\n[3/5] Transformer Parameters & Training Throughput")

    params = _init_params()
    state = _init_adam_state(params)

    total_params = sum(v.size for v in params.values())
    param_table = {k: v.size for k, v in params.items()}

    # Training throughput: time to do 1 adam step per example
    history = [
        {"signal": random.choice(SIGNALS), "time_bucket": "morning",
         "context": {}, "confirmed_intent": random.choice(SIGNALS)}
        for _ in range(8)
    ]

    n_train = 500
    t0 = time.perf_counter()
    for _ in range(n_train):
        sig = random.choice(SIGNALS)
        intent = random.choice(SIGNALS)
        logits, cache = forward(sig, "morning", sample_context(), history, params)
        label = make_soft_label(intent, "correct", None)
        grads = backward(cache, label, params)
        adam_step(params, grads, state)
    train_ms = (time.perf_counter() - t0) * 1000
    per_step_us = (train_ms / n_train) * 1000  # microseconds per step

    # Inference throughput
    n_inf = 2000
    t1 = time.perf_counter()
    for _ in range(n_inf):
        tf_predict(random.choice(SIGNALS), "morning", {}, history, params)
    inf_ms = (time.perf_counter() - t1) * 1000
    inf_per_step_us = (inf_ms / n_inf) * 1000

    result = {
        "total_params": total_params,
        "param_table": param_table,
        "train_us_per_step": per_step_us,
        "inf_us_per_step": inf_per_step_us,
        "train_throughput_eps": 1e6 / per_step_us,
        "inf_throughput_eps": 1e6 / inf_per_step_us,
    }

    print(f"  Total parameters:     {total_params:,}")
    print(f"  Parameter breakdown:")
    for k, v in param_table.items():
        bar_w = int(v / total_params * 40)
        print(f"    {k:<12} {'█' * bar_w} {v:>5} ({v/total_params:.0%})")
    print(f"  Training throughput:  {result['train_throughput_eps']:,.0f} examples/sec  ({per_step_us:.0f}µs/step)")
    print(f"  Inference throughput: {result['inf_throughput_eps']:,.0f} examples/sec  ({inf_per_step_us:.0f}µs/step)")

    return result


# ── Benchmark 4: Soft-label vs Hard-label Training ────────────────────────────

def bench_soft_labels() -> dict:
    """
    Compare loss curves: soft labels (our approach) vs hard labels (standard).
    Run 100 training steps on a fixed patient (pain signal → pain intent).
    Shows faster convergence with soft labels when feedback is partial.
    """
    print("\n[4/5] Soft-label vs Hard-label Convergence")

    history = []

    def run_training(use_soft: bool, n_steps: int = 100) -> list[float]:
        params = _init_params()
        state = _init_adam_state(params)
        losses = []
        for i in range(n_steps):
            # Mix of correct and partial feedback
            feedback = "correct" if i % 3 != 0 else "partial"
            if use_soft:
                label = make_soft_label("pain", feedback, "water")
            else:
                # Hard label: always one-hot on confirmed intent
                label = np.zeros(N_INTENTS, np.float32)
                label[INTENTS.index("pain")] = 1.0

            logits, cache = forward("pain", "morning", {"pain_visible": True}, history, params)
            loss = soft_cross_entropy(logits, label)
            losses.append(loss)
            grads = backward(cache, label, params)
            adam_step(params, grads, state, lr=5e-3)
        return losses

    soft_losses = run_training(use_soft=True)
    hard_losses = run_training(use_soft=False)

    result = {
        "soft_losses": soft_losses,
        "hard_losses": hard_losses,
        "soft_final": soft_losses[-1],
        "hard_final": hard_losses[-1],
        "soft_min": min(soft_losses),
        "hard_min": min(hard_losses),
    }

    print(f"  Soft-label final loss: {result['soft_final']:.4f}  (min: {result['soft_min']:.4f})")
    print(f"  Hard-label final loss: {result['hard_final']:.4f}  (min: {result['hard_min']:.4f})")
    print(f"  Soft labels {'converge faster' if result['soft_min'] < result['hard_min'] else 'similar convergence'}")

    return result


# ── Benchmark 5: Confidence Calibration ──────────────────────────────────────

def bench_calibration() -> dict:
    """
    Bucket predictions by confidence and measure actual accuracy per bucket.
    Well-calibrated: 80% confidence bucket → ~80% actual accuracy.
    """
    print("\n[5/5] Confidence Calibration")

    session = make_db()

    # Build a personalized history (50 feedback rounds)
    for i in range(50):
        sig = random.choice(SIGNALS)
        ctx = sample_context()
        now = datetime.now(timezone.utc) + timedelta(hours=i * 0.3)
        result = suggest(sig, PATIENT_ID, ctx, session, now)
        true_intent = GROUND_TRUTH[sig]
        if result["predictions"]:
            tb = _time_bucket(now)
            top = result["predictions"][0]["intent"]
            fb = "correct" if top == true_intent else "incorrect"
            log_id = -(i + 1)
            log = SignalLog(id=log_id, patient_id=PATIENT_ID, signal=sig, timestamp=now)
            session.add(log)
            session.commit()
            record_feedback(log_id, true_intent, fb, PATIENT_ID, sig, tb, session)

    # Evaluate calibration on 500 probes
    buckets: dict[str, list[int]] = {
        "0-40%": [], "40-60%": [], "60-80%": [], "80-100%": []
    }

    for _ in range(500):
        sig = random.choice(SIGNALS)
        ctx = sample_context()
        now = datetime.now(timezone.utc) + timedelta(hours=1000)
        result = suggest(sig, PATIENT_ID, ctx, session, now)
        if result["fallback"] or not result["predictions"]:
            continue
        pred = result["predictions"][0]
        conf = pred["confidence"]
        correct = int(pred["intent"] == GROUND_TRUTH[sig])

        if conf < 0.40:
            buckets["0-40%"].append(correct)
        elif conf < 0.60:
            buckets["40-60%"].append(correct)
        elif conf < 0.80:
            buckets["60-80%"].append(correct)
        else:
            buckets["80-100%"].append(correct)

    session.close()

    calib = {}
    for bucket, vals in buckets.items():
        calib[bucket] = {"acc": sum(vals)/len(vals) if vals else 0.0, "n": len(vals)}

    result = {"calibration": calib}

    print(f"  {'Confidence':<12} {'Actual Acc':>12} {'N':>6}")
    print(f"  {'-'*32}")
    for bucket, info in calib.items():
        acc = info["acc"]
        n = info["n"]
        bar_s = '█' * int(acc * 20)
        print(f"  {bucket:<12} {bar_s:<20} {acc:>5.1%}  n={n}")

    return result


# ── Plot generation ───────────────────────────────────────────────────────────

def generate_plots(
    conv: dict, lat: dict, tf: dict, soft: dict, calib: dict
) -> list[str]:
    if not HAS_MPL:
        print("\n  [plots] matplotlib not installed — skipping plot generation")
        return []

    saved = []
    plt.rcParams.update({
        "figure.dpi": 150,
        "font.family": "monospace",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.3,
    })

    # ── Plot 1: Accuracy convergence ──────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(8, 4))
    cps = conv["checkpoints"]
    rule_line = [conv["rule_acc"][0]] * len(cps)
    ax.plot(cps, rule_line, "--", color=PALETTE["rule"],
            label=f"Rule engine (baseline {conv['rule_acc'][0]:.0%})", linewidth=1.5)
    ax.plot(cps, conv["bayes_acc"], "-o", color=PALETTE["bayes"], markersize=4,
            label="Bayesian (with feedback)", linewidth=2)
    ax.fill_between(cps, rule_line, conv["bayes_acc"],
                    where=[b > r for b, r in zip(conv["bayes_acc"], rule_line)],
                    alpha=0.12, color=PALETTE["bayes"], label="Personalization gain")
    ax.set_xlabel("Caregiver feedback rounds")
    ax.set_ylabel("Top-1 accuracy")
    ax.set_ylim(0, 1.05)
    ax.set_title("Accuracy Convergence vs Feedback Rounds", fontweight="bold")
    ax.legend(fontsize=8)
    out = PLOTS_DIR / "accuracy_convergence.png"
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    saved.append(str(out))

    # ── Plot 2: Latency percentiles (grouped bar) ─────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 4))
    stages = ["Rule engine", "Bayesian", "Transformer"]
    keys = ["rule", "bayes", "transformer"]
    colors = [PALETTE["rule"], PALETTE["bayes"], PALETTE["transformer"]]
    x = np.arange(len(stages))
    w = 0.25
    for i, (pname, offset) in enumerate(zip(["p50", "p95", "p99"], [-w, 0, w])):
        vals = [lat[k][pname] for k in keys]
        bars = ax.bar(x + offset, vals, w, label=pname, color=colors, alpha=[0.6, 0.8, 1.0][i])
        for b in bars:
            h = b.get_height()
            ax.text(b.get_x() + b.get_width() / 2, h + 0.05,
                    f"{h:.1f}", ha="center", va="bottom", fontsize=7)
    ax.set_xticks(x)
    ax.set_xticklabels(stages)
    ax.set_ylabel("Latency (ms)")
    ax.set_title("Suggestion Latency by Engine Stage", fontweight="bold")
    ax.legend(title="Percentile", fontsize=8)
    out = PLOTS_DIR / "latency_distribution.png"
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    saved.append(str(out))

    # ── Plot 3: Parameter breakdown (pie) ────────────────────────────────────
    fig, ax = plt.subplots(figsize=(6, 4))
    labels = list(tf["param_table"].keys())
    sizes = list(tf["param_table"].values())
    colors_pie = ["#0ea5e9", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#64748b", "#14b8a6"]
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, autopct="%1.0f%%",
        colors=colors_pie[:len(labels)], startangle=140,
        textprops={"fontsize": 8}
    )
    ax.set_title(f"Parameter Distribution ({tf['total_params']:,} total)", fontweight="bold")
    out = PLOTS_DIR / "parameter_breakdown.png"
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    saved.append(str(out))

    # ── Plot 4: Soft-label vs Hard-label loss ─────────────────────────────────
    fig, ax = plt.subplots(figsize=(7, 4))
    steps = list(range(len(soft["soft_losses"])))
    # Smooth with rolling mean
    def smooth(vals, w=5):
        return [statistics.mean(vals[max(0, i-w):i+1]) for i in range(len(vals))]

    ax.plot(steps, smooth(soft["hard_losses"]), color=PALETTE["rule"],
            label="Hard labels (standard cross-entropy)", linewidth=2)
    ax.plot(steps, smooth(soft["soft_losses"]), color=PALETTE["bayes"],
            label="Soft labels (caregiver confidence encoding)", linewidth=2)
    ax.set_xlabel("Training step")
    ax.set_ylabel("Loss")
    ax.set_title("Soft-label vs Hard-label Training Loss", fontweight="bold")
    ax.legend(fontsize=9)
    out = PLOTS_DIR / "soft_vs_hard_loss.png"
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    saved.append(str(out))

    # ── Plot 5: Calibration chart ─────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(6, 4))
    bucket_labels = list(calib["calibration"].keys())
    actual_acc = [calib["calibration"][b]["acc"] for b in bucket_labels]
    midpoints = [0.2, 0.5, 0.7, 0.9]  # center of each confidence bucket
    ax.plot([0, 1], [0, 1], "k--", alpha=0.4, label="Perfect calibration")
    ax.scatter(midpoints, actual_acc, color=PALETTE["transformer"],
               s=80, zorder=5, label="Engine predictions")
    for x, y, lbl in zip(midpoints, actual_acc, bucket_labels):
        ax.annotate(f" {lbl}\n n={calib['calibration'][lbl]['n']}",
                    (x, y), fontsize=7, va="bottom")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Predicted confidence (bucket midpoint)")
    ax.set_ylabel("Actual accuracy")
    ax.set_title("Confidence Calibration", fontweight="bold")
    ax.legend(fontsize=8)
    out = PLOTS_DIR / "calibration.png"
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)
    saved.append(str(out))

    return saved


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("=" * 64)
    print("SignalBridge — Full Benchmark Suite")
    print("=" * 64)

    conv  = bench_accuracy_convergence()
    lat   = bench_latency()
    tf    = bench_transformer()
    soft  = bench_soft_labels()
    calib = bench_calibration()

    saved = generate_plots(conv, lat, tf, soft, calib)

    # Persist results JSON
    results = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accuracy_convergence": {k: v for k, v in conv.items() if k != "raw"},
        "latency_ms": {k: v for k, v in lat.items() if k != "raw"},
        "transformer": {k: v for k, v in tf.items() if k != "raw"},
        "soft_label": {k: v for k, v in soft.items() if "raw" not in k},
        "calibration": calib,
    }
    out_json = PLOTS_DIR / "results.json"
    out_json.write_text(json.dumps(results, indent=2))

    print("\n" + "=" * 64)
    print("Summary")
    print("=" * 64)
    print(f"  Rule engine top-1 accuracy:     {conv['rule_acc'][0]:.1%}")
    print(f"  Bayesian top-1 (after 200):     {conv['bayes_acc'][-1]:.1%}")
    delta = conv['bayes_acc'][-1] - conv['rule_acc'][0]
    print(f"  Personalization delta:           {delta:+.1%}")
    print(f"  Rule engine p99 latency:         {lat['rule']['p99']:.2f}ms")
    print(f"  Bayesian p99 latency:            {lat['bayes']['p99']:.2f}ms")
    print(f"  Transformer inference p99:       {lat['transformer']['p99']:.2f}ms")
    print(f"  Transformer parameters:          {tf['total_params']:,}")
    print(f"  Training throughput:             {tf['train_throughput_eps']:,.0f} examples/sec")
    print(f"  Inference throughput:            {tf['inf_throughput_eps']:,.0f} examples/sec")
    if saved:
        print(f"\n  Plots saved to: benchmarks/plots/")
        for p in saved:
            print(f"    {Path(p).name}")
    print(f"\n  Results: benchmarks/plots/results.json")
    print("=" * 64)


if __name__ == "__main__":
    main()
