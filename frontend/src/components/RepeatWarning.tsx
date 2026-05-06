interface Props {
  message: string;
  onDismiss: () => void;
}

export function RepeatWarning({ message, onDismiss }: Props) {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-xl border-2 border-red-500 bg-red-50 p-4"
    >
      <span className="text-2xl leading-none mt-0.5" aria-hidden>🚨</span>
      <div className="flex-1">
        <p className="font-bold text-red-800 text-sm">Repeated Signal Alert</p>
        <p className="text-sm text-red-700 mt-0.5 leading-relaxed">{message}</p>
      </div>
      <button
        onClick={onDismiss}
        aria-label="Dismiss alert"
        className="text-red-400 hover:text-red-600 text-xl leading-none font-bold"
      >
        ×
      </button>
    </div>
  );
}
