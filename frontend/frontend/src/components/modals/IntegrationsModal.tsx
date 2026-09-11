import React, { useState, useEffect, useCallback } from 'react';
import { authApi } from '../../services/authApi';
import { getApiBase, getAuthHeaders } from '../../services/apiConfig';

interface IntegrationsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const IntegrationsModal: React.FC<IntegrationsModalProps> = ({ isOpen, onClose }) => {
  // Google Connection State (backed by backend GET /api/connections)
  const [googleConnected, setGoogleConnected] = useState(false);
  const [googleStatus, setGoogleStatus] = useState<'not_connected' | 'active' | 'needs_reauthorization'>('not_connected');
  const [googleAddress, setGoogleAddress] = useState('');
  const [isConnectingGoogle, setIsConnectingGoogle] = useState(false);
  const [isDisconnectingGoogle, setIsDisconnectingGoogle] = useState(false);

  // Microsoft Connection State (backed by backend GET /api/connections)
  const [microsoftConnected, setMicrosoftConnected] = useState(false);
  const [microsoftStatus, setMicrosoftStatus] = useState<'not_connected' | 'active' | 'needs_reauthorization'>('not_connected');
  const [microsoftAddress, setMicrosoftAddress] = useState('');
  const [isConnectingMicrosoft, setIsConnectingMicrosoft] = useState(false);
  const [isDisconnectingMicrosoft, setIsDisconnectingMicrosoft] = useState(false);

  // GitHub Connection State (backed by backend GET /api/connections)
  const [githubConnected, setGithubConnected] = useState(false);
  const [githubStatus, setGithubStatus] = useState<'not_connected' | 'active' | 'needs_reauthorization'>('not_connected');
  const [githubUsername, setGithubUsername] = useState('');
  const [isConnectingGithub, setIsConnectingGithub] = useState(false);
  const [isDisconnectingGithub, setIsDisconnectingGithub] = useState(false);

  // Apple Connection State (backed by backend GET /api/connections)
  const [appleConnected, setAppleConnected] = useState(false);
  const [appleStatus, setAppleStatus] = useState<'not_connected' | 'active' | 'needs_reauthorization'>('not_connected');
  const [appleEmail, setAppleEmail] = useState('');
  const [isConnectingApple, setIsConnectingApple] = useState(false);
  const [isDisconnectingApple, setIsDisconnectingApple] = useState(false);

  // App Password Fallback State (Legacy/Alternative)
  const [appPasswordMode, setAppPasswordMode] = useState(false);
  const [inputGmail, setInputGmail] = useState('');
  const [inputAppPassword, setInputAppPassword] = useState('');

