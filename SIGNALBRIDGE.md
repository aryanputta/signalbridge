# SignalBridge

## One Line

An AI-assisted communication layer for people who cannot fully express themselves through speech, starting with family caregivers and expanding toward personalized assistive communication for homes, hospitals, and long-term care.

---

## The Non-Obvious Insight

Most people think the problem is that the person cannot produce enough signal.

That is wrong.

The person is communicating constantly, through gesture, repetition, timing, sound, posture, and behavior. The signal exists. The bottleneck is the decoder.

**Communication failure in this context is not a production failure. It is a decoding failure.**

Every family builds a mental model of what their loved one's signals mean. That knowledge is real, hard-won, and deeply personal. And it evaporates when a caregiving shift ends.

SignalBridge is not a device for the person. It is a structured decoder for the caregiver. It turns ephemeral caregiving knowledge into a transferable, improving, personalized communication profile.

---

## What Most People Misunderstand

1. **They think this is an accessibility problem.** Accessibility is about producing output. This is about decoding input. Different problem, different solution.

2. **They think it requires more data.** It requires better structure on one person's data, not scale.

3. **They think the solution is more sophisticated AI.** The solution is a better feedback mechanism. The AI makes the feedback loop useful. The feedback loop is the product.

4. **They think the person cannot communicate.** The person is already communicating. The system around them has lost its ability to decode.

5. **They think this is a clinical problem.** The most important caregiving moments happen at home, not in a hospital, with family members who have no clinical training.

---

## Founder Insight

This project comes from a specific moment: trying to understand what my mom needed after disability changed how she could communicate.

Not from a market map. Not from user interviews. From sitting with someone I care about, making a third consecutive guess about what they needed, and realizing that I had learned something in six weeks that no tool had helped me capture or transfer.

That moment is the founding insight. The product is the structure that moment was missing.

---

## Contrarian Belief

> The highest-impact communication technology of the next decade will not be for people who want to write faster. It will be for people who have lost part of their ability to communicate and the people trying to understand them.

AI should not only help people produce more. It should also help people be understood when they cannot fully speak.

---

## The Startup Narrative

**The pain:**

Millions of families care for loved ones who cannot communicate clearly through speech. After stroke, neurological injury, illness, or aging, the person is still present and still has needs. But the mechanism has changed.

The family becomes the interpreter. They build a model of what each signal means, through weeks of trial and error, under stress. That model lives only in their head. When a shift ends, it resets. Every new caregiver starts from zero. Every missed signal costs something.

**Why now:**

Edge compute, local-first storage, lightweight ML, and fast web tooling have made it possible to build private assistive tools that learn from one specific person over time, without cloud dependency, clinical approval, or expensive hardware.

**Why I am the right person:**

Lived experience with the problem. Technical depth to build fast. Product instinct from a real pain point. No distance between the problem and the builder.

**What the first product does:**

A caregiver taps a signal. The system suggests the most likely intent, ranked by what has been confirmed before for this person. The caregiver confirms or corrects. The system records the outcome. After 30 interactions, the suggestions shift toward what this specific person actually needs.

**What the long-term platform becomes:**

A portable communication profile that travels with the person. Legible to any new caregiver in minutes. Useful in homes, care facilities, hospitals, and therapy sessions. Not owned by an institution. Owned by the family.

---

## MVP Scope

**The one loop that must work:**

Signal logged → context captured → intent suggested → caregiver confirms → system learns → next suggestion is better.

**What is in the MVP:**

- 16 predefined signals (pain, water, food, bathroom, tired, uncomfortable, yes, no, help, reposition, medication, temperature, cold, hot, anxiety, confused)
- Caregiver context panel (pain visible, hours since meal, hours since medication, low sleep, no movement, room temperature, caregiver note)
- Ranked intent suggestions with plain-language explanations
- Three-button feedback (correct, partial, incorrect)
- Custom intent input when the top suggestion is wrong
- Pattern dashboard with accuracy metrics and time-of-day breakdown
- Markdown export for caregiver handoff
- Local storage only, no account required

**What is explicitly not in the MVP:**

- Multi-patient profiles (one person per device)
- Custom signal creation
- Multi-device sync
- Audio or video capture
- Alert or notification system
- User accounts or passwords
- Clinical validation claims

---

## Technical Architecture

### Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Backend | Python FastAPI |
| Storage | SQLite via SQLModel |
| Benchmark | Python script, in-memory SQLite |

### Data Model

**SignalLog** — one row per caregiver interaction
- signal, timestamp, patient_id
- context_json (context flags at time of signal)
- suggested_intent, confidence, urgency, explanation
- confirmed_intent, feedback ("correct", "partial", "incorrect")
- caregiver_note, session_id

**PatternSummary** — one row per (patient, signal, confirmed_intent) triple
- count (how many times this signal was confirmed as this intent)
- time_buckets (JSON: how often this confirmation occurred in each time window)
- last_seen

