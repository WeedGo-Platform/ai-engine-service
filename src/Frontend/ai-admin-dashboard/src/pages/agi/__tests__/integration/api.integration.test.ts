/**
 * API Integration Tests
 * End-to-end tests for AGI API endpoints
 */

import { apiService } from '../../services/api';
import { setupServer } from 'msw/node';
import { rest } from 'msw';

const API_BASE = 'http://localhost:5024/api/agi';

// Mock server for integration tests
const server = setupServer(
  // Agent endpoints
  rest.get(`${API_BASE}/agents`, (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'agent-1',
          name: 'Assistant Agent',
          type: 'conversational',
          model: 'gpt-4',
          state: 'active',
          capabilities: ['chat', 'reasoning'],
          performance: { successRate: 95, totalTasks: 100 }
        },
        {
          id: 'agent-2',
          name: 'Analyzer Agent',
          type: 'analytical',
          model: 'claude-3',
          state: 'idle',
          capabilities: ['analysis', 'data_processing'],
          performance: { successRate: 88, totalTasks: 50 }
        }
      ])
    );
  }),

  rest.post(`${API_BASE}/agents`, (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({
        id: 'agent-new',
        ...req.body,
        state: 'idle',
        created_at: new Date().toISOString()
      })
    );
  }),

  rest.put(`${API_BASE}/agents/:id`, (req, res, ctx) => {
    return res(
      ctx.json({
        id: req.params.id,
        ...req.body,
        updated_at: new Date().toISOString()
      })
    );
  }),

  rest.delete(`${API_BASE}/agents/:id`, (req, res, ctx) => {
    return res(ctx.status(204));
  }),

  // Stats endpoint
  rest.get(`${API_BASE}/stats`, (req, res, ctx) => {
    return res(
      ctx.json({
        total_agents: 10,
        active_tasks: 25,
        success_rate: 92.5,
        average_response_time: 250,
        cpu_usage: 45,
        memory_usage: 62,
        disk_usage: 38,
        network_load: 15
      })
    );
  }),

  // Security endpoints
  rest.get(`${API_BASE}/security/status`, (req, res, ctx) => {
    return res(
      ctx.json({
        content_filtering: 'enabled',
        rate_limiting: 'active',
        threats_blocked: 15,
        total_events: 450,
        last_threat: {
          type: 'sql_injection',
          timestamp: new Date().toISOString()
        }
      })
    );
  }),

  rest.get(`${API_BASE}/security/events`, (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'event-1',
          type: 'authentication',
          severity: 'low',
          description: 'User login successful',
          timestamp: new Date().toISOString()
        }
      ])
    );
  }),

  // Learning endpoints
  rest.get(`${API_BASE}/learning/metrics`, (req, res, ctx) => {
    return res(
      ctx.json({
        learning_rate: 0.85,
        pattern_count: 156,
        confidence_score: 0.92,
        adaptations_today: 12,
        feedback_positive: 78
      })
    );
  }),

  rest.get(`${API_BASE}/learning/patterns`, (req, res, ctx) => {
    return res(
      ctx.json([
        {
          id: 'pattern-1',
          type: 'user_behavior',
          confidence: 0.89,
          occurrences: 45
        }
      ])
    );
  }),

  // Chat endpoint with streaming
  rest.post(`${API_BASE}/chat`, (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.set('Content-Type', 'text/event-stream'),
      ctx.body('data: {"chunk": "Hello"}\ndata: {"chunk": " world"}\ndata: [DONE]\n')
    );
  }),

  // Activities endpoint
  rest.get(`${API_BASE}/activities`, (req, res, ctx) => {
    const limit = req.url.searchParams.get('limit') || '10';
    return res(
      ctx.json(
        Array.from({ length: parseInt(limit) }, (_, i) => ({
          id: `activity-${i}`,
          type: 'system',
          message: `System event ${i}`,
          timestamp: new Date(Date.now() - i * 60000).toISOString()
        }))
      )
    );
  })
);

// Setup and teardown
beforeAll(() => {
  server.listen({ onUnhandledRequest: 'warn' });
  localStorage.setItem('auth_token', 'test-integration-token');
});

afterEach(() => server.resetHandlers());

afterAll(() => {
  server.close();
  localStorage.clear();
});

