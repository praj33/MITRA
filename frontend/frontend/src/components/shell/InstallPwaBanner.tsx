// components/shell/InstallPwaBanner.tsx — Sleek Mobile & Desktop PWA Home-Screen Install Prompt
import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Download, X, Zap } from 'lucide-react';

export const InstallPwaBanner: React.FC = () => {
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);
  const [showBanner, setShowBanner] = useState(false);

  useEffect(() => {
    const handler = (e: any) => {
      e.preventDefault();
      setDeferredPrompt(e);
      // Check if user dismissed it recently
      const dismissed = localStorage.getItem('mitra_pwa_dismissed');
      if (!dismissed) {
        setShowBanner(true);
      }
    };

    window.addEventListener('beforeinstallprompt', handler);

    return () => {
      window.removeEventListener('beforeinstallprompt', handler);
    };
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setShowBanner(false);
    }
    setDeferredPrompt(null);
  };

  const handleDismiss = () => {
    setShowBanner(false);
    localStorage.setItem('mitra_pwa_dismissed', 'true');
  };

  if (!showBanner) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 50 }}
        className="fixed bottom-16 sm:bottom-6 left-3 right-3 sm:left-auto sm:right-6 z-40 max-w-sm bg-surface-elevated/95 border border-brand/40 shadow-2xl rounded-2xl p-3.5 flex items-center justify-between gap-3 backdrop-blur-xl select-none"
      >
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="w-9 h-9 rounded-xl bg-brand/20 border border-brand/40 flex items-center justify-center flex-shrink-0 text-brand-light">
            <Zap size={18} />
          </div>
          <div className="min-w-0">
            <h4 className="text-xs font-bold text-text-primary truncate">Install Mitra App</h4>
            <p className="text-2xs text-text-muted truncate">1-Tap home screen access & offline mode</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 flex-shrink-0">
          <button
            onClick={handleInstallClick}
            className="px-3 py-1.5 rounded-xl bg-brand hover:bg-brand-light text-white text-xs font-semibold flex items-center gap-1 shadow-md transition-all active:scale-95 cursor-pointer"
          >
            <Download size={14} /> Install
          </button>
          <button
            onClick={handleDismiss}
            className="p-1.5 rounded-lg text-text-muted hover:text-text-primary hover:bg-surface-overlay transition-colors"
          >
            <X size={14} />
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default InstallPwaBanner;
