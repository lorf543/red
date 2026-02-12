module.exports = {
  content: [
    './templates/**/*.html',
    './**/templates/**/*.html',
    './static/**/*.js',
    './**/*.js',
  ],
  theme: {
    extend: {},
  },
  plugins: [
    require('daisyui'),
    require('@tailwindcss/typography'),
  ],
  daisyui: {
    themes: true,
  },
}
