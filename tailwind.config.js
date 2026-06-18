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
        green: {
          dark: '#408048',
          darker: '#2e5f34',
          darkest: '#07330d',
        },
        purple: {
          dark: '#4d1445',
          darker: '#2c0527',
          darkest: '#23021f',
        },
      },
      fontFamily: {
        sans: ['Helvetica', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
