# AGI Management Dashboard - Comprehensive UI/UX Design Document

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [High-Level Architecture](#high-level-architecture)
3. [Navigation Structure](#navigation-structure)
4. [Component Hierarchy](#component-hierarchy)
5. [Detailed Section Designs](#detailed-section-designs)
6. [Data Flow Architecture](#data-flow-architecture)
7. [Real-Time Updates](#real-time-updates)
8. [Implementation Guidelines](#implementation-guidelines)

---

## Executive Summary

The AGI Management Dashboard is a comprehensive administrative interface for monitoring and controlling an AI Agent system. It provides real-time insights, system controls, and security management across 26 API endpoints organized into 8 major functional areas.

### Key Features
- Real-time agent monitoring and control
- Comprehensive security and audit logging
- Learning metrics and pattern recognition
- Rate limiting and access control
- WebSocket-based live updates
- Responsive, accessible design

### Technology Stack
- **Frontend**: React 18+ with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Context + Hooks
- **Real-time**: WebSocket connections
- **Charts**: Recharts/D3.js
- **Icons**: Lucide React

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         AGI Management Dashboard                         │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                         Navigation Bar                            │  │
│  │  [Logo] [Dashboard] [Agents] [Security] [Learning] [System]      │  │
│  │                                          [User] [Settings] [🔔]   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────┐  ┌──────────────────────────────────────────────┐  │
│  │                │  │                                              │  │
│  │   Sidebar      │  │            Main Content Area                 │  │
│  │   Navigation   │  │                                              │  │
│  │                │  │         (Dynamic based on route)            │  │
│  │ ┌────────────┐ │  │                                              │  │
│  │ │ Overview   │ │  │  ┌────────────────────────────────────────┐  │  │
│  │ │ Agents     │ │  │  │                                        │  │  │
│  │ │ Activities │ │  │  │         Component Display Area         │  │  │
│  │ │ Security   │ │  │  │                                        │  │  │
│  │ │ Learning   │ │  │  │                                        │  │  │
│  │ │ Rate Limit │ │  │  └────────────────────────────────────────┘  │  │
│  │ │ System     │ │  │                                              │  │
│  │ │ Chat       │ │  │                                              │  │
│  │ └────────────┘ │  └──────────────────────────────────────────────┘  │
│  └────────────────┘                                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                     WebSocket Status Bar                                │
│  [● Connected] [↑ 1.2KB/s] [↓ 3.4KB/s] [Last Update: 2s ago]         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Navigation Structure

### Primary Navigation Hierarchy

```
Dashboard (/)
├── Overview
│   ├── System Metrics
│   ├── Agent Status Grid
│   ├── Activity Timeline
│   └── Quick Actions
│
├── Agent Management (/agents)
│   ├── Agent List
│   ├── Agent Details
│   ├── Agent Actions
│   ├── Performance Metrics
│   └── Task Queue
│
├── Security Center (/security)
│   ├── Security Status
│   ├── Threat Monitor
│   ├── Access Control
│   ├── Content Filtering
│   └── Security Events
│
├── Learning Hub (/learning)
│   ├── Learning Metrics
│   ├── Pattern Recognition
│   ├── Feedback Analysis
│   └── Adaptation History
│
├── System Controls (/system)
│   ├── Rate Limiting
│   ├── Cache Management
│   ├── System Actions
│   └── Export/Import
│
└── Chat Interface (/chat)
    ├── Conversation View
    └── Message History
```

---

## Component Hierarchy

### Core Component Structure

```typescript
AGIDashboard/
├── components/
│   ├── layout/
│   │   ├── DashboardLayout.tsx
│   │   ├── NavigationBar.tsx
│   │   ├── Sidebar.tsx
│   │   └── WebSocketStatusBar.tsx
│   │
│   ├── agents/
│   │   ├── AgentGrid.tsx
│   │   ├── AgentCard.tsx
│   │   ├── AgentDetails.tsx
│   │   ├── AgentActions.tsx
│   │   └── AgentMetrics.tsx
│   │
│   ├── security/
│   │   ├── SecurityDashboard.tsx
│   │   ├── ThreatMonitor.tsx
│   │   ├── AccessControlPanel.tsx
│   │   ├── ContentFilter.tsx
│   │   └── SecurityEventLog.tsx
│   │
│   ├── learning/
│   │   ├── LearningMetrics.tsx
│   │   ├── PatternVisualization.tsx
│   │   ├── FeedbackAnalyzer.tsx
│   │   └── AdaptationTimeline.tsx
│   │
│   ├── monitoring/
│   │   ├── SystemMetrics.tsx
│   │   ├── ActivityFeed.tsx
│   │   ├── AuditLog.tsx
│   │   └── RealTimeChart.tsx
│   │
│   ├── controls/
│   │   ├── RateLimitManager.tsx
│   │   ├── SystemActions.tsx
│   │   ├── QuickActions.tsx
│   │   └── ExportManager.tsx
│   │
│   └── shared/
│       ├── Card.tsx
│       ├── Button.tsx
│       ├── Modal.tsx
│       ├── Alert.tsx
│       ├── DataTable.tsx
│       └── LoadingSpinner.tsx
│
├── hooks/
│   ├── useWebSocket.ts
│   ├── useAgents.ts
│   ├── useSecurity.ts
│   ├── useLearning.ts
│   └── useAuth.ts
│
├── contexts/
│   ├── DashboardContext.tsx
│   ├── WebSocketContext.tsx
│   └── AuthContext.tsx
│
├── services/
│   ├── api.ts
│   ├── websocket.ts
│   └── auth.ts
│
└── types/
    ├── agents.ts
    ├── security.ts
    ├── learning.ts
    └── system.ts
```

---

## Detailed Section Designs

### 1. Dashboard Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Dashboard Overview                             │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │   Total     │ │   Success   │ │  Response   │ │   System    │    │
│  │  Requests   │ │    Rate     │ │    Time     │ │   Uptime    │    │
│  │             │ │             │ │             │ │             │    │
│  │   8,462     │ │    98.5%    │ │   245ms     │ │    99.9%    │    │
│  │  ↑ 12.3%    │ │   ↑ 2.1%    │ │   ↓ 15ms    │ │   30 days   │    │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘    │
│                                                                        │
│  ┌──────────────────────────────┐ ┌──────────────────────────────┐   │
│  │      Agent Status Grid        │ │      Activity Timeline       │   │
│  │                                │ │                              │   │
│  │  ┌──────┐ ┌──────┐ ┌──────┐  │ │  10:45 Model invocation      │   │
│  │  │Research│Analyst│Executor│  │ │  10:44 Security check pass   │   │
│  │  │ ● Active│● Active│ ○ Idle │  │ │  10:43 User authenticated   │   │
│  │  │ 95% CPU│ 72% CPU│ 5% CPU │  │ │  10:42 Pattern recognized   │   │
│  │  └──────┘ └──────┘ └──────┘  │ │  10:41 Cache cleared        │   │
│  │                                │ │  10:40 Agent restarted      │   │
│  │  ┌──────┐ ┌──────┐            │ │                              │   │
│  │  │Validatr│Coordinatr│         │ │  [Load More...]              │   │
│  │  │ ● Active│● Active  │         │ │                              │   │
│  │  │ 45% CPU│ 88% CPU │         │ └──────────────────────────────┘   │
│  │  └──────┘ └──────┘            │                                    │
│  └──────────────────────────────┘                                     │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    System Performance Chart                     │   │
│  │                                                                 │   │
│  │  100% ┤                                                         │   │
│  │   75% ┤     ╱╲    ╱╲                                           │   │
│  │   50% ┤────╱──╲──╱──╲──────────────────────                    │   │
│  │   25% ┤   ╱    ╲╱    ╲                                         │   │
│  │    0% └──────────────────────────────────────────────           │   │
│  │         00:00  04:00  08:00  12:00  16:00  20:00  24:00        │   │
│  │                                                                 │   │
│  │  [Requests] [Response Time] [Error Rate] [Active Users]        │   │
│  └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 2. Agent Management Interface

```
┌────────────────────────────────────────────────────────────────────────┐
│                         Agent Management                                │
├────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────────────┐     │
│  │  Filters: [All Agents ▼] [Active ▼] [Model Type ▼]         │     │
│  │  Actions: [Restart All] [Clear Tasks] [Export Metrics]       │     │
│  └──────────────────────────────────────────────────────────────┘     │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │ Agent ID │ Name      │ Type     │ Status │ Load │ Actions      │   │
│  ├──────────┼───────────┼──────────┼────────┼──────┼──────────────┤   │
│  │ agent_01 │ Research  │ Research │ ● Active│ 65% │ [⟲] [⚙] [📊] │   │
│  │ agent_02 │ Analyst   │ Analysis │ ● Active│ 42% │ [⟲] [⚙] [📊] │   │
│  │ agent_03 │ Executor  │ Execute  │ ○ Idle  │  5% │ [▶] [⚙] [📊] │   │
│  │ agent_04 │ Validator │ Validate │ ● Active│ 78% │ [⟲] [⚙] [📊] │   │
│  │ agent_05 │ Coordintr │ Coord    │ ⟳ Restart│ -- │ [⏹] [⚙] [📊] │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                    Selected Agent Details                      │   │
│  │                                                                 │   │
│  │  Agent: Research Agent (agent_01)                              │   │
│  │  ┌─────────────────────────┐ ┌─────────────────────────────┐  │   │
│  │  │   Performance Metrics   │ │      Current Tasks         │  │   │
│  │  │                         │ │                            │  │   │
│  │  │  Tasks: 142             │ │  • Research AI trends      │  │   │
│  │  │  Success: 99.2%         │ │  • Analyze user feedback  │  │   │
│  │  │  Avg Time: 3.2s         │ │  • Generate report        │  │   │
│  │  │  Memory: 512MB          │ │                            │  │   │
│  │  └─────────────────────────┘ └─────────────────────────────┘  │   │
│  │                                                                 │   │
│  │  ┌──────────────────────────────────────────────────────────┐  │   │
│  │  │                    Task History Chart                    │  │   │
│  │  │  [Last Hour] [Last Day] [Last Week]                      │  │   │
│  │  │                                                           │  │   │
│  │  │  50 ┤  ╱╲                                               │  │   │
│  │  │  40 ┤ ╱  ╲    ╱╲                                        │  │   │
│  │  │  30 ┤╱    ╲  ╱  ╲                                       │  │   │
│  │  │  20 ┤      ╲╱    ╲────╱                                 │  │   │
│  │  │  10 ┤             ╲──╱                                  │  │   │
│  │  │   0 └──────────────────────────────────                 │  │   │
│  │  └──────────────────────────────────────────────────────────┘  │   │
│  └────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 3. Security Center

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Security Center                                │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ │
│  │   Content    │ │    Rate      │ │   Access     │ │   Threat     │ │
│  │  Filtering   │ │   Limiting   │ │   Control    │ │  Detection   │ │
│  │              │ │              │ │              │ │              │ │
│  │  ✓ Active    │ │  ✓ Active    │ │    RBAC      │ │  2 Blocked   │ │
│  │  14 Rules    │ │  6 Rules     │ │  5 Roles     │ │  Today       │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘ │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                     Security Event Timeline                    │   │
│  │                                                                 │   │
│  │  [Critical ●] [High ●] [Medium ●] [Low ●] [Info ●]           │   │
│  │                                                                 │   │
│  │  10:45 ● SQL injection attempt blocked                         │   │
│  │  10:43 ● Suspicious pattern detected in input                  │   │
│  │  10:40 ● Rate limit exceeded for IP 192.168.1.100             │   │
│  │  10:38 ● PII data redacted from response                      │   │
│  │  10:35 ● Authentication failed for user 'unknown'             │   │
│  │  10:32 ● New API key created for user 'developer'             │   │
│  │  10:30 ● Access granted to admin panel                        │   │
│  │                                                                 │   │
│  │  [Export Events] [Configure Alerts] [View Full Log]           │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌─────────────────────────┐ ┌────────────────────────────────────┐   │
│  │   Active Security Rules  │ │      Threat Distribution          │   │
│  │                           │ │                                   │   │
│  │  Content Filters:        │ │         ╱───╲                     │   │
│  │  • Block PII data        │ │       ╱       ╲                   │   │
│  │  • Sanitize HTML         │ │     ╱   SQL    ╲                 │   │
│  │  • Filter profanity      │ │    │    35%     │                │   │
│  │                           │ │    │             │                │   │
│  │  Rate Limits:            │ │    │   XSS  PII │                │   │
│  │  • 100 req/min (user)    │ │     ╲  25%  20%╱                 │   │
│  │  • 1000 req/min (global) │ │       ╲       ╱                   │   │
│  │  • 50 model calls/hour   │ │         ╲───╱                     │   │
│  │                           │ │        Other 20%                 │   │
│  │  [Edit Rules]            │ │                                   │   │
│  └─────────────────────────┘ └────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 4. Learning & Adaptation Hub

```
┌────────────────────────────────────────────────────────────────────────┐
│                      Learning & Adaptation Hub                          │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │                    Learning Performance Indicators              │  │
│  │                                                                 │  │
│  │  Pattern Recognition: 847 patterns     Confidence: 92%          │  │
│  │  Positive Feedback: 92%                Learning Rate: 0.85      │  │
│  │  Adaptations Today: 34                 Model Drift: 0.03        │  │
│  └─────────────────────────────────────────────────────────────────┘  │
│                                                                        │
│  ┌────────────────────────────────────────────────────────────────┐   │
│  │                     Pattern Recognition Map                     │   │
│  │                                                                 │   │
│  │    Conversation Flows          User Intents                    │   │
│  │    ┌─────────────────┐        ┌─────────────────┐             │   │
│  │    │  ● ● ●         │        │     ●   ●       │             │   │
│  │    │ ● ╱ ╲ ●        │        │   ●   ●   ●     │             │   │
│  │    │  ● ● ●         │        │ ●   ●   ●   ●   │             │   │
│  │    │   ● ●          │        │   ●   ●   ●     │             │   │
│  │    └─────────────────┘        └─────────────────┘             │   │
│  │                                                                 │   │
│  │    Error Patterns              Response Templates               │   │
│  │    ┌─────────────────┐        ┌─────────────────┐             │   │
│  │    │   ● ─── ●       │        │  ┌───┬───┬───┐  │             │   │
│  │    │  ╱       ╲      │        │  │███│▓▓▓│░░░│  │             │   │
│  │    │ ●         ●     │        │  │███│▓▓▓│░░░│  │             │   │
│  │    │  ╲       ╱      │        │  └───┴───┴───┘  │             │   │
│  │    └─────────────────┘        └─────────────────┘             │   │
│  └────────────────────────────────────────────────────────────────┘   │
│                                                                        │
│  ┌──────────────────────────┐ ┌───────────────────────────────────┐   │
│  │    Feedback Analysis     │ │      Adaptation Timeline         │   │
│  │                           │ │                                  │   │
│  │  Positive: ████████ 92%  │ │  12:00 Model weights updated    │   │
│  │  Negative: █       8%    │ │  11:45 New pattern recognized   │   │
│  │                           │ │  11:30 Feedback integrated      │   │
│  │  Categories:             │ │  11:15 Threshold adjusted       │   │
│  │  • Accuracy     95%       │ │  11:00 Response template added  │   │
│  │  • Relevance    89%       │ │  10:45 Error pattern detected   │   │
│  │  • Helpfulness  93%       │ │  10:30 Learning cycle complete  │   │
│  │  • Speed        87%       │ │                                  │   │
│  │                           │ │  [View Details] [Export]        │   │
│  └──────────────────────────┘ └───────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### 5. Chat Interface

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Chat Interface                                 │
├────────────────────────────────────────────────────────────────────────┤
│  ┌──────────────────────┐ ┌───────────────────────────────────────┐   │
│  │   Active Sessions     │ │         Chat Window                   │   │
│  │                       │ │                                       │   │
│  │  ┌─────────────────┐  │ │  ┌─────────────────────────────────┐  │   │
│  │  │ User: John Doe  │  │ │  │ AI: Hello! How can I help you? │  │   │
│  │  │ Session: 5 min  │  │ │  └─────────────────────────────────┘  │   │
│  │  │ Messages: 12    │  │ │                                       │   │
│  │  └─────────────────┘  │ │  ┌─────────────────────────────────┐  │   │
│  │                       │ │  │ User: I need help with the API  │  │   │
│  │  ┌─────────────────┐  │ │  └─────────────────────────────────┘  │   │
│  │  │ User: Jane S.   │  │ │                                       │   │
│  │  │ Session: 2 min  │  │ │  ┌─────────────────────────────────┐  │   │
│  │  │ Messages: 4     │  │ │  │ AI: I'll help you with the API │  │   │
│  │  └─────────────────┘  │ │  │ Which endpoint do you need?    │  │   │
│  │                       │ │  └─────────────────────────────────┘  │   │
│  │  [Load More...]      │ │                                       │   │
│  └──────────────────────┘ │  ┌──────────────────────────────────┐  │   │
│                            │  │ Type your message...            │  │   │
│  ┌──────────────────────┐ │  │                                  │  │   │
│  │   Session Metrics    │ │  └──────────────────────────────────┘  │   │
│  │                      │ │  [Send] [Clear] [Export]             │   │
│  │  Avg Duration: 8min  │ └───────────────────────────────────────┘   │
│  │  Resolution: 87%     │                                             │
│  │  Satisfaction: 4.5/5 │ ┌───────────────────────────────────────┐   │
│  │  Active Now: 23      │ │         Agent Assignment              │   │
│  └──────────────────────┘ │  Current: Research Agent               │   │
│                            │  Status: Processing                    │   │
│                            │  Confidence: 95%                       │   │
│                            └───────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow Architecture

### 1. State Management Flow

```typescript
// Global State Structure
interface DashboardState {
  agents: {
    list: Agent[];
    selected: Agent | null;
    loading: boolean;
    error: string | null;
  };
  security: {
    status: SecurityStatus;
    events: SecurityEvent[];
    rules: SecurityRule[];
  };
  learning: {
    metrics: LearningMetrics;
    patterns: Pattern[];
    feedback: Feedback[];
  };
  system: {
    stats: SystemStats;
    activities: Activity[];
    rateLimits: RateLimit[];
  };
  websocket: {
    connected: boolean;
    lastMessage: any;
    messageQueue: Message[];
  };
  auth: {
    user: User | null;
    token: string | null;
    permissions: string[];
  };
}
```

### 2. API Service Layer

```typescript
// api/services/AgentService.ts
class AgentService {
  private apiBase = '/agi/api';

  async getAgents(): Promise<Agent[]> {
    return fetch(`${this.apiBase}/agents`);
  }

  async getAgentDetails(id: string): Promise<AgentDetails> {
    return fetch(`${this.apiBase}/agents/${id}`);
  }

  async executeAction(id: string, action: AgentAction): Promise<ActionResult> {
    return fetch(`${this.apiBase}/agents/${id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ action })
    });
  }

  async getAgentStats(id: string): Promise<AgentStats> {
    return fetch(`${this.apiBase}/agents/${id}/stats`);
  }
}

// Similar services for Security, Learning, System, etc.
```

### 3. WebSocket Integration

```typescript
// hooks/useWebSocket.ts
interface WebSocketMessage {
  type: 'agent_update' | 'stats_update' | 'activity' | 'security_update';
  payload: any;
  timestamp: number;
}

const useWebSocket = () => {
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:5024/agi/ws');

    ws.onopen = () => {
      setConnected(true);
      ws.send(JSON.stringify({ type: 'auth', token: getAuthToken() }));
    };

    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      setLastMessage(message);

      // Update relevant state based on message type
      switch(message.type) {
        case 'agent_update':
          updateAgentState(message.payload);
          break;
        case 'stats_update':
          updateSystemStats(message.payload);
          break;
        case 'activity':
          addActivity(message.payload);
          break;
        case 'security_update':
          updateSecurityStatus(message.payload);
          break;
      }
    };

    ws.onclose = () => setConnected(false);

    return () => ws.close();
  }, []);

  return { connected, lastMessage };
};
```

---

## Real-Time Updates

### WebSocket Message Types

```typescript
// Real-time message definitions
enum MessageType {
  // Agent Messages
  AGENT_STATUS_CHANGE = 'agent.status.change',
  AGENT_TASK_COMPLETE = 'agent.task.complete',
  AGENT_ERROR = 'agent.error',

