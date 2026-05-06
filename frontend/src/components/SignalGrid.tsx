import { SIGNALS, type SignalKey } from "../types";

interface Props {
  selected: SignalKey | null;
  onSelect: (key: SignalKey) => void;
  disabled?: boolean;
}

const URGENCY_RING: Record<string, string> = {
  high: "ring-red-500 bg-red-50 hover:bg-red-100",
  medium: "ring-amber-400 bg-amber-50 hover:bg-amber-100",
  low: "ring-sky-400 bg-sky-50 hover:bg-sky-100",
};

export function SignalGrid({ selected, onSelect, disabled }: Props) {
  return (
    <div className="grid grid-cols-4 gap-3 sm:grid-cols-4">
      {SIGNALS.map((sig) => {
        const isSelected = selected === sig.key;
        const ringClass = URGENCY_RING[sig.urgency];
        return (
          <button
            key={sig.key}
            onClick={() => onSelect(sig.key as SignalKey)}
            disabled={disabled}
            aria-pressed={isSelected}
            aria-label={sig.label}
            className={`
              flex flex-col items-center justify-center gap-1 rounded-xl border-2 p-4
              text-center transition-all duration-150 focus:outline-none focus:ring-4
              focus:ring-offset-2 disabled:opacity-40
              ${isSelected
                ? "border-slate-900 bg-slate-900 text-white shadow-lg scale-105"
                : `border-transparent ring-2 ${ringClass} text-slate-800`
              }
            `}
          >
            <span className="text-3xl leading-none" aria-hidden="true">
              {sig.emoji}
            </span>
            <span className="text-sm font-semibold leading-tight">{sig.label}</span>
          </button>
        );
      })}
    </div>
  );
}
