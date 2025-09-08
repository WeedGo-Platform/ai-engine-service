/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eef9ff',
          100: '#d8f0ff',
          200: '#b9e6ff',
          300: '#89d8ff',
          400: '#52c0ff',
          500: '#2aa1ff',
          600: '#1381ff',
          700: '#0c6aeb',
          800: '#1154be',
          900: '#144995',
          950: '#112d5a',
        },
        cannabis: {
          50: '#f3faf3',
          100: '#e4f5e3',
          200: '#cbe9c8',
          300: '#a3d79d',
          400: '#73bd6a',
          500: '#4fa045',
          600: '#3d8335',
          700: '#31662b',
          800: '#295226',
          900: '#224320',
          950: '#0f240e',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
    },
  },
  plugins: [],
}