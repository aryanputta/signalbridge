import type { SuggestionResult, Prediction } from "../types";

interface Props {
  result: SuggestionResult;
  onFeedback: (intent: string, feedback: "correct" | "partial" | "incorrect") => void;
  onCustomIntent: (intent: string) => void;
  submitted: boolean;
}

const URGENCY_STYLE: Record<string, string> = {
  high: "bg-red-600 text-white",
  medium: "bg-amber-500 text-white",
  low: "bg-sky-600 text-white",
  unknown: "bg-slate-400 text-white",
};

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 70 ? "bg-emerald-500" : pct >= 45 ? "bg-amber-400" : "bg-red-400";
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 rounded-full bg-slate-200 h-2">
        <div
          className={`h-2 rounded-full ${color} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-mono text-slate-500 w-8 text-right">{pct}%</span>
    </div>
  );
}

function PredictionRow({ pred, rank }: { pred: Prediction; rank: number }) {
  return (
    <div
      className={`rounded-lg p-3 ${
        rank === 0
          ? "border-2 border-slate-900 bg-white shadow"
          : "border border-slate-200 bg-slate-50"
      }`}
    >
      <div className="flex items-center justify-between mb-1">
        <span className="font-bold text-slate-900 capitalize text-lg">
          {rank === 0 && "→ "}
          {pred.intent.replace(/_/g, " ")}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-semibold ${URGENCY_STYLE[pred.urgency]}`}
        >
          {pred.urgency}
        </span>
      </div>
      <ConfidenceBar value={pred.confidence} />
      {pred.explanation && (
        <p className="mt-2 text-xs text-slate-500 leading-relaxed">{pred.explanation}</p>
      )}
    </div>
  );
}

export function SuggestionCard({ result, onFeedback, onCustomIntent, submitted }: Props) {
  if (result.fallback) {
    return (
      <div className="rounded-xl border-2 border-amber-400 bg-amber-50 p-5 space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">⚠️</span>
          <h3 className="font-bold text-amber-900 text-base">Low Confidence</h3>
        </div>
        <p className="text-sm text-amber-800 leading-relaxed">{result.fallback_message}</p>
        {result.predictions.length > 0 && (
          <div className="space-y-2 pt-1">
            <p className="text-xs font-semibold text-amber-700 uppercase tracking-wide">
              Possible intents (uncertain)
            </p>
            {result.predictions.map((p, i) => (
              <PredictionRow key={p.intent} pred={p} rank={i + 1} />
            ))}
          </div>
        )}
        {!submitted && (
          <CustomIntentInput onSubmit={onCustomIntent} />
        )}
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-slate-800 text-base">Suggested Intent</h3>
        <span className="text-xs text-slate-400">{result.time_bucket}</span>
      </div>

      <div className="space-y-2">
        {result.predictions.map((pred, i) => (
          <PredictionRow key={pred.intent} pred={pred} rank={i} />
        ))}
      </div>

      {!submitted && (
        <>
          <div className="flex flex-col gap-2 pt-2">
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Was the top suggestion correct?
            </p>
            <div className="flex gap-2">
              <button
                onClick={() =>
                  onFeedback(result.predictions[0].intent, "correct")
                }
                className="flex-1 rounded-lg bg-emerald-600 px-4 py-3 text-sm font-bold text-white hover:bg-emerald-700 active:scale-95 transition-all"
              >
                Correct
              </button>
              <button
                onClick={() =>
                  onFeedback(result.predictions[0].intent, "partial")
                }
                className="flex-1 rounded-lg bg-amber-500 px-4 py-3 text-sm font-bold text-white hover:bg-amber-600 active:scale-95 transition-all"
              >
                Partial
              </button>
              <button
                onClick={() =>
                  onFeedback(result.predictions[0].intent, "incorrect")
                }
                className="flex-1 rounded-lg bg-red-600 px-4 py-3 text-sm font-bold text-white hover:bg-red-700 active:scale-95 transition-all"
              >
                Incorrect
              </button>
            </div>
          </div>
          <CustomIntentInput onSubmit={onCustomIntent} label="Actual intent (if different)" />
        </>
      )}

      {submitted && (
        <div className="rounded-lg bg-emerald-50 border border-emerald-200 px-4 py-3 text-sm font-medium text-emerald-800">
          Feedback recorded. System updated.
        </div>
      )}
    </div>
  );
}

function CustomIntentInput({
  onSubmit,
  label = "Enter actual intent",
}: {
  onSubmit: (intent: string) => void;
  label?: string;
}) {
  return (
    <form
      className="flex gap-2"
      onSubmit={(e) => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        const val = (fd.get("intent") as string).trim();
        if (val) {
          onSubmit(val);
          e.currentTarget.reset();
        }
      }}
    >
      <input
        name="intent"
        placeholder={label}
        className="flex-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
      />
      <button
        type="submit"
        className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-900"
      >
        Save
      </button>
    </form>
  );
}