  // Security Messages
  SECURITY_THREAT_DETECTED = 'security.threat.detected',
  SECURITY_RULE_TRIGGERED = 'security.rule.triggered',
  SECURITY_ACCESS_DENIED = 'security.access.denied',

  // Learning Messages
  LEARNING_PATTERN_RECOGNIZED = 'learning.pattern.recognized',
  LEARNING_FEEDBACK_RECEIVED = 'learning.feedback.received',
  LEARNING_ADAPTATION_COMPLETE = 'learning.adaptation.complete',

  // System Messages
  SYSTEM_STATS_UPDATE = 'system.stats.update',
  SYSTEM_ALERT = 'system.alert',
  SYSTEM_MAINTENANCE = 'system.maintenance'
}

// Update handler
const handleRealtimeUpdate = (message: WebSocketMessage) => {
  switch(message.type) {
    case MessageType.AGENT_STATUS_CHANGE:
      // Update agent status in UI
      updateAgentCard(message.agentId, message.status);
      showNotification(`Agent ${message.agentId} is now ${message.status}`);
      break;

    case MessageType.SECURITY_THREAT_DETECTED:
      // Show security alert
      showSecurityAlert(message.threat);
      updateSecurityDashboard(message);
      break;

    case MessageType.LEARNING_PATTERN_RECOGNIZED:
      // Update learning metrics
      incrementPatternCount();
      addPatternToVisualization(message.pattern);
      break;

    case MessageType.SYSTEM_STATS_UPDATE:
      // Update dashboard metrics
      updateMetricCards(message.stats);
      updatePerformanceChart(message.stats);
      break;
  }
};
```

### Real-Time Component Updates

```typescript
// components/agents/AgentCard.tsx
const AgentCard: React.FC<{ agentId: string }> = ({ agentId }) => {
  const [agent, setAgent] = useState<Agent | null>(null);
  const { subscribe, unsubscribe } = useWebSocket();

  useEffect(() => {
    // Subscribe to agent-specific updates
    const subscription = subscribe(
      `agent.${agentId}.*`,
      (message) => {
        if (message.agentId === agentId) {
          setAgent(prev => ({ ...prev, ...message.update }));
        }
      }
    );

    return () => unsubscribe(subscription);
  }, [agentId]);

  return (
    <div className={`agent-card ${agent?.status}`}>
      <h3>{agent?.name}</h3>
      <div className="status-indicator">
        <span className={`status-dot ${agent?.status}`} />
        {agent?.status}
      </div>
      <div className="metrics">
        <div>Load: {agent?.currentLoad}%</div>
        <div>Tasks: {agent?.tasks}</div>
        <div>Success: {agent?.successRate}%</div>
      </div>
    </div>
  );
};
```

---

## Implementation Guidelines

### 1. Component Development Standards

```typescript
// Standard component template
interface ComponentProps {
  // Props definition
  data?: any;
  onAction?: (action: string) => void;
  className?: string;
}

