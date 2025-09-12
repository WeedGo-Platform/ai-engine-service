#!/usr/bin/env node

/**
 * Script Generator for Multi-Tenant Development
 * Generates npm scripts and configuration files for multi-tenant setup
 * Follows Command Pattern for script generation
 */

import fs from 'fs';
import path from 'path';
import { viteConfigFactory } from '../vite.config.factory';

interface PackageJson {
  scripts?: Record<string, string>;
  [key: string]: any;
}

/**
 * Script generator for updating package.json with multi-tenant scripts
 */
class TenantScriptGenerator {
  private packageJsonPath: string;
  private packageJson: PackageJson;
  
  constructor(projectRoot: string = process.cwd()) {
    this.packageJsonPath = path.join(projectRoot, 'package.json');
    this.packageJson = this.loadPackageJson();
  }
  
  /**
   * Load package.json file
   */
  private loadPackageJson(): PackageJson {
    try {
      const content = fs.readFileSync(this.packageJsonPath, 'utf-8');
      return JSON.parse(content);
    } catch (error) {
      console.error('Failed to load package.json:', error);
      throw error;
    }
  }
  
  /**
   * Save updated package.json
   */
  private savePackageJson(): void {
    try {
      const content = JSON.stringify(this.packageJson, null, 2);
      fs.writeFileSync(this.packageJsonPath, content + '\n');
      console.log('✅ Updated package.json with tenant scripts');
    } catch (error) {
      console.error('Failed to save package.json:', error);
      throw error;
    }
  }
  
  /**
   * Generate and add tenant development scripts
   */
  generateTenantScripts(): void {
    console.log('🔧 Generating tenant scripts...');
    
    // Get generated scripts from factory
    const generatedScripts = viteConfigFactory.generateNpmScripts();
    
    // Preserve existing non-tenant scripts
    const existingScripts = this.packageJson.scripts || {};
    const preservedScripts: Record<string, string> = {};
    
    // Keep non-tenant scripts
    Object.entries(existingScripts).forEach(([key, value]) => {
      if (!key.includes(':') || key.startsWith('test') || key.startsWith('lint')) {
        preservedScripts[key] = value;
      }
    });
    
    // Merge scripts with generated ones
    this.packageJson.scripts = {
      ...preservedScripts,
      ...generatedScripts,
      
      // Add additional utility scripts
      'tenant:list': 'node -e "require(\'./scripts/list-tenants\')"',
      'tenant:generate-scripts': 'tsx scripts/generate-tenant-scripts.ts',
      'tenant:generate-configs': 'tsx scripts/generate-tenant-configs.ts',
      'tenant:setup': 'npm run tenant:generate-scripts && npm run tenant:generate-configs',
      
      // Development helpers
      'dev:default': 'VITE_PORT=5173 vite --port 5173',
      'dev:pot-palace': 'VITE_PORT=5174 vite --port 5174',
      'dev:dark-tech': 'VITE_PORT=5175 vite --port 5175',
      'dev:rasta-vibes': 'VITE_PORT=5176 vite --port 5176',
      'dev:weedgo': 'VITE_PORT=5177 vite --port 5177',
      'dev:vintage': 'VITE_PORT=5178 vite --port 5178',
      'dev:dirty': 'VITE_PORT=5179 vite --port 5179',
      'dev:metal': 'VITE_PORT=5180 vite --port 5180',
      
      // Parallel development (requires concurrently)
      'dev:all': 'concurrently "npm:dev:default" "npm:dev:pot-palace" "npm:dev:dark-tech" "npm:dev:rasta-vibes"',
      'dev:main': 'concurrently "npm:dev:default" "npm:dev:pot-palace" "npm:dev:dark-tech"',
      
      // Build scripts
      'build:default': 'VITE_PORT=5173 vite build --outDir dist-default',
      'build:pot-palace': 'VITE_PORT=5174 vite build --outDir dist-pot-palace',
      'build:dark-tech': 'VITE_PORT=5175 vite build --outDir dist-dark-tech',
      'build:rasta-vibes': 'VITE_PORT=5176 vite build --outDir dist-rasta-vibes',
      'build:weedgo': 'VITE_PORT=5177 vite build --outDir dist-weedgo',
      'build:vintage': 'VITE_PORT=5178 vite build --outDir dist-vintage',
      'build:dirty': 'VITE_PORT=5179 vite build --outDir dist-dirty',
      'build:metal': 'VITE_PORT=5180 vite build --outDir dist-metal',
      'build:all': 'npm run build:default && npm run build:pot-palace && npm run build:dark-tech && npm run build:rasta-vibes',
      
      // Preview scripts
      'preview:default': 'vite preview --port 5173 --outDir dist-default',
      'preview:pot-palace': 'vite preview --port 5174 --outDir dist-pot-palace',
      'preview:dark-tech': 'vite preview --port 5175 --outDir dist-dark-tech',
      'preview:rasta-vibes': 'vite preview --port 5176 --outDir dist-rasta-vibes',
      
      // Clean scripts
      'clean': 'rm -rf dist-*',
      'clean:all': 'rm -rf dist-* node_modules .vite'
    };
    
    this.savePackageJson();
  }
  
