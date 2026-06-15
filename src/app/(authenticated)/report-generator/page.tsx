"use client";

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { CheckCircle2, ChevronRight, ChevronLeft, FileText, Download, Calendar as CalendarIcon, Settings2, Play } from 'lucide-react';
import { DateRange } from 'react-day-picker';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { format } from 'date-fns';
import { useToast } from '@/hooks/use-toast';
import { generateReport, getTemplates, getMachineList } from '@/lib/api';

const steps = [
  { id: 'template', title: 'Select Template', icon: FileText },
  { id: 'parameters', title: 'Configure Parameters', icon: Settings2 },
  { id: 'daterange', title: 'Select Date Range', icon: CalendarIcon },
  { id: 'generate', title: 'Generate & Export', icon: Play },
];

export default function ReportGeneratorPage() {
  const [currentStep, setCurrentStep] = React.useState(0);
  const [selectedTemplate, setSelectedTemplate] = React.useState('');
  const [dateRange, setDateRange] = React.useState<DateRange | undefined>();
  const [isGenerating, setIsGenerating] = React.useState(false);
  
  // Dynamic data states
  const [templates, setTemplates] = React.useState<any[]>([]);
  const [machines, setMachines] = React.useState<any[]>([]);
  const [selectedMachine, setSelectedMachine] = React.useState('all');
  const [selectedShift, setSelectedShift] = React.useState('full');
  const [selectedReportType, setSelectedReportType] = React.useState('production_summary');
  const [reportTitle, setReportTitle] = React.useState('');

  const { toast } = useToast();

  React.useEffect(() => {
    // Fetch live templates and machines
    getTemplates().then(res => setTemplates(res.data)).catch(console.error);
    getMachineList().then(res => {
      // The API returns { data: { machines: [...] } }
      if (res.data?.data?.machines) {
        setMachines(res.data.data.machines);
      } else if (Array.isArray(res.data)) {
        setMachines(res.data);
      }
    }).catch(console.error);
  }, []);

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(s => s + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(s => s - 1);
    }
  };

  const handleGenerate = async () => {
    if (!dateRange?.from || !dateRange?.to) {
      toast({ title: 'Missing Date', description: 'Please select a date range', variant: 'destructive' });
      return;
    }
    
    setIsGenerating(true);
    try {
      toast({ title: 'Generating report...', description: 'This may take a few seconds.' });
      
      const payload = {
        date_range: {
          start: dateRange.from.toISOString(),
          end: dateRange.to.toISOString()
        },
        machine_id: selectedMachine,
        shift: selectedShift,
        report_type: selectedReportType,
        template_id: selectedTemplate,
        output_type: 'pdf',
        with_chart: true
      };

      const response = await generateReport(payload);
      
      // Create a Blob from the PDF Stream
      const blob = new Blob([response.data], { type: 'application/pdf' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = reportTitle || `${selectedTemplate}_report.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      window.URL.revokeObjectURL(url);
      
      toast({ title: 'Report Generated!', description: 'Your report is downloading.', variant: 'default' });
      setCurrentStep(3); // Stay on finish step
    } catch (e) {
      console.error(e);
      toast({ title: 'Generation Failed', description: 'Could not generate report.', variant: 'destructive' });
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="container max-w-5xl mx-auto py-8 animate-fade-in text-slate-900 dark:text-slate-100">
      <div className="mb-8 space-y-2">
        <h1 className="text-3xl font-black tracking-tight">Report Generator Wizard</h1>
        <p className="text-slate-500 dark:text-slate-400">Follow the steps below to configure and generate your SCADA production report.</p>
      </div>

      {/* Stepper Header */}
      <div className="mb-10 relative">
        <div className="absolute top-1/2 left-0 w-full h-1 bg-slate-200 dark:bg-slate-800 -translate-y-1/2 z-0 rounded-full"></div>
        <div 
          className="absolute top-1/2 left-0 h-1 bg-blue-600 dark:bg-blue-500 -translate-y-1/2 z-0 transition-all duration-500 rounded-full" 
          style={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
        ></div>
        
        <div className="relative z-10 flex justify-between">
          {steps.map((step, index) => {
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;
            const StepIcon = step.icon;
            
            return (
              <div key={step.id} className="flex flex-col items-center gap-2">
                <div 
                  className={`w-12 h-12 rounded-full flex items-center justify-center border-4 transition-all duration-300 ${
                    isActive 
                      ? 'bg-blue-600 border-blue-100 dark:border-blue-900 text-white scale-110 shadow-lg shadow-blue-500/30' 
                      : isCompleted 
                        ? 'bg-blue-600 border-white dark:border-slate-950 text-white' 
                        : 'bg-slate-100 border-white dark:bg-slate-800 dark:border-slate-950 text-slate-400'
                  }`}
                >
                  {isCompleted ? <CheckCircle2 className="h-6 w-6" /> : <StepIcon className="h-5 w-5" />}
                </div>
                <span className={`text-xs font-bold uppercase tracking-wider ${
                  isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500'
                }`}>
                  {step.title}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Content */}
      <Card className="glass-card-premium border-slate-200/50 dark:border-slate-800/40 shadow-xl min-h-[400px] flex flex-col">
        <CardHeader className="border-b border-slate-100 dark:border-slate-800/50 pb-4">
          <CardTitle className="text-xl font-bold">{steps[currentStep].title}</CardTitle>
          <CardDescription>Configure the required settings for this step.</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 p-6 relative">
          
          {/* Step 1: Template */}
          {currentStep === 0 && (
            <div className="space-y-6 animate-fade-in">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {templates.length === 0 ? (
                  <div className="col-span-2 text-center py-8 text-slate-500">Loading templates...</div>
                ) : templates.map((tmpl) => (
                  <div 
                    key={tmpl.id}
                    onClick={() => {
                      setSelectedTemplate(tmpl.id);
                      setReportTitle(`${tmpl.name} - Draft`);
                    }}
                    className={`p-6 rounded-xl border-2 cursor-pointer transition-all duration-200 ${
                      selectedTemplate === tmpl.id 
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 shadow-md shadow-blue-500/10' 
                        : 'border-slate-200 dark:border-slate-800 hover:border-blue-300 dark:hover:border-blue-700 bg-white/50 dark:bg-slate-900/50'
                    }`}
                  >
                    <FileText className={`h-8 w-8 mb-3 ${selectedTemplate === tmpl.id ? 'text-blue-600' : 'text-slate-400'}`} />
                    <h3 className="font-bold text-slate-900 dark:text-white">{tmpl.name || tmpl.id}</h3>
                    <p className="text-xs text-slate-500 mt-1">{tmpl.description || `Standard template for ${tmpl.name || tmpl.id}`}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 2: Parameters */}
          {currentStep === 1 && (
            <div className="space-y-6 max-w-xl animate-fade-in">
              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Report Title</label>
                  <Input 
                    placeholder="e.g. Q3 Plant Production" 
                    value={reportTitle} 
                    onChange={e => setReportTitle(e.target.value)} 
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Target Line / Machine</label>
                  <Select value={selectedMachine} onValueChange={setSelectedMachine}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select Line" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Lines</SelectItem>
                      {machines.map((m: any) => (
                        <SelectItem key={m.id || m} value={m.id || m}>{m.name || m}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Report Category</label>
                  <Select value={selectedReportType} onValueChange={setSelectedReportType}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select Category" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="production_summary">Production Summary</SelectItem>
                      <SelectItem value="downtime_analysis">Downtime Analysis</SelectItem>
                      <SelectItem value="quality_metrics">Quality Metrics</SelectItem>
                      <SelectItem value="all">Comprehensive (All Logs)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-500">Shift Type</label>
                  <Select value={selectedShift} onValueChange={setSelectedShift}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select Shift" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="full">Full Day (24h)</SelectItem>
                      <SelectItem value="Morning">Morning Shift (06:00 - 14:00)</SelectItem>
                      <SelectItem value="Evening">Evening Shift (14:00 - 22:00)</SelectItem>
                      <SelectItem value="Night">Night Shift (22:00 - 06:00)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Date Range */}
          {currentStep === 2 && (
            <div className="flex flex-col items-center justify-center py-6 animate-fade-in">
              <div className="mb-4 text-center">
                <h3 className="font-bold text-lg mb-2">Select Time Period</h3>
                <p className="text-sm text-slate-500">Choose the start and end dates for your report data.</p>
              </div>
              <div className="bg-white dark:bg-slate-900 rounded-xl shadow-sm border border-slate-200 dark:border-slate-800 p-2">
                <Calendar
                  mode="range"
                  selected={dateRange}
                  onSelect={setDateRange}
                  numberOfMonths={2}
                  className="rounded-md"
                />
              </div>
              {dateRange?.from && dateRange?.to && (
                <div className="mt-6 p-4 bg-emerald-50 dark:bg-emerald-900/20 text-emerald-800 dark:text-emerald-300 rounded-xl border border-emerald-200 dark:border-emerald-800/30 flex items-center gap-3">
                  <CheckCircle2 className="h-5 w-5" />
                  <span className="font-medium">
                    Selected: {format(dateRange.from, 'PPP')} - {format(dateRange.to, 'PPP')}
                  </span>
                </div>
              )}
            </div>
          )}

          {/* Step 4: Generate */}
          {currentStep === 3 && (
            <div className="flex flex-col items-center justify-center py-10 animate-fade-in text-center space-y-6">
              <div className="w-20 h-20 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center mb-2 shadow-inner">
                <Download className="h-10 w-10" />
              </div>
              <div>
                <h3 className="font-bold text-2xl">Ready to Generate</h3>
                <p className="text-slate-500 max-w-md mx-auto mt-2">
                  You have configured the <strong>{selectedTemplate || 'Report'}</strong> for the selected parameters. Click generate to compile the data into your document.
                </p>
              </div>
              
              <div className="flex gap-4 pt-4">
                <Button 
                  size="lg" 
                  onClick={handleGenerate} 
                  disabled={isGenerating}
                  className="bg-blue-600 hover:bg-blue-700 text-white rounded-xl shadow-lg shadow-blue-600/20 px-8"
                >
                  {isGenerating ? 'Compiling Data...' : 'Generate PDF Report'}
                </Button>
                <Button size="lg" variant="outline" className="rounded-xl border-slate-300 dark:border-slate-700">
                  Preview PDF
                </Button>
              </div>
            </div>
          )}
        </CardContent>

        {/* Footer Actions */}
        <div className="border-t border-slate-100 dark:border-slate-800/50 p-4 bg-slate-50/50 dark:bg-slate-900/20 flex justify-between rounded-b-xl">
          <Button 
            variant="ghost" 
            onClick={handleBack} 
            disabled={currentStep === 0 || isGenerating}
            className="text-slate-500"
          >
            <ChevronLeft className="mr-2 h-4 w-4" /> Back
          </Button>
          
          {currentStep < steps.length - 1 ? (
            <Button 
              onClick={handleNext} 
              disabled={(currentStep === 0 && !selectedTemplate) || (currentStep === 2 && !dateRange?.to)}
              className="bg-slate-900 hover:bg-slate-800 text-white dark:bg-white dark:hover:bg-slate-200 dark:text-slate-900 rounded-lg px-6"
            >
              Continue <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          ) : null}
        </div>
      </Card>
    </div>
  );
}
