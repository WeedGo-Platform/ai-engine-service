CREATE OR REPLACE VIEW recent_login_activity AS
 SELECT ull.id,
    ull.user_id,
    u.email,
    (((u.first_name)::text || ' '::text) || (u.last_name)::text) AS full_name,
    ull.tenant_id,
    t.name AS tenant_name,
    ull.login_timestamp,
    ull.login_successful,
    ull.login_method,
    ull.ip_address,
    ull.country,
    ull.city,
    ull.user_agent
   FROM ((user_login_logs ull
     JOIN users u ON ((ull.user_id = u.id)))
     LEFT JOIN tenants t ON ((ull.tenant_id = t.id)))
  WHERE (ull.login_timestamp > (CURRENT_TIMESTAMP - '30 days'::interval))
  ORDER BY ull.login_timestamp DESC;
;

-- ============================================================================
SELECT 'Stage 4: Views created' AS status;
