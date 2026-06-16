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
              isCurrent ? "bg-primary/10" : "hover:bg-muted/60"
            )}
          >
            <span
              className={cn(
                "mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full border text-xs font-semibold",
                isDone
                  ? "border-emerald-500/40 bg-emerald-500/15 text-emerald-600 dark:text-emerald-300"
                  : isCurrent
                  ? "border-primary bg-primary/15 text-primary"
                  : "border-border bg-muted text-muted-foreground"
              )}
            >
              {isDone ? <Check className="h-4 w-4" /> : i + 1}
            </span>
            <div className="min-w-0">
              <div className={cn("text-sm font-medium", isCurrent || isDone ? "text-foreground" : "text-muted-foreground")}>
                {s.title}
              </div>
              {s.subtitle && <div className="mt-0.5 text-xs text-muted-foreground">{s.subtitle}</div>}
            </div>
          </div>
        );
      })}
    </nav>
  );
}
