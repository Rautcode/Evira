"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity } from 'lucide-react';
import { getLogs } from '@/lib/api';

interface TimelineItem {
  id: string;
  title: string;
  description: string;
  timestamp: string;
  level?: string;
}

export default function WinccActivityLoggerPage() {
  const [logs, setLogs] = React.useState<TimelineItem[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    getLogs()
      .then((res) => {
        setLogs(
          (res.data.logs || []).map((log: any) => ({
            id: log.id,
            title: log.level || 'INFO',
            description: log.message || log.details || '',
            timestamp: log.timestamp || log.time || '',
            level: log.level,
          }))
        );
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load logs');
        setLoading(false);
      });
  }, []);

  return (
    <div className="container mx-auto py-8">
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center text-2xl font-bold">
            <Activity className="mr-3 h-7 w-7 text-primary" />
            WinCC Activity Logger
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4">
            View a timeline of WinCC system activity and logs. This helps monitor automation events, alarms, and operator actions.
          </p>
          {loading ? (
            <div className="text-center py-8">Loading activity logs...</div>
          ) : error ? (
            <div className="text-center text-destructive py-8">{error}</div>
          ) : logs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No activity logs found.</div>
          ) : (
            <div className="max-h-[600px] overflow-y-auto border-l-2 border-primary/30 pl-6 relative">
              {logs.map((item, idx) => (
                <div key={item.id} className="mb-8 flex items-start group relative">
                  <div className="absolute -left-7 top-1.5">
                    <span className={`block w-4 h-4 rounded-full border-2 ${item.level === 'ERROR' ? 'bg-red-500 border-red-500' : item.level === 'WARNING' ? 'bg-yellow-400 border-yellow-400' : 'bg-primary border-primary'} group-hover:scale-110 transition-transform`} />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-base text-foreground">{item.title}</span>
                      <span className="text-xs text-muted-foreground">{new Date(item.timestamp).toLocaleString()}</span>
                    </div>
                    <div className="text-sm text-muted-foreground mt-1">{item.description}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
