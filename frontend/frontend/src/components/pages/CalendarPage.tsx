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
      setEvents(prev => prev.filter(e => e.id !== eventId));
      await CompanionService.deleteCalendarEvent(eventId);
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
      className="page-container pb-20"
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

      {/* Grid view */}
      {loading ? (
        <div className="page-loading">Loading events...</div>
      ) : (
        <>
          <div className="calendar-week-strip mb-6">
            {weekDays.map(day => {
              const isToday = day.toDateString() === todayStr;
              const dayEvents = getEventsForDay(day);

              return (
                <div key={day.toISOString()} className={`calendar-day-col ${isToday ? 'is-today' : ''}`}>
                  <div className="calendar-day-header">
                    <span className="day-name">{DAYS[day.getDay()]}</span>
                    <span className={`day-number ${isToday ? 'today-pill' : ''}`}>{day.getDate()}</span>
                  </div>
                  <div className="calendar-day-events">
                    {dayEvents.map(ev => (
                      <div
                        key={ev.id}
                        className="calendar-event-chip"
                        style={{ borderLeftColor: ev.color }}
                        title={`${ev.title} (${formatTime(ev.start)})`}
                      >
                        <span className="event-time">{formatTime(ev.start)}</span>
                        <span className="event-title">{ev.title}</span>
                      </div>
                    ))}
                    {dayEvents.length === 0 && (
                      <span className="no-events-text">No events</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Upcoming Events List */}
          <div className="calendar-upcoming-section">
            <h3 className="section-title">Upcoming Events</h3>
            {upcomingEvents.length === 0 ? (
              <div className="page-empty">
                <Calendar size={28} className="text-text-muted" />
                <p>No upcoming events found</p>
              </div>
            ) : (
              <div className="page-card-list">
                {upcomingEvents.map(ev => (
                  <motion.div key={ev.id} className="page-card calendar-event-card" whileHover={{ scale: 1.01 }}>
                    <div className="event-color-bar" style={{ background: ev.color }} />
                    <div className="flex-1 min-w-0">
                      <h4 className="page-card-title">{ev.title}</h4>
                      {ev.description && <p className="page-card-desc">{ev.description}</p>}
                      <div className="flex items-center gap-3 mt-2 flex-wrap">
                        <span className="page-card-meta"><Clock size={12} /> {formatTime(ev.start)} – {formatTime(ev.end)}</span>
                        {ev.location && <span className="page-card-meta"><MapPin size={12} /> {ev.location}</span>}
                      </div>
                    </div>
                    <button
                      onClick={() => deleteEvent(ev.id)}
                      className="page-btn-icon text-text-muted hover:text-red-400"
                      title="Delete Event"
                    >
                      <Trash2 size={14} />
                    </button>
                  </motion.div>
                ))}
              </div>
            )}
          </div>
        </>
      )}
    </motion.div>
  );
};

export default CalendarPage;
