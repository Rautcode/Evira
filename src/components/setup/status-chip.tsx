"use client";

import { cn } from "@/lib/utils";

type State = "ok" | "error" | "pending" | "idle";

export function StatusChip({ state, label }: { state: State; label: string }) {
  const styles: Record<State, string> = {
    ok: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
    error: "bg-red-500/10 text-red-300 border-red-500/30",
    pending: "bg-amber-500/10 text-amber-300 border-amber-500/30",
    idle: "bg-slate-500/10 text-slate-400 border-slate-500/30",
  };
  const dot: Record<State, string> = {
    ok: "bg-emerald-400",
    error: "bg-red-400",
    pending: "bg-amber-400 animate-pulse",
    idle: "bg-slate-500",
  };
  return (
    <span className={cn("inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-medium", styles[state])}>
      <span className={cn("h-1.5 w-1.5 rounded-full", dot[state])} />
      {label}
    </span>
  );
}
