import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Get port from environment or use default
const port = parseInt(process.env.VITE_PORT || '5173')

// Port to tenant mapping
const tenantMapping: Record<number, any> = {
  5173: { tenantId: '00000000-0000-0000-0000-000000000001', tenantCode: 'default', templateId: 'modern-minimal' },
  5174: { tenantId: '00000000-0000-0000-0000-000000000002', tenantCode: 'pot-palace', templateId: 'pot-palace' },
  5175: { tenantId: '00000000-0000-0000-0000-000000000003', tenantCode: 'dark-tech', templateId: 'dark-tech' },
  5176: { tenantId: '00000000-0000-0000-0000-000000000004', tenantCode: 'rasta-vibes', templateId: 'rasta-vibes' },
  5177: { tenantId: '00000000-0000-0000-0000-000000000005', tenantCode: 'weedgo', templateId: 'weedgo' },
  5178: { tenantId: '00000000-0000-0000-0000-000000000006', tenantCode: 'vintage', templateId: 'vintage' },
  5179: { tenantId: '00000000-0000-0000-0000-000000000007', tenantCode: 'dirty', templateId: 'dirty' },
  5180: { tenantId: '00000000-0000-0000-0000-000000000008', tenantCode: 'metal', templateId: 'metal' }
}

const tenantConfig = tenantMapping[port] || tenantMapping[5173]

export default defineConfig({
  plugins: [react()],
  server: {
    port: port,
    proxy: {
      '/api': {
        target: 'http://localhost:5024',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            // Add tenant headers to all API requests
            proxyReq.setHeader('X-Tenant-Id', tenantConfig.tenantId)
            proxyReq.setHeader('X-Tenant-Code', tenantConfig.tenantCode)
            proxyReq.setHeader('X-Template-Id', tenantConfig.templateId)
          })
        }
      },
      '/v1': {
        target: 'http://localhost:5024',
        changeOrigin: true,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            proxyReq.setHeader('X-Tenant-Id', tenantConfig.tenantId)
            proxyReq.setHeader('X-Tenant-Code', tenantConfig.tenantCode)
            proxyReq.setHeader('X-Template-Id', tenantConfig.templateId)
          })
        }
      }
    }
  },
  define: {
    '__TENANT_CONFIG__': JSON.stringify(tenantConfig)
  }
})