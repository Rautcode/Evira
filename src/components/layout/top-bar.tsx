
"use client";

import * as React from 'react';
import { Bell, CalendarDays, ChevronRight, LogOut, Settings, User, PanelLeft, Sun, Moon } from 'lucide-react';
import { AppLogo } from './app-logo';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { useTheme } from '@/components/layout/theme-provider';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { format } from 'date-fns';
import { useSidebar } from '@/components/ui/sidebar';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export function TopBar() {
  const [date, setDate] = React.useState<Date | undefined>(new Date());
  const { toggleSidebar, isMobile } = useSidebar();
  const pathname = usePathname();
  const { theme, toggleTheme } = useTheme();

  const generateBreadcrumbs = () => {
    const pathSegments = pathname.split('/').filter(segment => segment);
    const breadcrumbs = [{ label: 'Home', href: '/dashboard' }];
    
    let currentPath = '';
    pathSegments.forEach(segment => {
      currentPath += `/${segment}`;
      // Avoid duplicating the "Home" breadcrumb if the current path is also /dashboard
      if (currentPath === '/dashboard' && breadcrumbs.length === 1 && breadcrumbs[0].href === '/dashboard') {
        // Potentially update the label of the first breadcrumb if needed, or just skip adding.
        // For now, let's assume the first "Home -> /dashboard" is sufficient if path is just /dashboard
        // Or, ensure the label for the specific segment is different.
        // The issue is the key, so if href is the same, label should be different or key needs index.
        // Let's assume the first item is fine and we only add subsequent different segments.
        if (segment.toLowerCase() !== 'dashboard') { // A more robust check might be needed
             breadcrumbs.push({
                label: segment.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
                href: currentPath
            });
        } else if (breadcrumbs.length > 0 && breadcrumbs[breadcrumbs.length-1].href !== currentPath) {
           // If path is /dashboard/something, then 'Dashboard' segment itself should be added.
            breadcrumbs.push({
                label: segment.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
                href: currentPath
            });
        }

      } else {
         breadcrumbs.push({
            label: segment.split('-').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' '),
            href: currentPath
        });
      }
    });
    // Remove duplicate /dashboard if the path starts with /dashboard
    if (breadcrumbs.length > 1 && breadcrumbs[0].href === breadcrumbs[1].href) {
        breadcrumbs.splice(0,1);
    }

    return breadcrumbs;
  };

  const breadcrumbs = generateBreadcrumbs();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b border-slate-200/50 bg-white/60 dark:bg-slate-950/60 backdrop-blur-md px-4 shadow-sm sm:px-6 transition-all duration-300 dark:border-slate-800/40">
      <div className="flex items-center gap-4">
        {isMobile && (
          <Button variant="ghost" size="icon" onClick={toggleSidebar} className="-ml-2">
            <PanelLeft className="h-6 w-6" />
            <span className="sr-only">Toggle Sidebar</span>
          </Button>
        )}
        {!isMobile && <AppLogo href="/dashboard" iconSize={24} textSize="text-lg" />}

        <nav aria-label="Breadcrumb" className="hidden md:flex items-center text-sm">
          <ol role="list" className="flex items-center space-x-1">
            {breadcrumbs.map((crumb, index) => (
              <li key={`${crumb.href}-${index}`}> {/* Ensure unique key by appending index */}
                <div className="flex items-center">
                  {index > 0 && <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />}
                  <Link
                    href={crumb.href}
                    className={`ml-1 font-medium ${index === breadcrumbs.length -1 ? 'text-foreground' : 'text-muted-foreground hover:text-foreground'}`}
                    aria-current={index === breadcrumbs.length - 1 ? 'page' : undefined}
                  >
                    {crumb.label}
                  </Link>
                </div>
              </li>
            ))}
          </ol>
        </nav>
      </div>

      <div className="flex items-center gap-3 md:gap-4">
        <Popover>
          <PopoverTrigger asChild>
            <Button variant="outline" className="w-auto justify-start text-left font-normal border-slate-200 dark:border-slate-800 bg-white/40 dark:bg-slate-900/40">
              <CalendarDays className="mr-2 h-4 w-4 text-muted-foreground" />
              {date ? format(date, 'PPP') : <span>Pick a date</span>}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0 border-slate-200 dark:border-slate-800" align="end">
            <Calendar
              mode="single"
              selected={date}
              onSelect={setDate}
            />
          </PopoverContent>
        </Popover>

        <Button 
          variant="ghost" 
          size="icon" 
          onClick={toggleTheme} 
          aria-label="Toggle theme" 
          className="text-foreground hover:bg-slate-100 dark:hover:bg-slate-900 rounded-full"
        >
          {theme === 'dark' ? (
            <Sun className="h-5 w-5 text-amber-400 transition-all duration-300 hover:rotate-45" />
          ) : (
            <Moon className="h-5 w-5 text-slate-700 transition-all duration-300 hover:-rotate-12" />
          )}
        </Button>

        <Button variant="ghost" size="icon" aria-label="Notifications" className="relative hover:bg-slate-100 dark:hover:bg-slate-900 rounded-full">

          <Bell className="h-5 w-5" />
          <span className="absolute -top-1 -right-1 flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
            <span className="relative inline-flex rounded-full h-3 w-3 bg-primary"></span>
          </span>
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-9 w-9 rounded-full">
              <Avatar className="h-9 w-9">
                <AvatarImage src="https://picsum.photos/100/100?grayscale" alt="User Avatar" data-ai-hint="person face"/>
                <AvatarFallback>UA</AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end" forceMount>
            <DropdownMenuLabel className="font-normal">
              <div className="flex flex-col space-y-1">
                <p className="text-sm font-medium leading-none">User Admin</p>
                <p className="text-xs leading-none text-muted-foreground">
                  admin@example.com
                </p>
              </div>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              <span>Profile</span>
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              <span>Settings</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="cursor-pointer" onClick={() => {
              localStorage.removeItem('auth_token');
              document.cookie = 'auth_token=; Max-Age=0; path=/;';
              window.location.href = '/login';
            }}>
              <LogOut className="mr-2 h-4 w-4" />
              <span>Log out</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