const StandardComponent: React.FC<ComponentProps> = ({
  data,
  onAction,
  className
}) => {
  // State management
  const [localState, setLocalState] = useState();

  // Context hooks
  const { globalState, dispatch } = useDashboardContext();

  // Custom hooks
  const { loading, error, refetch } = useApiData('/endpoint');

  // Effects
  useEffect(() => {
    // Setup and cleanup
  }, [dependencies]);

  // Event handlers
  const handleAction = useCallback((action: string) => {
    onAction?.(action);
  }, [onAction]);

  // Render
  return (
    <div className={`component ${className}`}>
      {/* Component content */}
    </div>
  );
};

export default StandardComponent;
```

### 2. Styling Guidelines (Tailwind CSS)

```css
/* Color Palette */
--primary: blue-600
--secondary: gray-600
--success: green-500
--warning: yellow-500
--danger: red-500
--info: blue-400

/* Component Classes */
.dashboard-card {
  @apply bg-white rounded-lg shadow-sm border border-gray-200 p-6;
}

.metric-value {
  @apply text-2xl font-bold text-gray-900;
}

.status-active {
  @apply bg-green-100 text-green-800;
}

.status-idle {
  @apply bg-gray-100 text-gray-800;
}

.status-error {
  @apply bg-red-100 text-red-800;
}

