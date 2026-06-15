
"use client";

import { cn } from "@/lib/utils";
import { Check } from "lucide-react";

interface StepIndicatorProps {
  steps: string[];
  currentStep: number;
  className?: string;
}

export function StepIndicator({ steps, currentStep, className }: StepIndicatorProps) {
  return (
    <nav aria-label="Progress" className={cn("mb-8", className)}>
      <ol role="list" className="flex items-center justify-around">
        {steps.map((step, stepIdx) => (
          <li key={step} className={cn("relative flex-1", stepIdx !== steps.length -1 ? "pr-8 sm:pr-20" : "")}>
            {stepIdx < currentStep ? (
              // Completed Step
              <div className="flex items-center">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-primary text-primary-foreground">
                  <Check className="h-6 w-6" aria-hidden="true" />
                </span>
                <span className="ml-3 text-sm font-medium text-primary hidden sm:block">{step}</span>
              </div>
            ) : stepIdx === currentStep ? (
              // Current Step
              <div className="flex items-center" aria-current="step">
                <span className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-primary bg-primary/10 text-primary">
                  <span className="h-3 w-3 rounded-full bg-primary" />
                </span>
                <span className="ml-3 text-sm font-medium text-primary hidden sm:block">{step}</span>
              </div>
            ) : (
              // Upcoming Step
              <div className="flex items-center">
                <span className="flex h-10 w-10 items-center justify-center rounded-full border-2 border-border bg-card text-muted-foreground group-hover:border-muted-foreground">
                  <span className="text-sm">{stepIdx + 1}</span>
                </span>
                <span className="ml-3 text-sm font-medium text-muted-foreground hidden sm:block">{step}</span>
              </div>
            )}

            {/* Connector line */}
            {stepIdx !== steps.length - 1 ? (
              <div className={cn(
                "absolute inset-0 top-5 left-auto right-0 hidden w-auto sm:block",
                stepIdx < currentStep ? "bg-primary" : "bg-border",
                "h-0.5 translate-x-[calc(100%_+_20px)]" 
                )} aria-hidden="true" 
                style={{width: 'calc(100% - 60px)'}}/>

            ) : null}
          </li>
        ))}
      </ol>
    </nav>
  );
}
