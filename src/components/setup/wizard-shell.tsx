"use client";

import * as React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Gauge } from "lucide-react";
import { StepRail, RailStep } from "./step-rail";

export function WizardShell({
  steps,
  current,
  done,
  onBack,
  onNext,
  nextLabel = "Continue",
  nextDisabled = false,
  busy = false,
  hideBack = false,
  headerRight,
  children,
}: {
  steps: RailStep[];
  current: number;
  done: boolean[];
  onBack: () => void;
  onNext: () => void;
  nextLabel?: string;
  nextDisabled?: boolean;
  busy?: boolean;
  hideBack?: boolean;
  headerRight?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <div className="mx-auto w-full max-w-6xl px-6 py-8">
      <header className="mb-8 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-primary/15 text-primary">
            <Gauge className="h-6 w-6" />
          </span>
          <div>
            <div className="text-base font-semibold text-foreground">Scada reports</div>
            <div className="text-xs text-muted-foreground">Guided setup</div>
          </div>
        </div>
        <div>{headerRight}</div>
      </header>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-[260px_1fr]">
        <aside className="h-fit rounded-2xl border border-border bg-card p-3 lg:sticky lg:top-8">
          <StepRail steps={steps} current={current} done={done} />
        </aside>

        <section className="flex min-h-[440px] flex-col rounded-2xl border border-border bg-card p-6 md:p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={current}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.25 }}
              className="flex-1"
            >
              {children}
            </motion.div>
          </AnimatePresence>

          <footer className="mt-8 flex items-center justify-between border-t border-border pt-5">
            <button
              type="button"
              onClick={onBack}
              className={`inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground transition-colors ${
                hideBack ? "invisible" : "hover:bg-muted"
              }`}
            >
              <ChevronLeft className="h-4 w-4" /> Back
            </button>
            <button
              type="button"
              onClick={onNext}
              disabled={nextDisabled || busy}
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-40"
            >
              {busy ? "Working…" : nextLabel}
              {!busy && <ChevronRight className="h-4 w-4" />}
            </button>
          </footer>
        </section>
      </div>
    </div>
  );
}