.action-button {
  @apply px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors;
}
```

### 3. Accessibility Requirements

- **ARIA Labels**: All interactive elements must have appropriate ARIA labels
- **Keyboard Navigation**: Full keyboard support for all features
- **Screen Reader Support**: Semantic HTML and proper heading hierarchy
- **Color Contrast**: WCAG AA compliance (4.5:1 for normal text, 3:1 for large text)
- **Focus Indicators**: Clear visual focus indicators for keyboard users
- **Loading States**: Announce loading states to screen readers
- **Error Messages**: Associate error messages with form fields

### 4. Performance Optimization

```typescript
// Optimization strategies

// 1. Code Splitting
const AgentDetails = lazy(() => import('./components/agents/AgentDetails'));

// 2. Memoization
const ExpensiveComponent = memo(({ data }) => {
  // Component logic
}, (prevProps, nextProps) => {
  return prevProps.data.id === nextProps.data.id;
});

// 3. Virtual Scrolling for large lists
import { FixedSizeList } from 'react-window';

const VirtualizedList = ({ items }) => (
  <FixedSizeList
    height={600}
    itemCount={items.length}
    itemSize={50}
    width="100%"
  >
    {({ index, style }) => (
      <div style={style}>
        {items[index].name}
      </div>
    )}
  </FixedSizeList>
);

