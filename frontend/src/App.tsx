import { useState } from "react";
import { SetupPage } from "./pages/SetupPage";
import { MainPage } from "./pages/MainPage";
import { DashboardPage } from "./pages/DashboardPage";
import { getStoredPatientId, setStoredPatientId } from "./lib/session";

type Tab = "signals" | "dashboard";

export function App() {
  const [patientId, setPatientId] = useState<number | null>(getStoredPatientId);
  const [tab, setTab] = useState<Tab>("signals");

  const handleCreated = (id: number) => {
    setStoredPatientId(id);
    setPatientId(id);
  };

  if (!patientId) {
    return <SetupPage onCreated={handleCreated} />;
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-lg items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🌉</span>
            <span className="text-base font-bold text-slate-900">SignalBridge</span>
          </div>
          <div className="flex rounded-lg border border-slate-200 bg-slate-100 p-0.5">
            <button
              onClick={() => setTab("signals")}
              className={`rounded-md px-4 py-1.5 text-sm font-semibold transition-colors ${
                tab === "signals"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Signals
            </button>
            <button
              onClick={() => setTab("dashboard")}
              className={`rounded-md px-4 py-1.5 text-sm font-semibold transition-colors ${
                tab === "dashboard"
                  ? "bg-white text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-700"
              }`}
            >
              Patterns
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-lg px-4 py-6">
        {tab === "signals" ? (
          <MainPage patientId={patientId} />
        ) : (
          <DashboardPage patientId={patientId} />
        )}
      </main>
    </div>
  );
}
