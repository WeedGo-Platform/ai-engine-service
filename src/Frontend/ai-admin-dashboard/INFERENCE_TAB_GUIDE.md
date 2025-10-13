# Inference Tab - User Guide

## Overview

The **Inference** tab in AI Configuration provides a simple interface to manage LLM Router hot-swap between local and cloud inference.

---

## Location

**Path:** AI Configuration → Inference Tab

1. Open admin dashboard
2. Navigate to "AI Configuration" page
3. Click on "Inference" tab (third tab)

---

## Features

### 1. Hot-Swap Toggle

**One-Click Switching:**
- **Switch to Cloud**: Use cloud providers (Groq, OpenRouter, LLM7) - 50-90% faster
- **Switch to Local**: Use local llama-cpp inference - unlimited capacity

**Current Mode Display:**
- ☁️ Cloud inference (3 providers available)
- 💻 Local inference (llama-cpp)

### 2. Performance Metrics

| Metric | Cloud | Local |
|--------|-------|-------|
| **Latency** | 0.5-2.5s | ~5s |
| **Model Size** | 70B params | 0.5-7B |
| **Cost/Month** | $0 | $0 |
| **Daily Limit** | 16K+ | Unlimited |

### 3. Provider Status Cards

**Groq** ⚡
- Ultra-fast (0.5s)
- Llama 3.3 70B
- 14,400 req/day

**OpenRouter** 🧠
- Reasoning (2s)
- DeepSeek R1
- 200 req/day

**LLM7** 🌐
- Fallback (2.5s)
- gpt-4o-mini
- 57,600 req/day

### 4. Router Statistics

- **Total Requests**: Cumulative count
- **Total Cost**: Always $0 (free tiers)
- **Status**: Current mode (Cloud/Local)
- **Provider Stats**: Request count and success rate per provider

---

## How to Use

### Switch to Cloud Inference

1. Open **AI Configuration → Inference**
2. Click **"Switch to Cloud"** button
3. Wait for confirmation toast
4. You're now using cloud providers (faster!)

### Switch to Local Inference

1. Open **AI Configuration → Inference**
2. Click **"Switch to Local"** button
3. Wait for confirmation toast
4. You're now using local model (unlimited)

### Refresh Stats

1. Click **"Refresh Stats"** button at bottom
2. Updates all provider statistics
3. Shows latest request counts and success rates

---

## When to Use Each Mode

### Use Cloud (Recommended)
✅ Need fast responses (0.5-2.5s)
✅ Want better quality (70B model)
✅ Under 16K requests/day
✅ Real-time customer interactions

### Use Local
✅ Over 16K requests/day
✅ Offline/no internet
✅ Testing/development
✅ Don't need speed

---

## Visual Design

### Mode Card (Gradient)
- **Indigo/Purple gradient** background
- Current mode prominently displayed
- Big toggle button (indigo for cloud, gray for local)
- Performance metrics grid below

### Provider Cards
- **Groq**: Yellow Zap icon ⚡
- **OpenRouter**: Blue Network icon 🔗
- **LLM7**: Purple Cloud icon ☁️
- Green "Active" badge on each
- Request count & success rate

### Statistics Dashboard
- Gray background card
- 3 metrics in grid:
  - Total Requests (white text)
  - Total Cost (green, always $0)
  - Status (indigo, Cloud/Local)

---

## Technical Details

### API Endpoints Used

```
GET  /api/admin/router/stats    - Fetch statistics
POST /api/admin/router/toggle   - Toggle mode
```

### Auto-Refresh
- Stats load automatically when tab opens
- Manual refresh button available
- No auto-polling (click to update)

### State Management
- React state for router stats
- Loading states for smooth UX
- Toast notifications for actions

---

## Troubleshooting

### "No router information available"
- **Cause**: Router not initialized
- **Fix**: Check backend logs, ensure API keys are set

### Toggle button disabled
- **Cause**: Router not enabled
- **Fix**: Restart backend with API keys loaded

### Stats showing 0 requests
- **Cause**: No requests made yet
- **Fix**: This is normal, stats will update after first cloud request

---

## Screenshots

*(When viewing the tab, you'll see:)*

1. **Top**: Large gradient card with mode and toggle
2. **Middle**: 3 provider cards in a grid
3. **Bottom**: Statistics dashboard
4. **Footer**: Refresh button

---

## Benefits

✅ **Simple**: One-click toggle, no complex settings
✅ **Visual**: Clear cards showing provider status
✅ **Informative**: Real-time stats and performance metrics
✅ **KISS**: Keep It Simple, Stupid - just what you need

---

**That's it!** You can now easily manage your inference mode and monitor cloud provider performance.

---

**Created:** October 12, 2025
**Version:** 1.0
**Tab Location:** AI Configuration → Inference
