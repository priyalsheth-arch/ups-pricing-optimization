import type { Config } from 'tailwindcss'

const config: Config = {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        brand: {
          brown: '#4B1600',
          gold: '#FFB500',
          'gold-light': '#FFD166',
        },
      },
    },
  },
  plugins: [],
}

export default config
