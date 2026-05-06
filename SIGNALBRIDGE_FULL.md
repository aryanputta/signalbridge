# SignalBridge
### AI-Assisted Communication for People Who Cannot Fully Speak
**Aryan Putta | aryansputta@gmail.com | github.com/aryanputta/signalbridge**

---

## Table of Contents

1. The Founding Moment
2. The Problem
3. The Non-Obvious Insight
4. What Most People Misunderstand
5. Contrarian Belief
6. The Startup Narrative
7. Why Now
8. Why I Am the Right Person
9. Product Vision
10. MVP Scope and Focus
11. Product Taste
12. Technical Architecture
13. Suggestion Engine Design
14. AI Architecture: Honest Evolution Path
15. Privacy Design
16. Data Strategy
17. Technical Moat
18. Success Metrics
19. Benchmark Design
20. Senior Engineering Constraints
21. Getting Started
22. File Structure
23. What This Is Not

---

## 1. The Founding Moment

This project starts with a specific moment.

Not a market map. Not a user interview. Not a pitch deck.

A moment of sitting with my mom after disability changed how she could communicate, making a third consecutive guess about what she needed, and realizing that I had learned something in six weeks that no tool had helped me capture, structure, or transfer to anyone else.

The knowledge existed. It was real. It was hard-won. And it was invisible to every system around us.

That moment is the founding insight. The product is the structure that moment was missing.

---

## 2. The Problem

Millions of families and caregivers support loved ones who cannot communicate clearly through speech. This happens after stroke, disability, neurological injury, illness, aging, or physical decline.

In most cases, the person is still communicating. They use gestures, repeated sounds, facial expressions, body movements, routine-based cues, and behavioral patterns. The signal exists.

The problem is that these signals are highly personal.

The same signal may mean different things depending on:
- Time of day
- Hours since the last meal
- Medication timing
- Pain or discomfort level
- Sleep quality
- Room temperature
- Emotional state
- Which caregiver is present
- Prior repeated patterns
- The specific person

Most families do not have a structured way to track this. The result is slower responses, caregiver stress, missed patterns, repeated guessing, and loss of dignity for the person trying to communicate.

And every time a caregiving shift ends, the knowledge resets. The next caregiver starts from zero.

---

## 3. The Non-Obvious Insight

Most people who hear this problem immediately think about building tools for the person to produce more output. AAC devices, eye-tracking keyboards, speech synthesis, symbol boards. Better tools for pushing signal outward.

This is the wrong frame.

The person has not stopped communicating. They are communicating constantly.

**The bottleneck is the decoder, not the encoder.**

Communication failure in this context is not a production failure. It is a decoding failure.

SignalBridge inverts the standard frame entirely. Instead of building a better microphone for the person, it builds a better interpreter for the caregiver.

The product is not a device for the person. It is a structured decoder for the caregiver — one that learns from repeated caregiving moments, accumulates implicit knowledge that currently evaporates, and makes that knowledge transferable.

Every confirmed signal-intent pair is a learning moment that currently lives only in one person's head. SignalBridge gives that knowledge a structure, a memory, and a way to move.

**The wedge:** caregiving labor, which families already perform, becomes training data as a side effect. The system gets smarter as caregivers do their jobs. No extra effort required.

---

## 4. What Most People Misunderstand

**Misunderstanding 1: This is an accessibility problem.**

Accessibility is about helping someone produce output. SignalBridge is about decoding input that already exists. These are categorically different problems. Almost every existing assistive communication tool is built for the sender side. This is the first product built primarily for the receiver side.

**Misunderstanding 2: This requires a large dataset.**

The dataset required is not large. It is structured. Fifty confirmed signal-intent pairs from one specific person, with context, are enough to produce measurably better suggestions. The insight is personalization depth, not data scale.

**Misunderstanding 3: The solution is more sophisticated AI.**

The solution is a better feedback mechanism. The AI layer makes the feedback loop feel useful enough to engage with. But the feedback loop itself is the product. If caregivers stop providing feedback, the system stops improving. The AI is the presentation layer. The loop is the engine.

**Misunderstanding 4: The person cannot communicate.**

