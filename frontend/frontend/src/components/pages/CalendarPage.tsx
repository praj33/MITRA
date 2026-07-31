import React, { useEffect, useState, useCallback } from 'react';
import { motion } from 'framer-motion';
import { Calendar, Clock, MapPin, Plus, ChevronLeft, ChevronRight, Trash2, X } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';
import { useCompanionStore } from '../../store/companion.store';
import { showToast } from '../shell/Toast';

interface CalendarEvent {
  id: string; title: string; start: string; end: string;
  color: string; description: string; location: string;
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const CalendarPage: React.FC<{ onChatNavigate: (msg: string) => void }> = ({ onChatNavigate }) => {
  const userId = useCompanionStore(s => s.userId);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewDate, setViewDate] = useState(new Date());
  const [eventFilter, setEventFilter] = useState<'upcoming' | 'past' | 'all'>('upcoming');

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await CompanionService.getCalendarEvents(userId);
      setEvents(data.events || []);
    } catch { setEvents([]); }
    setLoading(false);
  }, [userId]);

  useEffect(() => { fetchEvents(); }, [fetchEvents]);

  const deleteEvent = async (eventId: string) => {
    try {
      setEvents(prev => prev.filter(e => e.id !== eventId));
      await CompanionService.deleteCalendarEvent(eventId, userId);
      showToast('info', 'Event Deleted', 'Calendar event removed.');
    } catch (err) {
      console.error('Delete failed:', err);
      showToast('error', 'Error', 'Failed to delete event.');
    }
  };

  const handleClearPast = async () => {
    try {
      const todayStart = new Date(new Date().setHours(0, 0, 0, 0));
      const res = await CompanionService.clearPastCalendarEvents(userId);
      setEvents(prev => prev.filter(e => new Date(e.start) >= todayStart));
      showToast('success', 'Past Events Cleared', `Removed ${res.deleted_count || 0} past events.`);
    } catch (err) {
      console.error('Failed to clear past events:', err);
      showToast('error', 'Cleanup Failed', 'Could not clear past events.');
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

  // Event list filtering logic
  const todayStart = new Date(new Date().setHours(0, 0, 0, 0));
  const filteredEvents = events
    .filter(e => {
      const evDate = new Date(e.start);
      if (eventFilter === 'upcoming') return evDate >= todayStart;
      if (eventFilter === 'past') return evDate < todayStart;
      return true;
    })
    .sort((a, b) => new Date(a.start).getTime() - new Date(b.start).getTime());

  const pastEventsCount = events.filter(e => new Date(e.start) < todayStart).length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
      className="page-container pb-20"
    >
      {/* Header */}
      <div className="page-header flex-wrap">
        <div className="flex items-center gap-3">
          <div className="page-icon"><Calendar size={20} /></div>
          <div>
            <h1 className="page-title">Calendar</h1>
            <p className="page-subtitle">{viewDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</p>
          </div>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          {pastEventsCount > 0 && (
            <button
              onClick={handleClearPast}
              className="px-3 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 text-xs font-semibold flex items-center gap-1.5 transition-colors"
              title="Delete all events before today"
            >
              <Trash2 size={13} /> Clear Past ({pastEventsCount})
            </button>
          )}
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
                        className="calendar-event-chip group relative flex items-center justify-between gap-1 pr-1"
                        style={{ borderLeftColor: ev.color }}
                        title={`${ev.title} (${formatTime(ev.start)})`}
                      >
                        <div className="flex flex-col min-w-0 flex-1">
                          <span className="event-time">{formatTime(ev.start)}</span>
                          <span className="event-title truncate">{ev.title}</span>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteEvent(ev.id);
                          }}
                          className="opacity-60 hover:opacity-100 p-0.5 rounded text-text-muted hover:text-red-400 transition-opacity"
                          title="Delete Event"
                        >
                          <X size={12} />
                        </button>
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

          {/* Events List & Filter Tabs */}
          <div className="calendar-upcoming-section">
            <div className="flex items-center justify-between mb-3 flex-wrap gap-2">
              <h3 className="section-title capitalize">{eventFilter} Events</h3>
              <div className="flex items-center gap-1 p-1 rounded-xl bg-surface-raised border border-border-subtle text-xs font-medium">
                <button
                  onClick={() => setEventFilter('upcoming')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    eventFilter === 'upcoming' ? 'bg-surface-overlay text-text-primary font-semibold' : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Upcoming
                </button>
                <button
                  onClick={() => setEventFilter('past')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    eventFilter === 'past' ? 'bg-surface-overlay text-text-primary font-semibold' : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  Past ({pastEventsCount})
                </button>
                <button
                  onClick={() => setEventFilter('all')}
                  className={`px-3 py-1 rounded-lg transition-all ${
                    eventFilter === 'all' ? 'bg-surface-overlay text-text-primary font-semibold' : 'text-text-secondary hover:text-text-primary'
                  }`}
                >
                  All ({events.length})
                </button>
              </div>
            </div>

            {filteredEvents.length === 0 ? (
              <div className="page-empty">
                <Calendar size={28} className="text-text-muted" />
                <p>No {eventFilter} events found</p>
              </div>
            ) : (
              <div className="page-card-list">
                {filteredEvents.map(ev => (
                  <motion.div key={ev.id} className="page-card calendar-event-card" whileHover={{ scale: 1.01 }}>
                    <div className="event-color-bar" style={{ background: ev.color }} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <h4 className="page-card-title">{ev.title}</h4>
                        {new Date(ev.start) < todayStart && (
                          <span className="px-2 py-0.5 rounded text-[10px] bg-red-500/10 text-red-400 font-medium border border-red-500/20">
                            Past
                          </span>
                        )}
                      </div>
                      {ev.description && <p className="page-card-desc">{ev.description}</p>}
                      <div className="flex items-center gap-3 mt-2 flex-wrap">
                        <span className="page-card-meta"><Clock size={12} /> {new Date(ev.start).toLocaleDateString([], { month: 'short', day: 'numeric' })} @ {formatTime(ev.start)} – {formatTime(ev.end)}</span>
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
