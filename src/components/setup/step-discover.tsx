"use client";

import * as React from "react";
import { Button } from "@/components/ui/button";
import { StatusChip } from "./status-chip";
import { getScadaTags, reloadTagMapping } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

export function StepDiscover({ status, onChanged }: { status: any; onChanged: () => void }) {
  const { toast } = useToast();
  const [tags, setTags] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [scanning, setScanning] = React.useState(false);

  const load = React.useCallback(async () => {
    try {
      const r = await getScadaTags();
      setTags(r.data || []);
    } catch {
      /* ignore */
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const rescan = async () => {
    setScanning(true);
    try {
      const r = await reloadTagMapping();
      toast({ title: "Re-scan triggered", description: r.data?.message });
      await load();
      onChanged();
    } catch {
      toast({ title: "Re-scan failed", variant: "destructive" });
    } finally {
      setScanning(false);
    }
  };

  const connected = status?.steps?.connect?.wincc_connected;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Discover your tags</h1>
        <p className="mt-1 text-slate-400">The platform crawls your SCADA server and lists every variable it finds.</p>
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <StatusChip state={connected ? "ok" : "pending"} label={connected ? "OPC UA connected" : "Waiting for OPC UA"} />
        <StatusChip state={tags.length ? "ok" : "idle"} label={`${tags.length} tags discovered`} />
        <div className="ml-auto">
          <Button variant="outline" onClick={rescan} disabled={scanning}>
            {scanning ? "Scanning…" : "Re-scan now"}
          </Button>
        </div>
      </div>

      <div className="overflow-hidden rounded-xl border border-white/10">
        <div className="max-h-72 overflow-auto">
          <table className="w-full text-sm">
            <thead className="bg-white/5 text-slate-400">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Tag</th>
                <th className="px-4 py-2 text-left font-medium">Machine</th>
                <th className="px-4 py-2 text-left font-medium">Type</th>
                <th className="px-4 py-2 text-right font-medium">Value</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-500">Loading…</td></tr>
              ) : tags.length === 0 ? (
                <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-500">No tags yet. Connect your OPC UA server in step 1, then Re-scan.</td></tr>
              ) : (
                tags.slice(0, 100).map((t) => (
                  <tr key={t.id} className="border-t border-white/5">
                    <td className="px-4 py-2 font-mono text-xs text-slate-200">{t.tag_name}</td>
                    <td className="px-4 py-2 text-slate-300">{t.machine_id}</td>
                    <td className="px-4 py-2 text-slate-400">{t.tag_type}</td>
                    <td className="px-4 py-2 text-right font-mono text-slate-200">{t.value ?? "—"}</td>
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
