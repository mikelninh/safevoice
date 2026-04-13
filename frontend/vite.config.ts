import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      // Do NOT cache /api responses — reports, classifications, and PDFs must be fresh.
      // Also ensure the new service worker takes over immediately so users don't
      // see a stale JS bundle after a deploy.
      workbox: {
        skipWaiting: true,
        clientsClaim: true,
        navigateFallbackDenylist: [/^\/api\//, /^\/reports\//, /^\/health$/, /^\/orgs/],
        runtimeCaching: [
          {
            urlPattern: /^\/api\/.*/i,
            handler: 'NetworkOnly',
            options: { cacheName: 'api-no-cache' },
          },
        ],
      },
      manifest: {
        name: 'SafeVoice',
        short_name: 'SafeVoice',
        description: 'Document and report digital harassment',
        theme_color: '#6366f1',
        background_color: '#0f172a',
        display: 'standalone',
        start_url: '/',
        share_target: {
          action: '/share',
          method: 'POST',
          enctype: 'multipart/form-data',
          params: {
            title: 'title',
            text: 'text',
            url: 'url',
            files: [
              {
                name: 'screenshots',
                accept: ['image/*', '.png', '.jpg', '.jpeg', '.webp'],
              },
            ],
          },
        },
        categories: ['utilities', 'security'],
        lang: 'de-DE',
        screenshots: [],
        icons: [
          { src: '/icon-192.png', sizes: '192x192', type: 'image/png' },
          { src: '/icon-512.png', sizes: '512x512', type: 'image/png' },
        ],
      },
    }),
  ],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        rewrite: (path) => path.replace(/^\/api/, ''),
      },
    },
  },
})