// 4. Debounced Updates
const debouncedUpdate = useMemo(
  () => debounce(updateFunction, 300),
  [updateFunction]
);

// 5. Optimistic Updates
const optimisticUpdate = (action) => {
  // Update UI immediately
  dispatch({ type: 'OPTIMISTIC_UPDATE', payload: action });

  // Send to server
  api.executeAction(action)
    .catch(() => {
      // Rollback on error
      dispatch({ type: 'ROLLBACK_UPDATE', payload: action });
    });
};
```

### 5. Testing Requirements

```typescript
// Unit Test Example
describe('AgentCard', () => {
  it('displays agent information correctly', () => {
    const agent = {
      id: 'agent_01',
      name: 'Research Agent',
      status: 'active',
      currentLoad: 65
    };

    const { getByText } = render(<AgentCard agent={agent} />);

    expect(getByText('Research Agent')).toBeInTheDocument();
    expect(getByText('active')).toBeInTheDocument();
    expect(getByText('65%')).toBeInTheDocument();
  });

  it('handles status updates via WebSocket', async () => {
    const { rerender } = render(<AgentCard agentId="agent_01" />);

    // Simulate WebSocket message
    act(() => {
      mockWebSocket.send({
        type: 'agent_update',
        agentId: 'agent_01',
        update: { status: 'idle' }
      });
    });

    await waitFor(() => {
      expect(screen.getByText('idle')).toBeInTheDocument();
    });
  });
});