This is the most damaging misunderstanding of all. The person is not silent. They are generating signal constantly. The problem is that the decoder — the caregiver, the shift nurse, the new family member — does not have access to the interpretive model that took months to build. The person has not failed to send. The system around them has failed to receive.

**Misunderstanding 5: This is a clinical problem.**

Most innovation in this space targets clinical settings — hospitals, speech therapy clinics, formal AAC evaluations. But the most important caregiving moments happen at home, at 2am, with a family member who has no clinical training and no manual to reference. The clinical market is important. But the home market is where the real pain lives and where almost nothing exists.

---

## 5. Contrarian Belief

The current trajectory of AI communication is almost entirely oriented toward productivity for people who already communicate fluently. Faster writing, better search, sharper emails, cleaner summaries.

The implied assumption is that the marginal value of AI is at the high-functioning end of human communication.

This is wrong.

The highest leverage point is at the other end of the distribution — people whose ability to communicate has been disrupted by illness, injury, aging, or neurological change. These people are not on the productivity curve. They are on a different curve entirely, where the stakes of a missed signal are not a slower email, but physical pain, missed medication, a bathroom accident, or loss of dignity.

**AI has become sophisticated enough to recognize patterns, infer intent from incomplete signals, and adapt to feedback over time. These are exactly the capabilities needed to build a better decoder for non-standard communication.**

Most AI companies think the future is about giving people a better voice. SignalBridge is built on the belief that the future is also about giving people a better listener.

The most meaningful technology does not always start in a lab or a pitch deck. Sometimes it starts at home, when a normal interaction becomes hard and nobody has built the right tool yet.

---

## 6. The Startup Narrative

**The pain that exists today:**

Every day, millions of families are caring for loved ones who cannot fully communicate through speech. The person is still present. They still have needs, discomfort, preferences, and fear. But the mechanism for expressing those things has changed.

The family becomes the interpreter. Through weeks of trial and error, they build a mental model of what a repeated sound means, what a specific gesture signals, what the 2am restlessness usually indicates. That knowledge is real and hard-won.

And it lives only in one person's head.

When a shift ends, or a caregiver gets sick, or a new family member takes over, that knowledge resets. The next person starts from zero. The same guessing process begins again. The same signals are misread again. The same discomfort goes unresolved again.

This is not a failure of technology. It is a failure of structure. The knowledge exists. It just has nowhere to go.

**The wedge:**

The first product is not a full medical communication system. It is a private, local-first caregiver tool that helps families turn repeated signals into likely needs over time.

Start with one caregiver and one loved one. Start with simple signals. Start with repeated patterns. Start with the moments where guessing creates stress.

If the loop works there, it can expand into more advanced assistive communication.

**The loop:**

Signal entered → context captured → intent suggested → caregiver confirms → system learns → pattern summary improves.

This loop is the product. The goal is not to add features. The goal is to make this loop feel useful, fast, and trustworthy.

---

## 7. Why Now

The timing is different now for three reasons.

**Technology access:** Low-cost devices, local-first storage, edge AI, lightweight models, and fast web interfaces make it possible to build private assistive tools that learn from one specific person over time. A few years ago, this required cloud infrastructure and enterprise contracts.

**Trust landscape:** Families are no longer unfamiliar with AI making daily suggestions. The question is not whether people will trust AI suggestions — it is whether they will trust a system that is private, explainable, and locally controlled. For caregiving contexts, the answer is yes, because the alternative is no system at all.

**Market gap:** Most assistive communication tools are either too clinical (formal AAC devices requiring evaluation and insurance), too expensive, too generic (not personalized to the individual), or too disconnected from daily home care. The intersection of private, local, fast, and personally adaptive is empty.

---

## 8. Why I Am the Right Person

This project comes from lived experience, not a market map.

That matters because the smallest details of this problem are easy to miss from the outside. The emotional pressure, repeated guessing, caregiver fatigue, desire to preserve dignity, and specific texture of the 2am interaction are not abstract.

The unfair advantage is the combination of:
- Personal exposure to the problem at the ground level
- Technical interest in AI systems and inference optimization
- Ability to build fast prototypes with real architecture
- Concern for privacy and safety as first-order constraints
- Product instinct around real user pain
- Willingness to start before the solution is obvious

