/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['var(--font-inter)', 'system-ui', 'sans-serif'],
        serif: ['var(--font-playfair)', 'Georgia', 'serif'],
      },
      colors: {
        savannah: {
          sun: '#F59E0B',
          grass: '#10B981',
          earth: '#78350F',
          sky: '#0EA5E9',
          night: '#1E293B',
          cream: '#FEF3C7',
          gold: '#D97706',
        }
      }
    },
  },
  plugins: [],
}
