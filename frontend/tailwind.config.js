/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        vazir: ['Vazirmatn', 'Tahoma', 'sans-serif'],
      },
      colors: {
        primary: {
          50: '#eef4ff', 100: '#dce7fe', 200: '#c0d3fd', 300: '#94b6fb',
          400: '#618ef7', 500: '#3d67f2', 600: '#2747e6', 700: '#1f36d3',
          800: '#202fab', 900: '#1f2d87', 950: '#171e52',
        },
      },
    },
  },
  plugins: [],
};
