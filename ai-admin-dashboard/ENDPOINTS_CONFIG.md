# AI Admin Dashboard - Endpoints Configuration

## Overview
All API endpoints in the AI Admin Dashboard are now centralized in a single configuration file located at `src/config/endpoints.ts`. This ensures consistency and makes it easy to update endpoints across the entire application.

## Configuration File Structure

The endpoints configuration exports:
- `API_BASE_URL`: The base URL for all API requests
- `WS_BASE_URL`: The base URL for WebSocket connections
- `endpoints`: An object containing all endpoint paths organized by feature

## Environment Variables

The following environment variables can be used to configure the API endpoints:

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_HOST` | API server hostname | `window.location.hostname` |
| `VITE_API_PORT` | API server port | `5024` |
| `VITE_API_URL` | Complete API URL (overrides host/port) | Auto-generated |
| `VITE_WS_HOST` | WebSocket server hostname | Same as API host |
| `VITE_WS_PORT` | WebSocket server port | Same as API port |
| `VITE_WS_URL` | Complete WebSocket URL | Auto-generated |

## Usage Examples

### In Components

```typescript
import { endpoints } from '../config/endpoints';

// Using a simple endpoint
const response = await fetch(endpoints.chat.base, {
  method: 'POST',
  body: JSON.stringify(data)
});

// Using an endpoint with parameters
const historyUrl = endpoints.chat.history(customerId);

// Using the base URL directly
const customUrl = `${endpoints.base}/custom-endpoint`;
```

### In Services

```typescript
import { API_BASE_URL, endpoints } from '../config/endpoints';

class MyService {
  private baseUrl = API_BASE_URL;
  
  async getData() {
    return fetch(endpoints.models.list);
  }
}
```

## Endpoint Categories

The endpoints are organized into the following categories:

- **WebSocket**: Real-time communication endpoints
- **Chat**: Chat functionality and history
- **AI**: AI training, datasets, and personalities
- **Models**: Model management and deployment
- **Training**: Training examples and accuracy
- **Intents**: Intent management
- **Skip Words**: Skip word configuration
- **Products**: Product search and management
- **Services**: Service health and logs
- **Admin**: Administrative functions

## Migration from Hardcoded URLs

All components have been updated to use the centralized endpoints configuration. The following files were modified:

### Components Updated:
- UnifiedChatTestingHistory.tsx
- TrainingCenter.tsx
- LiveChatTestingFixed.tsx
- SearchTesting.tsx
- LiveChatTesting.tsx
- UnifiedTrainingHub.tsx
- DecisionTreeVisualizer.tsx
- AITrainingProgram.tsx
- AIConfiguration.tsx
- IntentManager.tsx
- ModernChatInterface.tsx
- ModelManagement.tsx
- DatasetCreationModal.tsx
- ServiceManager.tsx
- DatasetUploadModal.tsx
- LiveChat.tsx
- ModelDeploymentEnhanced.tsx
- App.tsx
- InteractiveTutorial.tsx
- ComprehensiveTutorial.tsx

### Services Updated:
- api.ts - Now imports from endpoints config
- websocket.ts - Dynamically loads endpoint configuration

## Development Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Update the environment variables as needed for your environment

3. Start the development server:
   ```bash
   npm run dev
   ```

## Production Deployment

For production deployments, set the environment variables in your deployment configuration:

```bash
VITE_API_HOST=api.yourdomain.com
VITE_API_PORT=443
VITE_API_URL=https://api.yourdomain.com
```

## Troubleshooting

### Issue: Endpoints not updating after changing .env
**Solution**: Restart the development server after changing environment variables.

### Issue: WebSocket connection failing
**Solution**: Ensure the WebSocket port is correct and the server supports WebSocket connections.

### Issue: CORS errors
**Solution**: Verify that the API server is configured to accept requests from your frontend domain.

## Adding New Endpoints

To add a new endpoint:

1. Open `src/config/endpoints.ts`
2. Add the endpoint to the appropriate category in the `endpoints` object
3. Use the endpoint in your component or service by importing from the config

Example:
```typescript
// In endpoints.ts
export const endpoints = {
  // ... existing endpoints
  myFeature: {
    list: `${API_BASE_URL}/api/${API_VERSION}/my-feature`,
    get: (id: string) => `${API_BASE_URL}/api/${API_VERSION}/my-feature/${id}`,
  }
};

// In your component
import { endpoints } from '../config/endpoints';
const data = await fetch(endpoints.myFeature.list);
```