/**
 * Vite Configuration Factory for Multi-Tenant Development
 * Generates Vite configurations for different templates/tenants on different ports
 * Follows Factory Pattern and SOLID principles
 */

import { defineConfig, UserConfig, ProxyOptions } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import fs from 'fs';

/**
 * Configuration for a tenant instance
 */
interface TenantConfig {
  tenantId: string;
  tenantCode: string;
  templateId: string;
  port: number;
  subdomain?: string;
  apiUrl?: string;
  customEnv?: Record<string, string>;
}

/**
 * Port mapping configuration
 */
interface PortMapping {
  [port: number]: TenantConfig;
}

/**
 * Default tenant configurations for development
 */
const DEFAULT_TENANT_CONFIGS: PortMapping = {
  5173: {
    tenantId: '00000000-0000-0000-0000-000000000001',
    tenantCode: 'default',
    templateId: 'modern-minimal',
    port: 5173,
    subdomain: 'default'
  },
  5174: {
    tenantId: '00000000-0000-0000-0000-000000000002',
    tenantCode: 'pot-palace',
    templateId: 'pot-palace',
    port: 5174,
    subdomain: 'pot-palace'
  },
  5175: {
    tenantId: '00000000-0000-0000-0000-000000000003',
    tenantCode: 'dark-tech',
    templateId: 'dark-tech',
    port: 5175,
    subdomain: 'dark-tech'
  },
  5176: {
    tenantId: '00000000-0000-0000-0000-000000000004',
    tenantCode: 'rasta-vibes',
    templateId: 'rasta-vibes',
    port: 5176,
    subdomain: 'rasta'
  },
  5177: {
    tenantId: '00000000-0000-0000-0000-000000000005',
    tenantCode: 'weedgo',
    templateId: 'weedgo',
    port: 5177,
    subdomain: 'weedgo'
  },
  5178: {
    tenantId: '00000000-0000-0000-0000-000000000006',
    tenantCode: 'vintage',
    templateId: 'vintage',
    port: 5178,
    subdomain: 'vintage'
  },
  5179: {
    tenantId: '00000000-0000-0000-0000-000000000007',
    tenantCode: 'dirty',
    templateId: 'dirty',
    port: 5179,
    subdomain: 'dirty'
  },
  5180: {
    tenantId: '00000000-0000-0000-0000-000000000008',
    tenantCode: 'metal',
    templateId: 'metal',
    port: 5180,
    subdomain: 'metal'
  }
};

/**
 * Vite Configuration Factory
 * Creates Vite configurations for multi-tenant setup
 */
export class ViteConfigFactory {
  private readonly baseApiUrl: string;
  private readonly tenantConfigs: PortMapping;
  
  constructor(
    baseApiUrl: string = 'http://localhost:5024',
    tenantConfigs: PortMapping = DEFAULT_TENANT_CONFIGS
  ) {
    this.baseApiUrl = baseApiUrl;
    this.tenantConfigs = tenantConfigs;
  }
  
