"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { FileText } from 'lucide-react';
import { getReportList, downloadReport } from '@/lib/api';
import { Button } from '@/components/ui/button';

export default function ReportHistoryPage() {
  const [reports, setReports] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [downloading, setDownloading] = React.useState<string | null>(null);

  React.useEffect(() => {
    getReportList()
      .then((res) => {
        setReports(res.data);
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load reports');
        setLoading(false);
      });
  }, []);

  const handleDownload = async (reportId: string, filename: string) => {
    setDownloading(reportId);
    try {
      const res = await downloadReport(reportId);
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename || `report_${reportId}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);
    } finally {
      setDownloading(null);
    }
  };

  return (
    <div className="container mx-auto py-8">
      <Card className="shadow-lg">
        <CardHeader>
          <CardTitle className="flex items-center text-2xl font-bold">
            <FileText className="mr-3 h-7 w-7 text-primary" />
            Report History
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4">
            View and download previously generated reports.
          </p>
          {loading ? (
            <div className="text-center py-8">Loading reports...</div>
          ) : error ? (
            <div className="text-center text-destructive py-8">{error}</div>
          ) : reports.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">No reports found.</div>
          ) : (
            <ul className="space-y-4">
              {reports.map((report: any) => (
                <li key={report.id} className="border rounded p-4 flex flex-col md:flex-row md:items-center md:justify-between">
                  <div>
                    <span className="font-semibold text-lg">{report.name || report.title || `Report #${report.id}`}</span>
                    <span className="block text-xs text-muted-foreground">ID: {report.id}</span>
                    <span className="block text-xs text-muted-foreground">Generated: {report.created_at ? new Date(report.created_at).toLocaleString() : 'N/A'}</span>
                  </div>
                  <Button
                    className="mt-2 md:mt-0"
                    onClick={() => handleDownload(report.id, report.filename || `report_${report.id}.pdf`)}
                    disabled={downloading === report.id}
                  >
                    {downloading === report.id ? 'Downloading...' : 'Download'}
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