describe('Agent Management API Integration', () => {
  it('should fetch all agents', async () => {
    const agents = await apiService.get('/agents');

    expect(agents).toHaveLength(2);
    expect(agents[0]).toHaveProperty('id', 'agent-1');
    expect(agents[0]).toHaveProperty('name', 'Assistant Agent');
    expect(agents[0]).toHaveProperty('state', 'active');
  });

  it('should create a new agent', async () => {
    const newAgent = {
      name: 'Test Agent',
      type: 'analytical',
      model: 'gpt-4',
      capabilities: ['analysis']
    };

    const created = await apiService.post('/agents', newAgent);

    expect(created).toHaveProperty('id');
    expect(created).toHaveProperty('name', 'Test Agent');
    expect(created).toHaveProperty('state', 'idle');
    expect(created).toHaveProperty('created_at');
  });

  it('should update an existing agent', async () => {
    const updates = {
      name: 'Updated Agent',
      capabilities: ['chat', 'analysis']
    };

    const updated = await apiService.put('/agents/agent-1', updates);

    expect(updated).toHaveProperty('id', 'agent-1');
    expect(updated).toHaveProperty('name', 'Updated Agent');
    expect(updated).toHaveProperty('updated_at');
  });

  it('should delete an agent', async () => {
    await expect(apiService.delete('/agents/agent-1')).resolves.not.toThrow();
  });

  it('should handle agent actions', async () => {
    server.use(
      rest.post(`${API_BASE}/agents/:id/actions`, (req, res, ctx) => {
        return res(ctx.json({ success: true, action: req.body }));
      })
    );

    const result = await apiService.post('/agents/agent-1/actions', {
      action: 'restart'
    });

    expect(result).toHaveProperty('success', true);
  });
});

describe('System Stats API Integration', () => {
  it('should fetch system statistics', async () => {
    const stats = await apiService.get('/stats');

    expect(stats).toHaveProperty('totalAgents', 10);
    expect(stats).toHaveProperty('activeTasks', 25);
    expect(stats).toHaveProperty('successRate', 92.5);
    expect(stats).toHaveProperty('cpuUsage', 45);
  });

  it('should handle stats refresh', async () => {
    const stats1 = await apiService.get('/stats');
    const stats2 = await apiService.get('/stats');

    expect(stats1).toEqual(stats2);
  });
});

describe('Security API Integration', () => {
  it('should fetch security status', async () => {
    const status = await apiService.get('/security/status');

    expect(status).toHaveProperty('contentFiltering', 'enabled');
    expect(status).toHaveProperty('rateLimiting', 'active');
    expect(status).toHaveProperty('threatsBlocked', 15);
  });

  it('should fetch security events', async () => {
    const events = await apiService.get('/security/events');

    expect(Array.isArray(events)).toBe(true);
    expect(events[0]).toHaveProperty('id');
    expect(events[0]).toHaveProperty('severity', 'low');
  });

  it('should update security settings', async () => {
    server.use(
      rest.put(`${API_BASE}/security/settings`, (req, res, ctx) => {
        return res(ctx.json({ ...req.body, updated: true }));
      })
    );

    const updated = await apiService.put('/security/settings', {
      content_filtering: 'strict',
      rate_limit: 100
    });

    expect(updated).toHaveProperty('updated', true);
  });
});

describe('Learning API Integration', () => {
  it('should fetch learning metrics', async () => {
    const metrics = await apiService.get('/learning/metrics');

    expect(metrics).toHaveProperty('learningRate', 0.85);
    expect(metrics).toHaveProperty('patternCount', 156);
    expect(metrics).toHaveProperty('confidenceScore', 0.92);
  });

  it('should fetch learning patterns', async () => {
    const patterns = await apiService.get('/learning/patterns');

    expect(Array.isArray(patterns)).toBe(true);
    expect(patterns[0]).toHaveProperty('type', 'user_behavior');
    expect(patterns[0]).toHaveProperty('confidence', 0.89);
  });

  it('should submit feedback', async () => {
    server.use(
      rest.post(`${API_BASE}/learning/feedback`, (req, res, ctx) => {
        return res(ctx.json({ success: true, feedback_id: 'fb-123' }));
      })
    );

    const result = await apiService.post('/learning/feedback', {
      type: 'positive',
      context: 'test_interaction'
    });

    expect(result).toHaveProperty('success', true);
    expect(result).toHaveProperty('feedbackId', 'fb-123');
  });
});

describe('Chat API Integration', () => {
  it('should send chat messages', async () => {
    const response = await apiService.post('/chat', {
      message: 'Hello',
      context: []
    });

    expect(response).toBeDefined();
  });

  it('should handle streaming responses', async () => {
    // Streaming is handled differently, test the endpoint availability
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': 'Bearer test-integration-token'
      },
      body: JSON.stringify({ message: 'Test' })
    });

    expect(response.status).toBe(200);
    expect(response.headers.get('content-type')).toBe('text/event-stream');
  });
});

