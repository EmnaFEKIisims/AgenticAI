// src/components/crud/LoadingState.tsx
export function LoadingState({ text = "Loading…" }: { text?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <div className="relative h-10 w-10">
        <span className="absolute inset-0 rounded-full border-2 border-slate-100" />
        <span className="absolute inset-0 animate-spin rounded-full border-2 border-transparent border-t-slate-900" />
      </div>
      <p className="text-sm text-slate-500">{text}</p>
    </div>
  );
}