"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { 
  Settings as SettingsIcon, Database, Mail, Server, CheckCircle2, 
  AlertTriangle, Search, RefreshCw, Cpu, Layers, Info, Wifi, WifiOff, Save, KeyRound 
} from 'lucide-react';
import { getScadaTags, getDashboardStats, getSmtpSettings, updateSmtpSettings, getSystemSettings, updateSystemSettings } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface ScadaTag {
  id: number;
  tag_name: string;
  tag_type: string;
  description: string;
  value: number | null;
  quality: string;
  last_update: string | null;
  machine_id: string;
  active: boolean;
}

interface SystemStatus {
  database: boolean;
  wincc: {
    connected: boolean;
    total_tags: number;
    active_tags: number;
    server_url?: string;
    last_update?: string;
  };
  email: boolean;
  report_engine: boolean;
}

export default function SettingsPage() {
  const [tags, setTags] = React.useState<ScadaTag[]>([]);
  const [systemStatus, setSystemStatus] = React.useState<SystemStatus | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [refreshing, setRefreshing] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const { toast } = useToast();
  
  // SMTP State
  const [smtpServer, setSmtpServer] = React.useState('smtp.gmail.com');
  const [smtpPort, setSmtpPort] = React.useState('587');
  const [smtpUser, setSmtpUser] = React.useState('');
  const [smtpPass, setSmtpPass] = React.useState('');
  const [savingSmtp, setSavingSmtp] = React.useState(false);

  // System Configuration State
  const [opcuaUrl, setOpcuaUrl] = React.useState('');
  const [opcuaUser, setOpcuaUser] = React.useState('');
  const [opcuaPass, setOpcuaPass] = React.useState('');
  
  const [dbServer, setDbServer] = React.useState('');
  const [dbName, setDbName] = React.useState('');
  const [dbAuthType, setDbAuthType] = React.useState('windows');
  const [dbUser, setDbUser] = React.useState('');
  const [dbPass, setDbPass] = React.useState('');
  const [savingSystem, setSavingSystem] = React.useState(false);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = React.useState('');
  const [machineFilter, setMachineFilter] = React.useState('ALL');
  const [paramFilter, setParamFilter] = React.useState('ALL');

  const fetchData = async (showProgress = false) => {
    if (showProgress) setRefreshing(true);
    try {
      const [tagsRes, statsRes] = await Promise.all([
        getScadaTags(),
        getDashboardStats()
      ]);
      
      if (tagsRes.status === 200) {
        setTags(tagsRes.data || []);
      }
      if (statsRes.status === 200) {
        setSystemStatus(statsRes.data.system_status || null);
      }
      setError(null);
    } catch (err) {
      console.error("Failed to load settings data", err);
      setError("Failed to fetch settings and SCADA configuration data from server.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  React.useEffect(() => {
    fetchData();
    
    // Load local SMTP from backend
    getSmtpSettings().then(res => {
      if (res.data) {
        setSmtpServer(res.data.host || 'smtp.gmail.com');
        setSmtpPort(res.data.port ? String(res.data.port) : '587');
        setSmtpUser(res.data.user || '');
      }
    }).catch(e => console.error("Failed to load SMTP settings", e));

    // Load System Configuration from backend
    getSystemSettings().then(res => {
      if (res.data) {
        setOpcuaUrl(res.data.opcua_url || '');
        setOpcuaUser(res.data.opcua_username || '');
        setDbServer(res.data.mssql_server || '');
        setDbName(res.data.mssql_database || '');
        setDbAuthType(res.data.mssql_auth_type || 'windows');
        setDbUser(res.data.mssql_username || '');
      }
    }).catch(e => console.error("Failed to load System Settings", e));

    // Auto-refresh tag values every 5 seconds
    const interval = setInterval(() => {
      fetchData(false);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleSaveSmtp = async () => {
    setSavingSmtp(true);
    try {
      await updateSmtpSettings({
        host: smtpServer,
        port: parseInt(smtpPort) || 587,
        user: smtpUser,
        password: smtpPass
      });
      toast({ title: 'SMTP Settings Saved', description: 'Your email credentials have been securely stored.' });
      setSmtpPass(''); // clear password field after save
    } catch (e) {
      toast({ title: 'Failed to Save', description: 'Network error or invalid credentials.', variant: 'destructive' });
    } finally {
      setSavingSmtp(false);
    }
  };

  const handleSaveSystemSettings = async () => {
    setSavingSystem(true);
    try {
      await updateSystemSettings({
        opcua_url: opcuaUrl,
        opcua_username: opcuaUser,
        opcua_password: opcuaPass,
        mssql_server: dbServer,
        mssql_database: dbName,
        mssql_auth_type: dbAuthType,
        mssql_username: dbUser,
        mssql_password: dbPass
      });
      toast({ title: 'System Connections Saved', description: 'Backend services have been hot-reloaded with the new connections.' });
      setOpcuaPass(''); // clear password fields
      setDbPass('');
    } catch (e) {
      toast({ title: 'Failed to Save', description: 'Network error or invalid configurations.', variant: 'destructive' });
    } finally {
      setSavingSystem(false);
    }
  };

  // Filter tags list based on queries
  const filteredTags = React.useMemo(() => {
    return tags.filter(tag => {
      const matchesSearch = 
        tag.tag_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tag.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tag.tag_type.toLowerCase().includes(searchQuery.toLowerCase()) ||
        tag.machine_id.toLowerCase().includes(searchQuery.toLowerCase());
        
      const matchesMachine = machineFilter === 'ALL' || tag.machine_id === machineFilter;
      const matchesParam = paramFilter === 'ALL' || tag.tag_type === paramFilter;
      
      return matchesSearch && matchesMachine && matchesParam;
    });
  }, [tags, searchQuery, machineFilter, paramFilter]);

  // Compute machine stats
  const machineStats = React.useMemo(() => {
    const counts: Record<string, number> = {
      M001: 0,
      M002: 0,
      M003: 0,
      M004: 0,
      M005: 0
    };
    tags.forEach(tag => {
      if (counts[tag.machine_id] !== undefined) {
        counts[tag.machine_id]++;
      }
    });
    return counts;
  }, [tags]);

  const machineNames: Record<string, string> = {
    M001: 'Extruder Alpha',
    M002: 'Injection Molder',
    M003: 'Cooling Chiller',
    M004: 'Packager unit',
    M005: 'High-Shear Mixer'
  };

  return (
    <div className="container mx-auto py-8 space-y-8 animate-fade-in">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-foreground tracking-tight flex items-center">
            <SettingsIcon className="mr-3 h-8 w-8 text-primary animate-spin-slow" />
            System & SCADA Settings
          </h1>
          <p className="text-muted-foreground mt-1">
            Monitor real-time OPC UA auto-discovery status, check tag mappings, and inspect system health.
          </p>
        </div>
        <Button 
          variant="outline" 
          size="sm" 
          onClick={() => fetchData(true)} 
          disabled={refreshing}
          className="shadow-sm transition-all"
        >
          <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
          {refreshing ? 'Refreshing...' : 'Refresh Mappings'}
        </Button>
      </div>

      {error && (
        <Card className="border-red-500 bg-red-500/10 text-red-500">
          <CardContent className="p-4 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-3 flex-shrink-0" />
            <p className="text-sm font-medium">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Grid: Server Connection Status & Machine Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* OPC UA Server status Card */}
        <Card className="shadow-md border-border bg-card overflow-hidden">
          <CardHeader className="border-b pb-4 bg-muted/20">
            <CardTitle className="text-lg flex items-center justify-between">
              <span className="flex items-center">
                <Cpu className="mr-2 h-5 w-5 text-primary" />
                Siemens WinCC OPC UA
              </span>
              {systemStatus?.wincc?.connected ? (
                <Badge variant="default" className="bg-green-500 hover:bg-green-600 flex items-center gap-1">
                  <Wifi className="h-3 w-3" /> Connected
                </Badge>
              ) : (
                <Badge variant="destructive" className="animate-pulse flex items-center gap-1">
                  <WifiOff className="h-3 w-3" /> Reconnecting
                </Badge>
              )}
            </CardTitle>
            <CardDescription className="font-mono text-xs break-all mt-1">
              Endpoint: {systemStatus?.wincc?.server_url || 'opc.tcp://localhost:4840'}
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="flex justify-between items-center text-sm border-b pb-2">
              <span className="text-muted-foreground">Total Discovered Tags</span>
              <span className="font-bold text-foreground font-mono">{systemStatus?.wincc?.total_tags ?? 0}</span>
            </div>
            <div className="flex justify-between items-center text-sm border-b pb-2">
              <span className="text-muted-foreground">Active Subscriptions</span>
              <span className="font-bold text-foreground font-mono text-green-500">{systemStatus?.wincc?.active_tags ?? 0}</span>
            </div>
            <div className="flex justify-between items-center text-sm">
              <span className="text-muted-foreground">Last Crawl Discovery</span>
              <span className="text-xs text-muted-foreground font-mono">
                {systemStatus?.wincc?.last_update ? new Date(systemStatus.wincc.last_update).toLocaleTimeString() : 'Never'}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Machine Mappings Card */}
        <Card className="lg:col-span-2 shadow-md border-border bg-card">
          <CardHeader className="border-b pb-4 bg-muted/20">
            <CardTitle className="text-lg flex items-center">
              <Layers className="mr-2 h-5 w-5 text-primary" />
              Machine Mappings Summary
            </CardTitle>
            <CardDescription>
              Count of auto-discovered OPC UA tags mapped to active factory floor machines.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-4">
              {Object.entries(machineStats).map(([mId, count]) => (
                <div key={mId} className="flex flex-col items-center justify-center p-3 rounded-lg border bg-muted/20 hover:bg-muted/40 transition-colors">
                  <span className="text-xs font-bold text-primary font-mono">{mId}</span>
                  <span className="text-xs text-muted-foreground text-center truncate w-full max-w-[120px]" title={machineNames[mId]}>
                    {machineNames[mId]}
                  </span>
                  <span className="text-2xl font-black mt-2 font-mono">{count}</span>
                  <span className="text-[10px] text-muted-foreground">tags</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Main Tags List Table */}
      <Card className="shadow-md border-border bg-card">
        <CardHeader className="border-b pb-4 bg-muted/20 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <CardTitle className="text-xl">Auto-Discovered SCADA Tags</CardTitle>
            <CardDescription>
              List of all tag endpoints recursively crawled on the WinCC Server. Values update live.
            </CardDescription>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="relative w-full sm:w-60">
              <Search className="absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search tags or description..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                className="pl-9 h-9 text-xs"
              />
            </div>
            {/* Machine Filter Dropdown */}
            <select
              value={machineFilter}
              onChange={e => setMachineFilter(e.target.value)}
              className="h-9 px-3 text-xs bg-background border border-input rounded-md text-foreground shadow-sm focus:outline-none"
            >
              <option value="ALL">All Machines</option>
              <option value="M001">M001 - Extruder</option>
              <option value="M002">M002 - Molder</option>
              <option value="M003">M003 - Chiller</option>
              <option value="M004">M004 - Packager</option>
              <option value="M005">M005 - Mixer</option>
            </select>
            {/* Parameter Filter Dropdown */}
            <select
              value={paramFilter}
              onChange={e => setParamFilter(e.target.value)}
              className="h-9 px-3 text-xs bg-background border border-input rounded-md text-foreground shadow-sm focus:outline-none"
            >
              <option value="ALL">All Parameters</option>
              <option value="Temperature">Temperature</option>
              <option value="Pressure">Pressure</option>
              <option value="Speed">Speed</option>
              <option value="Clamping Force">Clamping Force</option>
              <option value="Flow Rate">Flow Rate</option>
              <option value="Pack Count">Pack Count</option>
            </select>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
              <p className="text-sm text-muted-foreground mt-4 font-medium">Discovering SCADA nodes...</p>
            </div>
          ) : filteredTags.length === 0 ? (
            <div className="text-center py-16">
              <AlertTriangle className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
              <h3 className="font-semibold text-foreground text-sm">No tags found</h3>
              <p className="text-xs text-muted-foreground mt-1">
                Try adjusting your search queries or filter dropdowns.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/10">
                    <TableHead className="w-16 text-center font-bold">#</TableHead>
                    <TableHead className="font-semibold text-xs">Node ID (Tag Name)</TableHead>
                    <TableHead className="font-semibold text-xs w-48">Mapped Machine</TableHead>
                    <TableHead className="font-semibold text-xs w-36">Parameter Type</TableHead>
                    <TableHead className="font-semibold text-xs w-32 text-right">Live Value</TableHead>
                    <TableHead className="font-semibold text-xs w-28 text-center">Quality</TableHead>
                    <TableHead className="font-semibold text-xs w-44">Last Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredTags.map((tag, idx) => (
                    <TableRow key={tag.id} className="hover:bg-muted/5 transition-colors">
                      <TableCell className="text-center font-mono text-xs text-muted-foreground">
                        {idx + 1}
                      </TableCell>
                      <TableCell className="font-mono text-xs font-semibold text-foreground break-all">
                        {tag.tag_name}
                        {tag.description && (
                          <div className="text-[10px] text-muted-foreground font-normal mt-0.5 font-sans">
                            {tag.description}
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="text-xs font-bold text-primary font-mono">{tag.machine_id}</span>
                          <span className="text-[10px] text-muted-foreground truncate w-40" title={machineNames[tag.machine_id]}>
                            {machineNames[tag.machine_id]}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-[10px] font-semibold py-0.5">
                          {tag.tag_type}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right font-mono text-xs font-bold text-foreground">
                        {tag.value !== null ? `${tag.value.toFixed(2)} ${tag.tag_type === 'Temperature' ? '°C' : tag.tag_type === 'Pressure' ? 'bar' : tag.tag_type === 'Speed' ? 'RPM' : tag.tag_type === 'Clamping Force' ? 'kN' : tag.tag_type === 'Flow Rate' ? 'L/min' : tag.tag_type === 'Pack Count' ? 'pcs' : ''}` : 'N/A'}
                      </TableCell>
                      <TableCell className="text-center">
                        <Badge 
                          variant="outline" 
                          className={`text-[10px] font-semibold border-none py-0.5 ${
                            tag.quality.toLowerCase() === 'good' ? 'bg-green-500/10 text-green-500' : 'bg-yellow-500/10 text-yellow-500'
                          }`}
                        >
                          {tag.quality}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-xs text-muted-foreground font-mono">
                        {tag.last_update ? new Date(tag.last_update).toLocaleTimeString() : 'N/A'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Grid: Heuristic Documentation & Overall Health */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* System Health */}
        <Card className="shadow-md border-border bg-card">
          <CardHeader className="border-b pb-4 bg-muted/20">
            <CardTitle className="text-lg flex items-center">
              <Database className="mr-2 h-5 w-5 text-primary" />
              Connected System Health Status
            </CardTitle>
            <CardDescription>
              Real-time integration health of backend application-wide systems.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground flex items-center gap-2">
                <Database className="h-4 w-4" /> SQL Server Database
              </span>
              <span className="flex items-center gap-1.5 font-semibold text-xs">
                {systemStatus?.database ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-green-500" /> Operational
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4 w-4 text-red-500 animate-pulse" /> Disconnected
                  </>
                )}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground flex items-center gap-2">
                <Server className="h-4 w-4" /> WinCC OPC UA Driver
              </span>
              <span className="flex items-center gap-1.5 font-semibold text-xs">
                {systemStatus?.wincc?.connected ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-green-500" /> Active Subscription
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4 w-4 text-yellow-500 animate-pulse" /> Reconnecting...
                  </>
                )}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground flex items-center gap-2">
                <Mail className="h-4 w-4" /> SMTP Email Server
              </span>
              <span className="flex items-center gap-1.5 font-semibold text-xs">
                {systemStatus?.email ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-green-500" /> Online
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4 w-4 text-yellow-500" /> Degraded / Unset
                  </>
                )}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground flex items-center gap-2">
                <Cpu className="h-4 w-4" /> Report lab PDF Engine
              </span>
              <span className="flex items-center gap-1.5 font-semibold text-xs">
                {systemStatus?.report_engine ? (
                  <>
                    <CheckCircle2 className="h-4 w-4 text-green-500" /> Standby (Ready)
                  </>
                ) : (
                  <>
                    <AlertTriangle className="h-4 w-4 text-red-500" /> Error
                  </>
                )}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Heuristic Explanation */}
        <Card className="shadow-md border-border bg-card">
          <CardHeader className="border-b pb-4 bg-muted/20">
            <CardTitle className="text-lg flex items-center">
              <Info className="mr-2 h-5 w-5 text-primary" />
              Auto-Discovery Mapping Rules
            </CardTitle>
            <CardDescription>
              How our backend driver dynamically resolves OPC UA tags to report columns.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-6 text-sm text-muted-foreground space-y-3 leading-relaxed">
            <p>
              When the application starts, it performs a **recursive crawl** of the OPC UA server objects directory.
              Each discovered variable node is mapped to our metrics database using the following heuristics:
            </p>
            <ul className="list-disc pl-5 space-y-1.5 text-xs">
              <li>
                <strong className="text-foreground">Machine IDs:</strong> Matches tag path substrings. E.g., `extruder` maps to <strong className="text-foreground">M001</strong>, `molding` to <strong className="text-foreground">M002</strong>, `chiller/cooling` to <strong className="text-foreground">M003</strong>.
              </li>
              <li>
                <strong className="text-foreground">Parameters & Units:</strong> 
                Names containing `temp` map as <strong className="text-foreground">Temperature (°C)</strong>; `press` as <strong className="text-foreground">Pressure (bar)</strong>; `speed` or `rpm` as <strong className="text-foreground">Speed (RPM)</strong>; `force` as <strong className="text-foreground">Clamping Force (kN)</strong>.
              </li>
              <li>
                <strong className="text-foreground">Database Sync:</strong> New discovered tags are stored in the `wincc_tags` database table automatically, making them immediately available for report filters.
              </li>
            </ul>
          </CardContent>
        </Card>
      </div>

      {/* SMTP Configuration Form */}
      <Card className="shadow-md border-border bg-card">
        <CardHeader className="border-b pb-4 bg-muted/20">
          <CardTitle className="text-lg flex items-center">
            <Mail className="mr-2 h-5 w-5 text-primary" />
            SMTP Email Server Configuration
          </CardTitle>
          <CardDescription>Configure outgoing mail server for automated report dispatch.</CardDescription>
        </CardHeader>
        <CardContent className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-3xl">
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">SMTP Server</label>
              <Input value={smtpServer} onChange={e => setSmtpServer(e.target.value)} placeholder="e.g. smtp.gmail.com" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">SMTP Port</label>
              <Input value={smtpPort} onChange={e => setSmtpPort(e.target.value)} placeholder="e.g. 587" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Username / Email</label>
              <Input value={smtpUser} onChange={e => setSmtpUser(e.target.value)} placeholder="admin@factory.com" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">App Password</label>
              <Input value={smtpPass} onChange={e => setSmtpPass(e.target.value)} type="password" placeholder="••••••••••••" />
            </div>
          </div>
          <div className="mt-6 flex justify-end">
            <Button onClick={handleSaveSmtp} disabled={savingSmtp}>
              {savingSmtp ? 'Saving...' : <><Save className="w-4 h-4 mr-2" /> Save SMTP Configuration</>}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* System Configuration Forms */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="shadow-md border-border bg-card">
          <CardHeader className="border-b pb-4 bg-muted/20">
            <CardTitle className="text-lg flex items-center">
              <Server className="mr-2 h-5 w-5 text-primary" />
              SCADA OPC UA Connection
            </CardTitle>
            <CardDescription>Live telemetry subscription source.</CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">OPC UA Server URL</label>
              <Input value={opcuaUrl} onChange={e => setOpcuaUrl(e.target.value)} placeholder="opc.tcp://192.168.1.100:4840" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Username (Optional)</label>
              <Input value={opcuaUser} onChange={e => setOpcuaUser(e.target.value)} placeholder="WinCCAdmin" />
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Password (Optional)</label>
              <Input value={opcuaPass} onChange={e => setOpcuaPass(e.target.value)} type="password" placeholder="••••••••••••" />
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-md border-border bg-card">
          <CardHeader className="border-b pb-4 bg-muted/20">
            <CardTitle className="text-lg flex items-center">
              <Database className="mr-2 h-5 w-5 text-primary" />
              SQL Database Connection
            </CardTitle>
            <CardDescription>Backend metrics and report storage.</CardDescription>
          </CardHeader>
          <CardContent className="p-6 space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Server IP</label>
                <Input value={dbServer} onChange={e => setDbServer(e.target.value)} placeholder="192.168.1.50" />
              </div>
              <div className="space-y-2">
                <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Database</label>
                <Input value={dbName} onChange={e => setDbName(e.target.value)} placeholder="scada_reports" />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Auth Method</label>
              <select
                value={dbAuthType}
                onChange={e => setDbAuthType(e.target.value)}
                className="w-full h-10 px-3 text-sm bg-background border border-input rounded-md text-foreground focus:outline-none"
              >
                <option value="windows">Windows Active Directory</option>
                <option value="sql">SQL Server Account</option>
              </select>
            </div>
            {dbAuthType === 'sql' && (
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500">DB Username</label>
                  <Input value={dbUser} onChange={e => setDbUser(e.target.value)} placeholder="sa" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500">DB Password</label>
                  <Input value={dbPass} onChange={e => setDbPass(e.target.value)} type="password" placeholder="••••••••••••" />
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="flex justify-end pt-2 pb-8">
        <Button size="lg" onClick={handleSaveSystemSettings} disabled={savingSystem} className="w-full md:w-auto shadow-lg hover:shadow-xl transition-shadow bg-blue-600 hover:bg-blue-700 text-white">
          {savingSystem ? 'Applying New Configuration...' : <><KeyRound className="w-5 h-5 mr-2" /> Connect Systems & Hot-Reload</>}
        </Button>
      </div>

    </div>
  );
}
