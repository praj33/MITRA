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
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-iosGray-100 to-white dark:from-black dark:to-iosGray-900 px-4 py-8">
      <div className="w-full max-w-md">
        <div className="backdrop-blur-xl bg-white/70 dark:bg-iosGray-800/70 rounded-3xl p-6 sm:p-8 shadow-ios-lg border border-white/20 dark:border-iosGray-700/30">
          <div className="text-center mb-8">
            <div className="inline-flex items-center justify-center w-16 h-16 sm:w-20 sm:h-20 rounded-2xl bg-iosBlue-500/10 mb-4">
              <svg
                className="w-8 h-8 sm:w-10 sm:h-10 text-iosBlue-500"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <h1 className="text-2xl sm:text-3xl font-semibold text-iosGray-900 dark:text-white mb-2 font-sf">
              Welcome Back
            </h1>
            <p className="text-iosGray-600 dark:text-iosGray-400 font-sf">
              Sign in to continue to Mitra
            </p>
          </div>

          {authError && (
            <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl animate-slideDown">
              <p className="text-sm text-red-600 dark:text-red-400 font-sf">{authError}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-iosGray-700 dark:text-iosGray-300 mb-2 font-sf">
                Email
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => handleBlur('email')}
                disabled={isLoading}
                className={`
                  w-full px-4 py-3 rounded-xl bg-white/50 dark:bg-iosGray-900/50 
                  border text-iosGray-900 dark:text-white placeholder-iosGray-400 
                  focus:outline-none focus:ring-2 focus:border-transparent transition-all font-sf
                  disabled:opacity-50 disabled:cursor-not-allowed
                  ${errors.email && touched.email 
                    ? 'border-red-500 focus:ring-red-500/50' 
                    : 'border-iosGray-200 dark:border-iosGray-700 focus:ring-iosBlue-500'
                  }
                `}
                placeholder="Enter your email"
                aria-invalid={!!errors.email && touched.email}
                aria-describedby={errors.email && touched.email ? 'email-error' : undefined}
              />
              {errors.email && touched.email && (
                <p id="email-error" className="mt-1.5 text-xs text-red-500 font-sf animate-slideDown">
                  {errors.email}
                </p>
              )}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-iosGray-700 dark:text-iosGray-300 mb-2 font-sf">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  onBlur={() => handleBlur('password')}
                  disabled={isLoading}
                  className={`
                    w-full px-4 py-3 pr-12 rounded-xl bg-white/50 dark:bg-iosGray-900/50 
                    border text-iosGray-900 dark:text-white placeholder-iosGray-400 
                    focus:outline-none focus:ring-2 focus:border-transparent transition-all font-sf
                    disabled:opacity-50 disabled:cursor-not-allowed
                    ${errors.password && touched.password 
                      ? 'border-red-500 focus:ring-red-500/50' 
                      : 'border-iosGray-200 dark:border-iosGray-700 focus:ring-iosBlue-500'
                    }
                  `}
                  placeholder="Enter your password"
                  aria-invalid={!!errors.password && touched.password}
                  aria-describedby={errors.password && touched.password ? 'password-error' : undefined}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1.5 text-iosGray-400 hover:text-iosGray-600 dark:hover:text-iosGray-300 transition-colors"
                  aria-label={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                  )}
                </button>
              </div>
              {errors.password && touched.password && (
                <p id="password-error" className="mt-1.5 text-xs text-red-500 font-sf animate-slideDown">
                  {errors.password}
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={isLoading || !isFormValid}
              className="w-full py-3.5 px-4 bg-iosBlue-500 hover:bg-iosBlue-600 active:bg-iosBlue-700 disabled:bg-iosGray-300 dark:disabled:bg-iosGray-700 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-all duration-200 shadow-ios-md hover:shadow-ios-lg font-sf flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span>Signing in...</span>
                </>
              ) : (
                'Sign In'
              )}
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-iosGray-200 dark:border-iosGray-700 text-center">
            <p className="text-sm text-iosGray-600 dark:text-iosGray-400 font-sf">
              Don't have an account?{' '}
              <button
                onClick={onToggleForm}
                className="text-iosBlue-500 hover:text-iosBlue-600 font-medium transition-colors"
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