  /**
   * Generate proxy configuration for API calls
   * Automatically adds tenant headers based on port
   */
  private generateProxyConfig(tenantConfig: TenantConfig): Record<string, ProxyOptions> {
    const proxyTarget = tenantConfig.apiUrl || this.baseApiUrl;
    
    return {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          // Add tenant headers to all proxied requests
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            proxyReq.setHeader('X-Tenant-Id', tenantConfig.tenantId);
            proxyReq.setHeader('X-Tenant-Code', tenantConfig.tenantCode);
            proxyReq.setHeader('X-Template-Id', tenantConfig.templateId);
            
            // Add port-based tenant resolution header for backend
            proxyReq.setHeader('X-Dev-Port', tenantConfig.port.toString());
            
            // Log proxied requests in development
            if (process.env.NODE_ENV === 'development') {
              console.log(`[Proxy ${tenantConfig.port}] ${req.method} ${req.url} -> ${proxyTarget}`);
            }
          });
        }
      },
      '/v1': {
        target: proxyTarget,
        changeOrigin: true,
        secure: false,
        configure: (proxy, _options) => {
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            proxyReq.setHeader('X-Tenant-Id', tenantConfig.tenantId);
            proxyReq.setHeader('X-Tenant-Code', tenantConfig.tenantCode);
            proxyReq.setHeader('X-Template-Id', tenantConfig.templateId);
            proxyReq.setHeader('X-Dev-Port', tenantConfig.port.toString());
          });
        }
      }
    };
  }
  
  /**
   * Generate environment variables for tenant
   */
  private generateEnvVariables(tenantConfig: TenantConfig): Record<string, string> {
    return {
      VITE_TENANT_ID: tenantConfig.tenantId,
      VITE_TENANT_CODE: tenantConfig.tenantCode,
      VITE_TEMPLATE_ID: tenantConfig.templateId,
      VITE_PORT: tenantConfig.port.toString(),
      VITE_API_URL: tenantConfig.apiUrl || this.baseApiUrl,
      VITE_SUBDOMAIN: tenantConfig.subdomain || tenantConfig.tenantCode,
      ...tenantConfig.customEnv
    };
  }
  
  /**
   * Create Vite configuration for a specific port/tenant
   */
  createConfig(port: number): UserConfig {
    const tenantConfig = this.tenantConfigs[port];
    
    if (!tenantConfig) {
      throw new Error(`No tenant configuration found for port ${port}`);
    }
    
    // Set environment variables
    const envVars = this.generateEnvVariables(tenantConfig);
    Object.entries(envVars).forEach(([key, value]) => {
      process.env[key] = value;
    });
    
    return defineConfig({
      plugins: [react()],
      server: {
        port: tenantConfig.port,
        host: true,
        proxy: this.generateProxyConfig(tenantConfig)
      },
      define: {
        // Make tenant config available in the app
        '__TENANT_CONFIG__': JSON.stringify({
          tenantId: tenantConfig.tenantId,
          tenantCode: tenantConfig.tenantCode,
          templateId: tenantConfig.templateId,
          subdomain: tenantConfig.subdomain
        })
      },
      resolve: {
        alias: {
          '@': path.resolve(__dirname, './src'),
          '@templates': path.resolve(__dirname, './src/templates'),
          '@components': path.resolve(__dirname, './src/components'),
          '@services': path.resolve(__dirname, './src/services'),
          '@hooks': path.resolve(__dirname, './src/hooks'),
          '@contexts': path.resolve(__dirname, './src/contexts'),
          '@utils': path.resolve(__dirname, './src/utils'),
          '@types': path.resolve(__dirname, './src/types')
        }
      },
      build: {
        outDir: `dist-${tenantConfig.tenantCode}`,
        sourcemap: true,
        rollupOptions: {
          output: {
            manualChunks: {
              'react-vendor': ['react', 'react-dom', 'react-router-dom'],
              'ui-vendor': ['@headlessui/react', '@heroicons/react'],
              'utils': ['axios', 'date-fns', 'clsx']
            }
          }
        }
      }
    });
  }
  
  /**
   * Create configuration for a specific tenant by code
   */
  createConfigByTenantCode(tenantCode: string): UserConfig {
    const config = Object.values(this.tenantConfigs).find(
      c => c.tenantCode === tenantCode
    );
    
    if (!config) {
      throw new Error(`No configuration found for tenant code: ${tenantCode}`);
    }
    
    return this.createConfig(config.port);
  }
  
  /**
   * Create configuration for a specific template
   */
  createConfigByTemplateId(templateId: string): UserConfig {
    const config = Object.values(this.tenantConfigs).find(
      c => c.templateId === templateId
    );
    
    if (!config) {
      throw new Error(`No configuration found for template: ${templateId}`);
    }
    
    return this.createConfig(config.port);
  }
  
  /**
   * Get all configured tenants
   */
  getAllTenants(): TenantConfig[] {
    return Object.values(this.tenantConfigs);
  }
  
  /**
   * Load tenant configurations from external file
   */
  static loadFromFile(configPath: string): PortMapping {
    try {
      const configContent = fs.readFileSync(configPath, 'utf-8');
      return JSON.parse(configContent);
    } catch (error) {
      console.warn(`Failed to load tenant config from ${configPath}, using defaults`);
      return DEFAULT_TENANT_CONFIGS;
    }
  }
  
  /**
   * Generate launch configuration for VS Code
   */
  generateVSCodeLaunchConfig(): any {
    const configurations = Object.values(this.tenantConfigs).map(config => ({
      type: 'chrome',
      request: 'launch',
      name: `Launch ${config.tenantCode} (port ${config.port})`,
      url: `http://localhost:${config.port}`,
      webRoot: '${workspaceFolder}/src',
      env: this.generateEnvVariables(config)
    }));
    
    return {
      version: '0.2.0',
      configurations
    };
  }
  
  /**
   * Generate package.json scripts for all tenants
   */
  generateNpmScripts(): Record<string, string> {
    const scripts: Record<string, string> = {
      'dev': 'vite',
      'build': 'tsc && vite build',
      'preview': 'vite preview'
    };
    
    // Add individual tenant scripts
    Object.values(this.tenantConfigs).forEach(config => {
      scripts[`dev:${config.tenantCode}`] = `VITE_PORT=${config.port} vite --port ${config.port}`;
      scripts[`build:${config.tenantCode}`] = `VITE_PORT=${config.port} vite build --outDir dist-${config.tenantCode}`;
      scripts[`preview:${config.tenantCode}`] = `vite preview --port ${config.port} --outDir dist-${config.tenantCode}`;
    });
    
    // Add convenience scripts
    scripts['dev:all'] = Object.values(this.tenantConfigs)
      .map(c => `npm run dev:${c.tenantCode}`)
      .join(' & ');
    
    scripts['build:all'] = Object.values(this.tenantConfigs)
      .map(c => `npm run build:${c.tenantCode}`)
      .join(' && ');
    
    return scripts;
  }
}

/**
 * Singleton instance factory
 */
export class ViteConfigManager {
  private static instance: ViteConfigFactory;
  
  static getInstance(
    baseApiUrl?: string,
    tenantConfigs?: PortMapping
  ): ViteConfigFactory {
    if (!ViteConfigManager.instance) {
      // Try to load from external config file
      const externalConfig = process.env.TENANT_CONFIG_PATH
        ? ViteConfigFactory.loadFromFile(process.env.TENANT_CONFIG_PATH)
        : tenantConfigs;
      
      ViteConfigManager.instance = new ViteConfigFactory(
        baseApiUrl || process.env.API_BASE_URL || 'http://localhost:5024',
        externalConfig || DEFAULT_TENANT_CONFIGS
      );
    }
    return ViteConfigManager.instance;
  }
}

// Export default factory instance
export const viteConfigFactory = ViteConfigManager.getInstance();

// Export helper function for direct use in vite.config.ts
export function createTenantConfig(port?: number): UserConfig {
  const targetPort = port || parseInt(process.env.VITE_PORT || '5173');
  return viteConfigFactory.createConfig(targetPort);
}