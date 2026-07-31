// components/shell/AuthModal.tsx — Impressive Login & Sign Up Modal for MITRA
import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, User, Mail, Lock, Sparkles, LogIn, UserPlus, ArrowRight, Loader2, ShieldCheck } from 'lucide-react';
import { useCompanionStore } from '../../store/companion.store';
import { CompanionService } from '../../services/companion.service';
import { showToast } from './Toast';

interface Props {
  open: boolean;
  onClose: () => void;
}

const AuthModal: React.FC<Props> = ({ open, onClose }) => {
  const { setAuth, isAuthenticated, userName, userEmail, logoutUser } = useCompanionStore();
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  
  // Form states
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg('');

    if (!email.trim() || !password.trim()) {
      setErrorMsg('Please enter both email and password.');
      return;
    }

    if (mode === 'signup' && !name.trim()) {
      setErrorMsg('Please enter your full name.');
      return;
    }

    setLoading(true);
    try {
      if (mode === 'signup') {
        const data = await CompanionService.signup(name.trim(), email.trim(), password);
        setAuth(data.user, data.token);
        showToast('success', 'Account Created!', `Welcome to Mitra, ${data.user.name}`);
      } else {
        const data = await CompanionService.login(email.trim(), password);
        setAuth(data.user, data.token);
        showToast('success', 'Welcome Back!', `Logged in as ${data.user.name}`);
      }
      onClose();
    } catch (err: any) {
      console.warn('Authentication error:', err);
      const msg = err?.message || 'Authentication failed. Please check your credentials.';
      setErrorMsg(msg);
      showToast('error', 'Auth Error', msg);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await CompanionService.logout();
    } catch {}
    logoutUser();
    showToast('info', 'Logged Out', 'Switched back to Guest session.');
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="settings-backdrop"
            onClick={onClose}
          />

          {/* Modal Container */}
          <motion.div
            initial={{ opacity: 0, scale: 0.94, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.94, y: 20 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            className="fixed inset-0 m-auto max-w-md h-fit z-[201] p-5 sm:p-6 bg-surface-elevated border border-border-subtle rounded-2xl shadow-2xl overflow-hidden flex flex-col gap-5 text-text-primary"
            style={{ width: '92vw', maxHeight: '90vh' }}
          >
            {/* Header Accent Bar */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-accent-primary via-indigo-500 to-purple-500" />

            {/* Top Row: Brand & Close */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-accent-primary to-purple-600 flex items-center justify-center text-white shadow-md shadow-accent-primary/20">
                  <Sparkles size={18} />
                </div>
                <div>
                  <h2 className="text-lg font-bold tracking-tight">Mitra Account</h2>
                  <p className="text-xs text-text-secondary">Universal AI Companion</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-overlay transition-colors"
                aria-label="Close"
              >
                <X size={18} />
              </button>
            </div>

            {/* Authenticated State view */}
            {isAuthenticated ? (
              <div className="flex flex-col gap-4 py-2">
                <div className="p-4 rounded-xl bg-surface-overlay border border-border-subtle flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-accent-primary/10 border border-accent-primary/30 flex items-center justify-center text-accent-primary font-bold text-lg">
                    {userName ? userName.charAt(0).toUpperCase() : 'U'}
                  </div>
                  <div className="flex-1 overflow-hidden">
                    <div className="flex items-center gap-1.5 font-semibold text-sm text-text-primary">
                      <span>{userName}</span>
                      <ShieldCheck size={14} className="text-emerald-400" />
                    </div>
                    <p className="text-xs text-text-secondary truncate">{userEmail || 'Active User'}</p>
                  </div>
                </div>

                <p className="text-xs text-text-secondary">
                  Your companion memory, workflows, calendar, and history are synchronized to your account.
                </p>

                <button
                  onClick={handleLogout}
                  className="w-full py-2.5 px-4 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/20 text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
                >
                  <LogIn size={15} className="rotate-180" />
                  <span>Sign Out of Account</span>
                </button>
              </div>
            ) : (
              /* Tabbed Auth Form */
              <div className="flex flex-col gap-4">
                {/* Tabs */}
                <div className="grid grid-cols-2 p-1 rounded-xl bg-surface-overlay border border-border-subtle text-xs font-semibold">
                  <button
                    type="button"
                    onClick={() => { setMode('login'); setErrorMsg(''); }}
                    className={`py-2 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                      mode === 'login'
                        ? 'bg-surface-raised text-text-primary shadow-sm'
                        : 'text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    <LogIn size={14} />
                    <span>Log In</span>
                  </button>
                  <button
                    type="button"
                    onClick={() => { setMode('signup'); setErrorMsg(''); }}
                    className={`py-2 rounded-lg flex items-center justify-center gap-1.5 transition-all ${
                      mode === 'signup'
                        ? 'bg-surface-raised text-text-primary shadow-sm'
                        : 'text-text-secondary hover:text-text-primary'
                    }`}
                  >
                    <UserPlus size={14} />
                    <span>Create Account</span>
                  </button>
                </div>

                {/* Inline Error */}
                {errorMsg && (
                  <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-xs font-medium">
                    {errorMsg}
                  </div>
                )}

                <form onSubmit={handleSubmit} className="flex flex-col gap-3">
                  {/* Name field (signup mode) */}
                  {mode === 'signup' && (
                    <div className="flex flex-col gap-1">
                      <label className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                        Full Name
                      </label>
                      <div className="relative">
                        <User size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
                        <input
                          type="text"
                          required
                          value={name}
                          onChange={e => setName(e.target.value)}
                          placeholder="Raj Kumar"
                          className="w-full pl-9 pr-3 py-2 rounded-xl bg-surface-overlay border border-border-subtle text-xs text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-accent-primary transition-colors"
                        />
                      </div>
                    </div>
                  )}

                  {/* Email field */}
                  <div className="flex flex-col gap-1">
                    <label className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                      Email Address
                    </label>
                    <div className="relative">
                      <Mail size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
                      <input
                        type="email"
                        required
                        value={email}
                        onChange={e => setEmail(e.target.value)}
                        placeholder="raj@example.com"
                        className="w-full pl-9 pr-3 py-2 rounded-xl bg-surface-overlay border border-border-subtle text-xs text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-accent-primary transition-colors"
                      />
                    </div>
                  </div>

                  {/* Password field */}
                  <div className="flex flex-col gap-1">
                    <label className="text-[11px] font-medium text-text-secondary uppercase tracking-wider">
                      Password
                    </label>
                    <div className="relative">
                      <Lock size={15} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
                      <input
                        type="password"
                        required
                        minLength={6}
                        value={password}
                        onChange={e => setPassword(e.target.value)}
                        placeholder="••••••••"
                        className="w-full pl-9 pr-3 py-2 rounded-xl bg-surface-overlay border border-border-subtle text-xs text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-accent-primary transition-colors"
                      />
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={loading}
                    className="mt-2 w-full py-2.5 px-4 rounded-xl bg-gradient-to-r from-accent-primary to-purple-600 hover:from-accent-primary/90 hover:to-purple-600/90 text-white font-semibold text-xs flex items-center justify-center gap-2 shadow-lg shadow-accent-primary/20 transition-all disabled:opacity-50"
                  >
                    {loading ? (
                      <Loader2 size={16} className="animate-spin" />
                    ) : (
                      <>
                        <span>{mode === 'signup' ? 'Create Account' : 'Sign In'}</span>
                        <ArrowRight size={15} />
                      </>
                    )}
                  </button>
                </form>

                <div className="flex items-center justify-between text-[11px] text-text-secondary pt-1">
                  <span>Want to test without signing up?</span>
                  <button
                    type="button"
                    onClick={onClose}
                    className="text-accent-primary font-medium hover:underline"
                  >
                    Continue as Guest
                  </button>
                </div>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default AuthModal;
