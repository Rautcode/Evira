"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  BarChart3, FileText, Settings, Activity, FileWarning, Mail, CalendarClock,
  HelpCircle, ChevronsLeft, ChevronsRight, Wand2, Users, History,
} from 'lucide-react';

import {
  Sidebar, SidebarHeader, SidebarContent, SidebarFooter,
  SidebarMenu, SidebarMenuItem, SidebarMenuButton, SidebarTrigger,
  useSidebar,
} from '@/components/ui/sidebar';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { AppLogo } from './app-logo';
import { Separator } from '@/components/ui/separator';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAuth } from '@/context/auth-context';

const ROLE_LABEL: Record<string, string> = {
  admin: 'Admin',
  engineer: 'Engineer',
  operator: 'Operator',
};

const ROLE_COLOR: Record<string, string> = {
  admin: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  engineer: 'bg-amber-100 text-amber-700 dark:bg-amber-900/40 dark:text-amber-300',
  operator: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
};

const coreNavItems = [
  { href: '/dashboard',              label: 'Dashboard',            icon: BarChart3 },
  { href: '/setup',                  label: 'Setup',                icon: Wand2 },
  { href: '/report-generator',       label: 'Report Generator',     icon: BarChart3 },
  { href: '/report-history',         label: 'Report History',       icon: History },
  { href: '/templates',              label: 'Templates',            icon: FileText },
  { href: '/wincc-activity-logger',  label: 'WinCC Activity',       icon: Activity },
  { href: '/logs-errors',            label: 'Logs / Errors',        icon: FileWarning },
  { href: '/email-sender',           label: 'Email Sender',         icon: Mail },
  { href: '/scheduler',              label: 'Scheduler',            icon: CalendarClock },
  { href: '/settings',               label: 'Settings',             icon: Settings },
];

const engineerNavItems = [
  // nothing extra yet — settings is visible to all but editing is role-gated
];

const adminNavItems = [
  { href: '/users', label: 'Users', icon: Users },
];

const helpNavItem = { href: '/help', label: 'Help', icon: HelpCircle };

export function AppSidebar() {
  const pathname = usePathname();
  const { open, toggleSidebar, isMobile, state } = useSidebar();
  const { user, role } = useAuth();

  const navItems = [
    ...coreNavItems,
    ...(role === 'admin' ? adminNavItems : []),
  ];

  const initials = (user || 'U').slice(0, 2).toUpperCase();

  return (
    <Sidebar
      side="left"
      collapsible={isMobile ? 'offcanvas' : 'icon'}
      variant="sidebar"
      className="border-r border-slate-200/40 bg-white/50 dark:bg-slate-950/40 backdrop-blur-md transition-all duration-300 shadow-lg dark:border-slate-800/30"
    >
      <SidebarHeader className="p-4">
        <div className="flex items-center justify-between">
          {state === 'expanded' && <AppLogo href="/dashboard" />}
          {!isMobile && (
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleSidebar}
              className="text-sidebar-foreground hover:bg-slate-100 dark:hover:bg-slate-900 rounded-lg"
            >
              {open ? <ChevronsLeft /> : <ChevronsRight />}
              <span className="sr-only">Toggle Sidebar</span>
            </Button>
          )}
        </div>
        {state === 'expanded' && (
          <div className="mt-4 flex flex-col items-center gap-2">
            <Avatar className="h-14 w-14 border-2 border-border shadow-md">
              <AvatarFallback className="text-base font-bold">{initials}</AvatarFallback>
            </Avatar>
            <p className="text-sm font-semibold text-sidebar-foreground">{user || '—'}</p>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium uppercase tracking-wider ${ROLE_COLOR[role] ?? ROLE_COLOR.operator}`}>
              {ROLE_LABEL[role] ?? role}
            </span>
          </div>
        )}
      </SidebarHeader>

      <Separator className="my-2 bg-slate-200/60 dark:bg-slate-800/40" />

      <SidebarContent className="flex-1 px-2">
        <SidebarMenu className="gap-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href || (item.href !== '/dashboard' && pathname.startsWith(item.href));
            return (
              <SidebarMenuItem key={item.href}>
                <Link href={item.href} passHref legacyBehavior>
                  <SidebarMenuButton
                    isActive={isActive}
                    tooltip={{ children: item.label, className: 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 border-none font-medium px-3 py-1.5 shadow-md' }}
                    className={`text-sidebar-foreground hover:bg-slate-100 dark:hover:bg-slate-900/60 rounded-xl px-3 py-2 transition-all duration-300 ${
                      isActive ? 'bg-blue-600/10 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 font-semibold shadow-sm border-l-2 border-blue-600' : ''
                    }`}
                  >
                    <item.icon className={`h-5 w-5 ${isActive ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500'}`} />
                    {state === 'expanded' && <span className="ml-2">{item.label}</span>}
                  </SidebarMenuButton>
                </Link>
              </SidebarMenuItem>
            );
          })}
        </SidebarMenu>
      </SidebarContent>

      <Separator className="my-2 bg-slate-200/60 dark:bg-slate-800/40" />

      <SidebarFooter className="p-2">
        <SidebarMenu>
          <SidebarMenuItem>
            <Link href={helpNavItem.href} passHref legacyBehavior>
              <SidebarMenuButton
                isActive={pathname.startsWith(helpNavItem.href)}
                tooltip={{ children: helpNavItem.label, className: 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 border-none font-medium px-3 py-1.5 shadow-md' }}
                className={`text-sidebar-foreground hover:bg-slate-100 dark:hover:bg-slate-900/60 rounded-xl px-3 py-2 transition-all duration-300 ${
                  pathname.startsWith(helpNavItem.href) ? 'bg-blue-600/10 text-blue-600 dark:bg-blue-500/10 dark:text-blue-400 font-semibold border-l-2 border-blue-600' : ''
                }`}
              >
                <helpNavItem.icon className={`h-5 w-5 ${pathname.startsWith(helpNavItem.href) ? 'text-blue-600 dark:text-blue-400' : 'text-slate-500'}`} />
                {state === 'expanded' && <span className="ml-2">{helpNavItem.label}</span>}
              </SidebarMenuButton>
            </Link>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
