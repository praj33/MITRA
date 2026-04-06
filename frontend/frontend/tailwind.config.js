/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // iOS Blue colors
        iosBlue: {
          50: '#E8F4FD',
          100: '#D0E9FB',
          200: '#A1D3F7',
          300: '#72BDF3',
          400: '#43A7EF',
          500: '#0A84FF', // iOS Primary Blue
          600: '#0870CC',
          700: '#065C99',
          800: '#044866',
          900: '#023433',
        },
        // iOS Gray colors
        iosGray: {
          50: '#F9F9F9',
          100: '#F2F2F7',
          200: '#E5E5EA',
          300: '#D1D1D6',
          400: '#C7C7CC',
          500: '#AEAEB2',
          600: '#8E8E93',
          700: '#636366',
          800: '#48484A',
          900: '#1C1C1E',
        },
        // iOS Green colors
        iosGreen: {
          50: '#E8F8F0',
          100: '#D1F0E1',
          200: '#A3E1C3',
          300: '#75D2A5',
          400: '#47C387',
          500: '#34C759', // iOS Green
          600: '#2CA84A',
          700: '#23893B',
          800: '#1B6A2C',
          900: '#124B1D',
        },
        primary: {
          50: '#E8F4FD',
          100: '#D0E9FB',
          200: '#A1D3F7',
          300: '#72BDF3',
          400: '#43A7EF',
          500: '#0A84FF', // iOS Blue
          600: '#0870CC',
          700: '#065C99',
          800: '#044866',
          900: '#023433',
        },
      },
      fontFamily: {
        'sf': ['-apple-system', 'BlinkMacSystemFont', '"SF Pro Display"', '"SF Pro Text"', 'system-ui', 'sans-serif'],
      },
      backdropBlur: {
        'xs': '2px',
      },
      boxShadow: {
        'ios': '0 1px 3px rgba(0, 0, 0, 0.12), 0 1px 2px rgba(0, 0, 0, 0.24)',
        'ios-lg': '0 10px 40px rgba(0, 0, 0, 0.15), 0 5px 10px rgba(0, 0, 0, 0.1)',
      },
      keyframes: {
        slideDown: {
          '0%': { transform: 'translateX(-50%) translateY(-100%)', opacity: '0' },
          '100%': { transform: 'translateX(-50%) translateY(0)', opacity: '1' },
        },
      },
      animation: {
        slideDown: 'slideDown 0.3s ease-out',
      },
    },
  },
  plugins: [],
}

