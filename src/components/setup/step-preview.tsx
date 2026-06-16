"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { getMachineList, getReportPreview } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export function StepPreview() {
  const { toast } = useToast();
  const [machines, setMachines] = React.useState<any[]>([]);
  const [machine, setMachine] = React.useState("all");
  const [shift, setShift] = React.useState("full");
  const [type, setType] = React.useState("production_summary");
  const [rows, setRows] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(false);

  React.useEffect(() => {
    getMachineList()
      .then((r) => {
        const m = r.data?.data?.machines || (Array.isArray(r.data) ? r.data : []);
        setMachines(m);
      })
      .catch(() => {});
  }, []);

  const preview = async () => {
    setLoading(true);
    const end = new Date();
    const start = new Date();
    start.setDate(end.getDate() - 7);
    try {
      const r = await getReportPreview({
        date_range: { start: start.toISOString().slice(0, 10), end: end.toISOString().slice(0, 10) },
        machine_id: machine,
        shift,
        report_type: type,
      });
      const data = Array.isArray(r.data) ? r.data : [];
      setRows(data);
      if (!data.length) toast({ title: "No data in range", description: "Try a wider date range or another machine." });
    } catch {
      toast({ title: "Preview failed", variant: "destructive" });
    } finally {
      setLoading(false);
    }
  };

  const sel = (v: string, set: (x: string) => void, opts: [string, string][]) => (
    <select value={v} onChange={(e) => set(e.target.value)} className="h-10 rounded-md border border-border bg-background px-3 text-sm text-foreground">
      {opts.map(([val, lab]) => (
        <option key={val} value={val}>{lab}</option>
      ))}
    </select>
  );

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Preview your data</h1>
        <p className="mt-1 text-muted-foreground">Pick a scope and see the exact data your report will use — before you generate it.</p>
      </div>

      <div className="flex flex-wrap items-end gap-3">
        {sel(machine, setMachine, [["all", "All machines"], ...machines.map((m: any) => [m.id, `${m.id} - ${m.name}`] as [string, string])])}
        {sel(shift, setShift, [["full", "All shifts"], ["Morning", "Morning"], ["Evening", "Evening"], ["Night", "Night"]])}
        {sel(type, setType, [["production_summary", "Production summary"], ["downtime_analysis", "Downtime analysis"], ["quality_metrics", "Quality metrics"]])}
        <Button onClick={preview} disabled={loading} className="bg-primary text-primary-foreground hover:bg-primary/90">
          {loading ? "Loading…" : "Preview data"}
        </Button>
      </div>

      <div className="overflow-hidden rounded-xl border border-border">
        <div className="max-h-72 overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-muted-foreground">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Timestamp</th>
                <th className="px-4 py-2 text-left font-medium">Machine</th>
                <th className="px-4 py-2 text-left font-medium">Parameter</th>
                <th className="px-4 py-2 text-right font-medium">Value</th>
              </tr>
            </thead>
            <tbody>
              {rows.length === 0 ? (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">Run a preview to see live data here.</td></tr>
              ) : (
                rows.slice(0, 100).map((r, i) => (
                  <tr key={i} className="border-t border-border">
                    <td className="px-4 py-2 font-mono text-xs text-foreground">{String(r.timestamp).slice(0, 19)}</td>
                    <td className="px-4 py-2 text-foreground">{r.machine}</td>
                    <td className="px-4 py-2 text-muted-foreground">{r.parameter}</td>
                    <td className="px-4 py-2 text-right font-mono text-foreground">{r.value} {r.unit}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