describe('Activities API Integration', () => {
  it('should fetch activities with pagination', async () => {
    const activities = await apiService.get('/activities', {
      params: { limit: 5 }
    });

    expect(activities).toHaveLength(5);
    expect(activities[0]).toHaveProperty('id');
    expect(activities[0]).toHaveProperty('type', 'system');
  });

  it('should filter activities by type', async () => {
    server.use(
      rest.get(`${API_BASE}/activities`, (req, res, ctx) => {
        const type = req.url.searchParams.get('type');
        if (type === 'agent') {
          return res(
            ctx.json([
              {
                id: 'activity-agent',
                type: 'agent',
                message: 'Agent started',
                timestamp: new Date().toISOString()
              }
            ])
          );
        }
        return res(ctx.json([]));
      })
    );

    const activities = await apiService.get('/activities', {
      params: { type: 'agent' }
    });

    expect(activities).toHaveLength(1);
    expect(activities[0]).toHaveProperty('type', 'agent');
  });
});

describe('Audit Logs API Integration', () => {
  it('should fetch audit logs', async () => {
    server.use(
      rest.get(`${API_BASE}/audit/logs`, (req, res, ctx) => {
        return res(
          ctx.json({
            logs: [
              {
                id: 'log-1',
                user_id: 'user-1',
                action: 'agent.create',
                timestamp: new Date().toISOString(),
                status: 'success'
              }
            ],
            stats: {
              total_actions: 100,
              success_rate: 95
            }
          })
        );
      })
    );

    const response = await apiService.get('/audit/logs');

    expect(response).toHaveProperty('logs');
    expect(response).toHaveProperty('stats');
    expect(response.logs[0]).toHaveProperty('action', 'agent.create');
  });

  it('should export audit logs', async () => {
    server.use(
      rest.get(`${API_BASE}/audit/export`, (req, res, ctx) => {
        const format = req.url.searchParams.get('format');
        if (format === 'csv') {
          return res(
            ctx.set('Content-Type', 'text/csv'),
            ctx.body('id,action,timestamp\nlog-1,test,2024-01-01')
          );
        }
        return res(ctx.json([]));
      })
    );

    const response = await fetch(`${API_BASE}/audit/export?format=csv`, {
      headers: {
        'Authorization': 'Bearer test-integration-token'
      }
    });

    expect(response.headers.get('content-type')).toBe('text/csv');
  });
});

describe('System Control API Integration', () => {
  it('should execute system actions', async () => {
    server.use(
      rest.post(`${API_BASE}/system/actions/:action`, (req, res, ctx) => {
        return res(
          ctx.json({
            success: true,
            action: req.params.action,
            timestamp: new Date().toISOString()
          })
        );
      })
    );

    const result = await apiService.post('/system/actions/restart_all_agents', {});

    expect(result).toHaveProperty('success', true);
    expect(result).toHaveProperty('action', 'restart_all_agents');
  });

  it('should update system configuration', async () => {
    server.use(
      rest.put(`${API_BASE}/system/config`, (req, res, ctx) => {
        return res(ctx.json({ ...req.body, applied: true }));
      })
    );

    const config = await apiService.put('/system/config', {
      maintenance_mode: true,
      debug_mode: false
    });

    expect(config).toHaveProperty('applied', true);
    expect(config).toHaveProperty('maintenanceMode', true);
  });
});

describe('Error Handling Integration', () => {
  it('should handle 404 errors gracefully', async () => {
    server.use(
      rest.get(`${API_BASE}/nonexistent`, (req, res, ctx) => {
        return res(ctx.status(404), ctx.json({ message: 'Not found' }));
      })
    );

    await expect(apiService.get('/nonexistent')).rejects.toThrow('Not found');
  });

  it('should handle 500 errors with retry', async () => {
    let attempts = 0;
    server.use(
      rest.get(`${API_BASE}/flaky`, (req, res, ctx) => {
        attempts++;
        if (attempts < 3) {
          return res(ctx.status(500), ctx.json({ message: 'Server error' }));
        }
        return res(ctx.json({ success: true }));
      })
    );

    const result = await apiService.get('/flaky', { retry: 3 });
    expect(result).toHaveProperty('success', true);
    expect(attempts).toBe(3);
  });

  it('should handle rate limiting', async () => {
    server.use(
      rest.get(`${API_BASE}/limited`, (req, res, ctx) => {
        return res(
          ctx.status(429),
          ctx.json({ message: 'Too many requests' }),
          ctx.set('Retry-After', '60')
        );
      })
    );

    await expect(apiService.get('/limited')).rejects.toThrow('Too many requests');
  });
});