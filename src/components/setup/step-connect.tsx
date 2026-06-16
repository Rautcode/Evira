"use client";

import * as React from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { StatusChip } from "./status-chip";
import { getSystemSettings, updateSystemSettings, testConnection } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";

const field = (label: string, node: React.ReactNode) => (
  <div className="space-y-1.5">
    <label className="text-xs font-medium text-slate-400">{label}</label>
    {node}
  </div>
);

export function StepConnect({ onChanged }: { status: any; onChanged: () => void }) {
  const { toast } = useToast();
  const [opcuaUrl, setOpcuaUrl] = React.useState("");
  const [opcuaUser, setOpcuaUser] = React.useState("");
  const [opcuaPass, setOpcuaPass] = React.useState("");
  const [dbServer, setDbServer] = React.useState("");
  const [dbName, setDbName] = React.useState("");
  const [dbAuth, setDbAuth] = React.useState("sql");
  const [dbUser, setDbUser] = React.useState("");
  const [dbPass, setDbPass] = React.useState("");
  const [testing, setTesting] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [test, setTest] = React.useState<any>(null);

  React.useEffect(() => {
    getSystemSettings()
      .then((r) => {
        const d = r.data || {};
        setOpcuaUrl(d.opcua_url || "");
        setOpcuaUser(d.opcua_username || "");
        setDbServer(d.mssql_server || "");
        setDbName(d.mssql_database || "");
        setDbAuth(d.mssql_auth_type || "sql");
        setDbUser(d.mssql_username || "");
      })
      .catch(() => {});
  }, []);

  const payload = () => ({
    opcua_url: opcuaUrl,
    opcua_username: opcuaUser,
    opcua_password: opcuaPass,
    mssql_server: dbServer,
    mssql_database: dbName,
    mssql_auth_type: dbAuth,
    mssql_username: dbUser,
    mssql_password: dbPass,
  });

  const doTest = async () => {
    setTesting(true);
    setTest(null);
    try {
      const r = await testConnection(payload());
      setTest(r.data);
    } catch {
      toast({ title: "Test failed", variant: "destructive" });
    } finally {
      setTesting(false);
    }
  };

  const doSave = async () => {
    setSaving(true);
    try {
      await updateSystemSettings(payload());
      toast({ title: "Connected", description: "Systems saved and reloaded." });
      setOpcuaPass("");
      setDbPass("");
      onChanged();
    } catch {
      toast({ title: "Save failed", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Connect your systems</h1>
        <p className="mt-1 text-slate-400">Point the platform at your SCADA server and database. You only do this once.</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="space-y-4 rounded-xl border border-white/10 bg-slate-900/40 p-5">
          <h3 className="text-sm font-semibold text-white">SCADA OPC UA</h3>
          {field("Server URL", <Input value={opcuaUrl} onChange={(e) => setOpcuaUrl(e.target.value)} placeholder="opc.tcp://192.168.1.100:4840" />)}
          {field("Username (optional)", <Input value={opcuaUser} onChange={(e) => setOpcuaUser(e.target.value)} placeholder="WinCCAdmin" />)}
          {field("Password (optional)", <Input type="password" value={opcuaPass} onChange={(e) => setOpcuaPass(e.target.value)} placeholder="••••••••" />)}
        </div>
        <div className="space-y-4 rounded-xl border border-white/10 bg-slate-900/40 p-5">
          <h3 className="text-sm font-semibold text-white">SQL database</h3>
          {field("Server", <Input value={dbServer} onChange={(e) => setDbServer(e.target.value)} placeholder="192.168.1.50 or host,port" />)}
          {field("Database", <Input value={dbName} onChange={(e) => setDbName(e.target.value)} placeholder="scada_reports" />)}
          {field(
            "Auth method",
            <select value={dbAuth} onChange={(e) => setDbAuth(e.target.value)} className="h-10 w-full rounded-md border border-white/10 bg-slate-900 px-3 text-sm text-slate-100">
              <option value="sql">SQL Server account</option>
              <option value="windows">Windows Active Directory</option>
            </select>
          )}
          {dbAuth === "sql" && (
            <div className="grid grid-cols-2 gap-3">
              {field("Username", <Input value={dbUser} onChange={(e) => setDbUser(e.target.value)} placeholder="sa" />)}
              {field("Password", <Input type="password" value={dbPass} onChange={(e) => setDbPass(e.target.value)} placeholder="••••••••" />)}
            </div>
          )}
        </div>
      </div>

      {test && (
        <div className="flex flex-wrap gap-3">
          <StatusChip state={test.opcua_ok ? "ok" : "error"} label={test.opcua_ok ? "OPC UA reachable" : `OPC UA: ${(test.opcua_error || "failed").slice(0, 48)}`} />
          <StatusChip state={test.mssql_ok ? "ok" : "error"} label={test.mssql_ok ? "SQL reachable" : `SQL: ${(test.mssql_error || "failed").slice(0, 48)}`} />
        </div>
      )}

      <div className="flex gap-3">
        <Button variant="outline" onClick={doTest} disabled={testing}>
          {testing ? "Testing…" : "Test connection"}
        </Button>
        <Button onClick={doSave} disabled={saving} className="bg-teal-500 text-slate-950 hover:bg-teal-400">
          {saving ? "Saving…" : "Save & connect"}
        </Button>
      </div>
    </div>
  );
}