**PatientProfile** — name and notes only. No medical identifiers.

### Suggestion Engine

Three-stage scoring:

1. **Prior**: Signal-specific prior distribution over intents (e.g., "pain" signal → pain 70%, uncomfortable 15%, help 10%)
2. **Time modifier**: Multiplicative adjustment based on time of day (morning: medication +40%, food +30%; night: pain +40%, bathroom +30%)
3. **Context modifier**: Additional multipliers based on caregiver flags (pain visible → pain ×1.5; no movement → reposition ×1.5; hours since meal > 4 → food ×1.3)
4. **History**: Bayesian combination with confirmed history. If signal was confirmed as water 4 times before, likelihood of water is boosted proportionally to its share of all confirmations for this signal and patient.

Every suggestion includes a plain-language explanation. If top confidence is below 0.35, the system returns a fallback message instead of a low-confidence ranking.

---

## Privacy Design

**What is stored locally:**
- Signal logs with timestamps
- Caregiver context entries
- Suggestion history and confidence scores
- Confirmed intents from feedback
- Pattern summaries
- Patient name and notes only

**What is never stored:**
- Health records
- Biometric data
- Audio or video
- Location
- Device identifiers
- Account information

**What is never uploaded:**
- Nothing. The default is zero network calls for patient data.
- The suggestion engine runs entirely on the local machine.
- Export produces a file the caregiver controls. Nothing is sent anywhere by the system.

---

## AI Architecture: Honest Evolution Path

### Stage 1: Transparent rule engine (MVP, now)

Applies weighted priors by signal, adjusted for time of day and context flags. Bayesian combination with confirmed history counts. Every prediction is fully explainable in plain language.

**Proves:** The feedback loop is useful. Caregivers engage.

**Risk reduced:** Trust. No black box.

### Stage 2: Frequency-weighted personalization (after 20+ confirmed interactions)

Likelihood estimate shifts from zero (no history) to empirical (observed confirmations). Suggestions become patient-specific, not generic.

**Proves:** One patient's history produces measurably different outputs than another patient's history.

**Risk reduced:** Generality. Two patients with the same signal get different suggestions.

### Stage 3: Context-conditioned Naive Bayes (after 60+ confirmed interactions)

Conditions on context buckets as well as signal. Trains a small classifier locally on the patient's own history. No cloud. No shared training data. Runs on device.

**Proves:** Context is a real modifier. The same signal at 2am after poor sleep predicts different intents than at noon after a meal.

**Risk reduced:** Context blindness.

### Stage 4: On-device lightweight model (future)

Replaces Naive Bayes with a small MLP trained on full patient history. Runs in browser via ONNX or local Python. Model under 10MB. Personalized to one patient, never shared.

**Proves:** Accumulated history supports a learned model that outperforms the rule-based baseline.

**Risk reduced:** Accuracy ceiling.

### Stage 5: Multimodal (not now)

Wearable heart rate variability for pain detection. Camera-based gesture recognition. Voice tone analysis. Requires full privacy redesign, user consent framework, hardware layer.

---

## Success Metrics with Numbers

### Latency targets
- Suggestion engine: under 50ms p99
- Full round trip (tap to render): under 300ms p99
- Feedback submission: under 100ms p50

### Accuracy targets
| Metric | Baseline | After 30 interactions | After 100 interactions |
|---|---|---|---|
| Top-1 accuracy | 40-55% | 60%+ | 70%+ |
| Top-3 match rate | 75%+ | 85%+ | 88%+ |
| Fallback rate | 15-20% | 12% | <10% |
| Correction rate | 40-60% | <30% | <20% |

### Personalization delta (the key number)
- Accuracy in interactions 50-60 minus accuracy in interactions 1-10
- Target: +15 percentage points minimum
- Under +10 indicates the feedback loop is not contributing enough
- This is the headline metric that proves the product hypothesis

---

## Technical Moat

**The moat is not the algorithm. The moat is the accumulated data structure.**

| Component | Why it cannot be replicated |
|---|---|
| Signal history | Hundreds of confirmed signal-intent pairs per patient, generated only by using the product |
| Feedback labels | Supervised training examples produced as a side effect of caregiving, not data collection |
| Context memory | Person-specific correlations between context and intent that only appear after months of use |
| Calibrated confidence | Confidence scores calibrated to one person's real outcomes, not population priors |
| Local storage | Data stays with the family. A competitor cannot access it, copy it, or train on it. |
| Switching cost | After six months of use, switching means starting from zero. Pure data stickiness, no artificial lock-in. |

---

## Product Taste

**What creates real user value:**

- Instant suggestion on signal tap (under 300ms feels like the system is paying attention)
- Plain-language explanation, not a confidence score
- Three-button feedback: one tap, done
- Caregiver note field, which becomes the handoff mechanism between shifts
- Pattern dashboard showing that the system is actually improving over time