// Integration Test Example
describe('Dashboard Integration', () => {
  it('loads all dashboard sections', async () => {
    render(<AGIDashboard />);

    await waitFor(() => {
      expect(screen.getByText('System Metrics')).toBeInTheDocument();
      expect(screen.getByText('Agent Status')).toBeInTheDocument();
      expect(screen.getByText('Security Status')).toBeInTheDocument();
      expect(screen.getByText('Learning Metrics')).toBeInTheDocument();
    });
  });
});
```

### 6. Security Considerations

```typescript
// Security best practices

// 1. Input Sanitization
const sanitizeInput = (input: string): string => {
  return DOMPurify.sanitize(input, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'a'],
    ALLOWED_ATTR: ['href']
  });
};

// 2. XSS Prevention
const SafeHTML: React.FC<{ html: string }> = ({ html }) => {
  const sanitized = sanitizeInput(html);
  return <div dangerouslySetInnerHTML={{ __html: sanitized }} />;
};

// 3. CSRF Protection
const apiCall = async (url: string, options: RequestInit = {}) => {
  const csrfToken = getCsrfToken();

  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      'X-CSRF-Token': csrfToken,
      'Content-Type': 'application/json'
    },
    credentials: 'include'
  });
};

// 4. Rate Limiting on Client
const rateLimitedAction = rateLimit(
  async (action: string) => {
    return await api.executeAction(action);
  },
  { maxCalls: 10, windowMs: 60000 }
);