  /**
   * Generate VS Code launch configuration
   */
  generateVSCodeConfig(): void {
    console.log('🔧 Generating VS Code launch configuration...');
    
    const vscodePath = path.join(process.cwd(), '.vscode');
    if (!fs.existsSync(vscodePath)) {
      fs.mkdirSync(vscodePath, { recursive: true });
    }
    
    const launchConfig = viteConfigFactory.generateVSCodeLaunchConfig();
    const launchPath = path.join(vscodePath, 'launch.json');
    
    fs.writeFileSync(launchPath, JSON.stringify(launchConfig, null, 2) + '\n');
    console.log('✅ Generated .vscode/launch.json');
  }
  
  /**
   * Generate tenant configuration file
   */
  generateTenantConfigFile(): void {
    console.log('🔧 Generating tenant configuration file...');
    
    const tenants = viteConfigFactory.getAllTenants();
    const configPath = path.join(process.cwd(), 'tenant-config.json');
    
    const config = {
      tenants: tenants.map(t => ({
        tenantId: t.tenantId,
        tenantCode: t.tenantCode,
        templateId: t.templateId,
        port: t.port,
        subdomain: t.subdomain,
        development: {
          port: t.port,
          apiUrl: 'http://localhost:5024'
        },
        production: {
          subdomain: t.subdomain,
          domain: `${t.subdomain}.weedgo.com`,
          apiUrl: 'https://api.weedgo.com'
        }
      }))
    };
    
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2) + '\n');
    console.log('✅ Generated tenant-config.json');
  }
  
  /**
   * Check and install required dependencies
   */
  checkDependencies(): void {
    console.log('🔍 Checking dependencies...');
    
    const requiredDeps = ['concurrently'];
    const devDependencies = this.packageJson.devDependencies || {};
    const missingDeps = requiredDeps.filter(dep => !devDependencies[dep]);
    
    if (missingDeps.length > 0) {
      console.log('⚠️  Missing dependencies:', missingDeps.join(', '));
      console.log('Run: npm install --save-dev', missingDeps.join(' '));
    } else {
      console.log('✅ All required dependencies installed');
    }
  }
  
  /**
   * Generate all configurations
   */
  generateAll(): void {
    console.log('🚀 Setting up multi-tenant development environment...\n');
    
    this.generateTenantScripts();
    this.generateVSCodeConfig();
    this.generateTenantConfigFile();
    this.checkDependencies();
    
    console.log('\n✨ Multi-tenant setup complete!');
    console.log('\nAvailable commands:');
    console.log('  npm run dev:default     - Run default tenant (port 5173)');
    console.log('  npm run dev:pot-palace  - Run Pot Palace tenant (port 5174)');
    console.log('  npm run dev:dark-tech   - Run Dark Tech tenant (port 5175)');
    console.log('  npm run dev:main        - Run main tenants in parallel');
    console.log('  npm run dev:all         - Run all tenants in parallel');
    console.log('\nTenant management:');
    console.log('  npm run tenant:list     - List all configured tenants');
    console.log('  npm run tenant:setup    - Regenerate all configurations');
  }
}

// Execute if run directly
if (require.main === module) {
  const generator = new TenantScriptGenerator();
  generator.generateAll();
}

export { TenantScriptGenerator };