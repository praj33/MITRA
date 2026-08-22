import React, { useState, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';

interface LoginProps {
  onToggleForm: () => void;
}

interface FormErrors {
  email?: string;
  password?: string;
}

const Login: React.FC<LoginProps> = ({ onToggleForm }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<{ [key: string]: boolean }>({});
  const { login, isLoading, error: authError } = useAuth();

  // Validation functions
  const validateEmail = useCallback((value: string): string | undefined => {
    if (!value) return 'Email is required';
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(value)) return 'Please enter a valid email address';
    return undefined;
  }, []);

  const validatePassword = useCallback((value: string): string | undefined => {
    if (!value) return 'Password is required';
    if (value.length < 6) return 'Password must be at least 6 characters';
    return undefined;
  }, []);

  // Validate form on change
  React.useEffect(() => {
    const newErrors: FormErrors = {};
    if (touched.email) {
      newErrors.email = validateEmail(email);
    }
    if (touched.password) {
      newErrors.password = validatePassword(password);
    }
    setErrors(newErrors);
  }, [email, password, touched, validateEmail, validatePassword]);

  const handleBlur = (field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Validate all fields
    const emailError = validateEmail(email);
    const passwordError = validatePassword(password);
    
    setTouched({ email: true, password: true });
    setErrors({ email: emailError, password: passwordError });
    
    if (emailError || passwordError) {
      return;
    }

    try {
      await login(email, password);
    } catch {
      // Error is handled in context
    }
  };

  const isFormValid = !validateEmail(email) && !validatePassword(password);

  return (
    <div className="min-h-screen flex items-center justify-center bg-black px-4 py-8 text-white font-sans">
      <div className="w-full max-w-md text-center">
        {/* Header matching user reference */}
        <h1 className="text-4xl sm:text-5xl font-serif tracking-tight mb-3 text-gray-100">
          Question what's next
        </h1>
        <p className="text-lg text-gray-300 font-light mb-8">
          Your thinking partner for big ambitions
        </p>

        {/* Card Container */}
        <div className="bg-[#121212] rounded-3xl p-6 sm:p-8 border border-white/10 shadow-2xl backdrop-blur-2xl">
          {authError && (
            <div className="mb-6 p-4 bg-red-950/40 border border-red-800/50 rounded-xl text-left">
              <p className="text-sm text-red-400 font-sans">{authError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4 text-left" noValidate>
            <div>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => handleBlur('email')}
                disabled={isLoading}
                className={`
                  w-full px-5 py-3.5 rounded-xl bg-[#1E1E1E] text-white placeholder-gray-500 
                  border focus:outline-none transition-all text-base
                  disabled:opacity-50 disabled:cursor-not-allowed
                  ${errors.email && touched.email 
                    ? 'border-red-500/80 focus:border-red-500' 
                    : 'border-white/10 focus:border-white/30'
                  }
                `}
                placeholder="Enter your email"
                aria-invalid={!!errors.email && touched.email}
              />
              {errors.email && touched.email && (
                <p className="mt-1 text-xs text-red-400">
                  {errors.email}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading || !email}
              className="w-full py-3.5 px-4 bg-white hover:bg-gray-100 active:bg-gray-200 text-black font-semibold rounded-xl transition-all duration-200 text-base flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <span>Connecting...</span>
              ) : (
                'Continue with email'
              )}
            </button>
          </form>

          {/* OR Divider */}
          <div className="relative my-6 flex items-center justify-center">
            <div className="absolute inset-0 flex items-center">
              <div className="w-full border-t border-white/10"></div>
            </div>
            <span className="relative px-3 bg-[#121212] text-xs font-semibold tracking-wider text-gray-400 uppercase">
              OR
            </span>
          </div>

          {/* Social OAuth Buttons (Google & Apple) */}
          <div className="grid grid-cols-2 gap-3">
            {/* Google OAuth Button */}
            <button
              type="button"
              onClick={() => window.location.href = '/api/auth/google'}
              className="w-full py-3 px-4 bg-[#1E1E1E] hover:bg-[#282828] border border-white/10 rounded-xl flex items-center justify-center transition-colors group"
              title="Sign in with Google"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path
                  fill="#EA4335"
                  d="M12 5c1.6 0 3 .6 4.1 1.6l3.1-3.1C17.3 1.7 14.8 1 12 1 7.5 1 3.7 3.6 1.9 7.3l3.7 2.9C6.5 7.3 9 5 12 5z"
                />
                <path
                  fill="#4285F4"
                  d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.8-2.4 3.7l3.7 2.9c2.2-2 3.7-5 3.7-8.8z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.6 14.8c-.2-.7-.4-1.5-.4-2.3s.2-1.6.4-2.3L1.9 7.3C.7 9.7 0 10.8 0 12s.7 2.3 1.9 4.7l3.7-1.9z"
                />
                <path
                  fill="#34A853"
                  d="M12 23c3.2 0 6-1.1 8-3l-3.7-2.9c-1.1.7-2.5 1.2-4.3 1.2-3 0-5.5-2.3-6.4-5.2L1.9 16c1.8 3.7 5.6 7 10.1 7z"
                />
              </svg>
            </button>

            {/* Apple OAuth Button */}
            <button
              type="button"
              onClick={() => window.location.href = '/api/auth/apple'}
              className="w-full py-3 px-4 bg-[#1E1E1E] hover:bg-[#282828] border border-white/10 rounded-xl flex items-center justify-center transition-colors"
              title="Sign in with Apple"
            >
              <svg className="w-5 h-5 fill-current text-white" viewBox="0 0 170 170">
                <path d="M150.37 130.25c-2.45 5.66-5.35 10.87-8.71 15.66-4.58 6.53-8.33 11.05-11.22 13.56-4.48 4.12-9.28 6.23-14.42 6.35-3.69 0-8.14-1.05-13.32-3.18-5.19-2.12-9.97-3.17-14.34-3.17-4.58 0-9.49 1.05-14.75 3.17-5.26 2.13-9.5 3.24-12.74 3.35-4.34.13-9.16-1.9-14.48-6.1-3.32-2.64-7.27-7.25-11.87-13.84-6.84-9.82-12.18-20.91-16.02-33.27-3.84-12.36-5.76-24.36-5.76-36 0-14.39 3.65-26.24 10.96-35.54 7.31-9.3 16.48-14.07 27.51-14.3 4.87 0 10.15 1.25 15.84 3.75 5.69 2.5 9.77 3.75 12.24 3.75 2.12 0 6.26-1.25 12.43-3.75 6.17-2.5 11.27-3.69 15.3-3.56 10.5.54 19.34 4.54 26.51 12.02-9.46 5.76-14.07 13.91-13.84 24.45.24 8.24 3.4 15.42 9.5 21.55 6.1 6.13 13.43 9.49 22 10.08-2.12 6.34-4.87 12.6-8.25 18.78zm-30.82-106.9c0 6.64-2.45 13.16-7.35 19.56-5.83 7.4-12.98 11.66-21.46 12.78-.12-1.04-.19-2.02-.19-2.94 0-6.64 2.54-13.3 7.62-19.98 5.08-6.68 12.26-10.99 21.54-12.93.12 1.05.19 2.21.19 3.51z" />
              </svg>
            </button>
          </div>

          <div className="mt-8 pt-6 border-t border-white/10 text-center">
            <p className="text-sm text-gray-400 font-sans">
              Don't have an account?{' '}
              <button
                type="button"
                onClick={onToggleForm}
                className="text-white hover:underline font-medium transition-colors"
              >
                Sign up
              </button>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
