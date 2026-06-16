"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { WizardShell } from "@/components/setup/wizard-shell";
import { StatusChip } from "@/components/setup/status-chip";
import { ThemeToggle } from "@/components/layout/theme-toggle";
import { StepConnect } from "@/components/setup/step-connect";
import { StepDiscover } from "@/components/setup/step-discover";
import { StepMap } from "@/components/setup/step-map";
import { StepPreview } from "@/components/setup/step-preview";
import { StepAutomate } from "@/components/setup/step-automate";
import { getSetupStatus, completeSetup } from "@/lib/api";

const STEPS = [
  { id: "connect", title: "Connect", subtitle: "Database and SCADA" },
  { id: "discover", title: "Discover", subtitle: "Find your tags" },
  { id: "map", title: "Map", subtitle: "Tags to machines" },
  { id: "preview", title: "Preview", subtitle: "Verify the data" },
  { id: "automate", title: "Automate", subtitle: "Schedule reports" },
];

export default function SetupPage() {
  const router = useRouter();
  const [step, setStep] = React.useState(0);
  const [status, setStatus] = React.useState<any>(null);
  const [busy, setBusy] = React.useState(false);

  const done = STEPS.map((s) => status?.steps?.[s.id]?.done ?? false);

  const refresh = React.useCallback(async () => {
    try {
      const r = await getSetupStatus();
      setStatus(r.data);
    } catch {
      /* ignore */
    }
  }, []);

  React.useEffect(() => {
    refresh();
  }, [refresh]);

  const isLast = step === STEPS.length - 1;

  const onNext = async () => {
    if (isLast) {
      setBusy(true);
      try {
        await completeSetup();
      } catch {
        /* ignore */
      }
      router.push("/dashboard");
      return;
    }
    setStep((s) => s + 1);
    refresh();
  };

  const onBack = () => setStep((s) => Math.max(0, s - 1));

  return (
    <WizardShell
      steps={STEPS}
      current={step}
      done={done}
      onBack={onBack}
      onNext={onNext}
      hideBack={step === 0}
      busy={busy}
      nextLabel={isLast ? "Finish setup" : "Continue"}
      headerRight={
        <div className="flex items-center gap-2">
          <StatusChip
            state={status?.database_reachable ? "ok" : "pending"}
            label={status?.database_reachable ? "System online" : "Checking…"}
          />
          <ThemeToggle />
        </div>
      }
    >
      {step === 0 && <StepConnect status={status} onChanged={refresh} />}
      {step === 1 && <StepDiscover status={status} onChanged={refresh} />}
      {step === 2 && <StepMap />}
      {step === 3 && <StepPreview />}
      {step === 4 && <StepAutomate status={status} onChanged={refresh} />}
    </WizardShell>
  );
}
