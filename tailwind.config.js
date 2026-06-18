/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './wine_cellar/templates/**/*.html',
    './wine_cellar/apps/**/templates/**/*.html',
    './wine_cellar/assets/**/*.{js,ts}',
    './wine_cellar/react/**/*.{ts,tsx}',
  ],
  corePlugins: {
    // Disable preflight while PureCSS is still in the bundle
    preflight: false,
  },
  theme: {
    extend: {
      colors: {
        cellar: {
          green: '#408048',
          'green-dark': '#2e5f34',
          'green-darkest': '#07330d',
          'green-tint': 'rgba(64,128,72,0.08)',
          purple: '#4d1445',
          'purple-dark': '#2c0527',
          bg: '#f6f5ef',
          text: '#333333',
          muted: '#525252',
          border: '#d0d0d0',
          'border-light': '#eeeeee',
          danger: '#bb0000',
          'danger-tint': '#fde8e8',
          warning: '#d47500',
          gold: '#d4a017',
        },
      },
      fontFamily: {
        sans: ['Helvetica', 'sans-serif'],
      },
      maxWidth: {
        content: '1140px',
      },
      boxShadow: {
        card: 'rgba(149,157,165,0.2) 0px 8px 24px',
      },
    },
  },
  plugins: [],
}