The people building in this space are mostly medical device companies locked in clinical validation cycles, large platforms too generic to care about this edge, and academic researchers without product instincts. None of them have lived the specific moment this product is designed for.

---

## 9. Product Vision

**The first version:**

A caregiver logs a signal. The system suggests the most likely intent based on context, time, and prior confirmed history. The caregiver confirms or corrects. The system updates. After thirty interactions, the suggestions for this person visibly shift.

**The larger vision:**

A portable communication profile that travels with the person. Usable at home, in a care facility, during hospital stays, during therapy sessions. Not a medical record. A pattern record. A decoder that gets more accurate over time and transfers with the person wherever they go.

Future versions could support:
- Speech therapy workflows
- Stroke recovery support
- Elder care facilities
- Hospital caregiver handoffs
- Wearable signal capture
- Gesture and voice-assisted input
- On-device AI for full privacy
- Personalized communication models per individual

The long-term goal is not another caregiving app. The long-term goal is a system that helps preserve connection when normal communication breaks down.

---

## 10. MVP Scope and Focus

**The riskiest assumption to test:**

Does caregiver feedback, accumulated over even a few days, measurably change the accuracy of suggestions?

If yes, there is a product. If no, the hypothesis is wrong.

**What is in the MVP:**

- 16 predefined signals: pain, water, food, bathroom, tired, uncomfortable, yes, no, help, reposition, medication, temperature, cold, hot, anxiety, confused
- Caregiver context panel: pain visible, hours since meal, hours since medication, low sleep, no movement, room temperature, caregiver note
- Ranked intent suggestions with plain-language explanations
- Confidence scoring with a transparent fallback when confidence is low
- Three-button feedback: correct, partial, incorrect
- Custom intent input when the top suggestion is wrong
- Pattern dashboard showing top signals, confirmed needs, time-of-day activity, and accuracy trend
- Markdown export for caregiver handoff
- Local SQLite storage, no account required, nothing uploaded

**What is explicitly not in the MVP:**

- Multi-patient profiles
- Custom signal creation
- Multi-device sync
- Audio or video capture
- Alert or notification system
- User accounts or passwords
- Clinical validation claims
- Training visualization or explainability graphs

The MVP must prove that the loop works before expanding the surface area.

---

## 11. Product Taste

**What creates real user value:**

Instant suggestion on signal tap. Under 300ms feels like the system is paying attention. Over one second feels like a tool that is getting in the way.

Plain-language explanation, not a raw confidence score. "Confirmed as water 4 times before, usually in the afternoon" is trustworthy. "0.82" is not.

Three-button feedback. One tap, done. The easier the feedback is to give, the more of it accumulates, the faster personalization works.

The caregiver note field. This is the handoff mechanism. A note attached to a signal at 11pm becomes context for the 7am caregiver. This is where the product earns long-term trust.

The pattern dashboard showing measurable improvement. Accuracy going from 42% to 67% over three weeks is the headline proof that the product works.

**What does not belong in the MVP:**

Animations celebrating correct predictions. Wrong emotional register entirely.

Onboarding tours and tooltips. If the UI requires explanation, the UI is wrong.

Multiple patient profiles in v1. Prove the loop works for one person first.

Color themes or customization. The accessible high-contrast design is the design, not a feature to toggle.

Alert or notification system. The caregiver opens the app when they need it. The app does not interrupt them.

**How the first version should feel:**

Fast. Tap and get something useful within one second.

Calm. No aggressive colors, no alert sounds, no flashing elements. The caregiving environment is already stressful. The app should feel like a quiet presence, not a notification system.

Private. The first screen says, in plain language, that everything stays on this device. Not buried in a settings menu. Front and center.

Useful in the moment. The test is not whether the app looks good in a demo. The test is: if someone is actively trying to understand what their loved one needs at 2am, does this make that faster? If yes, the product works.

---

## 12. Technical Architecture

**Stack:**

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, TypeScript, Tailwind CSS |
| Backend | Python FastAPI |
| Storage | SQLite via SQLModel |
| Benchmark | Python script, in-memory SQLite |

**Core data tables:**