  // WhatsApp State
  const [whatsappConnected, setWhatsappConnected] = useState(false);
  const [whatsappNumber, setWhatsappNumber] = useState('');
  const [showOtpModal, setShowOtpModal] = useState(false);
  const [otpCode, setOtpCode] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);

  // Global Feedback Messages
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const API_BASE = getApiBase();

  const fetchConnections = useCallback(async () => {
    try {
      // 1. Fetch OAuth connected accounts metadata from backend
      const data = await authApi.getConnections();

      // Check Google connection
      const googleConn = data.connections?.find(
        (c) => c.provider.toLowerCase() === 'google'
      );
      if (googleConn) {
        setGoogleConnected(true);
        setGoogleAddress(googleConn.email || 'Connected Google Account');
        if (googleConn.status === 'needs_reauthorization') {
          setGoogleStatus('needs_reauthorization');
        } else {
          setGoogleStatus('active');
        }
      } else {
        setGoogleConnected(false);
        setGoogleStatus('not_connected');
        setGoogleAddress('');
      }

      // Check Microsoft connection
      const msConn = data.connections?.find(
        (c) => c.provider.toLowerCase() === 'microsoft'
      );
      if (msConn) {
        setMicrosoftConnected(true);
        setMicrosoftAddress(msConn.email || 'Connected Microsoft Account');
        if (msConn.status === 'needs_reauthorization') {
          setMicrosoftStatus('needs_reauthorization');
        } else {
          setMicrosoftStatus('active');
        }
      } else {
        setMicrosoftConnected(false);
        setMicrosoftStatus('not_connected');
        setMicrosoftAddress('');
      }

      // Check GitHub connection
      const ghConn = data.connections?.find(
        (c) => c.provider.toLowerCase() === 'github'
      );
      if (ghConn) {
        setGithubConnected(true);
        setGithubUsername(ghConn.email || (ghConn as any).username || 'Connected GitHub Account');
        if (ghConn.status === 'needs_reauthorization') {
          setGithubStatus('needs_reauthorization');
        } else {
          setGithubStatus('active');
        }
      } else {
        setGithubConnected(false);
        setGithubStatus('not_connected');
        setGithubUsername('');
      }

      // Check Apple connection
      const appleConn = data.connections?.find(
        (c) => c.provider.toLowerCase() === 'apple'
      );
      if (appleConn) {
        setAppleConnected(true);
        setAppleEmail(appleConn.email || 'Apple Account');
        setAppleStatus(appleConn.status === 'needs_reauthorization' ? 'needs_reauthorization' : 'active');
      } else {
        setAppleConnected(false);
        setAppleStatus('not_connected');
        setAppleEmail('');
      }

      // 2. Fetch WhatsApp status
      try {
        const res = await fetch(`${API_BASE}/api/integrations`, { headers: getAuthHeaders() });
        if (res.ok) {
          const intData = await res.json();
          if (intData.whatsapp?.verified) {
            setWhatsappConnected(true);
            setWhatsappNumber(intData.whatsapp.phone || '');
          }
        }
      } catch (e) {
        console.warn("WhatsApp integration check warning:", e);
      }
    } catch (err) {
      console.warn("Failed fetching user connections:", err);
    }
  }, [API_BASE]);

  // Load real connections on modal open
  useEffect(() => {
    if (!isOpen) return;
    fetchConnections();
  }, [isOpen, fetchConnections]);

  if (!isOpen) return null;

  // 1. Real Google OAuth Flow Handler (Redirects to Google Consent)
  const handleConnectGoogle = async () => {
    setIsConnectingGoogle(true);
    setStatusMessage("Initiating PKCE-protected Google OAuth transaction...");
    setErrorMessage(null);
    try {
      const data = await authApi.startOAuth('google', 'connect');
      if (data.url) {
        window.location.href = data.url;
      } else {
        throw new Error("No authorization URL returned from OAuth start endpoint.");
      }
    } catch (err: any) {
      setIsConnectingGoogle(false);
      setErrorMessage(err.message || "Failed starting Google connection. Please try again.");
    }
  };

  // 2. Real Google OAuth Disconnect Handler
  const handleDisconnectGoogle = async () => {
    setIsDisconnectingGoogle(true);
    setStatusMessage("Disconnecting Google account...");
    setErrorMessage(null);
    try {
      await authApi.disconnectAccount('google');
      setGoogleConnected(false);
      setGoogleStatus('not_connected');
      setGoogleAddress('');
      setStatusMessage("Google account disconnected successfully.");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed disconnecting Google account.");
    } finally {
      setIsDisconnectingGoogle(false);
    }
  };

  // 3. Real Microsoft OAuth Flow Handler
  const handleConnectMicrosoft = async () => {
    setIsConnectingMicrosoft(true);
    setStatusMessage("Initiating PKCE-protected Microsoft OAuth transaction...");
    setErrorMessage(null);
    try {
      const data = await authApi.startOAuth('microsoft', 'connect');
      if (data.url) {
        window.location.href = data.url;
      } else {
        throw new Error("No authorization URL returned from Microsoft OAuth endpoint.");
      }
    } catch (err: any) {
      setIsConnectingMicrosoft(false);
      setErrorMessage(err.message || "Failed starting Microsoft connection. Please try again.");
    }
  };

  // 4. Real Microsoft OAuth Disconnect Handler
  const handleDisconnectMicrosoft = async () => {
    setIsDisconnectingMicrosoft(true);
    setStatusMessage("Disconnecting Microsoft account...");
    setErrorMessage(null);
    try {
      await authApi.disconnectAccount('microsoft');
      setMicrosoftConnected(false);
      setMicrosoftStatus('not_connected');
      setMicrosoftAddress('');
      setStatusMessage("Microsoft account disconnected successfully.");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed disconnecting Microsoft account.");
    } finally {
      setIsDisconnectingMicrosoft(false);
    }
  };

  // 5. Real GitHub OAuth Flow Handler
  const handleConnectGithub = async () => {
    setIsConnectingGithub(true);
    setStatusMessage("Initiating secure GitHub OAuth transaction...");
    setErrorMessage(null);
    try {
      const data = await authApi.startOAuth('github', 'connect');
      if (data.url) {
        window.location.href = data.url;
      } else {
        throw new Error("No authorization URL returned from GitHub OAuth endpoint.");
      }
    } catch (err: any) {
      setIsConnectingGithub(false);
      setErrorMessage(err.message || "Failed starting GitHub connection. Please try again.");
    }
  };

  // 6. Real GitHub OAuth Disconnect Handler
  const handleDisconnectGithub = async () => {
    setIsDisconnectingGithub(true);
    setStatusMessage("Disconnecting GitHub account...");
    setErrorMessage(null);
    try {
      await authApi.disconnectAccount('github');
      setGithubConnected(false);
      setGithubStatus('not_connected');
      setGithubUsername('');
      setStatusMessage("GitHub account disconnected successfully.");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed disconnecting GitHub account.");
    } finally {
      setIsDisconnectingGithub(false);
    }
  };

  // 7. Real Apple Sign-In Connect & Disconnect Handlers
  const handleConnectApple = async () => {
    setIsConnectingApple(true);
    setStatusMessage("Redirecting to Apple Sign-In authorization...");
    setErrorMessage(null);
    try {
      const data = await authApi.startOAuth('apple', 'login');
      if (data?.url) {
        window.location.href = data.url;
      } else {
        setErrorMessage("Apple Sign-In is not configured on this server. Please configure APPLE_CLIENT_ID in backend .env.");
      }
    } catch (err: any) {
      setErrorMessage(err.message || "Apple Sign-In is not configured on this server. Please configure APPLE_CLIENT_ID in backend .env.");
    } finally {
      setIsConnectingApple(false);
    }
  };

  const handleDisconnectApple = async () => {
    setIsDisconnectingApple(true);
    setStatusMessage("Disconnecting Apple account...");
    setErrorMessage(null);
    try {
      await authApi.disconnectAccount('apple');
      setAppleConnected(false);
      setAppleStatus('not_connected');
      setAppleEmail('');
      setStatusMessage("Apple account disconnected successfully.");
    } catch (err: any) {
      setErrorMessage(err.message || "Failed disconnecting Apple account.");
    } finally {
      setIsDisconnectingApple(false);
    }
  };

  // 5. Fallback App Password Handler
  const handleSaveGmailAppPassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputGmail || !inputAppPassword) return;
    setIsVerifying(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/integrations/gmail`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          email: inputGmail,
          app_password: inputAppPassword,
        })
      });
      const data = await res.json();
      if (res.ok && data.status === 'success') {
        setGoogleConnected(true);
        setGoogleStatus('active');
        setGoogleAddress(inputGmail);
        setAppPasswordMode(false);
        setStatusMessage(`Gmail account ${inputGmail} connected (AES-256 encrypted App Password).`);
      } else {
        setErrorMessage(data.detail || data.message || "Failed saving Gmail App Password.");
      }
    } catch (err: any) {
      setErrorMessage("Network error connecting Gmail account.");
    } finally {
      setIsVerifying(false);
    }
  };

  // 6. WhatsApp OTP Dispatch
  const handleSendWhatsappOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!whatsappNumber) return;
    setIsVerifying(true);
    setErrorMessage(null);
    setStatusMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/integrations/whatsapp/send-otp`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ phone: whatsappNumber })
      });
      const data = await res.json();
      if (res.ok && (data.status === 'success' || data.otp_sent)) {
        setShowOtpModal(true);
        setStatusMessage(`OTP dispatched to ${whatsappNumber}. Enter 6-digit code to verify.`);
      } else {
        setErrorMessage(data.detail || data.message || "Failed sending OTP to WhatsApp.");
      }
    } catch (err: any) {
      setErrorMessage("Network error sending WhatsApp OTP.");
    } finally {
      setIsVerifying(false);
    }
  };

  // 7. WhatsApp OTP Verification
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otpCode.length !== 6) return;
    setIsVerifying(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/integrations/whatsapp/verify-otp`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ phone: whatsappNumber, otp: otpCode })
      });
      const data = await res.json();
      if (res.ok && (data.status === 'success' || data.verified)) {
        setWhatsappConnected(true);
        setShowOtpModal(false);
        setOtpCode('');
        setStatusMessage(`WhatsApp number ${whatsappNumber} verified successfully!`);
      } else {
        setErrorMessage(data.detail || data.message || "Invalid OTP code. Please check and try again.");
      }
    } catch (err: any) {
      setErrorMessage("Network error verifying WhatsApp OTP.");
    } finally {
      setIsVerifying(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 z-50 animate-fade-in">
      <div className="bg-[#141414] border border-white/10 rounded-3xl p-6 md:p-8 max-w-xl w-full text-white shadow-2xl relative">
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-6 right-6 text-gray-400 hover:text-white transition-colors cursor-pointer"
        >
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Modal Title */}
        <div className="mb-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold uppercase tracking-wider mb-2">
            🔒 AES-256 Connections Vault
          </div>
          <h2 className="text-2xl font-bold text-gray-100">MITRA Service Connections</h2>
          <p className="text-sm text-gray-400 mt-1">
            Connect your personal accounts to enable automated email sending, calendar sync, and executive briefings.
          </p>
        </div>

        {/* Web Application Calendar Sync Notice */}
        <div className="mb-4 p-3 rounded-xl bg-white/5 border border-white/10 flex items-start gap-2.5 text-xs text-gray-300">
          <span className="text-blue-400 text-sm">ℹ️</span>
          <div>
            <strong className="text-white">Mobile Sync Notice:</strong> Web browsers cannot directly write to native mobile device calendars without an active Google Calendar or Microsoft Outlook connection.
          </div>
        </div>

        {statusMessage && (
          <div className="mb-4 p-4 rounded-xl bg-emerald-950/40 border border-emerald-500/30 text-emerald-300 text-xs flex items-center gap-2">
            <svg className="w-4 h-4 shrink-0 fill-current text-emerald-400" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>{statusMessage}</span>
          </div>
        )}

        {errorMessage && (
          <div className="mb-4 p-4 rounded-xl bg-red-950/40 border border-red-500/30 text-red-300 text-xs flex items-center gap-2">
            <span>⚠️ {errorMessage}</span>
          </div>
        )}

        <div className="space-y-6 max-h-[60vh] overflow-y-auto pr-1">
          {/* 1. GOOGLE INTEGRATION CARD */}
          <div className="p-5 rounded-2xl bg-[#1A1A1A] border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
                  <svg className="w-5 h-5" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-200">Google Account</h3>
                  <p className="text-xs text-gray-400">Gmail dispatch & Google Calendar sync</p>
                </div>
              </div>

              {googleStatus === 'active' ? (
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
                    Connected
                  </span>
                  <button
                    onClick={handleDisconnectGoogle}
                    disabled={isDisconnectingGoogle}
                    className="px-3 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium rounded-xl transition-colors cursor-pointer"
                  >
                    {isDisconnectingGoogle ? "Disconnecting..." : "Disconnect"}
                  </button>
                </div>
              ) : googleStatus === 'needs_reauthorization' ? (
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium">
                    Needs Reauthorization
                  </span>
                  <button
                    onClick={handleConnectGoogle}
                    disabled={isConnectingGoogle}
                    className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-black font-semibold text-xs rounded-xl transition-colors cursor-pointer"
                  >
                    {isConnectingGoogle ? "Redirecting..." : "Reconnect Google"}
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleConnectGoogle}
                  disabled={isConnectingGoogle}
                  className="px-4 py-2 bg-white text-black hover:bg-gray-200 font-semibold text-xs rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                >
                  {isConnectingGoogle ? "Connecting..." : "Connect Google"}
                </button>
              )}
            </div>

            {/* Google Account Metadata & Capabilities */}
            {googleConnected && (
              <div className="mt-3 pt-3 border-t border-white/5 space-y-2 text-xs">
                <div className="flex items-center justify-between text-gray-400">
                  <span>Account: <strong className="text-gray-200">{googleAddress}</strong></span>
                  <span className="text-emerald-400 font-medium">AES-256 Encrypted</span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300 text-[10px]">
                    ✉️ Gmail API (Send)
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300 text-[10px]">
                    📅 Google Calendar API
                  </span>
                </div>
              </div>
            )}

            {/* App Password Fallback Trigger */}
            {!googleConnected && (
              <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-gray-500">
                <span>OAuth unavailable or using app passwords?</span>
                <button
                  onClick={() => setAppPasswordMode(!appPasswordMode)}
                  className="text-blue-400 hover:underline cursor-pointer"
                >
                  {appPasswordMode ? "Hide App Password Form" : "Use App Password"}
                </button>
              </div>
            )}

            {appPasswordMode && !googleConnected && (
              <form onSubmit={handleSaveGmailAppPassword} className="mt-3 pt-3 border-t border-white/10 space-y-3">
                <input
                  type="email"
                  required
                  value={inputGmail}
                  onChange={(e) => setInputGmail(e.target.value)}
                  placeholder="your.email@gmail.com"
                  className="w-full px-4 py-2 rounded-xl bg-[#242424] text-white text-xs border border-white/10 focus:outline-none"
                />
                <input
                  type="password"
                  required
                  value={inputAppPassword}
                  onChange={(e) => setInputAppPassword(e.target.value)}
                  placeholder="Gmail 16-character App Password"
                  className="w-full px-4 py-2 rounded-xl bg-[#242424] text-white text-xs border border-white/10 focus:outline-none"
                />
                <button
                  type="submit"
                  disabled={isVerifying}
                  className="w-full py-2 bg-emerald-500 hover:bg-emerald-600 text-black font-bold text-xs rounded-xl transition-colors"
                >
                  {isVerifying ? "Encrypting & Connecting..." : "Save Gmail App Password"}
                </button>
              </form>
            )}
          </div>

          {/* 2. MICROSOFT INTEGRATION CARD */}
          <div className="p-5 rounded-2xl bg-[#1A1A1A] border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
                  <div className="w-5 h-5 grid grid-cols-2 gap-0.5">
                    <div className="bg-[#F25022] rounded-xs" />
                    <div className="bg-[#7FBA00] rounded-xs" />
                    <div className="bg-[#00A4EF] rounded-xs" />
                    <div className="bg-[#FFB900] rounded-xs" />
                  </div>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-200">Microsoft Account</h3>
                  <p className="text-xs text-gray-400">Outlook mail dispatch & Microsoft Calendar sync</p>
                </div>
              </div>

              {microsoftStatus === 'active' ? (
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
                    Connected
                  </span>
                  <button
                    onClick={handleDisconnectMicrosoft}
                    disabled={isDisconnectingMicrosoft}
                    className="px-3 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium rounded-xl transition-colors cursor-pointer"
                  >
                    {isDisconnectingMicrosoft ? "Disconnecting..." : "Disconnect"}
                  </button>
                </div>
              ) : microsoftStatus === 'needs_reauthorization' ? (
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium">
                    Needs Reauthorization
                  </span>
                  <button
                    onClick={handleConnectMicrosoft}
                    disabled={isConnectingMicrosoft}
                    className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-black font-semibold text-xs rounded-xl transition-colors cursor-pointer"
                  >
                    {isConnectingMicrosoft ? "Redirecting..." : "Reconnect Microsoft"}
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleConnectMicrosoft}
                  disabled={isConnectingMicrosoft}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white font-semibold text-xs rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                >
                  {isConnectingMicrosoft ? "Connecting..." : "Connect Microsoft"}
                </button>
              )}
            </div>

            {/* Microsoft Account Metadata & Capabilities */}
            {microsoftConnected && (
              <div className="mt-3 pt-3 border-t border-white/5 space-y-2 text-xs">
                <div className="flex items-center justify-between text-gray-400">
                  <span>Account: <strong className="text-gray-200">{microsoftAddress}</strong></span>
                  <span className="text-emerald-400 font-medium">AES-256 Encrypted</span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300 text-[10px]">
                    ✉️ Outlook Graph API (Send)
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300 text-[10px]">
                    📅 Microsoft Calendar API
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* 3. GITHUB DEVELOPER INTEGRATION CARD */}
          <div className="p-5 rounded-2xl bg-[#1A1A1A] border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
                  <svg className="w-6 h-6 fill-current text-white" viewBox="0 0 24 24">
                    <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-200">GitHub Developer Account</h3>
                  <p className="text-xs text-gray-400">Repositories, GitHub Issues & Pull Requests API</p>
                </div>
              </div>

              {githubStatus === 'active' ? (
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
                    Connected
                  </span>
                  <button
                    onClick={handleDisconnectGithub}
                    disabled={isDisconnectingGithub}
                    className="px-3 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium rounded-xl transition-colors cursor-pointer"
                  >
                    {isDisconnectingGithub ? "Disconnecting..." : "Disconnect"}
                  </button>
                </div>
              ) : githubStatus === 'needs_reauthorization' ? (
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium">
                    Needs Reauthorization
                  </span>
                  <button
                    onClick={handleConnectGithub}
                    disabled={isConnectingGithub}
                    className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-black font-semibold text-xs rounded-xl transition-colors cursor-pointer"
                  >
                    {isConnectingGithub ? "Redirecting..." : "Reconnect GitHub"}
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleConnectGithub}
                  disabled={isConnectingGithub}
                  className="px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                >
                  {isConnectingGithub ? "Connecting..." : "Connect GitHub"}
                </button>
              )}
            </div>

            {/* GitHub Account Metadata & Capabilities */}
            {githubConnected && (
              <div className="mt-3 pt-3 border-t border-white/5 space-y-2 text-xs">
                <div className="flex items-center justify-between text-gray-400">
                  <span>Account: <strong className="text-gray-200">{githubUsername}</strong></span>
                  <span className="text-emerald-400 font-medium">AES-256 Encrypted</span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300 text-[10px]">
                    📦 Repositories API
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300 text-[10px]">
                    🐛 Issues API
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300 text-[10px]">
                    🔀 Pull Requests API
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* 3. APPLE SIGN-IN / IDENTITY CARD */}
          <div className="p-5 rounded-2xl bg-[#1A1A1A] border border-white/10">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/5 border border-white/10 flex items-center justify-center">
                  <svg className="w-5 h-5 fill-current text-white" viewBox="0 0 24 24">
                    <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.81-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M15.97 6.85c.66-.8 1.11-1.92.99-3.04-.96.04-2.12.64-2.8 1.44-.61.71-1.14 1.86-1 2.97 1.07.08 2.15-.57 2.81-1.37z" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-semibold text-gray-200">Apple Account</h3>
                  <p className="text-xs text-gray-400">Sign in with Apple & Private Relay Email identity</p>
                </div>
              </div>

              {appleStatus === 'active' ? (
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-medium">
                    Connected
                  </span>
                  <button
                    onClick={handleDisconnectApple}
                    disabled={isDisconnectingApple}
                    className="px-3 py-1 bg-red-500/10 hover:bg-red-500/20 text-red-400 border border-red-500/30 text-xs font-medium rounded-xl transition-colors cursor-pointer"
                  >
                    {isDisconnectingApple ? "Disconnecting..." : "Disconnect"}
                  </button>
                </div>
              ) : appleStatus === 'needs_reauthorization' ? (
                <div className="flex items-center gap-2">
                  <span className="px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-400 text-xs font-medium">
                    Needs Reauthorization
                  </span>
                  <button
                    onClick={handleConnectApple}
                    disabled={isConnectingApple}
                    className="px-3 py-1 bg-amber-500 hover:bg-amber-600 text-black font-semibold text-xs rounded-xl transition-colors cursor-pointer"
                  >
                    {isConnectingApple ? "Redirecting..." : "Reconnect Apple"}
                  </button>
                </div>
              ) : (
                <button
                  onClick={handleConnectApple}
                  disabled={isConnectingApple}
                  className="px-4 py-2 bg-white text-black hover:bg-gray-200 font-semibold text-xs rounded-xl transition-colors cursor-pointer disabled:opacity-50"
                >
                  {isConnectingApple ? "Connecting..." : "Connect Apple"}
                </button>
              )}
            </div>

            {/* Apple Account Metadata & Capabilities */}
            {appleConnected && (
              <div className="mt-3 pt-3 border-t border-white/5 space-y-2 text-xs">
                <div className="flex items-center justify-between text-gray-400">
                  <span>Identity: <strong className="text-gray-200">{appleEmail}</strong></span>
                  <span className="text-emerald-400 font-medium">ES256 Verified</span>
                </div>
                <div className="flex flex-wrap gap-2 pt-1">
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300 text-[10px]">
                    🍎 Sign in with Apple
                  </span>
                  <span className="px-2 py-0.5 rounded bg-white/5 border border-white/10 text-gray-300 text-[10px]">
                    🛡️ Private Relay Support
                  </span>
                </div>
              </div>
            )}
          </div>

          {/* 4. WHATSAPP INTEGRATION CARD */}
          <div className="p-5 rounded-2xl bg-[#1A1A1A] border border-white/10">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                <svg className="w-6 h-6 fill-current" viewBox="0 0 24 24">
                  <path d="M.057 24l1.687-6.163c-1.041-1.804-1.588-3.849-1.587-5.946.003-6.556 5.338-11.891 11.893-11.891 3.181.001 6.167 1.24 8.413 3.488 2.245 2.248 3.481 5.236 3.48 8.414-.003 6.557-5.338 11.892-11.893 11.892-1.99-.001-3.951-.5-5.688-1.448l-6.305 1.654zm6.597-3.807c1.676.995 3.276 1.591 5.392 1.592 5.448 0 9.886-4.434 9.889-9.885.002-5.462-4.415-9.89-9.881-9.892-5.452 0-9.887 4.434-9.889 9.884-.001 2.225.651 3.891 1.746 5.634l-1.099 4.019 4.012-1.052z" />
                </svg>
              </div>
              <div>
                <h3 className="font-semibold text-gray-200">WhatsApp Messaging</h3>
                <p className="text-xs text-gray-400">Receive 8:45 AM morning briefings & price alerts</p>
              </div>
            </div>

            {whatsappConnected ? (
              <div className="flex items-center justify-between text-xs text-gray-400 pt-2 border-t border-white/5">
                <span>Phone: <strong className="text-gray-200">{whatsappNumber}</strong></span>
                <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-medium">
                  Verified & Active
                </span>
              </div>
            ) : (
              <form onSubmit={handleSendWhatsappOtp} className="flex gap-2">
                <input
                  type="tel"
                  value={whatsappNumber}
                  onChange={(e) => setWhatsappNumber(e.target.value)}
                  placeholder="+91 98765 43210"
                  className="flex-1 px-4 py-2.5 rounded-xl bg-[#242424] text-white placeholder-gray-500 text-xs border border-white/10 focus:outline-none focus:border-white/30"
                />
                <button
                  type="submit"
                  disabled={isVerifying || !whatsappNumber}
                  className="px-4 py-2.5 bg-emerald-500 hover:bg-emerald-600 active:bg-emerald-700 text-black font-semibold text-xs rounded-xl transition-colors disabled:opacity-50 cursor-pointer"
                >
                  {isVerifying ? "Sending OTP..." : "Send OTP"}
                </button>
              </form>
            )}
          </div>
        </div>

        {/* OTP Modal Overlay */}
        {showOtpModal && (
          <div className="absolute inset-0 bg-black/90 backdrop-blur-xl rounded-3xl p-6 flex flex-col justify-center items-center text-center z-10">
            <h3 className="text-lg font-bold mb-1">Verify WhatsApp Number</h3>
            <p className="text-xs text-gray-400 mb-4">Enter the 6-digit code sent to {whatsappNumber}</p>
            <form onSubmit={handleVerifyOtp} className="w-full max-w-xs space-y-4">
              <input
                type="text"
                maxLength={6}
                value={otpCode}
                onChange={(e) => setOtpCode(e.target.value)}
                placeholder="123456"
                className="w-full px-4 py-3 text-center text-xl tracking-widest font-mono rounded-xl bg-[#1E1E1E] text-white border border-white/20 focus:outline-none"
              />
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowOtpModal(false)}
                  className="flex-1 py-2.5 bg-gray-800 hover:bg-gray-700 text-gray-300 text-xs font-medium rounded-xl cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={otpCode.length !== 6 || isVerifying}
                  className="flex-1 py-2.5 bg-emerald-500 hover:bg-emerald-600 text-black text-xs font-bold rounded-xl disabled:opacity-50 cursor-pointer"
                >
                  {isVerifying ? "Verifying..." : "Confirm OTP"}
                </button>
              </div>
            </form>
          </div>
        )}
      </div>
    </div>
  );
};
