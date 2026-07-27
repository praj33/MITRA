// components/pages/CalendarPage.tsx — Weekly calendar view
import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Clock, MapPin, Plus, ChevronLeft, ChevronRight } from 'lucide-react';
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

  useEffect(() => {
    (async () => {
      try {
        const data = await CompanionService.getCalendarEvents();
        setEvents(data.events || []);
      } catch { setEvents([]); }
      setLoading(false);
    })();
  }, []);

  const todayStr = new Date().toDateString();
  const weekStart = new Date(viewDate);
  weekStart.setDate(weekStart.getDate() - weekStart.getDay());
  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(weekStart);
    d.setDate(d.getDate() + i);
    return d;
  });

  const getEventsForDay = (day: Date) =>
    events.filter(e => new Date(e.start).toDateString() === day.toDateString());

  const formatTime = (iso: string) =>
    new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

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
          <button onClick={() => { const d = new Date(viewDate); d.setDate(d.getDate() - 7); setViewDate(d); }} className="page-btn-icon"><ChevronLeft size={16} /></button>
          <button onClick={() => setViewDate(new Date())} className="page-btn-sm">Today</button>
          <button onClick={() => { const d = new Date(viewDate); d.setDate(d.getDate() + 7); setViewDate(d); }} className="page-btn-icon"><ChevronRight size={16} /></button>
          <button onClick={() => onChatNavigate('Create a calendar event')} className="page-btn-primary"><Plus size={14} /> Add Event</button>
        </div>
      </div>

      {/* Week strip */}
      <div className="calendar-week-strip">
        {weekDays.map((day, i) => {
          const isToday = day.toDateString() === todayStr;
          const dayEvents = getEventsForDay(day);
          return (
            <div key={i} className={`calendar-day-col ${isToday ? 'calendar-day-today' : ''}`}>
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
        ) : events.length === 0 ? (
          <div className="page-empty">
            <Calendar size={32} className="text-text-muted" />
            <p>No upcoming events</p>
            <button onClick={() => onChatNavigate('Create a calendar event for tomorrow')} className="page-btn-primary mt-2"><Plus size={14} /> Create Event</button>
          </div>
        ) : (
          <div className="page-card-list">
            {events.map(ev => (
              <motion.div key={ev.id} className="page-card" whileHover={{ scale: 1.01 }} style={{ borderLeftColor: ev.color, borderLeftWidth: 3 }}>
                <div className="page-card-header">
                  <h4 className="page-card-title">{ev.title}</h4>
                  <span className="page-card-badge" style={{ background: ev.color + '22', color: ev.color }}>
                    <Clock size={10} /> {formatTime(ev.start)} – {formatTime(ev.end)}
                  </span>
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