SignalLog — one row per caregiver interaction. Fields: signal, timestamp, patient_id, context_json, suggested_intent, confidence, urgency, explanation, confirmed_intent, feedback, caregiver_note, session_id.

PatternSummary — one row per (patient, signal, confirmed_intent) triple. Fields: count, time_buckets (JSON), last_seen. This is what drives personalization.

PatientProfile — name and notes only. No medical identifiers.

**API endpoints:**

- POST /signals/suggest — accepts signal + context, returns ranked predictions + log_id
- POST /signals/feedback — accepts log_id + confirmed_intent + feedback, updates PatternSummary
- GET /patterns/{patient_id}/summary — returns full dashboard metrics
- GET /patterns/{patient_id}/export — returns markdown + JSON for caregiver handoff
- POST /patients/ — create patient profile
- GET /patients/ — list patients

---

## 13. Suggestion Engine Design

The engine applies four scoring layers in sequence.

**Layer 1 — Signal prior:**

Each signal has a prior distribution over intents. Pain signal: pain 70%, uncomfortable 15%, help 10%, reposition 5%. Water signal: water 75%, food 10%, medication 10%, tired 5%. These priors encode the typical meaning of each signal before any personalization.

**Layer 2 — Time modifier:**

Multiplicative adjustment based on the hour of the interaction. Morning: medication +40%, food +30%, water +20%. Evening: food +30%, tired +20%, medication +20%. Night: pain +40%, bathroom +30%, uncomfortable +20%. The same signal means different things at different times of day.

**Layer 3 — Context modifier:**

Caregiver context flags apply additional multipliers. Pain visible → pain intent multiplied by 1.5, help by 1.2. Hours since meal greater than 4 → food multiplied by 1.3, water by 1.2. Hours since medication greater than 6 → medication multiplied by 1.4. Low sleep → tired multiplied by 1.4, pain by 1.2. No movement → reposition multiplied by 1.5. Room cold or hot → matching temperature intent boosted.

**Layer 4 — History (Bayesian personalization):**

For each confirmed signal-intent pair in the PatternSummary table, the likelihood is estimated as count / total_confirmations for this signal and patient. This likelihood is used to update the prior via Bayesian combination: posterior = prior × (1 + likelihood × 2). Additionally, time-bucket confirmations apply a secondary boost when the current time bucket matches historical patterns.

**Output:**

Top 3 ranked intents with confidence scores (normalized), urgency level, and plain-language explanation for the top prediction. If top confidence is below 0.35, a fallback message replaces the ranking entirely.

**Fallback message:**

"The system is not confident enough to suggest a specific intent. Please check directly with the person. Consider: pain, water, bathroom, comfort, medication."

**Plain-language explanation logic:**

If confirmed 3+ times before: "This signal was confirmed as [intent] [count] times before and often appears in the [time bucket]."
If confirmed 1-2 times: "This signal was confirmed as [intent] [count] time before."
If no history: "Based on typical patterns, [signal] signals most commonly indicate [intent]."
Context flags append additional sentences where relevant.

---

## 14. AI Architecture: Honest Evolution Path

No overclaiming. Each stage activates when there is enough data to justify it.

**Stage 1 — Transparent rule engine (now)**

What it does: signal priors plus time modifiers plus context modifiers plus Bayesian history combination.

What it proves: the feedback loop is useful. Caregivers engage. Suggestions improve.

Risk it reduces: trust. Every prediction is fully explainable. No black box. The caregiver can read the reasoning and reject it. This is the trust baseline required for later stages.

Trigger: always active from the first interaction.

**Stage 2 — Frequency-weighted personalization (after 20+ confirmed interactions)**

What it does: the likelihood estimate shifts from zero to empirical. Suggestions become patient-specific rather than generic.

What it proves: one patient's history produces measurably different outputs than another patient's history for identical signals.

Risk it reduces: generality. Two patients with the same signal get different suggestions if their histories differ.

Trigger: automatic once PatternSummary has 20+ rows.

**Stage 3 — Context-conditioned Naive Bayes (after 60+ confirmed interactions)**

What it does: conditions on context buckets in addition to signal. Trains a small classifier locally on the patient's own history. No cloud. No shared training data.

