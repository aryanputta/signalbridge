/**
 * Shift handoff view — the first screen a new caregiver opens.
 * Shows the last 8 signals, top 3 confirmed needs in the last 24h,
 * any caregiver notes, and time of last interaction.
 */
import { useState, useEffect } from "react";
import { api } from "../lib/api";
import type { PatternSummary } from "../types";

interface SignalLog {
  id: number;
  signal: string;
  confirmed_intent: string | null;
  caregiver_note: string | null;
  urgency: string | null;
  timestamp: string;
}

interface Props {
  patientId: number;
}

function timeSince(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

const URGENCY_DOT: Record<string, string> = {
  high: "bg-red-500",
  medium: "bg-amber-400",
  low: "bg-sky-400",
};

export function HandoffPage({ patientId }: Props) {
  const [logs, setLogs] = useState<SignalLog[]>([]);
  const [summary, setSummary] = useState<PatternSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetch(`/api/signals/history/${patientId}?limit=8`).then((r) => r.json()),
      api.getPatternSummary(patientId),
    ])
      .then(([logsData, summaryData]) => {
        setLogs(logsData);
        setSummary(summaryData);
      })
      .finally(() => setLoading(false));
  }, [patientId]);

  if (loading) {
    return (
      <div className="flex justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-sky-600" />
      </div>
    );
  }

  const lastLog = logs[0];
  const notes = logs.filter((l) => l.caregiver_note);

  const oneDayAgo = Date.now() - 24 * 60 * 60 * 1000;
  const recentNeeds = logs
    .filter((l) => l.confirmed_intent && new Date(l.timestamp).getTime() > oneDayAgo)
    .reduce<Record<string, number>>((acc, l) => {
      acc[l.confirmed_intent!] = (acc[l.confirmed_intent!] ?? 0) + 1;
      return acc;
    }, {});
  const topNeeds = Object.entries(recentNeeds)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3);

  return (
    <div className="space-y-5">
      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h2 className="text-base font-bold text-slate-800 mb-1">Shift Handoff</h2>
        {lastLog ? (
          <p className="text-sm text-slate-500">
            Last interaction: <span className="font-semibold text-slate-700">{timeSince(lastLog.timestamp)}</span>
          </p>
        ) : (
          <p className="text-sm text-slate-400">No interactions logged yet.</p>
        )}
      </div>

      {topNeeds.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Top Confirmed Needs (Last 24h)</h3>
          <div className="space-y-2">
            {topNeeds.map(([need, count]) => (
              <div key={need} className="flex items-center justify-between">
                <span className="text-sm font-medium capitalize text-slate-800">
                  {need.replace(/_/g, " ")}
                </span>
                <span className="rounded-full bg-sky-100 px-2 py-0.5 text-xs font-semibold text-sky-700">
                  {count}×
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="rounded-xl border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-semibold text-slate-700 mb-3">Last 8 Signals</h3>
        {logs.length === 0 ? (
          <p className="text-xs text-slate-400">No signals logged yet.</p>
        ) : (
          <div className="space-y-2">
            {logs.map((log) => (
              <div key={log.id} className="flex items-center gap-3 rounded-lg bg-slate-50 px-3 py-2">
                <span
                  className={`h-2 w-2 flex-shrink-0 rounded-full ${URGENCY_DOT[log.urgency ?? "low"] ?? "bg-slate-300"}`}
                />
                <div className="flex-1 min-w-0">
                  <span className="text-sm font-semibold capitalize text-slate-800">{log.signal}</span>
                  {log.confirmed_intent && (
                    <span className="text-xs text-slate-500 ml-2">→ {log.confirmed_intent.replace(/_/g, " ")}</span>
                  )}
                </div>
                <span className="text-xs text-slate-400 flex-shrink-0">{timeSince(log.timestamp)}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {notes.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Caregiver Notes</h3>
          <div className="space-y-2">
            {notes.map((log) => (
              <div key={log.id} className="rounded-lg bg-amber-50 border border-amber-100 px-3 py-2">
                <p className="text-xs text-amber-700 font-medium mb-0.5">{timeSince(log.timestamp)} · {log.signal}</p>
                <p className="text-sm text-slate-700">{log.caregiver_note}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {summary && summary.total_interactions > 0 && (
        <div className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-center">
          <p className="text-xs text-slate-500">
            Overall accuracy across {summary.total_interactions} interactions:{" "}
            <span className="font-bold text-slate-800">
              {Math.round(summary.top_1_accuracy * 100)}%
            </span>
          </p>
        </div>
      )}
    </div>
  );
}
