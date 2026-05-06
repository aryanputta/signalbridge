import type { CaregiverContext } from "../types";

interface Props {
  context: CaregiverContext;
  onChange: (ctx: CaregiverContext) => void;
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <label className="flex cursor-pointer items-center gap-3 rounded-lg border border-slate-200 bg-white p-3 hover:bg-slate-50">
      <div
        className={`relative h-6 w-11 rounded-full transition-colors ${
          checked ? "bg-sky-600" : "bg-slate-300"
        }`}
        onClick={() => onChange(!checked)}
      >
        <span
          className={`absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-5" : "translate-x-0.5"
          }`}
        />
      </div>
      <span className="text-sm font-medium text-slate-700">{label}</span>
    </label>
  );
}

function NumberInput({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: number | null;
  onChange: (v: number | null) => void;
  placeholder: string;
}) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </span>
      <input
        type="number"
        min={0}
        max={72}
        step={0.5}
        placeholder={placeholder}
        value={value ?? ""}
        onChange={(e) =>
          onChange(e.target.value === "" ? null : parseFloat(e.target.value))
        }
        className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500"
      />
    </label>
  );
}

export function ContextPanel({ context, onChange }: Props) {
  const set = <K extends keyof CaregiverContext>(k: K, v: CaregiverContext[K]) =>
    onChange({ ...context, [k]: v });

  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <h2 className="text-base font-semibold text-slate-800">Caregiver Context</h2>

      <div className="grid grid-cols-2 gap-2">
        <Toggle
          label="Pain visible"
          checked={context.pain_visible}
          onChange={(v) => set("pain_visible", v)}
        />
        <Toggle
          label="Low sleep"
          checked={context.low_sleep}
          onChange={(v) => set("low_sleep", v)}
        />
        <Toggle
          label="No movement"
          checked={context.no_movement}
          onChange={(v) => set("no_movement", v)}
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <NumberInput
          label="Hours since meal"
          value={context.hours_since_meal}
          onChange={(v) => set("hours_since_meal", v)}
          placeholder="e.g. 3.5"
        />
        <NumberInput
          label="Hours since meds"
          value={context.hours_since_medication}
          onChange={(v) => set("hours_since_medication", v)}
          placeholder="e.g. 6"
        />
      </div>

      <div className="flex flex-col gap-1">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Room temperature
        </span>
        <div className="flex gap-2">
          {(["cold", "hot", null] as const).map((val) => (
            <button
              key={String(val)}
              onClick={() => set("room_temp", val)}
              className={`flex-1 rounded-lg border px-3 py-2 text-sm font-medium transition-colors ${
                context.room_temp === val
                  ? "border-sky-600 bg-sky-600 text-white"
                  : "border-slate-200 bg-white text-slate-700 hover:bg-slate-100"
              }`}
            >
              {val === null ? "Normal" : val === "cold" ? "Cold 🥶" : "Hot 🥵"}
            </button>
          ))}
        </div>
      </div>

      <div className="flex flex-col gap-1">
        <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Caregiver note
        </span>
        <textarea
          rows={2}
          value={context.caregiver_note}
          onChange={(e) => set("caregiver_note", e.target.value)}
          placeholder="Optional note for handoff or context..."
          className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500 resize-none"
        />
      </div>
    </div>
  );
}
