# Message Broadcast System Design Document

## 1. System Overview

### Purpose
Enable administrators (Super Admin, Tenant Admin, Store Manager) to send targeted broadcast messages to customers via email, SMS, and push notifications through a unified communication interface in the AI Admin Dashboard.

### Core Principles
- **SRP (Single Responsibility)**: Each service handles one communication channel
- **DRY (Don't Repeat Yourself)**: Shared interfaces and base classes for common functionality
- **SOLID**: Dependency injection, interface segregation, open/closed principle
- **Production Ready**: Error handling, retry logic, rate limiting, audit logging

## 2. Architecture Design

### 2.1 Backend Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (React)                       │
│              Communication Management UI                 │
└─────────────────────┬───────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Broadcast API Gateway                       │
│         /api/v1/communications/*                        │
└─────────────────────┬───────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┬──────────────┐
        ▼             ▼             ▼              ▼
┌──────────────┐┌──────────────┐┌──────────────┐┌──────────────┐
│   Broadcast  ││   Channel    ││   Recipient  ││  Template    │
│   Service    ││  Services    ││   Service    ││   Service    │
└──────────────┘└──────────────┘└──────────────┘└──────────────┘
        │             │             │              │
        └─────────────┴─────────────┴──────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────┐
│                    Database Layer                        │
│  broadcasts | recipients | templates | audit_logs        │
└─────────────────────────────────────────────────────────┘
```

### 2.2 Service Architecture

```python
# Base Communication Interface
interface ICommunicationChannel:
    - send_single(recipient, message, metadata)
    - send_batch(recipients, message, metadata)
    - validate_recipient(recipient)
    - get_delivery_status(message_id)
    - get_rate_limits()

# Concrete Implementations
EmailService implements ICommunicationChannel
SMSService implements ICommunicationChannel
PushNotificationService implements ICommunicationChannel

# Broadcast Orchestrator
BroadcastService:
    - create_broadcast(channels, recipients, message, schedule)
    - execute_broadcast(broadcast_id)
    - pause_broadcast(broadcast_id)
    - cancel_broadcast(broadcast_id)
    - get_broadcast_analytics(broadcast_id)
```

## 3. Database Schema

### 3.1 Core Tables

```sql
-- Broadcast campaigns table
CREATE TABLE broadcasts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    store_id UUID NOT NULL REFERENCES stores(id),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    created_by UUID NOT NULL REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'draft', -- draft, scheduled, sending, sent, cancelled
    scheduled_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_recipients INTEGER DEFAULT 0,
    successful_sends INTEGER DEFAULT 0,
    failed_sends INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Broadcast messages per channel
CREATE TABLE broadcast_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID NOT NULL REFERENCES broadcasts(id),
    channel_type VARCHAR(50) NOT NULL, -- email, sms, push
    subject VARCHAR(500),
    content TEXT NOT NULL,
    template_id UUID REFERENCES message_templates(id),
    template_variables JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Recipients for each broadcast
CREATE TABLE broadcast_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID NOT NULL REFERENCES broadcasts(id),
    customer_id UUID NOT NULL REFERENCES customers(id),
    email VARCHAR(255),
    phone_number VARCHAR(20),
    push_token VARCHAR(500),
    channels JSONB, -- {email: true, sms: false, push: true}
    status VARCHAR(50) DEFAULT 'pending', -- pending, sent, failed, bounced, unsubscribed
    sent_at TIMESTAMP,
    delivered_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Message templates
CREATE TABLE message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    channel_type VARCHAR(50) NOT NULL,
    category VARCHAR(100), -- promotional, transactional, alert
    subject VARCHAR(500),
    content TEXT NOT NULL,
    variables JSONB, -- {name: "string", points: "number"}
    store_id UUID REFERENCES stores(id),
    tenant_id UUID REFERENCES tenants(id),
    is_active BOOLEAN DEFAULT true,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Push notification subscriptions
CREATE TABLE push_subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    device_token VARCHAR(500) NOT NULL,
    device_type VARCHAR(50), -- ios, android, web
    endpoint VARCHAR(500), -- For web push
    auth_key VARCHAR(500), -- For web push
    p256dh_key VARCHAR(500), -- For web push
    is_active BOOLEAN DEFAULT true,
    last_used TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(device_token)
);

-- Communication preferences
CREATE TABLE communication_preferences (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    channel_email BOOLEAN DEFAULT true,
    channel_sms BOOLEAN DEFAULT true,
    channel_push BOOLEAN DEFAULT true,
    promotional BOOLEAN DEFAULT true,
    transactional BOOLEAN DEFAULT true,
    frequency VARCHAR(50) DEFAULT 'normal', -- immediate, daily, weekly
    quiet_hours_start TIME,
    quiet_hours_end TIME,
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(customer_id)
);

-- Audit log for compliance
CREATE TABLE broadcast_audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    broadcast_id UUID REFERENCES broadcasts(id),
    action VARCHAR(100) NOT NULL,
    performed_by UUID REFERENCES users(id),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 4. UI/UX Design

### 4.1 Communication Dashboard Layout

```
┌────────────────────────────────────────────────────────────┐
│  📨 Communications                                Store: [x] │
├────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Quick Stats                                        │  │
│  │  📧 Emails Sent Today: 1,234  ✅ Delivered: 98.5%   │  │
│  │  💬 SMS Sent Today: 567      ✅ Delivered: 96.2%    │  │
│  │  🔔 Push Sent Today: 890     ✅ Delivered: 94.1%    │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─── Navigation Tabs ──────────────────────────────────┐  │
│  │ [New Broadcast] [Campaigns] [Templates] [Analytics]  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
└────────────────────────────────────────────────────────────┘
```

### 4.2 New Broadcast Flow

```
Step 1: Recipients
┌────────────────────────────────────────────────┐
│  Select Recipients                              │
│  ┌──────────────────────────────────────┐      │
│  │ 🔍 Filter Customers                   │      │
│  │  □ All Customers (1,234)              │      │
│  │  □ New Customers (Last 30 days)       │      │
│  │  □ VIP Customers                      │      │
│  │  □ Custom Segment                     │      │
│  │    ├─ Last Purchase: [Date Range]     │      │
│  │    ├─ Total Spent: [Min] - [Max]      │      │
│  │    ├─ Location: [City/Postal]         │      │
│  │    └─ Tags: [Select Tags]             │      │
│  └──────────────────────────────────────┘      │
│  Selected: 456 customers                        │
│                                [Next →]          │
└────────────────────────────────────────────────┘

Step 2: Message Composition
┌────────────────────────────────────────────────┐
│  Compose Message                                │
│  ┌──────────────────────────────────────┐      │
│  │ Campaign Name: [________________]     │      │
│  │                                        │      │
│  │ 📧 Email     □ Enable                 │      │
│  │   Subject: [_____________________]    │      │
│  │   Template: [Select Template ▼]       │      │
│  │   [Rich Text Editor]                   │      │
│  │                                        │      │
│  │ 💬 SMS       □ Enable                 │      │
│  │   [160 chars remaining]               │      │
│  │   [________________________]          │      │
│  │                                        │      │
│  │ 🔔 Push      □ Enable                 │      │
│  │   Title: [__________________]         │      │
│  │   Body: [___________________]          │      │
│  └──────────────────────────────────────┘      │
│                    [← Back] [Preview] [Next →]  │
└────────────────────────────────────────────────┘

Step 3: Schedule & Review
┌────────────────────────────────────────────────┐
│  Schedule & Review                              │
│  ┌──────────────────────────────────────┐      │
│  │ Send Time:                            │      │
│  │  ○ Send Now                           │      │
│  │  ○ Schedule for: [Date] [Time]        │      │
│  │  ○ Optimal Time (AI Suggested)        │      │
│  │                                        │      │
│  │ Summary:                               │      │
│  │  Recipients: 456 customers             │      │
│  │  Channels: Email, SMS                  │      │
│  │  Est. Cost: $23.40                     │      │
│  │  Est. Delivery Time: 5-10 mins         │      │
│  └──────────────────────────────────────┘      │
│                    [← Back] [Send Broadcast →]  │
└────────────────────────────────────────────────┘
```

### 4.3 Campaign Management View

```
┌────────────────────────────────────────────────────────────┐
│  Broadcast Campaigns                                        │
├────────────────────────────────────────────────────────────┤
│  [+ New Broadcast]  🔍 Search: [_________]  Filter: [All ▼]│
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ Campaign    | Status   | Sent    | Delivered | Actions│  │
│  ├─────────────────────────────────────────────────────┤  │
│  │ 🎄 Holiday  | ✅ Sent  | 1,234   | 98.5%     | [📊][✏️]│  │
│  │ 🎁 Flash Sale| 🕐 Sched | --      | --        | [✏️][🗑️]│  │
│  │ 📢 New Items| 📤 Sending| 567/890 | 95.2%     | [⏸️][📊]│  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────┘
```

## 5. API Endpoints

### 5.1 Broadcast Management
```
POST   /api/v1/communications/broadcasts          - Create broadcast
GET    /api/v1/communications/broadcasts          - List broadcasts
GET    /api/v1/communications/broadcasts/:id      - Get broadcast details
PUT    /api/v1/communications/broadcasts/:id      - Update broadcast
DELETE /api/v1/communications/broadcasts/:id      - Cancel broadcast
POST   /api/v1/communications/broadcasts/:id/send - Execute broadcast
POST   /api/v1/communications/broadcasts/:id/pause- Pause broadcast
```

### 5.2 Recipient Management
```
GET    /api/v1/communications/recipients          - List available recipients
POST   /api/v1/communications/recipients/filter   - Filter recipients
GET    /api/v1/communications/recipients/:id/prefs- Get preferences
PUT    /api/v1/communications/recipients/:id/prefs- Update preferences
```

### 5.3 Template Management
```
GET    /api/v1/communications/templates           - List templates
POST   /api/v1/communications/templates           - Create template
PUT    /api/v1/communications/templates/:id       - Update template
DELETE /api/v1/communications/templates/:id       - Delete template
POST   /api/v1/communications/templates/:id/preview - Preview template
```

### 5.4 Analytics
```
GET    /api/v1/communications/analytics/overview  - Dashboard stats
GET    /api/v1/communications/analytics/broadcast/:id - Broadcast analytics
GET    /api/v1/communications/analytics/engagement - Engagement metrics
```

## 6. Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- Database schema creation
- Base service interfaces
- Authentication/authorization
- Audit logging framework

### Phase 2: Channel Services (Week 2)
- Update Email service for broadcast
- Update SMS service for broadcast
- Implement Push notification service
- Rate limiting and retry logic

### Phase 3: Broadcast Service (Week 3)
- Broadcast orchestrator
- Recipient segmentation
- Template engine
- Scheduling system

### Phase 4: Frontend UI (Week 4)
- Communication dashboard
- Broadcast creation wizard
- Campaign management
- Analytics dashboard

### Phase 5: Testing & Optimization (Week 5)
- End-to-end testing
- Performance optimization
- Error handling
- Documentation

## 7. Security Considerations

### 7.1 Authentication & Authorization
- Role-based access control (Super Admin, Tenant Admin, Store Manager)
- Store-level data isolation
- API key management for external services

### 7.2 Data Protection
- PII encryption at rest
- Secure token storage
- GDPR compliance (opt-in/opt-out)
- Data retention policies

### 7.3 Rate Limiting
- Per-channel rate limits
- Per-store quotas
- Burst protection
- Graceful degradation

## 8. Performance Requirements

### 8.1 Scalability
- Handle 10,000+ recipients per broadcast
- Process 100+ messages/second per channel
- Queue-based async processing
- Horizontal scaling support

### 8.2 Reliability
- 99.9% uptime SLA
- Automatic retry with exponential backoff
- Dead letter queue for failed messages
- Circuit breaker pattern for external services

## 9. Monitoring & Analytics

### 9.1 Key Metrics
- Delivery rate by channel
- Open/click rates (email)
- Response rates (SMS)
- Engagement rates (push)
- Cost per message
- ROI per campaign

### 9.2 Alerting
- Failed broadcast alerts
- Low delivery rate warnings
- Rate limit approaching
- Service health checks

## 10. Compliance & Legal

### 10.1 Regulations
- CAN-SPAM compliance (email)
- TCPA compliance (SMS)
- CASL compliance (Canadian law)
- Opt-out management
- Unsubscribe handling

### 10.2 Audit Trail
- All actions logged
- Message content archived
- Consent tracking
- Compliance reporting