What it proves: context is a real modifier, not just a heuristic. The same signal at 2am after poor sleep predicts different intents than at noon after a meal.

Risk it reduces: context blindness. The rule-based stage applies context modifiers uniformly; this stage learns them per patient.

Trigger: automatic once PatternSummary has 60+ rows.

**Stage 4 — On-device lightweight model (future)**

What it does: replaces Naive Bayes with a small MLP trained on the full patient history. Runs in the browser via ONNX or in a local Python process. Model under 10MB. Personalized to one patient, never shared.

What it proves: accumulated history supports a learned model that outperforms the rule-based baseline on top-1 accuracy.

Risk it reduces: accuracy ceiling. The rule-based and Naive Bayes stages have hard limits. A learned model captures non-linear interactions.

**Stage 5 — Multimodal (not now)**

What it does: incorporates wearable heart rate variability for pain detection, camera-based gesture recognition for non-verbal signals, voice tone analysis for distress detection.

What it requires: privacy architecture redesign, user consent framework, hardware integration layer. This is a future product, not an MVP feature.

**The principle that applies throughout all stages:**

Every prediction must be explainable in plain language. If the system cannot explain why it made a suggestion, it should not make that suggestion with high confidence. The fallback message is not a failure. It is a feature that builds caregiver trust.

---

## 15. Privacy Design

**What is stored locally (SQLite, on device):**

Signal logs with timestamps, caregiver context entries, suggestion history and confidence scores, confirmed intents from caregiver feedback, pattern summaries, patient name and notes only.

**What is never stored:**

Health records, biometric data, audio, video, images, location, device identifiers, account information, insurance data, clinical history.

**What is never uploaded:**

Nothing. The default is zero network calls for patient data. The suggestion engine runs entirely in the backend process on the same machine as the caregiver's browser. No cloud inference. No telemetry. No sync to a remote server.

**Export design:**

Export produces a JSON or Markdown file summarizing the session. The file stays with the caregiver. Nothing is sent anywhere by the system. A new caregiver can read this file to onboard faster without starting from zero.

**Why local-first is not just a feature but a requirement:**

Families will not use this product if they believe sensitive care data is being sent somewhere. Medical and elder care contexts have zero tolerance for data leakage. Local-first removes a whole category of trust questions before they arise. It also means the product works offline, which matters in home care settings.

---

## 16. Data Strategy

Every field in the data model has a defined purpose. Nothing is collected speculatively.

| Field | Why collected | Use |
|---|---|---|
| Signal | Input variable | Inference |
| Timestamp | Time-of-day context | Personalization |
| Pain visible | Context modifier | Boosts pain and help priors |
| Hours since meal | Context modifier | Boosts food and water when >4 hours |
| Hours since medication | Context modifier | Boosts medication when >6 hours |
| Low sleep | Context modifier | Boosts tired and pain priors |
| No movement | Context modifier | Boosts reposition prior |
| Room temperature | Context modifier | Boosts cold or hot priors |
| Suggested intent | Model output | Accuracy measurement |
| Confidence | Model output | Fallback threshold, accuracy tracking |
| Feedback | Personalization label | PatternSummary update |
| Confirmed intent | Ground truth | Future model training |
| Caregiver note | Free text | Export only, not used for inference |
| Session ID | Grouping | Session summary only |

**How feedback becomes labels:**

Every time a caregiver confirms an intent, that confirmation is stored in the PatternSummary table as a (signal, confirmed_intent, time_bucket) triple with a count. When the suggestion engine runs next time for the same signal and patient, it applies the Bayesian update. The more confirmations, the stronger the likelihood, the more the personalized history dominates over the generic prior.

**What is never collected:** Audio, video, biometrics, location, device identifiers, insurance data, or health records. The system does not need any of this to work.

---

## 17. Technical Moat

The moat is not the algorithm. Algorithms can be copied. The moat is the data structure that grows inside the product as it is used.

**Repeated signal history:**

Every confirmed signal-intent pair is recorded with timestamp and context. Over three months, a family accumulates hundreds of these pairs for one specific person. That dataset does not exist anywhere else. It cannot be scraped, synthesized, or purchased. It only exists because someone used the product.