**What does not belong in the MVP:**

- Animations celebrating correct predictions (wrong emotional register for caregiving)
- Onboarding tours (if the UI needs explanation, the UI is wrong)
- Multiple patient profiles (prove the loop works for one person first)
- Color themes or customization (the accessible high-contrast design is the design)
- Alert or notification system (the caregiver comes to the app; the app does not interrupt them)

**How the first version should feel:**

Fast. Tap and get something useful within one second.

Calm. No aggressive colors, no alert sounds, no flashing. The environment is already stressful. The app should feel like a quiet presence.

Private. The first screen says, in plain language, that everything stays on this device. Not buried in settings.

Useful in the moment. The test: if someone is trying to understand what their loved one needs at 2am, does this make it faster?

---

## Data Strategy

**Every field has a defined use. Nothing is collected speculatively.**

| Field | Why it is collected | Use |
|---|---|---|
| Signal | Input variable | Inference |
| Timestamp | Primary context variable | Time-of-day personalization |
| Pain visible | Modifier | Boosts pain and help priors |
| Hours since meal | Modifier | Boosts food and water priors when > 4 hours |
| Hours since medication | Modifier | Boosts medication prior when > 6 hours |
| Low sleep | Modifier | Boosts tired and pain priors |
| No movement | Modifier | Boosts reposition prior |
| Room temperature | Modifier | Boosts cold or hot priors |
| Suggested intent | Model output | Accuracy measurement |
| Confidence | Model output | Fallback threshold, accuracy tracking |
| Feedback | Label | Personalization input |
| Confirmed intent | Ground truth | PatternSummary update, future model training |
| Caregiver note | Free text | Export only, not used for inference |
| Session ID | Grouping | Session summary only |

**What is never collected:** Audio, video, biometrics, location, device ID, health records, insurance information.

---

## Benchmark Design

```
Phase 1: Baseline accuracy (n=50, no personalization)
Phase 2: Feedback training (n=100, with caregiver corrections at 15% noise)
Phase 3: Post-personalization accuracy (n=50)

Report:
  - Top-1 accuracy (phase 1 vs phase 3)
  - Top-3 match rate (phase 1 vs phase 3)
  - Fallback rate (phase 1 vs phase 3)
  - Personalization delta
  - Latency p50, p95, p99

Targets:
  - Baseline top-1 >= 40%
  - Post-training top-1 >= 60%
  - Baseline top-3 >= 75%
  - Personalization delta >= +10 percentage points
  - p99 latency < 50ms
```

Run with: `cd signalbridge/backend && python ../benchmarks/bench_suggestions.py`

---

## Getting Started

```bash
# Install dependencies
make install

# Terminal 1: start backend
make backend

# Terminal 2: start frontend
make frontend

# Open http://localhost:5173

# Run benchmark
make bench
```

---

## File Structure

```
signalbridge/
├── backend/
│   ├── main.py               FastAPI app, CORS, startup
│   ├── models.py             SQLModel tables: PatientProfile, SignalLog, PatternSummary
│   ├── database.py           SQLite engine and session
│   ├── suggestion_engine.py  Rule-based engine with Bayesian personalization
│   └── routers/
│       ├── signals.py        POST /signals/suggest, POST /signals/feedback, GET /signals/history
│       ├── patients.py       POST /patients, GET /patients, GET /patients/{id}
│       └── patterns.py       GET /patterns/{id}/summary, GET /patterns/{id}/export
├── frontend/
│   └── src/
│       ├── types.ts           All TypeScript interfaces and signal definitions
│       ├── lib/api.ts         Typed API client
│       ├── lib/session.ts     Session and patient ID persistence
│       ├── components/
│       │   ├── SignalGrid.tsx         16-signal accessible tap grid
│       │   ├── ContextPanel.tsx       Caregiver context toggles and inputs
│       │   ├── SuggestionCard.tsx     Ranked suggestions with feedback buttons
│       │   └── PatternDashboard.tsx   Accuracy metrics and pattern charts
│       ├── pages/
│       │   ├── SetupPage.tsx          First-run patient setup
│       │   ├── MainPage.tsx           Core caregiving loop
│       │   └── DashboardPage.tsx      Pattern summary and export
│       └── App.tsx                    Tab routing: Signals / Patterns
└── benchmarks/
    └── bench_suggestions.py   Latency and accuracy benchmark
```

---

## What This Is Not

- Not a diagnostic tool
- Not a replacement for doctors, nurses, or speech therapists
- Not claiming clinical validation
- Not using private medical data
- Not a surveillance product
- Not trying to solve every disability communication case at once

This is a focused MVP for caregiver-assisted communication support, designed to prove one thing: a simple personalized system can become more useful over time by learning from caregiver feedback.

---

*Built by Aryan Putta. Local-first. Private by default. No account required.*
