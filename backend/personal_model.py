"""
PersonalModel — online learning wrapper around SignalTransformer.

Lifecycle:
  Stage 0 (<20 confirmed): rule engine only, no model
  Stage 1 (20-49 confirmed): Bayesian personalization only
  Stage 2 (>=50 confirmed): Transformer blended with Bayesian engine

Training strategy: full replay.
  After each new feedback, run one epoch over ALL past examples.
  With 50-200 examples, this takes <80ms on CPU and avoids catastrophic
  forgetting without needing a separate memory consolidation mechanism.

Storage:
  ./models/patient_{id}/model.pt           — model weights + optimizer state
  ./models/patient_{id}/replay_buffer.json — all training examples
  Both stay local. Nothing is uploaded.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import torch
import torch.optim as optim

from mini_transformer import (
    SignalTransformer,
    make_soft_label,
    soft_cross_entropy,
    encode_context_flags,
    signal_to_idx,
    intent_to_idx,
    time_to_idx,
    INTENT_PAD_IDX,
    SIGNAL_PAD_IDX,
    SEQ_LEN,
    N_CONTEXT,
    N_INTENTS,
    INTENTS,
)

STAGE_THRESHOLD = 50  # confirmed examples before Transformer activates
LEARNING_RATE = 3e-3
MODELS_DIR = Path("./models")


@dataclass
class TrainingExample:
    signal: str
    time_bucket: str
    context: list[float]       # length N_CONTEXT
    confirmed_intent: str
    feedback: str              # "correct" | "partial" | "incorrect"
    suggested_intent: str      # what the engine suggested at the time
    history: list[dict]        # list of prior {signal, time_bucket, context, confirmed_intent}


class PersonalModel:
    """
    Per-patient online Transformer with full-replay training.

    The model is created lazily once the patient reaches STAGE_THRESHOLD
    confirmed interactions. Before that, this class is a no-op and the
    caller falls back to the Bayesian suggestion engine.
    """

    def __init__(self, patient_id: int):
        self.patient_id = patient_id
        self.model_dir = MODELS_DIR / f"patient_{patient_id}"
        self.model_dir.mkdir(parents=True, exist_ok=True)

        self._model: Optional[SignalTransformer] = None
        self._optimizer: Optional[optim.Adam] = None
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
            context=encode_context_flags(context),
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
        if self.stage < 2 or self._model is None:
            return None

        self._model.eval()
        with torch.no_grad():
            batch = self._build_batch([(signal, time_bucket, context, history)])
            logits = self._model(**batch)
            probs = torch.softmax(logits[0], dim=-1).tolist()

        return {INTENTS[i]: probs[i] for i in range(N_INTENTS)}

    # ── Training ──────────────────────────────────────────────────────────────

    def _ensure_model(self) -> None:
        if self._model is None:
            self._model = SignalTransformer(d_model=64, n_heads=4, n_layers=2)
            self._optimizer = optim.Adam(
                self._model.parameters(), lr=LEARNING_RATE, weight_decay=1e-4
            )

    def _train_one_epoch(self) -> float:
        assert self._model is not None and self._optimizer is not None
        self._model.train()
        total_loss = 0.0

        for ex in self._replay:
            self._optimizer.zero_grad()

            batch = self._build_batch(
                [(ex.signal, ex.time_bucket, {
                    "pain_visible": ex.context[0] > 0.5,
                    "low_sleep": ex.context[1] > 0.5,
                    "no_movement": ex.context[2] > 0.5,
                    "room_temp": "cold" if ex.context[3] > 0.5 else ("hot" if ex.context[4] > 0.5 else None),
                    "hours_since_meal": 5.0 if ex.context[5] > 0.5 else None,
                    "hours_since_medication": 7.0 if ex.context[6] > 0.5 else None,
                }, ex.history)]
            )
            logits = self._model(**batch)

            soft_label = make_soft_label(
                ex.confirmed_intent, ex.feedback, ex.suggested_intent
            ).unsqueeze(0)

            loss = soft_cross_entropy(logits, soft_label)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(self._model.parameters(), max_norm=1.0)
            self._optimizer.step()
            total_loss += loss.item()

        return total_loss / max(len(self._replay), 1)

    # ── Batch construction ────────────────────────────────────────────────────

    def _build_batch(
        self,
        items: list[tuple],  # [(signal, time_bucket, context_dict, history)]
    ) -> dict[str, torch.Tensor]:
        b_signals, b_times, b_contexts, b_intents = [], [], [], []

        for signal, time_bucket, context_dict, history in items:
            signals, times, contexts, intents = self._encode_sequence(
                signal, time_bucket, context_dict, history
            )
            b_signals.append(signals)
            b_times.append(times)
            b_contexts.append(contexts)
            b_intents.append(intents)

        return {
            "signal_idxs": torch.tensor(b_signals, dtype=torch.long),
            "time_idxs": torch.tensor(b_times, dtype=torch.long),
            "contexts": torch.tensor(b_contexts, dtype=torch.float),
            "intent_idxs": torch.tensor(b_intents, dtype=torch.long),
        }

    def _encode_sequence(
        self,
        current_signal: str,
        current_time: str,
        current_context: dict,
        history: list[dict],
    ) -> tuple[list, list, list, list]:
        """
        Build a (SEQ_LEN,) sequence of encoded steps.
        History is padded or truncated to SEQ_LEN-1 steps.
        The last step is always the current signal (intent unknown → PAD).
        """
        hist = history[-(SEQ_LEN - 1):]  # take most recent history slots
        pad_len = (SEQ_LEN - 1) - len(hist)

        signals = [SIGNAL_PAD_IDX] * pad_len
        times = [0] * pad_len
        contexts = [[0.0] * N_CONTEXT] * pad_len
        intents = [INTENT_PAD_IDX] * pad_len

        for h in hist:
            signals.append(signal_to_idx(h.get("signal", "")))
            times.append(time_to_idx(h.get("time_bucket", "morning")))
            ctx = h.get("context", {})
            contexts.append(encode_context_flags(ctx) if isinstance(ctx, dict) else [0.0] * N_CONTEXT)
            intents.append(intent_to_idx(h.get("confirmed_intent", "unknown")))

        # Current step
        signals.append(signal_to_idx(current_signal))
        times.append(time_to_idx(current_time))
        contexts.append(encode_context_flags(current_context))
        intents.append(INTENT_PAD_IDX)

        return signals, times, contexts, intents

    # ── Persistence ───────────────────────────────────────────────────────────

    def _save_model(self) -> None:
        if self._model is None or self._optimizer is None:
            return
        torch.save(
            {
                "model_state": self._model.state_dict(),
                "optimizer_state": self._optimizer.state_dict(),
                "confirmed_count": self._confirmed_count,
            },
            self.model_dir / "model.pt",
        )

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
        replay_path = self.model_dir / "replay_buffer.json"
        replay_path.write_text(json.dumps(data))

    def _load(self) -> None:
        replay_path = self.model_dir / "replay_buffer.json"
        if replay_path.exists():
            raw = json.loads(replay_path.read_text())
            self._replay = [
                TrainingExample(
                    signal=r["signal"],
                    time_bucket=r["time_bucket"],
                    context=r["context"],
                    confirmed_intent=r["confirmed_intent"],
                    feedback=r["feedback"],
                    suggested_intent=r.get("suggested_intent", "unknown"),
                    history=r.get("history", []),
                )
                for r in raw
            ]
            self._confirmed_count = len(self._replay)

        model_path = self.model_dir / "model.pt"
        if model_path.exists() and self.stage == 2:
            self._ensure_model()
            checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
            self._model.load_state_dict(checkpoint["model_state"])
            self._optimizer.load_state_dict(checkpoint["optimizer_state"])
            self._confirmed_count = checkpoint.get("confirmed_count", self._confirmed_count)


# ── Module-level cache: one PersonalModel instance per patient ────────────────

_model_cache: dict[int, PersonalModel] = {}


def get_personal_model(patient_id: int) -> PersonalModel:
    if patient_id not in _model_cache:
        _model_cache[patient_id] = PersonalModel(patient_id)
    return _model_cache[patient_id]
