"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tags, Plus, Trash2, RefreshCw } from 'lucide-react';
import {
  getTagMappingRules, createTagMappingRule, deleteTagMappingRule, reloadTagMapping,
} from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface Rule {
  id: number;
  rule_type: 'machine' | 'parameter';
  match_text: string;
  machine_id?: string | null;
  parameter?: string | null;
  unit?: string | null;
  priority: number;
  active: boolean;
}

export function TagMappingManager() {
  const [rules, setRules] = React.useState<Rule[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [reloading, setReloading] = React.useState(false);
  const [saving, setSaving] = React.useState(false);

  // New-rule form
  const [ruleType, setRuleType] = React.useState<'machine' | 'parameter'>('machine');
  const [matchText, setMatchText] = React.useState('');
  const [machineId, setMachineId] = React.useState('');
  const [parameter, setParameter] = React.useState('');
  const [unit, setUnit] = React.useState('');

  const { toast } = useToast();

  const load = React.useCallback(async () => {
    try {
      const res = await getTagMappingRules();
      setRules(res.data || []);
    } catch {
      toast({ title: 'Failed to load mapping rules', variant: 'destructive' });
    } finally {
      setLoading(false);
    }
  }, [toast]);

  React.useEffect(() => { load(); }, [load]);

  const addRule = async () => {
    if (!matchText.trim()) {
      toast({ title: 'Match text is required', variant: 'destructive' });
      return;
    }
    if (ruleType === 'machine' && !machineId.trim()) {
      toast({ title: 'Machine ID is required', variant: 'destructive' });
      return;
    }
    if (ruleType === 'parameter' && !parameter.trim()) {
      toast({ title: 'Parameter is required', variant: 'destructive' });
      return;
    }
    setSaving(true);
    try {
      await createTagMappingRule({
        rule_type: ruleType,
        match_text: matchText.trim().toLowerCase(),
        machine_id: ruleType === 'machine' ? machineId.trim() : null,
        parameter: ruleType === 'parameter' ? parameter.trim() : null,
        unit: ruleType === 'parameter' ? unit.trim() : null,
        priority: 50,
        active: true,
      });
      toast({ title: 'Rule added', description: 'Re-map tags to apply it to live data.' });
      setMatchText(''); setMachineId(''); setParameter(''); setUnit('');
      load();
    } catch (e: any) {
      toast({ title: 'Failed to add rule', description: e?.response?.data?.detail, variant: 'destructive' });
    } finally {
      setSaving(false);
    }
  };

  const removeRule = async (id: number) => {
    try {
      await deleteTagMappingRule(id);
      toast({ title: 'Rule deleted' });
      load();
    } catch {
      toast({ title: 'Failed to delete rule', variant: 'destructive' });
    }
  };

  const remap = async () => {
    setReloading(true);
    try {
      const res = await reloadTagMapping();
      toast({ title: 'Mapping reloaded', description: res.data?.message });
    } catch {
      toast({ title: 'Reload failed', variant: 'destructive' });
    } finally {
      setReloading(false);
    }
  };

  const machineRules = rules.filter((r) => r.rule_type === 'machine');
  const paramRules = rules.filter((r) => r.rule_type === 'parameter');

  const RuleTable = ({ title, items, target }: { title: string; items: Rule[]; target: 'machine' | 'parameter' }) => (
    <div>
      <h4 className="text-sm font-semibold text-foreground mb-2">{title} <span className="text-muted-foreground font-normal">({items.length})</span></h4>
      <div className="rounded-md border overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/10">
              <TableHead className="text-sm">If tag name contains…</TableHead>
              <TableHead className="text-sm">{target === 'machine' ? 'Map to machine' : 'Map to parameter'}</TableHead>
              <TableHead className="text-sm w-16 text-center">Active</TableHead>
              <TableHead className="w-12"></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {items.length === 0 ? (
              <TableRow><TableCell colSpan={4} className="text-center text-sm text-muted-foreground py-4">No rules yet</TableCell></TableRow>
            ) : items.map((r) => (
              <TableRow key={r.id} className="hover:bg-muted/5">
                <TableCell className="font-mono text-sm">{r.match_text}</TableCell>
                <TableCell className="text-sm">
                  {target === 'machine'
                    ? <Badge variant="secondary">{r.machine_id}</Badge>
                    : <span>{r.parameter}{r.unit ? <span className="text-muted-foreground"> ({r.unit})</span> : null}</span>}
                </TableCell>
                <TableCell className="text-center">
                  <Badge variant="outline" className={r.active ? 'bg-green-500/10 text-green-600 border-none' : 'bg-slate-500/10 text-slate-500 border-none'}>
                    {r.active ? 'Yes' : 'No'}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500 hover:text-red-600 hover:bg-red-500/10" onClick={() => removeRule(r.id)} aria-label="Delete rule">
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  );

  return (
    <Card className="shadow-md border-border bg-card">
      <CardHeader className="border-b pb-4 bg-muted/20 flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div>
          <CardTitle className="text-lg flex items-center">
            <Tags className="mr-2 h-5 w-5 text-primary" />
            Tag Mapping Rules
          </CardTitle>
          <CardDescription>
            Teach the app how your WinCC tag names map to machines and parameters. Matching is case-insensitive substring.
          </CardDescription>
        </div>
        <Button variant="outline" size="sm" onClick={remap} disabled={reloading}>
          <RefreshCw className={`h-4 w-4 mr-2 ${reloading ? 'animate-spin' : ''}`} />
          {reloading ? 'Re-mapping…' : 'Re-map Tags'}
        </Button>
      </CardHeader>
      <CardContent className="p-6 space-y-6">
        {/* Add-rule form */}
        <div className="flex flex-col lg:flex-row lg:items-end gap-3 p-4 rounded-lg border bg-muted/10">
          <div className="space-y-1">
            <label className="text-xs font-semibold text-muted-foreground">Rule type</label>
            <select
              value={ruleType}
              onChange={(e) => setRuleType(e.target.value as 'machine' | 'parameter')}
              className="h-10 px-3 text-sm bg-background border border-input rounded-md w-full lg:w-40"
            >
              <option value="machine">Machine</option>
              <option value="parameter">Parameter</option>
            </select>
          </div>
          <div className="space-y-1 flex-1">
            <label className="text-xs font-semibold text-muted-foreground">If tag contains</label>
            <Input value={matchText} onChange={(e) => setMatchText(e.target.value)} placeholder="e.g. extruder, rx100, temp" className="h-10" />
          </div>
          {ruleType === 'machine' ? (
            <div className="space-y-1 flex-1">
              <label className="text-xs font-semibold text-muted-foreground">Map to machine ID</label>
              <Input value={machineId} onChange={(e) => setMachineId(e.target.value)} placeholder="e.g. M001" className="h-10" />
            </div>
          ) : (
            <>
              <div className="space-y-1 flex-1">
                <label className="text-xs font-semibold text-muted-foreground">Parameter</label>
                <Input value={parameter} onChange={(e) => setParameter(e.target.value)} placeholder="e.g. Temperature" className="h-10" />
              </div>
              <div className="space-y-1 w-full lg:w-28">
                <label className="text-xs font-semibold text-muted-foreground">Unit</label>
                <Input value={unit} onChange={(e) => setUnit(e.target.value)} placeholder="e.g. C" className="h-10" />
              </div>
            </>
          )}
          <Button onClick={addRule} disabled={saving} className="h-10">
            <Plus className="h-4 w-4 mr-1" /> {saving ? 'Adding…' : 'Add Rule'}
          </Button>
        </div>

        {loading ? (
          <p className="text-sm text-muted-foreground text-center py-6">Loading rules…</p>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <RuleTable title="Machine Rules" items={machineRules} target="machine" />
            <RuleTable title="Parameter Rules" items={paramRules} target="parameter" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
