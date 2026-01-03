"use client";

import { Card } from "@/components/ui/card";

interface Event {
  id: string;
  title: string;
  location?: string;
  start_at: string;
  end_at: string;
  all_day: boolean;
}

interface DailyScheduleViewProps {
  events: Event[];
  date: Date;
}

const TIME_SLOTS = [
  "12 AM", "1 AM", "2 AM", "3 AM", "4 AM", "5 AM", "6 AM", "7 AM",
  "8 AM", "9 AM", "10 AM", "11 AM", "noon", "1 PM", "2 PM", "3 PM",
  "4 PM", "5 PM", "6 PM", "7 PM", "8 PM", "9 PM", "10 PM", "11 PM"
];

const COLORS = [
  "bg-blue-300",
  "bg-gray-300",
  "bg-purple-300",
  "bg-green-300",
  "bg-yellow-300",
  "bg-pink-300",
];

export function DailyScheduleView({ events, date }: DailyScheduleViewProps) {
  // Convert time string to hour (8 AM = 8, 1 PM = 13, etc.)
  const timeToHour = (timeStr: string): number => {
    const hour = new Date(timeStr).getHours();
    return hour;
  };

  // Calculate position and height for an event
  const getEventStyle = (event: Event) => {
    const startHour = timeToHour(event.start_at);
    const endHour = timeToHour(event.end_at);
    const startMinutes = new Date(event.start_at).getMinutes();
    const endMinutes = new Date(event.end_at).getMinutes();

    // Calculate position from 12 AM (hour 0)
    const startPosition = startHour * 100 + (startMinutes / 60) * 100;
    const duration = (endHour - startHour) * 100 + ((endMinutes - startMinutes) / 60) * 100;

    return {
      top: `${startPosition}px`,
      height: `${duration}px`,
    };
  };

  // Assign colors to events
  const eventsWithColors = events.map((event, idx) => ({
    ...event,
    color: COLORS[idx % COLORS.length],
  }));

  return (
    <div className="w-full max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-semibold">
          {date.toLocaleDateString("en-US", {
            weekday: "short",
            month: "short",
            day: "numeric",
            year: "numeric"
          })}
        </h2>
      </div>

      {/* Schedule Grid */}
      <div className="relative bg-black text-white rounded-lg overflow-hidden">
        {/* Time slots */}
        <div className="relative">
          {TIME_SLOTS.map((time, idx) => (
            <div
              key={time}
              className="relative h-[100px] border-t border-white/20"
              style={{ borderTopStyle: idx === 0 ? 'none' : 'solid' }}
            >
              {/* Time label */}
              <div className="absolute left-4 top-2 text-sm font-medium">
                {time}
              </div>

              {/* Dotted line at 30 minutes */}
              {idx < TIME_SLOTS.length - 1 && (
                <div className="absolute bottom-0 left-0 right-0 border-b border-dotted border-white/30" />
              )}
            </div>
          ))}
        </div>

        {/* Events overlay */}
        <div className="absolute top-0 left-24 right-4 h-full pointer-events-none">
          {eventsWithColors.map((event) => {
            const style = getEventStyle(event);

            return (
              <div
                key={event.id}
                className={`absolute left-0 right-0 ${event.color} rounded-md p-3 text-black pointer-events-auto`}
                style={style}
              >
                <div className="font-semibold text-sm">{event.title}</div>
                {event.location && (
                  <div className="text-xs mt-1">{event.location}</div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Event count */}
      <div className="mt-4 text-sm text-gray-600 dark:text-gray-400">
        {events.length} {events.length === 1 ? 'event' : 'events'} today
      </div>
    </div>
  );
}
