import type { PatternSummary } from "../types";

interface Props {
  summary: PatternSummary;
  onExport: () => void;
  exporting: boolean;
  personalizationDelta?: number | null; // percentage points improvement
  stage?: number;
}

function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4 text-center">
      <div className="text-3xl font-bold text-slate-900">{value}</div>
      <div className="text-xs font-semibold uppercase tracking-wide text-slate-500 mt-1">{label}</div>
      {sub && <div className="text-xs text-slate-400 mt-0.5">{sub}</div>}
    </div>
  );
}

const TIME_LABELS: Record<string, string> = {
  morning: "Morning",
  afternoon: "Afternoon",
  evening: "Evening",
  night: "Night",
};

const STAGE_LABEL: Record<number, string> = {
  0: "Rule engine",
  1: "Bayesian personalisation",
  2: "Transformer active",
};

export function PatternDashboard({ summary, onExport, exporting, personalizationDelta, stage }: Props) {
  const accuracy = Math.round(summary.top_1_accuracy * 100);
  const fallbackRate =
    summary.total_interactions > 0
      ? Math.round((summary.low_confidence_count / summary.total_interactions) * 100)
      : 0;

  const maxTime = Math.max(...Object.values(summary.time_of_day_distribution), 1);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-900">Pattern Dashboard</h2>
        <button
          onClick={onExport}
          disabled={exporting}
          className="rounded-lg bg-slate-800 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-900 disabled:opacity-50"
        >
          {exporting ? "Exporting..." : "Export Summary"}
        </button>
      </div>

      {(personalizationDelta != null || stage != null) && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 flex items-center justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">AI Stage</p>
            <p className="text-sm font-bold text-emerald-900 mt-0.5">
              {STAGE_LABEL[stage ?? 0]}
            </p>
          </div>
          {personalizationDelta != null && (
            <div className="text-right">
              <p className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
                Personalisation Gain
              </p>
              <p className="text-2xl font-bold text-emerald-900 mt-0.5">
                {personalizationDelta > 0 ? "+" : ""}
                {Math.round(personalizationDelta)}pp
              </p>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <StatCard
          label="Total Interactions"
          value={summary.total_interactions}
        />
        <StatCard
          label="Top-1 Accuracy"
          value={`${accuracy}%`}
          sub={`${summary.correct_count} correct`}
        />
        <StatCard
          label="Urgent Events"
          value={summary.urgent_events}
        />
        <StatCard
          label="Fallback Rate"
          value={`${fallbackRate}%`}
          sub={`${summary.low_confidence_count} low conf.`}
        />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Most Frequent Signals</h3>
          <div className="space-y-2">
            {summary.top_signals.slice(0, 6).map(([sig, count]) => (
              <div key={sig} className="flex items-center gap-2">
                <span className="w-24 text-sm text-slate-700 capitalize font-medium truncate">
                  {sig}
                </span>
                <div className="flex-1 rounded-full bg-slate-100 h-3">
                  <div
                    className="h-3 rounded-full bg-sky-500"
                    style={{
                      width: `${Math.round(
                        (count / (summary.top_signals[0]?.[1] || 1)) * 100
                      )}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-slate-400 w-5 text-right">{count}</span>
              </div>
            ))}
            {summary.top_signals.length === 0 && (
              <p className="text-xs text-slate-400">No data yet.</p>
            )}
          </div>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Confirmed Needs</h3>
          <div className="space-y-2">
            {summary.top_confirmed_needs.slice(0, 6).map(([need, count]) => (
              <div key={need} className="flex items-center gap-2">
                <span className="w-24 text-sm text-slate-700 capitalize font-medium truncate">
                  {need.replace(/_/g, " ")}
                </span>
                <div className="flex-1 rounded-full bg-slate-100 h-3">
                  <div
                    className="h-3 rounded-full bg-emerald-500"
                    style={{
                      width: `${Math.round(
                        (count / (summary.top_confirmed_needs[0]?.[1] || 1)) * 100
                      )}%`,
                    }}
                  />
                </div>
                <span className="text-xs text-slate-400 w-5 text-right">{count}</span>
              </div>
            ))}
            {summary.top_confirmed_needs.length === 0 && (
              <p className="text-xs text-slate-400">No confirmed intents yet.</p>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Time of Day Activity</h3>
        <div className="flex items-end gap-3 h-24">
          {["morning", "afternoon", "evening", "night"].map((bucket) => {
            const count = summary.time_of_day_distribution[bucket] ?? 0;
            const height = maxTime > 0 ? Math.round((count / maxTime) * 100) : 0;
            return (
              <div key={bucket} className="flex flex-1 flex-col items-center gap-1">
                <div className="w-full flex items-end justify-center" style={{ height: 80 }}>
                  <div
                    className="w-full rounded-t-md bg-sky-400"
                    style={{ height: `${height}%` }}
                  />
                </div>
                <span className="text-xs text-slate-500">{TIME_LABELS[bucket]}</span>
                <span className="text-xs font-semibold text-slate-700">{count}</span>
              </div>
            );
          })}
        </div>
      </div>

      {summary.patterns.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Personalized Patterns</h3>
          <div className="space-y-2">
            {summary.patterns.slice(0, 8).map((p, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm"
              >
                <span className="text-slate-700">
                  <span className="font-semibold capitalize">{p.signal}</span>
                  {" → "}
                  <span className="capitalize">{p.confirmed_intent.replace(/_/g, " ")}</span>
                </span>
                <span className="text-xs text-slate-400 font-mono">{p.count}x</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