**Caregiver feedback as implicit labels:**

Every time a caregiver marks a suggestion incorrect and types the real intent, they produce a labeled training example under real-world conditions. This is expensive to generate any other way. Supervised datasets in assistive communication require clinical researchers, IRB approval, and months of collection. SignalBridge generates them as a side effect of caregiving.

**Context memory:**

The system learns which context modifiers matter for this specific person. One person's pain signals spike at night. Another signals water most often after medication. These correlations are person-specific and take time to appear. A new product cannot reproduce them on day one even if it copies every algorithm.

**Calibrated confidence:**

Generic models apply population-level priors. SignalBridge calibrates confidence scores to one person's real outcomes. That calibration only exists after sustained feedback.

**Local storage as a data moat:**

All of this data stays on the device. There is no central server. The data cannot be extracted and used to train a competitor's system.

**Switching cost:**

After six months of use, switching to a different tool means starting from zero. No profile, no history, no calibrated suggestions. The longer the system is used, the higher the switching cost, without any artificial lock-in. It is pure data stickiness.

---

## 18. Success Metrics

**Latency targets:**

- Suggestion engine p99: under 50ms
- Full round trip (tap to suggestion render): under 300ms p99
- Feedback submission: under 100ms p50

**Accuracy targets:**

| Metric | Baseline (day 1) | After 30 confirmed | After 100 confirmed |
|---|---|---|---|
| Top-1 accuracy | 40-55% | 60%+ | 70%+ |
| Top-3 match rate | 75%+ | 85%+ | 88%+ |
| Fallback rate | 15-20% | 12% | <10% |
| Correction rate | 40-60% | <30% | <20% |

**Personalization delta — the headline metric:**

Compare top-1 accuracy in interactions 1-10 versus interactions 51-60 for the same patient.

Target: at least +15 percentage points improvement.

If this improvement does not appear after 50 interactions with feedback, the personalization loop is not working and the product hypothesis is wrong.

**Why the correction rate matters:**

A high correction rate early is expected and healthy. It means the system is wrong and caregivers are correcting it, which feeds personalization. The meaningful signal is the trend: a correction rate that declines from 55% to 20% over thirty interactions is proof that the feedback loop works.

---

## 19. Benchmark Design

The benchmark script runs three phases against an in-memory SQLite database with a synthetic patient.

**Phase 1 — Baseline (n=50, no feedback):**

Runs 50 suggestions across all 16 signals with random context. Measures top-1 accuracy, top-3 match rate, fallback rate, and latency percentiles. No feedback is submitted. This is the prior-only baseline.

**Phase 2 — Feedback training (n=100, with corrections):**

Runs 100 suggestions and submits caregiver feedback after each, with 15% noise (meaning 15% of the time the signal observed by the caregiver differs from the true signal). This simulates real caregiving conditions. PatternSummary accumulates after each confirmed intent.

**Phase 3 — Post-personalization (n=50):**

Runs 50 more suggestions without feedback submission. Measures the same metrics as Phase 1. The delta between Phase 1 and Phase 3 is the personalization improvement score.

**Targets the benchmark checks:**

- Baseline top-1 >= 40%
- Post-training top-1 >= 60%
- Baseline top-3 >= 75%
- Personalization delta >= +10 percentage points
- p99 latency < 50ms

**Run with:**

```bash
cd signalbridge/backend
python ../benchmarks/bench_suggestions.py
```

---

## 20. Senior Engineering Constraints

**What must be simple:**

The signal grid: one tap, no confirmation dialog, no dropdown, no modal. Operable with one hand, readable in low light, fast enough that waiting never feels like a blocker.

The feedback buttons: three choices, one tap, done. More granularity destroys the experience.

**What must be reliable:**

The suggestion engine must always return something. A low-confidence fallback with a plain-language message is always better than an empty state or a spinner that never resolves. The caregiver needs to act regardless of whether the system is confident.

Feedback submission must never silently fail. The feedback record is the product's long-term value. Losing it is worse than any UI bug.

**What must be explainable:**

Every suggestion includes a plain English reason. Not "confidence: 0.82." Something a caregiver can read and evaluate. If the explanation does not make sense to them, they will not trust the suggestion.

