// frontend_b2b_marketplace/tailwind.config.js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'brand-cream': '#F5EEDD',
        'brand-mint': '#7AE2CF',
        'brand-deep-teal': '#077A7D',
        'brand-charcoal': '#06202B',
      },
      fontFamily: {
        // Example: If you want to set a default sans-serif font
        // sans: ['Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
};