import { useState, useEffect } from "react";
import { PatternDashboard } from "../components/PatternDashboard";
import { api } from "../lib/api";
import type { PatternSummary } from "../types";

interface Props {
  patientId: number;
}

export function DashboardPage({ patientId }: Props) {
  const [summary, setSummary] = useState<PatternSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .getPatternSummary(patientId)
      .then(setSummary)
      .catch(() => setError("Could not load pattern summary."))
      .finally(() => setLoading(false));
  }, [patientId]);

  const handleExport = async () => {
    setExporting(true);
    try {
      const data = await api.exportSummary(patientId);
      const blob = new Blob([data.markdown], { type: "text/markdown" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `signalbridge-export-${new Date().toISOString().slice(0, 10)}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Export failed.");
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-200 border-t-sky-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700">
        {error}
      </div>
    );
  }

  if (!summary || summary.total_interactions === 0) {
    return (
      <div className="rounded-xl border border-slate-200 bg-slate-50 p-8 text-center">
        <p className="text-slate-500 text-sm">
          No interaction history yet. Log a few signals to see patterns here.
        </p>
      </div>
    );
  }

  return (
    <PatternDashboard
      summary={summary}
      onExport={handleExport}
      exporting={exporting}
    />
  );
}
