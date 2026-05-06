export interface Patient {
  id: number;
  name: string;
  notes?: string;
  created_at: string;
}

export interface CaregiverContext {
  pain_visible: boolean;
  hours_since_meal: number | null;
  hours_since_medication: number | null;
  low_sleep: boolean;
  no_movement: boolean;
  room_temp: "cold" | "hot" | null;
  caregiver_note: string;
  session_id: string | null;
}

export interface Prediction {
  intent: string;
  confidence: number;
  urgency: "high" | "medium" | "low";
  explanation: string;
}

export interface SuggestionResult {
  log_id: number;
  predictions: Prediction[];
  fallback: boolean;
  fallback_message: string | null;
  urgency: string;
  time_bucket: string;
  stage: 0 | 1 | 2;
}

export interface FeedbackPayload {
  log_id: number;
  confirmed_intent: string;
  feedback: "correct" | "partial" | "incorrect";
}

export interface PatternEntry {
  signal: string;
  confirmed_intent: string;
  count: number;
  last_seen: string;
  time_buckets: Record<string, number>;
}

export interface PatternSummary {
  patient_id: number;
  total_interactions: number;
  top_1_accuracy: number;
  correct_count: number;
  incorrect_count: number;
  low_confidence_count: number;
  urgent_events: number;
  top_signals: [string, number][];
  top_confirmed_needs: [string, number][];
  time_of_day_distribution: Record<string, number>;
  patterns: PatternEntry[];
}

export const SIGNALS = [
  { key: "pain", label: "Pain", emoji: "🔴", urgency: "high" },
  { key: "help", label: "Help", emoji: "🆘", urgency: "high" },
  { key: "water", label: "Water", emoji: "💧", urgency: "medium" },
  { key: "food", label: "Food", emoji: "🍽️", urgency: "medium" },
  { key: "bathroom", label: "Bathroom", emoji: "🚻", urgency: "high" },
  { key: "tired", label: "Tired", emoji: "😴", urgency: "low" },
  { key: "uncomfortable", label: "Uncomfortable", emoji: "😣", urgency: "medium" },
  { key: "yes", label: "Yes", emoji: "✅", urgency: "low" },
  { key: "no", label: "No", emoji: "❌", urgency: "low" },
  { key: "reposition", label: "Reposition", emoji: "🔄", urgency: "medium" },
  { key: "medication", label: "Medication", emoji: "💊", urgency: "high" },
  { key: "temperature", label: "Temperature", emoji: "🌡️", urgency: "medium" },
  { key: "cold", label: "Cold", emoji: "🥶", urgency: "medium" },
  { key: "hot", label: "Hot", emoji: "🥵", urgency: "medium" },
  { key: "anxiety", label: "Anxiety", emoji: "😰", urgency: "medium" },
  { key: "confused", label: "Confused", emoji: "😕", urgency: "medium" },
] as const;

export type SignalKey = (typeof SIGNALS)[number]["key"];
