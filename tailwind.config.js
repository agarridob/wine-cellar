/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './wine_cellar/templates/**/*.html',
    './wine_cellar/apps/**/templates/**/*.html',
    './wine_cellar/assets/**/*.{js,ts}',
    './wine_cellar/react/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        cellar: {
          wine: '#6e0f2a',
          'wine-dark': '#56091f',
          'wine-darkest': '#3a0716',
          'wine-tint': 'rgba(110,15,42,0.08)',
          bronze: '#8a5a2a',
          'bronze-dark': '#5a3a20',
          cream: '#f5ecd5',
          'cream-card': '#efe3c2',
          text: '#2a1812',
          muted: '#6b5440',
          border: '#ddc9a0',
          'border-light': '#efe3c2',
          danger: '#a02818',
          'danger-tint': '#f7e3df',
          warning: '#c8762e',
          gold: '#a8771a',
        },
      },
      fontFamily: {
        sans: ['Montserrat', 'Helvetica', 'Arial', 'sans-serif'],
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
