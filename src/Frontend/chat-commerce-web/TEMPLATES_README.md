# WeedGo Multi-Template Development

This project includes multiple UI templates that can be run simultaneously for development and testing.

## Available Templates

| Template | Port | Description |
|----------|------|-------------|
| **weedgo** | 5173 | Default green-themed template |
| **pot-palace** | 5174 | Vibrant gradient design |
| **modern-minimal** | 5175 | Clean, minimalist Apple-inspired design |
| **vintage** | 5176 | Classic vintage cannabis aesthetic |
| **rasta-vibes** | 5177 | Rastafarian-inspired colorful theme |
| **dark-tech** | 5178 | Cyberpunk/Matrix-style dark theme |
| **metal** | 5179 | Heavy metal inspired dark design |
| **dirty** | 5180 | Earthy, organic brown theme |

## Quick Start

### Run All Templates At Once

```bash
# Using npm (recommended)
npm start
# or
npm run start:dev
# or
npm run dev:all

# Using bash script directly
npm run dev:all:bash
```

### Run Individual Templates

```bash
# Run specific template
npm run dev:weedgo
npm run dev:pot-palace
npm run dev:modern-minimal
npm run dev:vintage
npm run dev:rasta-vibes
npm run dev:dark-tech
npm run dev:metal
npm run dev:dirty
```

### Run Default Development Server

```bash
# Runs on port 5173 with default template
npm run dev
```

## Available NPM Scripts

- `npm start` - Start all template servers (alias for dev:all)
- `npm run start:dev` - Start all template servers (alias for dev:all)
- `npm run dev` - Run single dev server (default template)
- `npm run dev:all` - Run all templates using Node.js script
- `npm run dev:all:bash` - Run all templates using bash script
- `npm run dev:[template-name]` - Run specific template
- `npm run build` - Build for production
- `npm run preview` - Preview production build

## Features Implemented

All templates include:
- ✅ Shopping cart with item count badge
- ✅ Product search dropdown with autocomplete
- ✅ Product selection with console logging
- ✅ Cart modal overlay
- ✅ User authentication UI
- ✅ Responsive design

## Development Tips

1. **Check Running Servers**: View which templates are running:
   ```bash
   lsof -i :5173-5180 | grep LISTEN
   ```

2. **Kill All Servers**: Stop all template servers:
   ```bash
   for port in {5173..5180}; do lsof -ti:$port | xargs kill -9 2>/dev/null; done
   ```

3. **Console Debugging**: Open browser console to see product selection logs

4. **Template Switching**: Each template runs independently, so you can test features across different designs simultaneously

## File Structure

```
chat-commerce-web/
├── scripts/
│   ├── run-all-templates.js    # Node.js runner with colors
│   ├── dev-all.sh              # Bash script runner
│   └── start_all_templates.sh  # Simple bash starter
├── src/
│   └── templates/
│       ├── weedgo/
│       ├── pot-palace/
│       ├── modern-minimal/
│       ├── vintage/
│       ├── rasta-vibes/
│       ├── dark-tech/
│       ├── metal/
│       └── dirty/
└── package.json                 # NPM scripts configuration
```

## Troubleshooting

### Ports Already in Use
If you get "port already in use" errors, run:
```bash
npm run dev:all:bash
```
This script automatically kills existing processes before starting.

### Template Not Loading
1. Check if the server is running: `lsof -i :PORT`
2. Check browser console for errors
3. Ensure API server is running on port 5024

### Performance Issues
Running all 8 templates simultaneously requires significant resources. Consider:
- Running only needed templates
- Closing unused browser tabs
- Increasing Node.js memory limit if needed

## Environment Variables

Each template automatically receives:
- `VITE_TEMPLATE` - Template name
- `PORT` - Server port number

These are set automatically when using the npm scripts.