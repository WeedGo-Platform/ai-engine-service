#!/usr/bin/env node
import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const rootDir = join(__dirname, '..');

const templates = [
  { name: 'weedgo', port: 5173 },
  { name: 'pot-palace', port: 5174 },
  { name: 'modern-minimal', port: 5175 },
  { name: 'vintage', port: 5176 },
  { name: 'rasta-vibes', port: 5177 },
  { name: 'dark-tech', port: 5178 },
  { name: 'metal', port: 5179 },
  { name: 'dirty', port: 5180 }
];

const processes = [];
let shutdownInProgress = false;

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  dim: '\x1b[2m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m',
  white: '\x1b[37m'
};

function log(message, color = colors.white) {
  console.log(`${color}${message}${colors.reset}`);
}

function logTemplate(template, message, color = colors.white) {
  const prefix = `[${template.name}:${template.port}]`.padEnd(20);
  console.log(`${colors.dim}${prefix}${colors.reset} ${color}${message}${colors.reset}`);
}

// Clean shutdown handler
function shutdown() {
  if (shutdownInProgress) return;
  shutdownInProgress = true;
  
  log('\n🛑 Shutting down all template servers...', colors.yellow);
  
  processes.forEach(({ process, template }) => {
    if (process && !process.killed) {
      logTemplate(template, 'Stopping...', colors.yellow);
      process.kill('SIGTERM');
    }
  });
  
  setTimeout(() => {
    process.exit(0);
  }, 1000);
}

// Register shutdown handlers
process.on('SIGINT', shutdown);
process.on('SIGTERM', shutdown);
process.on('exit', shutdown);

async function startTemplate(template) {
  return new Promise((resolve, reject) => {
    const env = {
      ...process.env,
      VITE_TEMPLATE: template.name,
      PORT: template.port
    };
    
    logTemplate(template, 'Starting...', colors.cyan);
    
    const viteProcess = spawn('npm', ['run', 'dev', '--', '--port', template.port.toString()], {
      cwd: rootDir,
      env,
      stdio: ['inherit', 'pipe', 'pipe'],
      shell: true
    });
    
    let started = false;
    
    viteProcess.stdout.on('data', (data) => {
      const message = data.toString().trim();
      if (message.includes('ready in') || message.includes('Local:')) {
        if (!started) {
          started = true;
          logTemplate(template, `✓ Ready at http://localhost:${template.port}`, colors.green);
          resolve();
        }
      }
      // Show build errors
      if (message.includes('error') || message.includes('Error')) {
        logTemplate(template, message, colors.red);
      }
    });
    
    viteProcess.stderr.on('data', (data) => {
      const message = data.toString().trim();
      if (message) {
        logTemplate(template, `Error: ${message}`, colors.red);
      }
    });
    
    viteProcess.on('close', (code) => {
      if (code !== 0 && !shutdownInProgress) {
        logTemplate(template, `Process exited with code ${code}`, colors.red);
      }
    });
    
    viteProcess.on('error', (err) => {
      logTemplate(template, `Failed to start: ${err.message}`, colors.red);
      reject(err);
    });
    
    processes.push({ process: viteProcess, template });
    
    // Timeout after 30 seconds
    setTimeout(() => {
      if (!started) {
        logTemplate(template, 'Timeout waiting for server to start', colors.red);
        reject(new Error('Timeout'));
      }
    }, 30000);
  });
}

async function main() {
  console.clear();
  log('🚀 WeedGo Multi-Template Development Server', colors.bright + colors.green);
  log('=' .repeat(50), colors.dim);
  log('');
  
  // Start all templates in parallel
  const startPromises = templates.map(template => 
    startTemplate(template).catch(err => {
      logTemplate(template, `Failed to start: ${err.message}`, colors.red);
      return null;
    })
  );
  
  await Promise.all(startPromises);
  
  log('');
  log('=' .repeat(50), colors.dim);
  log('📦 All template servers are running!', colors.bright + colors.green);
  log('');
  log('Access your templates at:', colors.cyan);
  templates.forEach(template => {
    log(`  ${template.name.padEnd(15)} → http://localhost:${template.port}`, colors.white);
  });
  log('');
  log('Press Ctrl+C to stop all servers', colors.yellow);
  log('=' .repeat(50), colors.dim);
}

// Run the main function
main().catch(err => {
  log(`Fatal error: ${err.message}`, colors.red);
  process.exit(1);
});