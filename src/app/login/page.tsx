import { LoginForm } from '@/components/auth/login-form';
import { AppLogo } from '@/components/layout/app-logo';
import { Cpu, FileSpreadsheet, Clock, ShieldCheck } from 'lucide-react';

export default function LoginPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-abstract overflow-hidden transition-colors duration-300">
      {/* Subtle modern abstract background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-[10%] -left-[10%] w-[45%] h-[45%] bg-blue-500/10 dark:bg-blue-500/15 rounded-full blur-[100px] animate-pulse-subtle" />
        <div className="absolute top-[60%] -right-[10%] w-[40%] h-[50%] bg-indigo-500/10 dark:bg-indigo-500/15 rounded-full blur-[110px] animate-pulse-subtle" />
        <div className="absolute top-[20%] left-[60%] w-[35%] h-[35%] bg-emerald-500/5 dark:bg-emerald-500/10 rounded-full blur-[80px]" />
      </div>

      <div className="z-10 w-full max-w-md px-6 py-12 animate-fade-in-up">
        {/* Main Glassmorphic Login Card */}
        <div className="bg-card/85 backdrop-blur-xl border border-border shadow-xl rounded-[2.5rem] p-8 sm:p-10 transition-all duration-300">
          <div className="flex flex-col items-center text-center mb-8 space-y-4">
            <AppLogo className="mb-2" iconSize={44} textSize="text-2xl" href="/login" />
            
            <div className="space-y-1.5">
              <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-100">
                Welcome back
              </h1>
              <p className="text-sm text-slate-500 dark:text-slate-400 font-medium">
                Log in to your Evira workspace
              </p>
            </div>
          </div>
          
          <div className="w-full">
            <LoginForm />
          </div>

          <div className="mt-8 pt-6 border-t border-slate-100 dark:border-slate-900 flex flex-col items-center justify-center space-y-1">
            <p className="text-xs font-semibold text-slate-400 dark:text-slate-500 uppercase tracking-widest">Evira v1.2.0</p>
            <p className="text-[10px] text-slate-400 dark:text-slate-500">Enterprise Automation Report Engine</p>
          </div>
        </div>

        {/* Minimalist Feature Icons Below */}
        <div className="mt-8 flex items-center justify-center gap-6 text-slate-400 dark:text-slate-500">
          <div className="group flex items-center gap-2 hover:text-blue-500 dark:hover:text-blue-400 transition-colors duration-300">
            <Cpu className="h-4.5 w-4.5" />
            <span className="text-[10px] font-bold tracking-wider uppercase opacity-0 group-hover:opacity-100 transition-opacity duration-300 max-w-0 group-hover:max-w-xs overflow-hidden">OPC UA Mapping</span>
          </div>
          <div className="group flex items-center gap-2 hover:text-indigo-500 dark:hover:text-indigo-400 transition-colors duration-300">
            <FileSpreadsheet className="h-4.5 w-4.5" />
            <span className="text-[10px] font-bold tracking-wider uppercase opacity-0 group-hover:opacity-100 transition-opacity duration-300 max-w-0 group-hover:max-w-xs overflow-hidden">Reports</span>
          </div>
          <div className="group flex items-center gap-2 hover:text-emerald-500 dark:hover:text-emerald-400 transition-colors duration-300">
            <Clock className="h-4.5 w-4.5" />
            <span className="text-[10px] font-bold tracking-wider uppercase opacity-0 group-hover:opacity-100 transition-opacity duration-300 max-w-0 group-hover:max-w-xs overflow-hidden">Scheduler</span>
          </div>
          <div className="group flex items-center gap-2 hover:text-amber-500 dark:hover:text-amber-400 transition-colors duration-300">
            <ShieldCheck className="h-4.5 w-4.5" />
            <span className="text-[10px] font-bold tracking-wider uppercase opacity-0 group-hover:opacity-100 transition-opacity duration-300 max-w-0 group-hover:max-w-xs overflow-hidden">Security</span>
          </div>
        </div>
      </div>
    </div>
  );
}
