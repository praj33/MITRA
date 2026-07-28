// components/pages/CalendarPage.tsx — Weekly calendar view with navigation
import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Clock, MapPin, Plus, ChevronLeft, ChevronRight, Trash2 } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';

interface CalendarEvent {
  id: string; title: string; start: string; end: string;
  color: string; description: string; location: string;
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const CalendarPage: React.FC<{ onChatNavigate: (msg: string) => void }> = ({ onChatNavigate }) => {
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewDate, setViewDate] = useState(new Date());

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await CompanionService.getCalendarEvents();
      setEvents(data.events || []);
    } catch { setEvents([]); }
    setLoading(false);
  }, []);

  useEffect(() => { fetchEvents(); }, [fetchEvents]);

  const deleteEvent = async (eventId: string) => {
    try {
      const base = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      await fetch(`${base}/api/pages/calendar/events/${eventId}`, { method: 'DELETE' });
      setEvents(prev => prev.filter(e => e.id !== eventId));
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  const todayStr = new Date().toDateString();
  const weekStart = new Date(viewDate);
  weekStart.setDate(weekStart.getDate() - weekStart.getDay());
  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + i);
    return d;
  });

  const goToPrevWeek = () => {
    setViewDate(prev => {
      const d = new Date(prev);
      d.setDate(d.getDate() - 7);
      return d;
    });
  };

  const goToNextWeek = () => {
    setViewDate(prev => {
      const d = new Date(prev);
      d.setDate(d.getDate() + 7);
      return d;
    });
  };

  const goToToday = () => setViewDate(new Date());

  const getEventsForDay = (day: Date) =>
    events.filter(e => new Date(e.start).toDateString() === day.toDateString());

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // Get upcoming events from today onwards
  const now = new Date();
  const upcomingEvents = events
    .filter(e => new Date(e.start) >= new Date(now.toDateString()))
    .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      className="page-container"
    >
      {/* Header */}
      <div className="page-header">
        <div className="flex items-center gap-3">
          <div className="page-icon"><Calendar size={20} /></div>
          <div>
            <h1 className="page-title">Calendar</h1>
            <p className="page-subtitle">{viewDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button onClick={goToPrevWeek} className="page-btn-icon" aria-label="Previous week"><ChevronLeft size={16} /></button>
          <button onClick={goToToday} className="page-btn-sm">Today</button>
          <button onClick={goToNextWeek} className="page-btn-icon" aria-label="Next week"><ChevronRight size={16} /></button>
          <button onClick={() => onChatNavigate('Create a calendar event')} className="page-btn-primary"><Plus size={14} /> Add Event</button>
        </div>
      </div>

      {/* Week strip */}
      <div className="calendar-week-strip">
        {weekDays.map((day, i) => {
          const isToday = day.toDateString() === todayStr;
          const dayEvents = getEventsForDay(day);
          return (
            <div
              key={`${day.toISOString()}-${i}`}
              className={`calendar-day-col ${isToday ? 'calendar-day-today' : ''}`}
              onClick={() => setViewDate(new Date(day))}
              style={{ cursor: 'pointer' }}
            >
              <span className="calendar-day-label">{DAYS[day.getDay()]}</span>
              <span className={`calendar-day-num ${isToday ? 'active' : ''}`}>{day.getDate()}</span>
              <div className="calendar-day-events">
                {dayEvents.map(ev => (
                  <div key={ev.id} className="calendar-event-chip" style={{ borderLeftColor: ev.color }}>
                    <span className="calendar-event-time">{formatTime(ev.start)}</span>
                    <span className="calendar-event-title">{ev.title}</span>
                    {ev.location && <span className="calendar-event-loc"><MapPin size={10} /> {ev.location}</span>}
                  </div>
                ))}
                {dayEvents.length === 0 && <span className="calendar-no-events">No events</span>}
              </div>
            </div>
          );
        })}
      </div>

      {/* Upcoming list */}
      <div className="page-section">
        <h3 className="page-section-title">Upcoming Events</h3>
        {loading ? (
          <div className="page-loading">Loading events...</div>
        ) : upcomingEvents.length === 0 ? (
          <div className="page-empty">
            <Calendar size={32} className="text-text-muted" />
            <p>No upcoming events</p>
            <button onClick={() => onChatNavigate('Create a calendar event for tomorrow')} className="page-btn-primary mt-2"><Plus size={14} /> Create Event</button>
          </div>
        ) : (
          <div className="page-card-list">
            {upcomingEvents.map(ev => (
              <motion.div key={ev.id} className="page-card" whileHover={{ scale: 1.01 }} style={{ borderLeftColor: ev.color, borderLeftWidth: 3 }}>
                <div className="page-card-header">
                  <h4 className="page-card-title">{ev.title}</h4>
                  <div className="flex items-center gap-2">
                    <span className="page-card-badge" style={{ background: ev.color + '22', color: ev.color }}>
                      <Clock size={10} /> {formatTime(ev.start)} – {formatTime(ev.end)}
                    </span>
                    <button onClick={() => deleteEvent(ev.id)} className="page-btn-icon text-text-muted hover:text-red-400" title="Delete event"><Trash2 size={14} /></button>
                  </div>
                </div>
                {ev.description && <p className="page-card-desc">{ev.description}</p>}
                {ev.location && <p className="page-card-meta"><MapPin size={12} /> {ev.location}</p>}
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
};

export default CalendarPage;
