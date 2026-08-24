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
            <div className="absolute top-0 left-0 right-0 h-1 bg-brand" />

            {/* Top Row: Brand & Close */}
            <div className="flex items-center justify-between pt-1">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-xl bg-brand flex items-center justify-center text-white shadow-md shadow-brand/20">
                  <Sparkles size={18} />
                </div>
                <div>
                  <h2 className="text-lg font-bold tracking-tight text-text-primary">Mitra Account</h2>
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
                  <div className="w-12 h-12 rounded-full bg-brand/10 border border-brand/30 flex items-center justify-center text-brand font-bold text-lg">
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
                  className="w-full py-2.5 px-4 rounded-xl bg-red-500/10 hover:bg-red-500/20 text-red-500 border border-red-500/20 text-xs font-semibold flex items-center justify-center gap-2 transition-colors"
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
                  <div className="p-2.5 rounded-lg bg-red-500/10 border border-red-500/20 text-red-500 text-xs font-medium">
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
                          className="w-full pl-9 pr-3 py-2 rounded-xl bg-surface-overlay border border-border-subtle text-xs text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-brand transition-colors"
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
                        className="w-full pl-9 pr-3 py-2 rounded-xl bg-surface-overlay border border-border-subtle text-xs text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-brand transition-colors"
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
                        className="w-full pl-9 pr-3 py-2 rounded-xl bg-surface-overlay border border-border-subtle text-xs text-text-primary placeholder:text-text-secondary/50 focus:outline-none focus:border-brand transition-colors"
                      />
                    </div>
                  </div>

                  {/* Submit Button */}
                  <button
                    type="submit"
                    disabled={loading}
                    className="mt-2 w-full py-3 px-4 rounded-xl bg-brand hover:bg-brand-light text-white font-bold text-xs flex items-center justify-center gap-2 shadow-lg shadow-brand/20 transition-all disabled:opacity-50 cursor-pointer"
                    style={{ backgroundColor: 'var(--brand)', color: '#ffffff' }}
                  >
                    {loading ? (
                      <Loader2 size={16} className="animate-spin text-white" />
                    ) : (
                      <>
                        <span className="text-white font-bold text-xs tracking-wide">{mode === 'signup' ? 'Create Account' : 'Sign In'}</span>
                        <ArrowRight size={15} className="text-white" />
                      </>
                    )}
                  </button>
                </form>

                {/* OR Divider */}
                <div className="relative my-2 flex items-center justify-center">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-border-subtle"></div>
                  </div>
                  <span className="relative px-3 bg-surface-elevated text-[10px] font-bold tracking-wider text-text-secondary uppercase">
                    OR
                  </span>
                </div>

                {/* Social OAuth Buttons */}
                <div className="grid grid-cols-2 gap-2.5">
                  <button
                    type="button"
                    onClick={() => window.location.href = '/api/auth/google'}
                    className="w-full py-2.5 px-3 bg-surface-overlay hover:bg-surface-raised border border-border-subtle rounded-xl flex items-center justify-center gap-2 transition-all text-xs font-semibold text-text-primary cursor-pointer"
                    title="Sign in with Google"
                  >
                    <svg className="w-4 h-4" viewBox="0 0 24 24">
                      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                    </svg>
                    <span>Google</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => window.location.href = '/api/auth/apple'}
                    className="w-full py-2.5 px-3 bg-surface-overlay hover:bg-surface-raised border border-border-subtle rounded-xl flex items-center justify-center gap-2 transition-all text-xs font-semibold text-text-primary cursor-pointer"
                    title="Sign in with Apple"
                  >
                    <svg className="w-4 h-4 fill-current text-white" viewBox="0 0 170 170">
                      <path d="M150.37 130.25c-2.45 5.66-5.35 10.87-8.71 15.66-4.58 6.53-8.33 11.05-11.22 13.56-4.48 4.12-9.28 6.23-14.42 6.35-3.69 0-8.14-1.05-13.32-3.18-5.19-2.12-9.97-3.17-14.34-3.17-4.58 0-9.49 1.05-14.75 3.17-5.26 2.13-9.5 3.24-12.74 3.35-4.34.13-9.16-1.9-14.48-6.1-3.32-2.64-7.27-7.25-11.87-13.84-6.84-9.82-12.18-20.91-16.02-33.27-3.84-12.36-5.76-24.36-5.76-36 0-14.39 3.65-26.24 10.96-35.54 7.31-9.3 16.48-14.07 27.51-14.3 4.87 0 10.15 1.25 15.84 3.75 5.69 2.5 9.77 3.75 12.24 3.75 2.12 0 6.26-1.25 12.43-3.75 6.17-2.5 11.27-3.69 15.3-3.56 10.5.54 19.34 4.54 26.51 12.02-9.46 5.76-14.07 13.91-13.84 24.45.24 8.24 3.4 15.42 9.5 21.55 6.1 6.13 13.43 9.49 22 10.08-2.12 6.34-4.87 12.6-8.25 18.78zm-30.82-106.9c0 6.64-2.45 13.16-7.35 19.56-5.83 7.4-12.98 11.66-21.46 12.78-.12-1.04-.19-2.02-.19-2.94 0-6.64 2.54-13.3 7.62-19.98 5.08-6.68 12.26-10.99 21.54-12.93.12 1.05.19 2.21.19 3.51z" />
                    </svg>
                    <span>Apple</span>
                  </button>
                </div>

                <div className="flex items-center justify-between text-[11px] text-text-secondary pt-1">
                  <span>Want to test without signing up?</span>
                  <button
                    type="button"
                    onClick={onClose}
                    className="text-brand font-medium hover:underline"
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