The fallback message must be actionable, not a disclaimer. "Use your own judgment" is not useful. "Check pain, water, bathroom, comfort, and medication timing" is.

**What must not be overengineered in the MVP:**

No user accounts. No passwords. No email verification. One patient per device to start.

No custom signal creation in v1. The 16 predefined signals are enough to prove the loop.

No multi-device sync. Sync requires infrastructure, conflict resolution, and trust architecture.

No training visualization. Showing a graph of how the model is learning sounds impressive but creates false trust in a system that is not yet validated.

---

## 21. Getting Started

**Requirements:** Python 3.10+, Node 18+

```bash
# Clone the repo
git clone https://github.com/aryanputta/signalbridge
cd signalbridge

# Install all dependencies
make install

# Terminal 1: start the backend
make backend

# Terminal 2: start the frontend
make frontend

# Open in browser
open http://localhost:5173

# Run the benchmark
make bench
```

On first load, enter the name of the person you are caring for. No account required. Everything stays on your machine.

---

## 22. File Structure

```
signalbridge/
├── Makefile                         install, backend, frontend, bench commands
├── SIGNALBRIDGE.md                  concise strategy doc
├── SIGNALBRIDGE_FULL.md             this document
│
├── backend/
│   ├── main.py                      FastAPI app, CORS middleware, startup hook
│   ├── models.py                    SQLModel tables: PatientProfile, SignalLog, PatternSummary
│   ├── database.py                  SQLite engine, session factory
│   ├── suggestion_engine.py         Rule-based engine with Bayesian personalization and feedback loop
│   ├── requirements.txt             fastapi, uvicorn, sqlmodel, pydantic
│   └── routers/
│       ├── __init__.py
│       ├── signals.py               POST /suggest, POST /feedback, GET /history
│       ├── patients.py              POST /, GET /, GET /{id}
│       └── patterns.py             GET /summary, GET /export
│
├── frontend/
│   ├── index.html
│   ├── package.json                 react, vite, tailwindcss, typescript
│   ├── vite.config.ts               proxy /api to backend port 8000
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── src/
│       ├── types.ts                 All interfaces, signal definitions
│       ├── index.css                Tailwind base
│       ├── main.tsx                 React root
│       ├── App.tsx                  Tab routing: Signals / Patterns
│       ├── lib/
│       │   ├── api.ts               Typed API client
│       │   └── session.ts           Session ID and patient ID persistence
│       ├── components/
│       │   ├── SignalGrid.tsx        16-signal accessible tap grid with urgency color coding
│       │   ├── ContextPanel.tsx      Caregiver context toggles, numeric inputs, note field
│       │   ├── SuggestionCard.tsx    Ranked predictions, confidence bars, feedback buttons
│       │   └── PatternDashboard.tsx  Accuracy metrics, bar charts, pattern list
│       └── pages/
│           ├── SetupPage.tsx         First-run: patient name, privacy statement, no account
│           ├── MainPage.tsx          Core caregiving loop: signal → suggestion → feedback
│           └── DashboardPage.tsx     Pattern summary and markdown export
│
└── benchmarks/
    └── bench_suggestions.py         Three-phase accuracy and latency benchmark
```

---

## 23. What This Is Not

This is not a diagnostic tool.

This is not a replacement for doctors, nurses, speech therapists, caregivers, or family judgment.

This is not claiming clinical validation.

This is not using private medical data.

This is not a surveillance product.

This is not trying to solve every disability communication case at once.

This is a focused MVP for caregiver-assisted communication support, designed to prove one thing: a simple personalized system can become more useful over time by learning from caregiver feedback.

The prototype proves whether repeated signals plus context plus caregiver feedback can create a useful personalization loop.

---

## Final Note

The most meaningful technology does not always start in a lab or a pitch deck.

Sometimes it starts at home, when a normal interaction becomes hard and nobody has built the right tool yet.

SignalBridge starts from that moment.

---

**GitHub:** https://github.com/aryanputta/signalbridge
**Contact:** aryansputta@gmail.com
**Built by:** Aryan Putta — CS and Data Science, Rutgers University

*Local-first. Private by default. No account required. Everything stays on your device.*
