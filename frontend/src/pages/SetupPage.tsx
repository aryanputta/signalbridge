import { useState } from "react";
import { api } from "../lib/api";
import { setStoredPatientId } from "../lib/session";

interface Props {
  onCreated: (id: number) => void;
}

export function SetupPage({ onCreated }: Props) {
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const patient = await api.createPatient(name.trim(), notes.trim());
      setStoredPatientId(patient.id);
      onCreated(patient.id);
    } catch {
      setError("Could not connect to the backend. Make sure it is running on port 8000.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <div className="text-4xl mb-3">🌉</div>
          <h1 className="text-2xl font-bold text-slate-900">SignalBridge</h1>
          <p className="mt-2 text-sm text-slate-500 leading-relaxed">
            A private, local tool that helps caregivers understand repeated signals
            and build a personalized communication profile over time.
          </p>
          <p className="mt-3 text-xs text-emerald-700 font-medium">
            Everything stays on this device. Nothing is uploaded.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
          <div className="flex flex-col gap-1">
            <label className="text-sm font-semibold text-slate-700">
              Name of the person you are caring for
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Mom, Dad, or a first name"
              required
              className="rounded-lg border border-slate-200 px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-sky-500"
            />
          </div>

          <div className="flex flex-col gap-1">
            <label className="text-sm font-semibold text-slate-700">
              Notes (optional)
            </label>
            <textarea
              rows={2}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Any useful context about their communication patterns..."
              className="rounded-lg border border-slate-200 px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none"
            />
          </div>

          {error && (
            <p className="text-sm text-red-600">{error}</p>
          )}

          <button
            type="submit"
            disabled={loading || !name.trim()}
            className="w-full rounded-xl bg-slate-900 py-4 text-base font-bold text-white hover:bg-slate-800 disabled:opacity-40 transition-colors"
          >
            {loading ? "Setting up..." : "Start"}
          </button>
        </form>

        <p className="text-center text-xs text-slate-400">
          Local storage only. No account required.
        </p>
      </div>
    </div>
  );
}
