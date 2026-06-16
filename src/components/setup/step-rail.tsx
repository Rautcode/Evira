"use client";

import { Check } from "lucide-react";
import { cn } from "@/lib/utils";

export interface RailStep {
  id: string;
  title: string;
  subtitle?: string;
}

export function StepRail({ steps, current, done }: { steps: RailStep[]; current: number; done: boolean[] }) {
  return (
    <nav className="space-y-1" aria-label="Setup steps">
      {steps.map((s, i) => {
        const isCurrent = i === current;
        const isDone = done[i];
        return (
          <div
            key={s.id}
            aria-current={isCurrent ? "step" : undefined}
            className={cn(
              "flex items-start gap-3 rounded-xl px-3 py-3 transition-colors",
              isCurrent ? "bg-teal-500/10" : "hover:bg-white/5"
            )}
          >
            <span
              className={cn(
                "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold",
                isDone
                  ? "border-emerald-400/40 bg-emerald-500/15 text-emerald-300"
                  : isCurrent
                  ? "border-teal-400 bg-teal-500/15 text-teal-300"
                  : "border-slate-700 bg-slate-800/50 text-slate-500"
              )}
            >
              {isDone ? <Check className="h-4 w-4" /> : i + 1}
            </span>
            <div className="min-w-0">
              <div className={cn("text-sm font-medium", isCurrent ? "text-white" : isDone ? "text-slate-200" : "text-slate-400")}>
                {s.title}
              </div>
              {s.subtitle && <div className="mt-0.5 text-xs text-slate-500">{s.subtitle}</div>}
            </div>
          </div>
        );
      })}
    </nav>
  );
}
