import { useState, useCallback } from "react";
import { SignalGrid } from "../components/SignalGrid";
import { ContextPanel } from "../components/ContextPanel";
import { SuggestionCard } from "../components/SuggestionCard";
import { RepeatWarning } from "../components/RepeatWarning";
import { api } from "../lib/api";
import { getOrCreateSessionId } from "../lib/session";
import { submitFeedbackWithQueue, useOfflineFlusher } from "../hooks/useOfflineQueue";
import { useRepeatDetection } from "../hooks/useRepeatDetection";
import type { CaregiverContext, SuggestionResult, SignalKey, FeedbackPayload } from "../types";

const DEFAULT_CONTEXT: CaregiverContext = {
  pain_visible: false,
  hours_since_meal: null,
  hours_since_medication: null,
  low_sleep: false,
  no_movement: false,
  room_temp: null,
  caregiver_note: "",
  session_id: null,
};

interface Props {
  patientId: number;
}

export function MainPage({ patientId }: Props) {
  const [selectedSignal, setSelectedSignal] = useState<SignalKey | null>(null);
  const [context, setContext] = useState<CaregiverContext>(DEFAULT_CONTEXT);
  const [suggestion, setSuggestion] = useState<SuggestionResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { warning, recordSignal, resolveSignal, dismissWarning } = useRepeatDetection();
  useOfflineFlusher(api.feedback);

  const handleSignalSelect = useCallback(async (key: SignalKey) => {
    setSelectedSignal(key);
    setSuggestion(null);
    setFeedbackSubmitted(false);
    setError(null);
    setLoading(true);
    recordSignal(key);

    try {
      const ctx: CaregiverContext = { ...context, session_id: getOrCreateSessionId() };
      const result = await api.suggest(patientId, key, ctx);
      setSuggestion(result);
    } catch {
      setError("Could not reach the suggestion engine. Make sure the backend is running.");
    } finally {
      setLoading(false);
    }
  }, [context, patientId, recordSignal]);

  const submitFeedback = useCallback(async (payload: FeedbackPayload) => {
    await submitFeedbackWithQueue(payload, api.feedback);
  }, []);

  const handleFeedback = useCallback(
    async (intent: string, feedback: "correct" | "partial" | "incorrect") => {
      if (!suggestion) return;
      try {
        await submitFeedback({ log_id: suggestion.log_id, confirmed_intent: intent, feedback });
        resolveSignal(selectedSignal ?? "");
        setFeedbackSubmitted(true);
      } catch {
        setError("Failed to submit feedback. It will be saved and retried automatically.");
        setFeedbackSubmitted(true); // already queued offline
      }
    },
    [suggestion, selectedSignal, submitFeedback, resolveSignal]
  );

  const handleCustomIntent = useCallback(
    async (intent: string) => {
      if (!suggestion) return;
      try {
        await submitFeedback({ log_id: suggestion.log_id, confirmed_intent: intent, feedback: "incorrect" });
        resolveSignal(selectedSignal ?? "");
        setFeedbackSubmitted(true);
      } catch {
        setFeedbackSubmitted(true);
      }
    },
    [suggestion, selectedSignal, submitFeedback, resolveSignal]
  );

  const handleReset = () => {
    setSelectedSignal(null);
    setSuggestion(null);
    setFeedbackSubmitted(false);
    setError(null);
  };

  return (
    <div className="space-y-5">
      {warning && <RepeatWarning message={warning} onDismiss={dismissWarning} />}

      <div>
        <h2 className="text-lg font-bold text-slate-800 mb-1">What signal is the person showing?</h2>
        <p className="text-sm text-slate-500">
          Tap a signal. The system suggests the most likely intent based on context and history.
        </p>
      </div>

      <SignalGrid selected={selectedSignal} onSelect={handleSignalSelect} disabled={loading} />

      {loading && (
        <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-sky-600" />
          <span className="text-sm text-slate-600">Reading context and history...</span>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {suggestion && !loading && (
        <>
          {suggestion.stage === 2 && (
            <div className="flex items-center gap-2 rounded-lg bg-emerald-50 border border-emerald-200 px-3 py-2">
              <span className="text-xs font-semibold text-emerald-700">Transformer active</span>
              <span className="text-xs text-emerald-500">personalised model contributing</span>
            </div>
          )}
          <SuggestionCard
            result={suggestion}
            onFeedback={handleFeedback}
            onCustomIntent={handleCustomIntent}
            submitted={feedbackSubmitted}
          />
        </>
      )}

      {(suggestion || selectedSignal) && (
        <button
          onClick={handleReset}
          className="w-full rounded-xl border border-slate-200 bg-white py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
        >
          Log another signal
        </button>
      )}

      <ContextPanel context={context} onChange={setContext} />
    </div>
  );
}