// 5. Secure WebSocket Connection
const secureWebSocket = () => {
  const ws = new WebSocket('wss://secure-domain.com/agi/ws');

  ws.onopen = () => {
    // Authenticate with token
    const token = getSecureToken();
    ws.send(JSON.stringify({
      type: 'auth',
      token,
      timestamp: Date.now(),
      nonce: generateNonce()
    }));
  };

  return ws;
};
```

---

## API Endpoint Coverage Matrix

### Complete Endpoint Mapping (26 Endpoints)

| Category | Endpoint | Method | UI Component | Real-time Updates |
|----------|----------|--------|--------------|-------------------|
| **Agent Management (5)** |
| 1 | `/agents` | GET | AgentGrid | ✓ WebSocket |
| 2 | `/agents/{id}` | GET | AgentDetails | ✓ WebSocket |
| 3 | `/agents/{id}/actions` | POST | AgentActions | ✓ WebSocket |
| 4 | `/agents/{id}/stats` | GET | AgentMetrics | ✓ Polling |
| 5 | `/agents/{id}/tasks` | GET | TaskQueue | ✓ WebSocket |
| **Authentication (6)** |
| 6 | `/auth/login` | POST | LoginForm | - |
| 7 | `/auth/logout` | POST | LogoutButton | - |
| 8 | `/auth/refresh` | POST | TokenManager | Auto |
| 9 | `/auth/me` | GET | UserProfile | - |
| 10 | `/auth/api-keys` | POST | ApiKeyManager | - |
| 11 | `/auth/api-keys/{id}` | DELETE | ApiKeyManager | - |
| **Statistics & Monitoring (2)** |
| 12 | `/stats` | GET | SystemMetrics | ✓ WebSocket |
| 13 | `/agents/{id}/stats` | GET | AgentStats | ✓ Polling |
| **Activity & Audit (2)** |
| 14 | `/activities` | GET | ActivityFeed | ✓ WebSocket |
| 15 | `/audit-logs` | GET | AuditLog | ✓ Polling |
| **Security (3)** |
| 16 | `/security/status` | GET | SecurityDashboard | ✓ WebSocket |
| 17 | `/security/events` | GET | SecurityEventLog | ✓ WebSocket |
| 18 | `/security/rules/{rule}` | PUT | SecurityRules | ✓ WebSocket |
| **Learning & Feedback (3)** |
| 19 | `/learning/metrics` | GET | LearningMetrics | ✓ Polling |
| 20 | `/learning/patterns` | GET | PatternVisualizer | ✓ Polling |
| 21 | `/learning/feedback` | GET | FeedbackAnalyzer | ✓ WebSocket |
| **Rate Limiting (2)** |
| 22 | `/rate-limits` | GET | RateLimitManager | ✓ Polling |
| 23 | `/rate-limits/{rule}` | PUT | RateLimitEditor | - |
| **System Controls (3)** |
| 24 | `/system/restart-agents` | POST | SystemActions | ✓ WebSocket |
| 25 | `/system/clear-cache` | POST | SystemActions | ✓ WebSocket |
| 26 | `/system/export-logs` | GET | ExportManager | - |
| **Chat Interface (2)** |
| 27 | `/chat/send` | POST | ChatInterface | ✓ WebSocket |
| 28 | `/chat/history` | GET | ChatHistory | ✓ Polling |

---

## Responsive Design Breakpoints

```css
/* Tailwind Breakpoints */
sm: 640px   /* Mobile landscape */
md: 768px   /* Tablet */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
2xl: 1536px /* Extra large desktop */

