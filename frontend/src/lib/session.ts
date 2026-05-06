export function getOrCreateSessionId(): string {
  const key = "sb_session_id";
  let id = sessionStorage.getItem(key);
  if (!id) {
    id = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    sessionStorage.setItem(key, id);
  }
  return id;
}

export function getStoredPatientId(): number | null {
  const raw = localStorage.getItem("sb_patient_id");
  return raw ? parseInt(raw, 10) : null;
}

export function setStoredPatientId(id: number): void {
  localStorage.setItem("sb_patient_id", String(id));
}
