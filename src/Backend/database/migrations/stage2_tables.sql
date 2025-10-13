CREATE TABLE IF NOT EXISTS agi_audit_aggregates (
    id integer NOT NULL DEFAULT nextval('agi_audit_aggregates_id_seq'::regclass),
    period_start timestamp with time zone NOT NULL,
    period_end timestamp with time zone NOT NULL,
    event_type text NOT NULL,
    severity text,
    count bigint NOT NULL DEFAULT 0,
    unique_users integer DEFAULT 0,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agi_audit_alerts (
    id integer NOT NULL DEFAULT nextval('agi_audit_alerts_id_seq'::regclass),
    alert_type text NOT NULL,
    severity text NOT NULL,
    event_count integer NOT NULL,
    time_window_minutes integer NOT NULL,
    triggered_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    resolved_at timestamp with time zone,
    alert_data jsonb DEFAULT '{}'::jsonb,
    acknowledged boolean DEFAULT false,
    acknowledged_by text,
    acknowledged_at timestamp with time zone
);

CREATE TABLE IF NOT EXISTS agi_audit_logs (
    id bigint NOT NULL DEFAULT nextval('agi_audit_logs_id_seq'::regclass),
    event_type text NOT NULL,
    severity text NOT NULL,
    user_id text,
    session_id text,
    resource_type text,
    resource_id text,
    action text,
    result text,
    ip_address text,
    user_agent text,
    error_message text,
    stack_trace text,
    metadata jsonb DEFAULT '{}'::jsonb,
    event_hash text NOT NULL,
    timestamp timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agi_rate_limit_buckets (
    key text NOT NULL,
    tokens double precision NOT NULL,
    last_update timestamp with time zone NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS agi_rate_limit_rules (
    name text NOT NULL,
    scope text NOT NULL,
    strategy text NOT NULL,
    limit_value integer NOT NULL,
    window_seconds integer NOT NULL,
    burst_size integer,
    priority integer DEFAULT 0,
    enabled boolean DEFAULT true,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS agi_rate_limit_violations (
    id integer NOT NULL DEFAULT nextval('agi_rate_limit_violations_id_seq'::regclass),
    rule_name text NOT NULL,
    identifier text NOT NULL,
    resource text,
    attempts integer NOT NULL,
    window_start timestamp with time zone NOT NULL,
    window_end timestamp with time zone NOT NULL,
    metadata jsonb DEFAULT '{}'::jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================

SELECT 'Stage 2: Tables created successfully' AS status;
