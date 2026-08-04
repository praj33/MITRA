import React, { useEffect, useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Calendar, Clock, MapPin, Plus, ChevronLeft, ChevronRight, Trash2, X, Check } from 'lucide-react';
import { CompanionService } from '../../services/companion.service';
import { useCompanionStore } from '../../store/companion.store';
import { showToast } from '../shell/Toast';

interface CalendarEvent {
  id: string; title: string; start: string; end: string;
  color: string; description: string; location: string;
  has_time?: boolean;
}

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const CalendarPage: React.FC<{ onChatNavigate: (msg: string) => void }> = ({ onChatNavigate }) => {
  const userId = useCompanionStore(s => s.userId);
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewDate, setViewDate] = useState(new Date());
  const [eventFilter, setEventFilter] = useState<'upcoming' | 'past' | 'all'>('upcoming');

  // Add Event Form State
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDate, setNewDate] = useState(new Date().toISOString().split('T')[0]);
  const [newStartTime, setNewStartTime] = useState('09:00');
  const [newEndTime, setNewEndTime] = useState('10:00');
  const [newLocation, setNewLocation] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const data = await CompanionService.getCalendarEvents(userId);
      setEvents(data.events || []);
    } catch { setEvents([]); }
    setLoading(false);
  }, [userId]);

  useEffect(() => { fetchEvents(); }, [fetchEvents]);

  const handleCreateEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim() || submitting) return;

    setSubmitting(true);
    try {
      const startIso = newStartTime ? `${newDate}T${newStartTime}:00` : newDate;
      const endIso = newEndTime ? `${newDate}T${newEndTime}:00` : newDate;

      const res = await CompanionService.createCalendarEvent(
        newTitle.trim(),
        startIso,
        endIso,
        newLocation.trim(),
        newDescription.trim(),
        '#7c5cfc',
        userId
      );

      if (res && res.event) {
        setEvents(prev => [...prev, res.event]);
      } else {
        await fetchEvents();
      }

      showToast('success', 'Event Created', `Added "${newTitle.trim()}" to calendar.`);
      setNewTitle('');
      setNewLocation('');
      setNewDescription('');
      setShowAddForm(false);
    } catch (err) {
      console.error('Failed to create event:', err);
      showToast('error', 'Error', 'Failed to create calendar event.');
    } finally {
      setSubmitting(false);
    }
  };

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

  const formatTime = (iso: string, hasTime?: boolean) => {
    if (hasTime === false || !iso || !iso.includes('T')) return 'No time set';
    return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

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
      className="page-container pb-24 px-3 sm:px-6"
    >
      {/* Header — Fully Responsive on Mobile */}
      <div className="flex flex-col sm:flex-row gap-3 sm:items-center justify-between mb-4 border-b border-border-subtle pb-4">
        <div className="flex items-center gap-3">
          <div className="page-icon"><Calendar size={20} /></div>
          <div>
            <h1 className="page-title text-base sm:text-xl font-bold">Calendar</h1>
            <p className="page-subtitle text-xs text-text-muted">{viewDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap w-full sm:w-auto justify-between sm:justify-end">
          {pastEventsCount > 0 && (
            <button
              onClick={handleClearPast}
              className="px-2.5 py-1.5 rounded-lg bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 text-2xs font-semibold flex items-center gap-1 transition-colors"
              title="Delete all events before today"
            >
              <Trash2 size={12} /> Clear ({pastEventsCount})
            </button>
          )}
          <div className="flex items-center gap-1">
            <button onClick={goToPrevWeek} className="page-btn-icon p-1.5" aria-label="Previous week"><ChevronLeft size={16} /></button>
            <button onClick={goToToday} className="page-btn-sm text-2xs py-1 px-2.5">Today</button>
            <button onClick={goToNextWeek} className="page-btn-icon p-1.5" aria-label="Next week"><ChevronRight size={16} /></button>
          </div>
          <button
            onClick={() => setShowAddForm(prev => !prev)}
            className="page-btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
          >
            <Plus size={14} /> Add Event
          </button>
        </div>
      </div>

      {/* Mobile-Optimized Inline Add Event Form */}
      <AnimatePresence>
        {showAddForm && (
          <motion.form
            initial={{ opacity: 0, height: 0, y: -10 }}
            animate={{ opacity: 1, height: 'auto', y: 0 }}
            exit={{ opacity: 0, height: 0, y: -10 }}
            onSubmit={handleCreateEvent}
            className="mb-6 p-4 rounded-xl bg-surface-elevated border border-brand/30 flex flex-col gap-3 shadow-xl max-w-full overflow-hidden"
          >
            <div className="flex items-center justify-between border-b border-border-subtle pb-2">
              <h3 className="text-xs sm:text-sm font-semibold text-text-primary flex items-center gap-2">
                <Calendar size={16} className="text-brand-light" /> Create Calendar Event
              </h3>
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="text-text-muted hover:text-text-primary p-1"
              >
                <X size={16} />
              </button>
            </div>

            <div className="flex flex-col gap-3">
              <div>
                <label className="block text-2xs text-text-muted mb-1 font-medium">Event Title *</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  onChange={e => setNewTitle(e.target.value)}
                  placeholder="e.g. Ganesh Utsav / Client Meeting"
                  className="w-full bg-surface-overlay border border-border-subtle rounded-lg px-3 py-2 text-xs text-text-primary focus:outline-none focus:border-brand"
                />
              </div>

              <div>
                <label className="block text-2xs text-text-muted mb-1 font-medium">Date *</label>
                <input
                  type="date"
                  required
                  value={newDate}
                  onChange={e => setNewDate(e.target.value)}
                  className="w-full bg-surface-overlay border border-border-subtle rounded-lg px-3 py-2 text-xs text-text-primary focus:outline-none focus:border-brand"
                />
              </div>

              <div className="grid grid-cols-2 gap-2 sm:gap-3">
                <div>
                  <label className="block text-2xs text-text-muted mb-1 font-medium">Start Time</label>
                  <input
                    type="time"
                    value={newStartTime}
                    onChange={e => setNewStartTime(e.target.value)}
                    className="w-full bg-surface-overlay border border-border-subtle rounded-lg px-2.5 py-2 text-xs text-text-primary focus:outline-none focus:border-brand"
                  />
                </div>

                <div>
                  <label className="block text-2xs text-text-muted mb-1 font-medium">End Time</label>
                  <input
                    type="time"
                    value={newEndTime}
                    onChange={e => setNewEndTime(e.target.value)}
                    className="w-full bg-surface-overlay border border-border-subtle rounded-lg px-2.5 py-2 text-xs text-text-primary focus:outline-none focus:border-brand"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <button
                type="button"
                onClick={() => setShowAddForm(false)}
                className="px-3 py-1.5 rounded-lg border border-border-subtle text-xs text-text-muted hover:bg-surface-overlay"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting || !newTitle.trim()}
                className="px-4 py-1.5 rounded-lg bg-brand text-white text-xs font-semibold hover:bg-brand-light transition-colors flex items-center gap-1.5"
              >
                <Check size={14} /> {submitting ? 'Saving...' : 'Save Event'}
              </button>
            </div>
          </motion.form>
        )}
      </AnimatePresence>

      {/* Grid view */}
      {loading ? (
        <div className="page-loading py-8 text-center text-xs text-text-muted">Loading events...</div>
      ) : (
        <>
          <div className="calendar-week-strip mb-6 overflow-x-auto pb-2 flex gap-2">
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
                        title={`${ev.title} (${formatTime(ev.start, ev.has_time)})`}
                      >
                        <div className="flex flex-col min-w-0 flex-1">
                          <span className="event-time">{formatTime(ev.start, ev.has_time)}</span>
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

          {/* Filter Bar & Event list */}
          <div className="flex items-center justify-between mb-4 flex-wrap gap-2">
            <div className="flex items-center gap-1">
              {(['upcoming', 'past', 'all'] as const).map(f => (
                <button
                  key={f}
                  onClick={() => setEventFilter(f)}
                  className={`px-2.5 py-1 rounded-full text-2xs capitalize transition-colors ${
                    eventFilter === f
                      ? 'bg-brand-muted text-brand-light font-semibold border border-brand/30'
                      : 'text-text-muted hover:text-text-secondary'
                  }`}
                >
                  {f} ({
                    f === 'upcoming' ? events.filter(e => new Date(e.start) >= todayStart).length :
                    f === 'past' ? events.filter(e => new Date(e.start) < todayStart).length :
                    events.length
                  })
                </button>
              ))}
            </div>
          </div>

          {filteredEvents.length === 0 ? (
            <div className="page-empty py-10 flex flex-col items-center gap-2">
              <Calendar size={32} className="text-text-muted" />
              <p className="text-xs text-text-muted">No {eventFilter} events</p>
              <button onClick={() => setShowAddForm(true)} className="page-btn-primary mt-1 text-xs py-1.5 px-3">
                <Plus size={14} /> Add Event
              </button>
            </div>
          ) : (
            <div className="page-card-list flex flex-col gap-2.5">
              {filteredEvents.map(ev => (
                <motion.div key={ev.id} className="page-card p-3 rounded-xl bg-surface-elevated border border-border-subtle" whileHover={{ scale: 1.005 }}>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-start gap-2.5 min-w-0 flex-1">
                      <div
                        className="w-2 h-9 rounded-full flex-shrink-0 mt-0.5"
                        style={{ backgroundColor: ev.color }}
                      />
                      <div className="min-w-0 flex-1">
                        <h4 className="page-card-title text-xs font-semibold text-text-primary truncate">{ev.title}</h4>
                        <div className="flex items-center gap-2 mt-1 text-2xs text-text-muted flex-wrap">
                          <span className="flex items-center gap-1 font-medium text-text-secondary">
                            <Clock size={11} className="text-brand-light" />
                            {new Date(ev.start).toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })} · {formatTime(ev.start, ev.has_time)}
                          </span>
                          {ev.location && (
                            <span className="flex items-center gap-1 truncate">
                              <MapPin size={11} /> {ev.location}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    <button
                      onClick={() => deleteEvent(ev.id)}
                      className="text-text-muted hover:text-red-400 p-1.5 rounded-lg hover:bg-red-500/10 transition-colors flex-shrink-0"
                      title="Delete event"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </motion.div>
              ))}
            </div>
          )}
        </>
      )}
    </motion.div>
  );
};

export default CalendarPage;
