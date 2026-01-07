/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/hn_herald/templates/**/*.html",
  ],
  darkMode: 'media', // Respects system preference
  theme: {
    extend: {
      colors: {
        // HackerNews orange theme
        primary: {
          50: '#fff7ed',
          100: '#ffedd5',
          200: '#fed7aa',
          300: '#fdba74',
          400: '#fb923c',
          500: '#ff6600', // HN orange
          600: '#ea580c',
          700: '#c2410c',
          800: '#9a3412',
          900: '#7c2d12',
          950: '#431407',
        },
        // HN beige/cream background
        hn: {
          bg: '#f6f6ef',
          border: '#ff6600',
          text: '#828282',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
          950: '#052e16',
        },
        warning: {
          50: '#fefce8',
          100: '#fef9c3',
          200: '#fef08a',
          300: '#fde047',
          400: '#facc15',
          500: '#eab308',
          600: '#ca8a04',
          700: '#a16207',
          800: '#854d0e',
          900: '#713f12',
          950: '#422006',
        },
        error: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
          950: '#450a0a',
        },
      },
      // Mobile-first breakpoints (Tailwind defaults)
      screens: {
        'sm': '640px',  // Large phones (landscape)
        'md': '768px',  // Tablets
        'lg': '1024px', // Small laptops
        'xl': '1280px', // Desktops
        '2xl': '1536px', // Large screens
      },
      // Custom utilities for touch targets
      minHeight: {
        '12': '48px', // Minimum touch target height
      },
      minWidth: {
        '12': '48px', // Minimum touch target width
      },
    },
  },
  plugins: [
    require('daisyui').default,
  ],
  daisyui: {
    themes: [
      {
        hackernews: {
          "primary": "#ff6600",
          "primary-content": "#ffffff",
          "secondary": "#828282",
          "accent": "#ff6600",
          "neutral": "#000000",
          "base-100": "#f6f6ef",
          "base-200": "#e8e8df",
          "base-300": "#d4d4cc",
          "info": "#3b82f6",
          "success": "#22c55e",
          "warning": "#eab308",
          "error": "#ef4444",
        },
      },
    ],
    darkTheme: "dark",
    base: true,
    styled: true,
    utils: true,
  },
}
