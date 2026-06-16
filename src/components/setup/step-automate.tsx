"use client";

import * as React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { createSchedule, getTemplates } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const field = (label: string, node: React.ReactNode) => (
  <div className="space-y-1.5">
    <label className="text-xs font-medium text-muted-foreground">{label}</label>
    {node}
  </div>
);

export function StepAutomate({ onChanged }: { status: any; onChanged: () => void }) {
  const { toast } = useToast();
  const [title, setTitle] = React.useState("Daily production report");
  const [cron, setCron] = React.useState("0 6 * * *");
  const [recipients, setRecipients] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [templates, setTemplates] = React.useState<any[]>([]);

  React.useEffect(() => {
    getTemplates().then((r) => setTemplates(r.data || [])).catch(() => {});
  }, []);

  const save = async () => {
    setSaving(true);
    try {
      await createSchedule({
        title,
        template_id: templates[0]?.id || "production_summary",
        machine_id: "all",
        cron_expression: cron,
        report_type: "pdf",
        recipients,
      });
      toast({ title: "Schedule created", description: "Reports will be generated automatically." });
      onChanged();
    } catch (e: any) {
      toast({ title: "Could not create schedule", description: e?.response?.data?.detail, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Automate your reports</h1>
        <p className="mt-1 text-muted-foreground">Optional: schedule a report to generate and email itself. You can also do this later from the Scheduler.</p>
      </div>

      <div className="grid max-w-2xl grid-cols-1 gap-4 rounded-xl border border-border bg-muted/40 p-5 md:grid-cols-2">
        {field("Report name", <Input value={title} onChange={(e) => setTitle(e.target.value)} />)}
        {field("Schedule (cron)", <Input value={cron} onChange={(e) => setCron(e.target.value)} placeholder="0 6 * * *" />)}
        <div className="md:col-span-2">
          {field("Email recipients (comma-separated)", <Input value={recipients} onChange={(e) => setRecipients(e.target.value)} placeholder="manager@factory.com" />)}
        </div>
      </div>

      <Button onClick={save} disabled={saving} className="bg-primary text-primary-foreground hover:bg-primary/90">
        {saving ? "Saving…" : "Create schedule"}
      </Button>

      <p className="text-sm text-muted-foreground">
        When you&apos;re done, click <span className="font-medium text-foreground">Finish setup</span> to head to your dashboard.
      </p>
    </div>
  );
}
