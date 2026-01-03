"use client";

import { useEffect, useState } from "react";
import { DailyScheduleView } from "@/components/DailyScheduleView";
import { Button } from "@/components/ui/button";
import { eventsAPI, calendarsAPI, oauthAPI, APIError } from "@/lib/api-client";

interface Event {
  id: string;
  title: string;
  location?: string;
  start_at: string;
  end_at: string;
  all_day: boolean;
}

export default function CalendarPage() {
  const [events, setEvents] = useState<Event[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const [checkingConnection, setCheckingConnection] = useState(true);
  const today = new Date();

  // Check OAuth connection status
  const checkConnection = async () => {
    setCheckingConnection(true);
    try {
      const accounts = await oauthAPI.getStatus();
      const connected = accounts && accounts.length > 0;
      setIsConnected(connected);
      console.log('Connection check:', connected ? 'Connected' : 'Not connected', accounts);
    } catch (err) {
      console.error('Error checking connection:', err);
      // If check fails, assume not connected but don't break the UI
      setIsConnected(false);
    } finally {
      setCheckingConnection(false);
    }
  };

  // Fetch today's events
  const fetchTodaysEvents = async () => {
    setLoading(true);
    setError(null);

    try {
      // Get start and end of today
      const startOfDay = new Date(today);
      startOfDay.setHours(0, 0, 0, 0);

      const endOfDay = new Date(today);
      endOfDay.setHours(23, 59, 59, 999);

      // Call backend API using the client
      const data = await eventsAPI.list({
        start_min: startOfDay.toISOString(),
        start_max: endOfDay.toISOString(),
      });

      setEvents(data.events || []);
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError('Failed to load events');
      }
      console.error('Error fetching events:', err);
    } finally {
      setLoading(false);
    }
  };

  // Sync calendars from Google
  const syncCalendars = async () => {
    setSyncing(true);
    setError(null);

    try {
      await calendarsAPI.sync();

      // After sync, fetch today's events
      await fetchTodaysEvents();
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError('Failed to sync calendars');
      }
      console.error('Error syncing calendars:', err);
    } finally {
      setSyncing(false);
    }
  };

  // Disconnect Google Calendar
  const disconnectGoogle = async () => {
    try {
      await oauthAPI.disconnect();
      setIsConnected(false);
      setEvents([]);
      setError('Google Calendar disconnected. Connect again to sync events.');
    } catch (err) {
      if (err instanceof APIError) {
        setError(err.message);
      } else {
        setError('Failed to disconnect');
      }
      console.error('Error disconnecting:', err);
    }
  };

  // Load connection status and events on mount
  useEffect(() => {
    // Check connection status (non-blocking)
    checkConnection();
    // Fetch events
    fetchTodaysEvents();
  }, []);

  // Re-check connection after OAuth redirect
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('success') === 'true') {
      // Just connected - check status and sync
      setTimeout(() => {
        checkConnection();
        syncCalendars();
      }, 500);
    }
  }, []);

  return (
    <main className="mx-auto w-full max-w-5xl px-6 py-10">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-3xl font-semibold tracking-tight">Calendar</h1>

        <div className="flex gap-2">
          <Button
            onClick={syncCalendars}
            disabled={syncing}
            variant="outline"
          >
            {syncing ? 'Syncing...' : 'Sync from Google'}
          </Button>

          {!isConnected ? (
            <Button
              onClick={async () => {
                // Get user ID and redirect to OAuth
                const sessionResponse = await fetch('/api/auth/session');
                const session = await sessionResponse.json();
                const userId = session?.user?.id;
                if (userId) {
                  window.location.href = `http://localhost:8000/oauth/google/authorize?user_id=${userId}`;
                } else {
                  setError('Please log in first');
                }
              }}
              variant="default"
              disabled={checkingConnection}
            >
              {checkingConnection ? 'Checking...' : 'Connect Google Calendar'}
            </Button>
          ) : (
            <Button
              onClick={disconnectGoogle}
              variant="outline"
              className="text-red-600 hover:text-red-700"
            >
              Disconnect
            </Button>
          )}

          <Button
            onClick={fetchTodaysEvents}
            disabled={loading}
          >
            {loading ? 'Loading...' : 'Refresh'}
          </Button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-lg">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-500">
          Loading today's schedule...
        </div>
      ) : (
        <>
          {events.length === 0 && (
            <div className="text-center mb-4">
              <p className="text-gray-500 text-sm">
                {!isConnected
                  ? 'No events for today. Click "Connect Google Calendar" to get started.'
                  : 'No events for today. Click "Sync from Google" to import your calendar.'}
              </p>
            </div>
          )}
          <DailyScheduleView events={events} date={today} />
        </>
      )}
    </main>
  );
}
