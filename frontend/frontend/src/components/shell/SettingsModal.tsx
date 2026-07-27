// components/shell/SettingsModal.tsx — Settings with theme toggle
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Sun, Moon, Monitor, User, Key, Palette, Info } from 'lucide-react';
import { useCompanionStore } from '../../store/companion.store';

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

  // Apply theme
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
    setUserName(localName || 'there');
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            className="settings-backdrop"
            onClick={onClose}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="settings-modal"
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
                    { value: 'light', icon: <Sun size={16} />, label: 'Light' },
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
                  <input
                    type="text" value={localName}
                    onChange={e => setLocalName(e.target.value)}
                    className="settings-input"
                    placeholder="Your name"
                  />
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
              <button onClick={handleSaveName} className="settings-btn-save">Save</button>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default SettingsModal;
