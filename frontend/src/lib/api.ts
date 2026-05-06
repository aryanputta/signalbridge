import type {
  Patient,
  CaregiverContext,
  SuggestionResult,
  FeedbackPayload,
  PatternSummary,
} from "../types";

const BASE = "/api";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  createPatient: (name: string, notes: string) =>
    post<Patient>("/patients/", { name, notes }),

  listPatients: () => get<Patient[]>("/patients/"),

  suggest: (patient_id: number, signal: string, context: CaregiverContext) =>
    post<SuggestionResult>("/signals/suggest", { patient_id, signal, context }),

  feedback: (payload: FeedbackPayload) =>
    post<{ status: string }>("/signals/feedback", payload),

  getPatternSummary: (patient_id: number) =>
    get<PatternSummary>(`/patterns/${patient_id}/summary`),

  exportSummary: (patient_id: number) =>
    get<{ markdown: string; json: PatternSummary }>(`/patterns/${patient_id}/export`),
};