/* Layout Adaptations */
/* Mobile (default) */
.dashboard-grid {
  @apply grid grid-cols-1 gap-4;
}

/* Tablet */
@media (min-width: 768px) {
  .dashboard-grid {
    @apply grid-cols-2;
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .dashboard-grid {
    @apply grid-cols-3;
  }
}

/* Large Desktop */
@media (min-width: 1280px) {
  .dashboard-grid {
    @apply grid-cols-4;
  }
}
```

---

## Deployment Considerations

### Environment Configuration

```typescript
// config/environments.ts
const environments = {
  development: {
    apiUrl: 'http://localhost:5024/agi/api',
    wsUrl: 'ws://localhost:5024/agi/ws',
    debug: true,
    mockData: false
  },
  staging: {
    apiUrl: 'https://staging.agi-system.com/api',
    wsUrl: 'wss://staging.agi-system.com/ws',
    debug: true,
    mockData: false
  },
  production: {
    apiUrl: 'https://api.agi-system.com',
    wsUrl: 'wss://ws.agi-system.com',
    debug: false,
    mockData: false
  }
};

export const config = environments[process.env.NODE_ENV || 'development'];
```

### Build Optimization

```json
// package.json scripts
{
  "scripts": {
    "build:dev": "webpack --mode development",
    "build:prod": "webpack --mode production --optimization-minimize",
    "build:analyze": "webpack-bundle-analyzer dist/stats.json",
    "test": "jest --coverage",
    "test:e2e": "cypress run",
    "lint": "eslint src/**/*.{ts,tsx}",
    "type-check": "tsc --noEmit"
  }
}
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build:prod

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Conclusion

This comprehensive design document provides a complete blueprint for implementing the AGI Management Dashboard with full coverage of all 26 API endpoints. The design emphasizes:

1. **Modularity**: Component-based architecture for maintainability
2. **Real-time Updates**: WebSocket integration for live data
3. **User Experience**: Intuitive navigation and clear information hierarchy
4. **Performance**: Optimized rendering and data fetching strategies
5. **Security**: Built-in security considerations and best practices
6. **Accessibility**: WCAG compliance and keyboard navigation
7. **Scalability**: Designed to handle growth in features and users

The implementation should follow the component hierarchy, utilize the provided hooks and services, and maintain consistency with the design patterns outlined in this document.