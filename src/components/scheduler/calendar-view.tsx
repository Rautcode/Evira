'use client';

import * as React from 'react';
import { Calendar, dateFnsLocalizer, Event } from 'react-big-calendar';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import { parse, startOfWeek, getDay, format } from 'date-fns';

const locales = {
  'en-US': require('date-fns/locale/en-US'),
};

const localizer = dateFnsLocalizer({
  format,
  parse,
  startOfWeek: () => startOfWeek(new Date(), { weekStartsOn: 1 }),
  getDay,
  locales,
});

interface CalendarViewProps {
  schedules: any[];
}

export function CalendarView({ schedules }: CalendarViewProps) {
  // Map schedules to calendar events
  const events: Event[] = schedules.map((sch: any) => ({
    id: sch.id,
    title: sch.name || sch.title || `Task #${sch.id}`,
    start: sch.next_run ? new Date(sch.next_run) : new Date(),
    end: sch.next_run ? new Date(sch.next_run) : new Date(),
    allDay: false,
    resource: sch,
  }));

  return (
    <div style={{ height: 600 }}>
      <Calendar
        localizer={localizer}
        events={events}
        startAccessor="start"
        endAccessor="end"
        titleAccessor="title"
        style={{ height: 600 }}
        popup
        views={['month', 'week', 'day', 'agenda']}
        eventPropGetter={() => ({ style: { backgroundColor: '#2563eb', color: 'white', borderRadius: 6 } })}
      />
    </div>
  );
}
