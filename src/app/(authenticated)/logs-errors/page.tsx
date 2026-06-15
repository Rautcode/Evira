"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileWarning } from 'lucide-react';
import { getLogs } from '@/lib/api';

export default function LogsErrorsPage() {
  const [logs, setLogs] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    getLogs()
      .then((res) => {
        setLogs(res.data);
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
            <FileWarning className="mr-3 h-7 w-7 text-primary" />
            System Logs & Errors
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4">
            View system logs and error reports in this section. This will help in diagnosing issues and monitoring the application's health.
          </p>
          {loading ? (
            <div className="text-center py-8">Loading logs...</div>
          ) : error ? (
            <div className="text-center text-destructive py-8">{error}</div>
          ) : logs.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No logs found.</div>
          ) : (
            <ul className="space-y-4">
              {logs.map((log: any) => (
                <li key={log.id} className="border rounded p-4 flex flex-col">
                  <span className="font-semibold text-lg">{log.level || 'INFO'} - {log.timestamp || log.time || ''}</span>
                  <span className="text-xs text-muted-foreground">ID: {log.id}</span>
                  <span className="text-sm text-muted-foreground mt-1">{log.message || 'No message'}</span>
                  {log.details && <span className="text-xs text-muted-foreground mt-1">Details: {log.details}</span>}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
