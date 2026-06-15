"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar } from '@/components/ui/calendar';
import { Badge } from '@/components/ui/badge';
import { Clock, CalendarClock, PlayCircle, Settings, Plus, MoreHorizontal, FileText, CheckCircle2, Save } from 'lucide-react';
import { format } from 'date-fns';
import { getSchedules, createSchedule, getTemplates, getMachineList } from '@/lib/api';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';

export default function SchedulerPage() {
  const [date, setDate] = React.useState<Date | undefined>(new Date());
  const [scheduledTasks, setScheduledTasks] = React.useState<any[]>([]);
  const [loading, setLoading] = React.useState(true);
  
  // Wizard state
  const [isModalOpen, setIsModalOpen] = React.useState(false);
  const [saving, setSaving] = React.useState(false);
  const [templates, setTemplates] = React.useState<any[]>([]);
  const [machines, setMachines] = React.useState<any[]>([]);
  
  const [newTask, setNewTask] = React.useState({
    title: '',
    template_id: '',
    machine_id: 'all',
    cron_expression: '0 6 * * *',
    report_type: 'pdf',
    recipients: ''
  });
  const { toast } = useToast();

  const fetchData = () => {
    setLoading(true);
    getSchedules()
      .then(res => setScheduledTasks(res.data))
      .catch(err => console.error(err))
      .finally(() => setLoading(false));
  };

  React.useEffect(() => {
    fetchData();
    getTemplates().then(res => setTemplates(res.data)).catch(console.error);
    getMachineList().then(res => {
      if (res.data?.data?.machines) setMachines(res.data.data.machines);
      else if (Array.isArray(res.data)) setMachines(res.data);
    }).catch(console.error);
  }, []);

  const handleSave = async () => {
    if (!newTask.title || !newTask.template_id) {
      toast({ title: 'Missing fields', description: 'Title and Template are required.', variant: 'destructive' });
      return;
    }
    setSaving(true);
    try {
      await createSchedule(newTask);
      toast({ title: 'Schedule Created', description: 'New automated report has been scheduled.' });
      setIsModalOpen(false);
      fetchData();
    } catch (e) {
      toast({ title: 'Error', description: 'Failed to create schedule.', variant: 'destructive' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="container mx-auto py-8 animate-fade-in text-slate-900 dark:text-slate-100">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
          <h1 className="text-3xl font-black tracking-tight">Report Scheduler</h1>
          <p className="text-slate-500 dark:text-slate-400">Manage automated report generation and dispatch triggers.</p>
        </div>
        <Button onClick={() => setIsModalOpen(true)} className="rounded-xl bg-blue-600 hover:bg-blue-700 text-white shadow-md shadow-blue-600/20">
          <Plus className="mr-2 h-4 w-4" />
          New Schedule
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Calendar Overview */}
        <div className="lg:col-span-1 space-y-6">
          <Card className="glass-card-premium border-slate-200/50 dark:border-slate-800/40 shadow-xl overflow-hidden">
            <div className="bg-slate-50 dark:bg-slate-900 border-b border-slate-100 dark:border-slate-800/50 p-4">
              <h3 className="font-bold flex items-center text-slate-700 dark:text-slate-200">
                <CalendarClock className="mr-2 h-5 w-5 text-blue-500" /> Execution Calendar
              </h3>
            </div>
            <CardContent className="p-4 flex justify-center">
              <Calendar
                mode="single"
                selected={date}
                onSelect={setDate}
                className="rounded-xl"
              />
            </CardContent>
          </Card>

          <Card className="glass-card-premium border-slate-200/50 dark:border-slate-800/40 shadow-xl overflow-hidden">
            <CardHeader className="bg-slate-50 dark:bg-slate-900 border-b border-slate-100 dark:border-slate-800/50 pb-4">
              <CardTitle className="text-sm">Engine Status</CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="relative flex h-4 w-4">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-4 w-4 bg-emerald-500"></span>
                  </div>
                  <div>
                    <p className="font-bold text-sm">Cron Daemon</p>
                    <p className="text-xs text-slate-500">Running smoothly</p>
                  </div>
                </div>
                <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/20 dark:text-emerald-400 dark:border-emerald-800">Online</Badge>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Column: Scheduled Tasks List */}
        <div className="lg:col-span-2">
          <Card className="glass-card-premium border-slate-200/50 dark:border-slate-800/40 shadow-xl h-full">
            <CardHeader className="border-b border-slate-100 dark:border-slate-800/50 pb-4 flex flex-row items-center justify-between">
              <div>
                <CardTitle className="text-xl">Active Schedules</CardTitle>
                <CardDescription>Tasks scheduled for automatic execution.</CardDescription>
              </div>
            </CardHeader>
            <CardContent className="p-0">
              <ul className="divide-y divide-slate-100 dark:divide-slate-800/50">
                {loading ? (
                  <li className="p-6 text-center text-slate-500">Loading schedules...</li>
                ) : scheduledTasks.length === 0 ? (
                  <li className="p-6 text-center text-slate-500">No scheduled tasks found.</li>
                ) : scheduledTasks.map((task) => (
                  <li key={task.id} className="p-6 hover:bg-slate-50/50 dark:hover:bg-slate-900/20 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className={`p-3 rounded-xl flex items-center justify-center shadow-sm ${
                        task.status === 'active' 
                          ? 'bg-blue-50 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400' 
                          : 'bg-slate-100 text-slate-400 dark:bg-slate-800 dark:text-slate-500'
                      }`}>
                        <Clock className="h-6 w-6" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="font-bold text-lg text-slate-900 dark:text-white tracking-tight">{task.title}</h4>
                          {task.status === 'active' ? (
                            <Badge className="bg-emerald-100 text-emerald-800 hover:bg-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-400 rounded-full px-2 py-0">Active</Badge>
                          ) : (
                            <Badge variant="secondary" className="rounded-full px-2 py-0">Paused</Badge>
                          )}
                        </div>
                        <div className="flex items-center gap-4 text-xs font-medium text-slate-500 dark:text-slate-400">
                          <span className="flex items-center gap-1.5"><FileText className="h-3.5 w-3.5" /> {task.template_id}</span>
                          <span className="flex items-center gap-1.5"><CalendarClock className="h-3.5 w-3.5" /> {task.cron_expression}</span>
                        </div>
                        <p className="text-xs text-slate-400 mt-2 flex items-center gap-1.5">
                          Next run: <span className="text-slate-700 dark:text-slate-300 font-bold">{task.nextRun ? format(new Date(task.nextRun), 'PPpp') : 'Pending'}</span>
                        </p>
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2 sm:self-center self-end">
                      <Button variant="outline" size="sm" className="rounded-lg h-8 px-3 border-slate-200 dark:border-slate-800">
                        <PlayCircle className="mr-1.5 h-3.5 w-3.5 text-blue-500" /> Run Now
                      </Button>
                      <Button variant="ghost" size="icon" className="rounded-lg h-8 w-8 text-slate-400 hover:text-slate-600">
                        <Settings className="h-4 w-4" />
                      </Button>
                      <Button variant="ghost" size="icon" className="rounded-lg h-8 w-8 text-slate-400 hover:text-slate-600">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </div>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </div>

      </div>
      {/* Scheduler Modal */}
      <Dialog open={isModalOpen} onOpenChange={setIsModalOpen}>
        <DialogContent className="sm:max-w-[500px]">
          <DialogHeader>
            <DialogTitle>Create Automated Schedule</DialogTitle>
            <DialogDescription>Configure a recurring task to generate reports automatically.</DialogDescription>
          </DialogHeader>
          <div className="grid gap-4 py-4">
            <div className="space-y-2">
              <Label>Schedule Title</Label>
              <Input 
                value={newTask.title} 
                onChange={e => setNewTask({...newTask, title: e.target.value})} 
                placeholder="e.g., Daily Shift Handover" 
              />
            </div>
            <div className="space-y-2">
              <Label>Template</Label>
              <Select value={newTask.template_id} onValueChange={v => setNewTask({...newTask, template_id: v})}>
                <SelectTrigger><SelectValue placeholder="Select Template" /></SelectTrigger>
                <SelectContent>
                  {templates.map(t => (
                    <SelectItem key={t.id} value={t.id}>{t.name || t.id}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>Machine / Line</Label>
                <Select value={newTask.machine_id} onValueChange={v => setNewTask({...newTask, machine_id: v})}>
                  <SelectTrigger><SelectValue placeholder="Select Machine" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Machines</SelectItem>
                    {machines.map(m => (
                      <SelectItem key={m.id || m} value={m.id || m}>{m.name || m}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label>Cron Expression</Label>
                <Input 
                  value={newTask.cron_expression} 
                  onChange={e => setNewTask({...newTask, cron_expression: e.target.value})} 
                  placeholder="0 6 * * *" 
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Email Recipients (comma separated)</Label>
              <Input 
                value={newTask.recipients} 
                onChange={e => setNewTask({...newTask, recipients: e.target.value})} 
                placeholder="admin@factory.com" 
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsModalOpen(false)}>Cancel</Button>
            <Button onClick={handleSave} disabled={saving}>
              {saving ? 'Saving...' : <><Save className="w-4 h-4 mr-2"/> Schedule Task</>}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
