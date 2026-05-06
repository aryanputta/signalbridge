import { useState } from "react";
import { SetupPage } from "./pages/SetupPage";
import { MainPage } from "./pages/MainPage";
import { DashboardPage } from "./pages/DashboardPage";
import { HandoffPage } from "./pages/HandoffPage";
import { getStoredPatientId, setStoredPatientId } from "./lib/session";

type Tab = "signals" | "dashboard" | "handoff";

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

  const tabs: { key: Tab; label: string }[] = [
    { key: "signals", label: "Signals" },
    { key: "handoff", label: "Handoff" },
    { key: "dashboard", label: "Patterns" },
  ];

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-10 border-b border-slate-200 bg-white px-4 py-3">
        <div className="mx-auto flex max-w-lg items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🌉</span>
            <span className="text-base font-bold text-slate-900">SignalBridge</span>
          </div>
          <div className="flex rounded-lg border border-slate-200 bg-slate-100 p-0.5">
            {tabs.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setTab(key)}
                className={`rounded-md px-3 py-1.5 text-sm font-semibold transition-colors ${
                  tab === key
                    ? "bg-white text-slate-900 shadow-sm"
                    : "text-slate-500 hover:text-slate-700"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-lg px-4 py-6">
        {tab === "signals" && <MainPage patientId={patientId} />}
        {tab === "handoff" && <HandoffPage patientId={patientId} />}
        {tab === "dashboard" && <DashboardPage patientId={patientId} />}
      </main>
    </div>
  );
}
