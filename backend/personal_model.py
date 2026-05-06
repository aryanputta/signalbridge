"""
PersonalModel — online learning wrapper around the SignalBridge numpy transformer.

Lifecycle:
  Stage 0 (<20 confirmed): rule engine only, no model
  Stage 1 (20-49 confirmed): Bayesian personalization only
  Stage 2 (>=50 confirmed): Transformer blended with Bayesian engine

Training strategy: full replay.
  After each new feedback, run one epoch over ALL past examples.
  With 50-200 examples, this takes <10ms on CPU (pure numpy, no framework).

Storage:
  ./models/patient_{id}/params.npz         — model weights (numpy arrays)
  ./models/patient_{id}/adam_state.npz     — Adam optimizer state
  ./models/patient_{id}/replay_buffer.json — all training examples
  All files stay local. Nothing is uploaded.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np

from mini_transformer import (
    _init_params,
    _init_adam_state,
    forward,
    backward,
    adam_step,
    predict as transformer_predict,
    make_soft_label,
    soft_cross_entropy,
    N_INTENTS,
    INTENTS,
)

STAGE_THRESHOLD = 50
LEARNING_RATE = 3e-3
MODELS_DIR = Path("./models")


@dataclass
class TrainingExample:
    signal: str
    time_bucket: str
    context: dict            # raw caregiver context dict
    confirmed_intent: str
    feedback: str            # "correct" | "partial" | "incorrect"
    suggested_intent: str
    history: list[dict]


class PersonalModel:
    """
    Per-patient online Transformer with full-replay training.

    The model is created lazily once the patient reaches STAGE_THRESHOLD
    confirmed interactions. Before that this class is a no-op and the
    caller falls back to the Bayesian suggestion engine.
    """

    def __init__(self, patient_id: int):
        self.patient_id = patient_id
        self.model_dir = MODELS_DIR / f"patient_{patient_id}"
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self._params: Optional[dict[str, np.ndarray]] = None
        self._adam_state: Optional[dict] = None
        self._replay: list[TrainingExample] = []
        self._confirmed_count = 0

        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def stage(self) -> int:
        if self._confirmed_count < 20:
            return 0
        if self._confirmed_count < STAGE_THRESHOLD:
            return 1
        return 2

    def add_and_train(
        self,
        signal: str,
        time_bucket: str,
        context: dict,
        confirmed_intent: str,
        feedback: str,
        suggested_intent: str,
        history: list[dict],
    ) -> None:
        """Record a new confirmed example and retrain on all history."""
        example = TrainingExample(
            signal=signal,
            time_bucket=time_bucket,
            context=context,
            confirmed_intent=confirmed_intent,
            feedback=feedback,
            suggested_intent=suggested_intent,
            history=history,
        )
        self._replay.append(example)
        self._confirmed_count = len(self._replay)
        self._save_replay()

        if self.stage == 2:
            self._ensure_model()
            self._train_one_epoch()
            self._save_model()

    def predict(
        self,
        signal: str,
        time_bucket: str,
        context: dict,
        history: list[dict],
    ) -> Optional[dict[str, float]]:
        """
        Returns a probability distribution over intents, or None if stage < 2.
        Caller blends this with the Bayesian engine output.
        """
        if self.stage < 2 or self._params is None:
            return None
        return transformer_predict(signal, time_bucket, context, history, self._params)

    # ── Training ──────────────────────────────────────────────────────────────

    def _ensure_model(self) -> None:
        if self._params is None:
            self._params = _init_params()
            self._adam_state = _init_adam_state(self._params)

    def _train_one_epoch(self) -> float:
        assert self._params is not None and self._adam_state is not None
        total_loss = 0.0

        for ex in self._replay:
            logits, cache = forward(
                ex.signal, ex.time_bucket, ex.context, ex.history, self._params
            )
            soft_label = make_soft_label(
                ex.confirmed_intent, ex.feedback, ex.suggested_intent
            )
            total_loss += soft_cross_entropy(logits, soft_label)
            grads = backward(cache, soft_label, self._params)
            adam_step(self._params, grads, self._adam_state, lr=LEARNING_RATE)

        return total_loss / max(len(self._replay), 1)

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save_model(self) -> None:
        if self._params is None or self._adam_state is None:
            return

        np.savez(str(self.model_dir / "params.npz"), **self._params)

        adam_flat: dict[str, np.ndarray] = {
            "t": np.array([self._adam_state["t"]], dtype=np.int64)
        }
        for k, v in self._adam_state["m"].items():
            adam_flat[f"m_{k}"] = v
        for k, v in self._adam_state["v"].items():
            adam_flat[f"v_{k}"] = v
        np.savez(str(self.model_dir / "adam_state.npz"), **adam_flat)

    def _save_replay(self) -> None:
        data = [
            {
                "signal": ex.signal,
                "time_bucket": ex.time_bucket,
                "context": ex.context,
                "confirmed_intent": ex.confirmed_intent,
                "feedback": ex.feedback,
                "suggested_intent": ex.suggested_intent,
                "history": ex.history,
            }
            for ex in self._replay
        ]
        (self.model_dir / "replay_buffer.json").write_text(json.dumps(data))

    def _load(self) -> None:
        replay_path = self.model_dir / "replay_buffer.json"
        if replay_path.exists():
            raw = json.loads(replay_path.read_text())
            self._replay = [
                TrainingExample(
                    signal=r["signal"],
                    time_bucket=r["time_bucket"],
                    context=r.get("context", {}),
                    confirmed_intent=r["confirmed_intent"],
                    feedback=r["feedback"],
                    suggested_intent=r.get("suggested_intent", "unknown"),
                    history=r.get("history", []),
                )
                for r in raw
            ]
            self._confirmed_count = len(self._replay)

        params_path = self.model_dir / "params.npz"
        adam_path = self.model_dir / "adam_state.npz"
        if params_path.exists() and self.stage == 2:
            self._ensure_model()
            loaded = np.load(str(params_path))
            for k in self._params:
                if k in loaded:
                    self._params[k] = loaded[k].copy()

            if adam_path.exists():
                adam_loaded = np.load(str(adam_path))
                self._adam_state["t"] = int(adam_loaded["t"][0])
                for k in self._params:
                    if f"m_{k}" in adam_loaded:
                        self._adam_state["m"][k] = adam_loaded[f"m_{k}"].copy()
                    if f"v_{k}" in adam_loaded:
                        self._adam_state["v"][k] = adam_loaded[f"v_{k}"].copy()


# ── Module-level cache: one PersonalModel instance per patient ────────────────

_model_cache: dict[int, PersonalModel] = {}


def get_personal_model(patient_id: int) -> PersonalModel:
    if patient_id not in _model_cache:
        _model_cache[patient_id] = PersonalModel(patient_id)
    return _model_cache[patient_id]
