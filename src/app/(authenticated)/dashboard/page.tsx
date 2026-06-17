"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {
  BarChart3, FilePlus, CalendarClock, Users, AlertTriangle,
  CheckCircle2, Mail, Database, Activity, Server, Bell, X
} from 'lucide-react';
import { getDashboardAlerts } from '@/lib/api';
import Link from 'next/link';
import { formatDistanceToNow } from 'date-fns';
import { motion } from 'framer-motion';

// Helper functions for formatting and displaying data
const getAllSystemsOperational = (status: any) => {
  return status.database && 
         status.wincc.connected && 
         status.email && 
         status.report_engine;
};

const getSystemStatusDescription = (status: any) => {
  const issues = [];
  if (!status.database) issues.push('Database');
  if (!status.wincc.connected) issues.push('WinCC');
  if (!status.email) issues.push('Email');
  if (!status.report_engine) issues.push('Report Engine');
  
  if (issues.length === 0) return 'All systems operational';
  return `Issues: ${issues.join(', ')}`;
};

const formatRelativeTime = (dateString: string) => {
  try {
    const date = new Date(dateString);
    return formatDistanceToNow(date, { addSuffix: true });
  } catch (e) {
    return dateString;
  }
};

const getActivityIcon = (eventType: string) => {
  switch (eventType.toLowerCase()) {
    case 'report':
      return FilePlus;
    case 'login':
    case 'user':
      return Users;
    case 'template':
      return BarChart3;
    case 'scheduler':
      return CalendarClock;
    case 'error':
      return AlertTriangle;
    case 'email':
      return Mail;
    case 'database':
      return Database;
    case 'wincc':
      return Server;
    default:
      return Activity;
  }
};

const getActivityColor = (severity: string) => {
  switch (severity.toLowerCase()) {
    case 'error':
      return 'text-red-500';
    case 'warning':
      return 'text-yellow-500';
    case 'success':
      return 'text-green-500';
    case 'info':
    default:
      return 'text-blue-500';
  }
};

const formatDate = (date: Date): string => {
  return new Intl.DateTimeFormat('en-US', {
    weekday: 'long',
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(date);
};

interface StatCardProps {
  title: string;
  value: string;
  icon: React.ElementType;
  description?: string;
  trend?: string;
  trendDirection?: 'up' | 'down';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, icon: Icon, description, trend, trendDirection }) => (
  <motion.div
    whileHover={{ y: -5, scale: 1.02 }}
    transition={{ type: "spring", stiffness: 300 }}
  >
    <Card className="glass-card-premium group relative overflow-hidden bg-white/60 dark:bg-slate-950/40 border-slate-200/50 dark:border-slate-800/40 hover:shadow-2xl duration-300 h-full">
      <div className="absolute top-0 right-0 -mt-4 -mr-4 w-24 h-24 bg-primary/5 dark:bg-primary/10 rounded-full blur-xl group-hover:scale-150 transition-transform duration-500"></div>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2 relative z-10">
        <CardTitle className="text-xs font-bold tracking-wider uppercase text-slate-500 dark:text-slate-400">{title}</CardTitle>
        <div className="p-2 rounded-xl bg-slate-100 dark:bg-slate-900 text-slate-600 dark:text-slate-300 group-hover:bg-primary group-hover:text-white transition-colors duration-300">
          <Icon className="h-5 w-5" />
        </div>
      </CardHeader>
      <CardContent className="relative z-10 pt-2">
        <div className="text-3xl font-black text-slate-900 dark:text-white tracking-tight">{value}</div>
        {description && <p className="text-xs text-slate-500 dark:text-slate-400 font-medium pt-1.5">{description}</p>}
        {trend && (
          <p className={`text-xs pt-1.5 font-bold ${trendDirection === 'up' ? 'text-emerald-500' : 'text-rose-500'}`}>
            {trend}
          </p>
        )}
      </CardContent>
    </Card>
  </motion.div>
);

interface QuickActionProps {
  title: string;
  icon: React.ElementType;
  href: string;
  description: string;
}

const QuickAction: React.FC<QuickActionProps> = ({ title, icon: Icon, href, description }) => (
  <Link href={href} passHref legacyBehavior>
    <motion.a
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.98 }}
      className="glass-card-premium block p-6 bg-white/60 dark:bg-slate-950/40 border border-slate-200/50 dark:border-slate-800/40 hover:border-blue-500/55 dark:hover:border-blue-400/55 group relative overflow-hidden transition-all duration-300 w-full cursor-pointer hover:shadow-2xl h-full"
    >
      <div className="absolute top-0 left-0 h-1 w-full bg-gradient-to-r from-blue-500 to-indigo-500 transform -translate-x-full group-hover:translate-x-0 transition-transform duration-500"></div>
      <div className="flex items-center mb-3">
        <div className="p-3 rounded-2xl bg-blue-50 dark:bg-blue-950/30 text-blue-600 dark:text-blue-400 group-hover:scale-110 group-hover:bg-blue-600 group-hover:text-white transition-all duration-300">
          <Icon className="h-6 w-6" />
        </div>
        <span className="text-lg font-bold text-slate-900 dark:text-white ml-4 tracking-tight group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors duration-300">{title}</span>
      </div>
      <p className="text-sm text-slate-500 dark:text-slate-400 font-medium leading-relaxed">{description}</p>
    </motion.a>
  </Link>
);

