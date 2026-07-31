// components/shell/SettingsModal.tsx — Settings with theme toggle & user profile
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sun, Moon, Monitor, User, Key, Palette, Info, Check } from 'lucide-react';
import { useCompanionStore } from '../../store/companion.store';
import { showToast } from './Toast';

type Theme = 'dark' | 'light' | 'system';

interface Props {
  open: boolean;
  onClose: () => void;
}

const SettingsModal: React.FC<Props> = ({ open, onClose }) => {
  const { userName, setUserName, apiBase } = useCompanionStore();
  const [theme, setTheme] = useState<Theme>(() => {
    return (localStorage.getItem('mitra-theme') as Theme) || 'dark';
  });
  const [localName, setLocalName] = useState(userName);

  // Keep localName synced when modal opens
  useEffect(() => {
    if (open) setLocalName(userName);
  }, [open, userName]);

  // Apply theme dynamically
  useEffect(() => {
    const root = document.documentElement;
    let resolved = theme;
    if (theme === 'system') {
      resolved = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    root.setAttribute('data-theme', resolved);
    localStorage.setItem('mitra-theme', theme);
  }, [theme]);

  const handleSaveName = () => {
    const cleanName = localName.trim() || 'User';
    setUserName(cleanName);
    localStorage.setItem('mitra_user_name', cleanName);
    showToast('success', 'Settings Saved', `Display name updated to "${cleanName}"`);
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="settings-backdrop"
          onClick={(e) => {
            if (e.target === e.currentTarget) onClose();
          }}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 16 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 16 }}
            transition={{ duration: 0.2 }}
            className="settings-modal"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="settings-header">
              <h2 className="settings-title">Settings</h2>
              <button onClick={onClose} className="settings-close"><X size={16} /></button>
            </div>

            {/* Sections */}
            <div className="settings-body">
              {/* Appearance */}
              <section className="settings-section">
                <h3 className="settings-section-title"><Palette size={14} /> Appearance</h3>
                <div className="settings-theme-row">
                  {([
                    { value: 'dark', icon: <Moon size={16} />, label: 'Dark' },
                    { value: 'light', icon: <Sun size={16} />, label: 'Light (Day)' },
                    { value: 'system', icon: <Monitor size={16} />, label: 'System' },
                  ] as { value: Theme; icon: React.ReactNode; label: string }[]).map(t => (
                    <button
                      key={t.value}
                      onClick={() => setTheme(t.value)}
                      className={`settings-theme-btn ${theme === t.value ? 'active' : ''}`}
                    >
                      {t.icon} {t.label}
                    </button>
                  ))}
                </div>
              </section>

              {/* Profile */}
              <section className="settings-section">
                <h3 className="settings-section-title"><User size={14} /> Profile</h3>
                <div className="settings-field">
                  <label className="settings-label">Display Name</label>
                  <div className="flex items-center gap-2 mt-1">
                    <input
                      type="text" value={localName}
                      onChange={e => setLocalName(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') handleSaveName(); }}
                      className="settings-input flex-1"
                      placeholder="Your name"
                    />
                    <button
                      onClick={handleSaveName}
                      className="px-3 py-2 rounded-lg bg-brand hover:bg-brand-light text-white text-xs font-semibold flex items-center gap-1 transition-colors"
                    >
                      <Check size={14} /> Save
                    </button>
                  </div>
                </div>
              </section>

              {/* Connection */}
              <section className="settings-section">
                <h3 className="settings-section-title"><Key size={14} /> Connection</h3>
                <div className="settings-field">
                  <label className="settings-label">API Endpoint</label>
                  <div className="settings-value">{apiBase}</div>
                </div>
                <div className="settings-field">
                  <label className="settings-label">Status</label>
                  <div className="settings-value">
                    <span className="settings-status-dot" /> Connected
                  </div>
                </div>
              </section>

              {/* About */}
              <section className="settings-section">
                <h3 className="settings-section-title"><Info size={14} /> About</h3>
                <p className="settings-about">Mitra v5.0.0 — Universal AI Companion</p>
                <p className="settings-about-sub">11 capabilities · Email · Calendar · WhatsApp · Tasks · Reminders</p>
              </section>
            </div>

            {/* Footer */}
            <div className="settings-footer">
              <button onClick={onClose} className="settings-btn-cancel">Cancel</button>
              <button onClick={handleSaveName} className="settings-btn-save">Save Changes</button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};

export default SettingsModal;
