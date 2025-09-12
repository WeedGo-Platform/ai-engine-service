#!/usr/bin/env node

/**
 * List all configured tenants
 * Simple utility script to display tenant configurations
 */

const tenantConfigs = {
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

console.log('\n🏢 Configured Tenants:\n');
console.log('┌─────────┬─────────────────┬─────────────────┬──────────────────────────────────────┐');
console.log('│  Port   │   Tenant Code   │   Template ID   │              Tenant ID               │');
console.log('├─────────┼─────────────────┼─────────────────┼──────────────────────────────────────┤');

Object.values(tenantConfigs).forEach(config => {
  console.log(
    `│  ${config.port}  │ ${config.tenantCode.padEnd(15)} │ ${config.templateId.padEnd(15)} │ ${config.tenantId} │`
  );
});

console.log('└─────────┴─────────────────┴─────────────────┴──────────────────────────────────────┘');

console.log('\n📝 Development URLs:');
Object.values(tenantConfigs).forEach(config => {
  console.log(`  ${config.tenantCode}: http://localhost:${config.port}`);
});

console.log('\n🚀 Run Commands:');
Object.values(tenantConfigs).slice(0, 4).forEach(config => {
  console.log(`  npm run dev:${config.tenantCode}`);
});

console.log('\n💡 Tips:');
console.log('  • Run "npm run dev:main" to start the main tenants');
console.log('  • Run "npm run dev:all" to start all tenants');
console.log('  • Each tenant runs on its own port with isolated configuration');
console.log('  • Tenant context is automatically resolved from the port in development\n');

module.exports = tenantConfigs;