interface ActivityItemProps {
  title: string;
  description: string;
  time: string;
  icon: React.ElementType;
  iconColor?: string;
  index: number;
}

const ActivityItem: React.FC<ActivityItemProps> = ({ title, description, time, icon: Icon, iconColor = "text-muted-foreground", index }) => (
  <motion.li
    initial={{ opacity: 0, x: -20 }}
    animate={{ opacity: 1, x: 0 }}
    transition={{ delay: index * 0.1 }}
    className="flex items-start space-x-4 py-4 group border-b border-slate-100 dark:border-slate-900/60 last:border-0 hover:bg-slate-50/30 dark:hover:bg-slate-900/10 px-2 rounded-xl transition-all duration-200"
  >
    <div className={`p-2.5 rounded-xl bg-slate-100 dark:bg-slate-900/60 ${iconColor} bg-opacity-20 flex items-center justify-center transition-all duration-300 group-hover:scale-110`}>
      <Icon className={`h-5 w-5 ${iconColor}`} />
    </div>
    <div className="flex-1 min-w-0">
      <p className="text-sm font-bold text-slate-900 dark:text-slate-100 truncate">{title}</p>
      <p className="text-xs text-slate-500 dark:text-slate-400 font-medium mt-0.5">{description}</p>
    </div>
    <p className="text-[11px] text-slate-400 dark:text-slate-500 font-medium whitespace-nowrap pt-1">{time}</p>
  </motion.li>
);

// Dashboard interfaces
interface SystemStatus {
  database: boolean;
  wincc: {
    connected: boolean;
    total_tags: number;
    active_tags: number;
  };
  email: boolean;
  report_engine: boolean;
}

interface ReportStats {
  total: number;
  successful: number;
  failed: number;
  by_type: Record<string, number>;
}

interface SchedulerStats {
  total: number;
  active: number;
  upcoming_24h: number;
}

interface ActivityEvent {
  event_type: string;
  description: string;
  severity: string;
  created_at: string;
  user?: string;
  source?: string;
  metadata?: string;
}

interface DashboardData {
  system_status: SystemStatus;
  reports: ReportStats;
  scheduler: SchedulerStats;
  recent_activity: ActivityEvent[];
  last_updated: string;
}

interface Alert { machine_id: string; parameter: string; value: number | null; unit: string; status: string; timestamp: string | null; }

export default function DashboardPage() {
  const [currentTime, setCurrentTime] = React.useState<string>('');
  const [currentDate, setCurrentDate] = React.useState<string>('');
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [dashboardData, setDashboardData] = React.useState<DashboardData | null>(null);
  const [alerts, setAlerts] = React.useState<Alert[]>([]);
  const [alertsDismissed, setAlertsDismissed] = React.useState(false);

  // Update clock and date
  React.useEffect(() => {
    const update = () => {
      setCurrentTime(new Date().toLocaleTimeString('en-US', {
        hour: 'numeric',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
      }));
      setCurrentDate(formatDate(new Date()));
    };
    update();
    const timer = setInterval(update, 1000);
    return () => clearInterval(timer);
  }, []);
  // Set up WebSocket connection for real-time updates
  const ws = React.useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = React.useRef<NodeJS.Timeout>();
  const reconnectAttemptRef = React.useRef(0);

  React.useEffect(() => {
    let isMounted = true;
    
    // Initial fetch
    const fetchDashboardData = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/dashboard/stats`);
        if (!response.ok) throw new Error('Failed to fetch dashboard data');
        const data = await response.json();
        if (isMounted) {
          setDashboardData(data);
          setLoading(false);
        }
      } catch (err) {
        if (isMounted) {
          setError(err instanceof Error ? err.message : 'An error occurred');
          setLoading(false);
        }
      }
    };

    const fetchAlerts = async () => {
      try {
        const res = await getDashboardAlerts();
        if (isMounted) setAlerts(res.data ?? []);
      } catch { /* alerts are non-critical */ }
    };

    // WebSocket setup with exponential backoff
    const setupWebSocket = () => {
      if (!isMounted) return;
      
      const token = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null;
      const wsUrl = `${process.env.NEXT_PUBLIC_API_BASE_URL?.replace('http', 'ws')}/ws/dashboard${token ? `?token=${token}` : ''}`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        reconnectAttemptRef.current = 0; // Reset attempts on successful connection
      };

      ws.current.onmessage = (event) => {
        if (!isMounted) return;
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'dashboard_update') {
            const payload = data.data;
            if (payload.wincc && !payload.system_status) {
              // Partial wincc-only push from historian flush — merge into existing state
              setDashboardData(prev => prev ? {
                ...prev,
                system_status: { ...prev.system_status, wincc: payload.wincc },
              } : prev);
            } else {
              setDashboardData(payload);
            }
            setError(null);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.current.onerror = (event) => {
        if (!isMounted) return;
        console.error('WebSocket error:', event);
        setError('Lost connection to server');
      };

      ws.current.onclose = () => {
        if (!isMounted) return;
        
        // Exponential backoff
        const timeout = Math.min(1000 * Math.pow(2, reconnectAttemptRef.current), 30000);
        reconnectAttemptRef.current += 1;
        
        console.log(`WebSocket closed. Reconnecting in ${timeout}ms...`);
        reconnectTimeoutRef.current = setTimeout(setupWebSocket, timeout);
      };
    };

    // Initial setup
    fetchDashboardData();
    fetchAlerts();
    setupWebSocket();

    // Cleanup
    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);
  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="container mx-auto py-4 space-y-8 text-slate-850 dark:text-slate-100"
    >
      {/* Welcome Banner Card */}
      <div className="relative overflow-hidden rounded-[2rem] bg-gradient-to-r from-blue-600 to-indigo-650 dark:from-slate-900 dark:to-slate-950 p-8 shadow-xl dark:shadow-2xl border border-white/10 dark:border-slate-800/60 transition-all duration-300">
        <div className="absolute top-0 right-0 -mt-10 -mr-10 w-96 h-96 bg-white/5 dark:bg-blue-500/5 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-10 -left-10 w-80 h-80 bg-white/5 dark:bg-indigo-500/5 rounded-full blur-2xl pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="space-y-2">
            <span className="text-[10px] bg-white/20 dark:bg-blue-900/50 text-white dark:text-blue-300 px-3 py-1 rounded-full font-bold uppercase tracking-widest">Evira Operations Command Center</span>
            <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight">Welcome to Evira</h1>
            <p className="text-blue-100 dark:text-slate-400 font-medium">
              {currentDate} &mdash; <span className="font-semibold text-white dark:text-slate-200">{currentTime}</span>
            </p>
          </div>
          <div className="relative group shrink-0">
            <div className="absolute -inset-1 bg-gradient-to-r from-teal-400 to-emerald-400 rounded-2xl blur opacity-30 group-hover:opacity-75 transition duration-500"></div>
            <img 
              src="https://picsum.photos/seed/dashboard/200/100" 
              alt="Dashboard banner" 
              width={200} 
              height={100} 
              className="relative rounded-xl shadow-md border border-white/20 dark:border-slate-800" 
            />
          </div>
        </div>
      </div>

      {/* Alert Strip */}
      {alerts.length > 0 && !alertsDismissed && (
        <div className="rounded-xl border border-amber-400/40 bg-amber-50 dark:bg-amber-950/30 px-4 py-3 flex items-start gap-3">
          <Bell className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-bold text-amber-800 dark:text-amber-300 mb-1">
              {alerts.length} active alert{alerts.length > 1 ? 's' : ''} from SCADA tags
            </p>
            <ul className="space-y-0.5">
              {alerts.slice(0, 5).map((a, i) => (
                <li key={i} className="text-xs text-amber-700 dark:text-amber-400 truncate">
                  <span className={`font-semibold ${a.status === 'Error' ? 'text-red-600 dark:text-red-400' : ''}`}>[{a.status}]</span>{' '}
                  {a.machine_id} · {a.parameter}{a.value != null ? ` = ${a.value}${a.unit ? ' ' + a.unit : ''}` : ''}{a.timestamp ? ` — ${formatRelativeTime(a.timestamp)}` : ''}
                </li>
              ))}
              {alerts.length > 5 && (
                <li className="text-xs text-amber-600 dark:text-amber-500 font-medium">+ {alerts.length - 5} more</li>
              )}
            </ul>
          </div>
          <button
            onClick={() => setAlertsDismissed(true)}
            className="shrink-0 text-amber-500 hover:text-amber-700 dark:hover:text-amber-300 transition-colors"
            aria-label="Dismiss alerts"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Quick Actions Section */}
      <section className="space-y-4">
        <h2 className="text-xs font-bold tracking-widest uppercase text-slate-400 dark:text-slate-500">Quick Actions Command Panel</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <QuickAction title="New Report" icon={FilePlus} href="/report-generator" description="Access the interactive stepper wizard to generate custom SCADA reports instantly." />
          <QuickAction title="View Templates" icon={BarChart3} href="/templates" description="Design, configure, and modify existing SCADA report templates and charts." />
          <QuickAction title="Check Schedule" icon={CalendarClock} href="/scheduler" description="Review automated triggers, periodic tasks, and operational crontab schedules." />
        </div>
      </section>

      {/* System Overview Metrics Section */}
      <section className="space-y-4">
        <h2 className="text-xs font-bold tracking-widest uppercase text-slate-400 dark:text-slate-500">System Telemetry & Status</h2>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
          {dashboardData?.reports && (
            <StatCard
              title="Reports Generated (7d)"
              value={dashboardData.reports.total?.toString() ?? '0'}
              icon={FilePlus}
              description={`${dashboardData.reports.successful ?? 0} successful, ${dashboardData.reports.failed ?? 0} failed`}
              trendDirection={(dashboardData.reports.failed ?? 0) === 0 ? "up" : "down"}
            />
          )}
          {dashboardData?.scheduler && (
            <StatCard
              title="Active Schedules"
              value={dashboardData.scheduler.total?.toString() ?? '0'}
              icon={CalendarClock}
              description={`${dashboardData.scheduler.upcoming_24h ?? 0} scheduled runs in next 24h`}
              trendDirection={(dashboardData.scheduler.active ?? 0) > 0 ? "up" : "down"}
            />
          )}
          {dashboardData?.system_status?.wincc && (
            <StatCard
              title="SCADA Data Tags"
              value={dashboardData.system_status.wincc.total_tags?.toString() ?? '0'}
              icon={Users}
              description={`${dashboardData.system_status.wincc.active_tags ?? 0} live OPC UA tags monitoring`}
              trendDirection={dashboardData.system_status.wincc.connected ? "up" : "down"}
            />
          )}
          {dashboardData?.system_status && (
            <StatCard
              title="Diagnostics Verdict"
              value={getAllSystemsOperational(dashboardData.system_status) ? "Healthy" : "Issues"}
              icon={AlertTriangle}
              description={getSystemStatusDescription(dashboardData.system_status)}
              trendDirection={getAllSystemsOperational(dashboardData.system_status) ? "up" : "down"}
            />
          )}
        </div>
      </section>
      
      {/* Two Column Layout for Logs & Status */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <Card className="lg:col-span-2 glass-card-premium bg-white/60 dark:bg-slate-950/40 border border-slate-200/50 dark:border-slate-800/40 shadow-xl rounded-2xl">
          <CardHeader className="border-b border-slate-100 dark:border-slate-900/60 pb-4">
            <CardTitle className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">Recent Activity Stream</CardTitle>
            <CardDescription className="text-slate-500 dark:text-slate-400">Chronological telemetry events from PLC integrations, templates, and schedules.</CardDescription>
          </CardHeader>
          <CardContent className="pt-4">
            {loading ? (
              <div className="flex items-center justify-center py-12">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
              </div>
            ) : error ? (
              <div className="text-rose-500 text-center py-8 font-medium">{error}</div>
            ) : (
              <ul className="divide-y divide-slate-100 dark:divide-slate-900/60">
                {dashboardData?.recent_activity && Array.isArray(dashboardData.recent_activity) && dashboardData.recent_activity.length > 0 ? (
                  dashboardData.recent_activity.map((activity, index) => (
                    <ActivityItem
                      key={index}
                      title={activity.event_type}
                      description={activity.description}
                      time={formatRelativeTime(activity.created_at)}
                      icon={getActivityIcon(activity.event_type)}
                      iconColor={getActivityColor(activity.severity)}
                      index={index}
                    />
                  ))
                ) : (
                  <div className="text-sm text-slate-400 dark:text-slate-500 text-center py-8 font-medium">No recent activities logged.</div>
                )}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card className="glass-card-premium bg-white/60 dark:bg-slate-950/40 border border-slate-200/50 dark:border-slate-800/40 shadow-xl rounded-2xl">
          <CardHeader className="border-b border-slate-100 dark:border-slate-900/60 pb-4">
            <CardTitle className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">System Diagnostics</CardTitle>
            <CardDescription className="text-slate-500 dark:text-slate-400">Current status of active background processes and OPC UA links.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5 pt-6">
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50/50 dark:bg-slate-900/30 border border-slate-100 dark:border-slate-900/40">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Database Link</span>
              <div className="flex items-center gap-2">
                {dashboardData?.system_status?.database ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 glowing-ring">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Connected
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300 animate-pulse">
                    <AlertTriangle className="h-3.5 w-3.5" /> Disconnected
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50/50 dark:bg-slate-900/30 border border-slate-100 dark:border-slate-900/40">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">WinCC Interface</span>
              <div className="flex items-center gap-2">
                {dashboardData?.system_status?.wincc?.connected ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 glowing-ring">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Connected
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 animate-pulse">
                    <AlertTriangle className="h-3.5 w-3.5" /> Offline
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50/50 dark:bg-slate-900/30 border border-slate-100 dark:border-slate-900/40">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Email Dispatcher</span>
              <div className="flex items-center gap-2">
                {dashboardData?.system_status?.email ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 glowing-ring">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Operational
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
                    <AlertTriangle className="h-3.5 w-3.5" /> Degraded
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50/50 dark:bg-slate-900/30 border border-slate-100 dark:border-slate-900/40">
              <span className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Report Compiler</span>
              <div className="flex items-center gap-2">
                {dashboardData?.system_status?.report_engine ? (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300 glowing-ring">
                    <CheckCircle2 className="h-3.5 w-3.5" /> Ready
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-bold bg-rose-100 text-rose-800 dark:bg-rose-950/40 dark:text-rose-300">
                    <AlertTriangle className="h-3.5 w-3.5" /> Offline
                  </span>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </motion.div>
  );
}
