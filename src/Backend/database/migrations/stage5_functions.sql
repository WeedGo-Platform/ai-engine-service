CREATE OR REPLACE FUNCTION public.apply_discount_code(p_code character varying, p_user_id uuid, p_subtotal numeric, p_tenant_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_discount RECORD;
    v_usage_count INTEGER;
    v_discount_amount DECIMAL;
BEGIN
    -- Find valid discount code
    SELECT * INTO v_discount
    FROM discount_codes
    WHERE UPPER(code) = UPPER(p_code)
        AND is_active = TRUE
        AND (tenant_id = p_tenant_id OR tenant_id IS NULL)
        AND CURRENT_TIMESTAMP BETWEEN valid_from AND COALESCE(valid_until, CURRENT_TIMESTAMP + INTERVAL '1 day')
        AND p_subtotal >= minimum_purchase;
    
    IF NOT FOUND THEN
        RETURN jsonb_build_object(
            'success', FALSE,
            'message', 'Invalid or expired discount code'
        );
    END IF;
    
    -- Check usage limits
    IF v_discount.usage_limit IS NOT NULL AND v_discount.usage_count >= v_discount.usage_limit THEN
        RETURN jsonb_build_object(
            'success', FALSE,
            'message', 'Discount code usage limit reached'
        );
    END IF;
    
    -- Check per-customer usage limit
    IF p_user_id IS NOT NULL AND v_discount.usage_limit_per_customer IS NOT NULL THEN
        SELECT COUNT(*) INTO v_usage_count
        FROM discount_usage
        WHERE discount_id = v_discount.id AND user_id = p_user_id;
        
        IF v_usage_count >= v_discount.usage_limit_per_customer THEN
            RETURN jsonb_build_object(
                'success', FALSE,
                'message', 'You have already used this discount code'
            );
        END IF;
    END IF;
    
    -- Calculate discount amount
    IF v_discount.discount_type = 'percentage' THEN
        v_discount_amount := p_subtotal * (v_discount.discount_value / 100);
        IF v_discount.maximum_discount IS NOT NULL THEN
            v_discount_amount := LEAST(v_discount_amount, v_discount.maximum_discount);
        END IF;
    ELSIF v_discount.discount_type = 'fixed' THEN
        v_discount_amount := LEAST(v_discount.discount_value, p_subtotal);
    ELSE
        v_discount_amount := 0; -- Handle other types separately
    END IF;
    
    RETURN jsonb_build_object(
        'success', TRUE,
        'discount_id', v_discount.id,
        'discount_amount', ROUND(v_discount_amount, 2),
        'discount_type', v_discount.discount_type,
        'message', v_discount.description
    );
END;
$function$

;

CREATE OR REPLACE FUNCTION public.calculate_checkout_taxes(p_checkout_id uuid, p_subtotal numeric)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_tax_rate RECORD;
    v_province_id UUID;
    v_federal_tax DECIMAL;
    v_provincial_tax DECIMAL;
    v_excise_duty DECIMAL;
    v_total_tax DECIMAL;
BEGIN
    -- Get province from checkout session
    SELECT 
        COALESCE(
            s.province_territory_id,
            (checkout_sessions.delivery_address->>'province_id')::UUID
        ) INTO v_province_id
    FROM checkout_sessions
    LEFT JOIN stores s ON checkout_sessions.pickup_store_id = s.id
    WHERE checkout_sessions.id = p_checkout_id;
    
    -- Get applicable tax rates
    SELECT * INTO v_tax_rate
    FROM tax_rates
    WHERE province_territory_id = v_province_id
        AND is_active = TRUE
        AND CURRENT_DATE BETWEEN effective_from AND COALESCE(effective_to, CURRENT_DATE + INTERVAL '1 day')
    ORDER BY created_at DESC
    LIMIT 1;
    
    IF NOT FOUND THEN
        -- Default tax rates if not configured
        v_federal_tax := p_subtotal * 0.05; -- 5% GST
        v_provincial_tax := p_subtotal * 0.08; -- 8% PST (example)
        v_excise_duty := p_subtotal * 0.10; -- 10% excise (example)
    ELSE
        v_federal_tax := p_subtotal * v_tax_rate.federal_tax_rate;
        v_provincial_tax := p_subtotal * v_tax_rate.provincial_tax_rate;
        
        IF v_tax_rate.excise_calculation_method = 'percentage' THEN
            v_excise_duty := p_subtotal * (v_tax_rate.cannabis_excise_duty / 100);
        ELSE
            -- Would need to calculate based on weight
            v_excise_duty := v_tax_rate.cannabis_excise_duty;
        END IF;
    END IF;
    
    v_total_tax := v_federal_tax + v_provincial_tax + v_excise_duty;
    
    RETURN jsonb_build_object(
        'federal_tax', ROUND(v_federal_tax, 2),
        'provincial_tax', ROUND(v_provincial_tax, 2),
        'excise_duty', ROUND(v_excise_duty, 2),
        'total_tax', ROUND(v_total_tax, 2)
    );
END;
$function$

;

CREATE OR REPLACE FUNCTION public.calculate_distance(lat1 numeric, lon1 numeric, lat2 numeric, lon2 numeric)
 RETURNS numeric
 LANGUAGE plpgsql
AS $function$
DECLARE
    R CONSTANT DECIMAL := 6371; -- Earth radius in kilometers
    dlat DECIMAL;
    dlon DECIMAL;
    a DECIMAL;
    c DECIMAL;
BEGIN
    dlat := radians(lat2 - lat1);
    dlon := radians(lon2 - lon1);
    a := sin(dlat/2) * sin(dlat/2) +
         cos(radians(lat1)) * cos(radians(lat2)) *
         sin(dlon/2) * sin(dlon/2);
    c := 2 * atan2(sqrt(a), sqrt(1-a));
    RETURN R * c;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.calculate_final_price(p_product_id character varying, p_quantity integer, p_customer_id uuid, p_tenant_id uuid)
 RETURNS TABLE(base_price numeric, tier_discount numeric, promo_discount numeric, volume_discount numeric, final_price numeric)
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_base_price DECIMAL(10,2);
    v_tier_discount DECIMAL(10,2) := 0;
    v_promo_discount DECIMAL(10,2) := 0;
    v_volume_discount DECIMAL(10,2) := 0;
BEGIN
    -- Get base price from product catalog
    SELECT unit_price * p_quantity INTO v_base_price
    FROM product_catalog
    WHERE ocs_variant_number = p_product_id;
    
    -- Calculate tier discount
    SELECT COALESCE(MAX(pt.discount_percentage), 0) INTO v_tier_discount
    FROM customer_pricing_rules cpr
    JOIN price_tiers pt ON cpr.price_tier_id = pt.id
    WHERE cpr.tenant_id = p_tenant_id
    AND cpr.active = true;
    
    -- Calculate applicable promotions (simplified)
    SELECT COALESCE(MAX(discount_value), 0) INTO v_promo_discount
    FROM promotions
    WHERE active = true
    AND CURRENT_TIMESTAMP BETWEEN start_date AND COALESCE(end_date, CURRENT_TIMESTAMP + INTERVAL '1 day')
    AND (applies_to = 'all' OR p_product_id = ANY(product_ids));
    
    -- Calculate volume discount
    IF p_quantity >= 100 THEN
        v_volume_discount := 10;
    ELSIF p_quantity >= 50 THEN
        v_volume_discount := 7;
    ELSIF p_quantity >= 20 THEN
        v_volume_discount := 5;
    ELSIF p_quantity >= 10 THEN
        v_volume_discount := 3;
    END IF;
    
    RETURN QUERY
    SELECT 
        v_base_price,
        v_base_price * v_tier_discount / 100,
        v_base_price * v_promo_discount / 100,
        v_base_price * v_volume_discount / 100,
        v_base_price * (1 - (v_tier_discount + v_promo_discount + v_volume_discount) / 100);
END;
$function$

;

CREATE OR REPLACE FUNCTION public.calculate_holiday_date(p_year integer, p_holiday_id uuid)
 RETURNS date
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_holiday holidays%ROWTYPE;
    v_date DATE;
BEGIN
    SELECT * INTO v_holiday FROM holidays WHERE id = p_holiday_id;
    
    IF v_holiday.date_type = 'fixed' THEN
        v_date := make_date(p_year, v_holiday.fixed_month, v_holiday.fixed_day);
    ELSIF v_holiday.date_type = 'floating' THEN
        -- This would need more complex logic for floating dates
        -- Simplified example
        v_date := make_date(p_year, (v_holiday.floating_rule->>'month')::int, 1);
    ELSIF v_holiday.date_type = 'calculated' THEN
        -- Handle calculated dates like Easter
        -- This would require complex calculation
        v_date := make_date(p_year, 4, 1); -- Placeholder
    END IF;
    
    RETURN v_date;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.calculate_platform_fee(p_amount numeric, p_percentage_fee numeric, p_fixed_fee numeric)
 RETURNS TABLE(platform_fee numeric, tenant_net numeric)
 LANGUAGE plpgsql
AS $function$
BEGIN
    platform_fee := ROUND((p_amount * p_percentage_fee) + p_fixed_fee, 2);
    tenant_net := p_amount - platform_fee;
    RETURN NEXT;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.check_geofence_entry(point_lat numeric, point_lon numeric, fence_lat numeric, fence_lon numeric, fence_radius_meters integer)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    distance_km DECIMAL;
BEGIN
    distance_km := calculate_distance(point_lat, point_lon, fence_lat, fence_lon);
    RETURN (distance_km * 1000) <= fence_radius_meters;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.check_idempotency_key(p_key character varying, p_tenant_id uuid, p_request_hash character varying)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_result RECORD;
BEGIN
    -- Check for existing key
    SELECT status, response, request_hash
    INTO v_result
    FROM payment_idempotency_keys
    WHERE idempotency_key = p_key
    AND tenant_id = p_tenant_id
    AND expires_at > CURRENT_TIMESTAMP;
    
    IF v_result.status IS NOT NULL THEN
        -- Key exists, check if same request
        IF v_result.request_hash = p_request_hash THEN
            -- Same request, return cached response
            RETURN v_result.response;
        ELSE
            -- Different request with same key
            RAISE EXCEPTION 'Idempotency key already used for different request';
        END IF;
    END IF;
    
    -- Key doesn't exist, insert it
    INSERT INTO payment_idempotency_keys (
        idempotency_key, tenant_id, request_hash, status
    ) VALUES (
        p_key, p_tenant_id, p_request_hash, 'processing'
    );
    
    RETURN NULL;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.check_inventory_exists(p_sku character varying, p_batch_lot character varying)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_exists BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1 
        FROM batch_tracking 
        WHERE sku = p_sku 
        AND batch_lot = p_batch_lot 
        AND quantity_remaining > 0
    ) INTO v_exists;
    
    RETURN v_exists;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.check_otp_rate_limit(p_identifier character varying, p_identifier_type character varying, p_max_requests integer DEFAULT 5, p_window_minutes integer DEFAULT 60)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_rate_limit RECORD;
    v_window_start TIMESTAMP;
BEGIN
    v_window_start := CURRENT_TIMESTAMP - (p_window_minutes || ' minutes')::INTERVAL;
    
    -- Get or create rate limit record
    SELECT * INTO v_rate_limit
    FROM otp_rate_limits
    WHERE identifier = p_identifier 
    AND identifier_type = p_identifier_type;
    
    -- If blocked, check if block has expired
    IF v_rate_limit.blocked_until IS NOT NULL AND v_rate_limit.blocked_until > CURRENT_TIMESTAMP THEN
        RETURN FALSE;
    END IF;
    
    -- If no record exists, create one
    IF v_rate_limit.id IS NULL THEN
        INSERT INTO otp_rate_limits (identifier, identifier_type)
        VALUES (p_identifier, p_identifier_type);
        RETURN TRUE;
    END IF;
    
    -- Reset counter if outside window
    IF v_rate_limit.first_request_at < v_window_start THEN
        UPDATE otp_rate_limits
        SET request_count = 1,
            first_request_at = CURRENT_TIMESTAMP,
            last_request_at = CURRENT_TIMESTAMP,
            blocked_until = NULL
        WHERE id = v_rate_limit.id;
        RETURN TRUE;
    END IF;
    
    -- Check if limit exceeded
    IF v_rate_limit.request_count >= p_max_requests THEN
        -- Block for progressive duration
        UPDATE otp_rate_limits
        SET blocked_until = CURRENT_TIMESTAMP + (POWER(2, LEAST(v_rate_limit.request_count - p_max_requests + 1, 5)) || ' minutes')::INTERVAL
        WHERE id = v_rate_limit.id;
        RETURN FALSE;
    END IF;
    
    -- Increment counter
    UPDATE otp_rate_limits
    SET request_count = request_count + 1,
        last_request_at = CURRENT_TIMESTAMP
    WHERE id = v_rate_limit.id;
    
    RETURN TRUE;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.cleanup_expired_idempotency_keys()
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM payment_idempotency_keys
    WHERE expires_at < CURRENT_TIMESTAMP;
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.cleanup_expired_otp_codes()
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    DELETE FROM otp_codes 
    WHERE expires_at < CURRENT_TIMESTAMP 
    AND verified = FALSE;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.cleanup_expired_tokens()
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM auth_tokens
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days'
    OR (is_used = true AND used_at < CURRENT_TIMESTAMP - INTERVAL '30 days');

    GET DIAGNOSTICS v_deleted_count = ROW_COUNT;
    RETURN v_deleted_count;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.cleanup_old_audit_logs()
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_deleted INTEGER;
BEGIN
    DELETE FROM payment_audit_log
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
    GET DIAGNOSTICS v_deleted = ROW_COUNT;
    RETURN v_deleted;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.create_auth_token(p_user_id uuid, p_token_type character varying, p_token_hash character varying, p_expires_in_hours integer DEFAULT 24, p_metadata jsonb DEFAULT '{}'::jsonb)
 RETURNS uuid
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_token_id UUID;
BEGIN
    INSERT INTO auth_tokens (user_id, token_type, token_hash, expires_at, metadata)
    VALUES (
        p_user_id,
        p_token_type,
        p_token_hash,
        CURRENT_TIMESTAMP + (p_expires_in_hours || ' hours')::INTERVAL,
        p_metadata
    )
    RETURNING id INTO v_token_id;

    RETURN v_token_id;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.expire_checkout_sessions()
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    UPDATE checkout_sessions
    SET status = 'expired'
    WHERE status = 'draft'
        AND expires_at < CURRENT_TIMESTAMP;
    
    -- Release inventory reservations for expired sessions
    UPDATE inventory_reservations
    SET released = TRUE
    WHERE checkout_session_id IN (
        SELECT id FROM checkout_sessions
        WHERE status = 'expired'
    ) AND released = FALSE;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.generate_product_slug(p_brand text, p_product_name text, p_sub_category text, p_size text, p_colour text)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
DECLARE
    slug_parts TEXT[];
    result_slug TEXT;
BEGIN
    -- Initialize array
    slug_parts := ARRAY[]::TEXT[];
    
    -- Add brand if not null
    IF p_brand IS NOT NULL AND p_brand != '' THEN
        slug_parts := array_append(slug_parts, p_brand);
    END IF;
    
    -- Add product name if not null
    IF p_product_name IS NOT NULL AND p_product_name != '' THEN
        slug_parts := array_append(slug_parts, p_product_name);
    END IF;
    
    -- Add sub-category if not null
    IF p_sub_category IS NOT NULL AND p_sub_category != '' THEN
        slug_parts := array_append(slug_parts, p_sub_category);
    END IF;
    
    -- Add size if not null
    IF p_size IS NOT NULL AND p_size != '' THEN
        slug_parts := array_append(slug_parts, p_size);
    END IF;
    
    -- Add colour if not null (optional field)
    IF p_colour IS NOT NULL AND p_colour != '' THEN
        slug_parts := array_append(slug_parts, p_colour);
    END IF;
    
    -- Join parts with hyphen
    result_slug := array_to_string(slug_parts, '-');
    
    -- Clean up the slug
    -- Convert to lowercase
    result_slug := lower(result_slug);
    -- Replace spaces and special characters with hyphens
    result_slug := regexp_replace(result_slug, '[^a-z0-9-]+', '-', 'g');
    -- Remove multiple consecutive hyphens
    result_slug := regexp_replace(result_slug, '-+', '-', 'g');
    -- Remove leading and trailing hyphens
    result_slug := trim(BOTH '-' FROM result_slug);
    
    RETURN result_slug;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_staff_active_deliveries(staff_id uuid)
 RETURNS TABLE(delivery_id uuid, order_id uuid, customer_name character varying, delivery_address jsonb, status delivery_status, estimated_time timestamp without time zone)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        d.id,
        d.order_id,
        d.customer_name,
        d.delivery_address,
        d.status,
        d.estimated_delivery_time
    FROM deliveries d
    WHERE d.assigned_to = staff_id
    AND d.status NOT IN ('completed', 'failed', 'cancelled')
    ORDER BY d.scheduled_at, d.created_at;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_store_ai_config(p_store_id uuid, p_agent_name text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF p_agent_name IS NOT NULL THEN
        RETURN (
            SELECT value->p_agent_name
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'ai'
            AND key = 'agents'
        );
    ELSE
        RETURN (
            SELECT value
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'ai'
            AND key = 'agents'
        );
    END IF;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_store_hours(p_store_id uuid, p_day_of_week text DEFAULT NULL::text)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF p_day_of_week IS NOT NULL THEN
        RETURN (
            SELECT value->lower(p_day_of_week)
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'hours'
            AND key = 'regular_hours'
        );
    ELSE
        RETURN (
            SELECT value
            FROM store_settings
            WHERE store_id = p_store_id
            AND category = 'hours'
            AND key = 'regular_hours'
        );
    END IF;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_tenant_primary_provider(p_tenant_id uuid, p_provider_type character varying DEFAULT NULL::character varying)
 RETURNS uuid
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_provider_id UUID;
BEGIN
    SELECT tpp.id INTO v_provider_id
    FROM tenant_payment_providers tpp
    JOIN payment_providers pp ON tpp.provider_id = pp.id
    WHERE tpp.tenant_id = p_tenant_id
    AND tpp.is_active = true
    AND tpp.is_primary = true
    AND (p_provider_type IS NULL OR pp.provider_type = p_provider_type)
    LIMIT 1;
    
    -- If no primary, get first active
    IF v_provider_id IS NULL THEN
        SELECT tpp.id INTO v_provider_id
        FROM tenant_payment_providers tpp
        JOIN payment_providers pp ON tpp.provider_id = pp.id
        WHERE tpp.tenant_id = p_tenant_id
        AND tpp.is_active = true
        AND (p_provider_type IS NULL OR pp.provider_type = p_provider_type)
        ORDER BY tpp.created_at
        LIMIT 1;
    END IF;
    
    RETURN v_provider_id;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_user_context(user_id_param uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    result jsonb;
BEGIN
    SELECT jsonb_build_object(
        'user', jsonb_build_object(
            'id', u.id,
            'email', u.email,
            'first_name', u.first_name,
            'last_name', u.last_name,
            'role', u.role,
            'tenant_id', u.tenant_id,
            'store_id', u.store_id,
            'active', u.active
        ),
        'tenant', CASE 
            WHEN u.tenant_id IS NOT NULL THEN jsonb_build_object(
                'id', t.id,
                'name', t.name
            )
            ELSE NULL
        END,
        'store', CASE 
            WHEN u.store_id IS NOT NULL THEN jsonb_build_object(
                'id', s.id,
                'name', s.name,
                'store_code', s.store_code
            )
            ELSE NULL
        END,
        'permissions', (
            SELECT jsonb_agg(resource_type || ':' || action)
            FROM role_permissions 
            WHERE role = u.role AND granted = true
        )
    ) INTO result
    FROM users u
    LEFT JOIN tenants t ON u.tenant_id = t.id
    LEFT JOIN stores s ON u.store_id = s.id
    WHERE u.id = user_id_param;
    
    RETURN result;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_user_login_stats(p_user_id uuid)
 RETURNS TABLE(total_logins integer, successful_logins integer, failed_logins integer, unique_ips integer, unique_countries integer, last_login timestamp with time zone, most_common_ip inet, most_common_country character varying)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_logins,
        COUNT(*) FILTER (WHERE login_successful = true)::INTEGER as successful_logins,
        COUNT(*) FILTER (WHERE login_successful = false)::INTEGER as failed_logins,
        COUNT(DISTINCT ip_address)::INTEGER as unique_ips,
        COUNT(DISTINCT country)::INTEGER as unique_countries,
        MAX(login_timestamp) as last_login,
        MODE() WITHIN GROUP (ORDER BY ip_address) as most_common_ip,
        MODE() WITHIN GROUP (ORDER BY country) as most_common_country
    FROM user_login_logs
    WHERE user_id = p_user_id;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.get_wishlist_stats(p_customer_id uuid)
 RETURNS TABLE(total_items integer, high_priority_items integer, on_sale_items integer, out_of_stock_items integer, total_value numeric)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::INTEGER as total_items,
        COUNT(CASE WHEN w.priority = 1 THEN 1 END)::INTEGER as high_priority_items,
        0::INTEGER as on_sale_items, -- Sales tracking would need separate table
        COUNT(CASE WHEN p.quantity_available = 0 OR p.is_available = false THEN 1 END)::INTEGER as out_of_stock_items,
        COALESCE(SUM(COALESCE(p.retail_price, p.unit_price)), 0)::DECIMAL as total_value
    FROM wishlist w
    LEFT JOIN comprehensive_product_inventory_view p
        ON w.product_id = p.product_id
        AND w.store_id = p.store_id
    WHERE w.customer_id = p_customer_id;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.gin_extract_query_trgm(text, internal, smallint, internal, internal, internal, internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gin_extract_query_trgm$function$

;

CREATE OR REPLACE FUNCTION public.gin_extract_value_trgm(text, internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gin_extract_value_trgm$function$

;

CREATE OR REPLACE FUNCTION public.gin_trgm_consistent(internal, smallint, text, integer, internal, internal, internal, internal)
 RETURNS boolean
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gin_trgm_consistent$function$

;

CREATE OR REPLACE FUNCTION public.gin_trgm_triconsistent(internal, smallint, text, integer, internal, internal, internal)
 RETURNS "char"
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gin_trgm_triconsistent$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_compress(internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_compress$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_consistent(internal, text, smallint, oid, internal)
 RETURNS boolean
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_consistent$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_decompress(internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_decompress$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_distance(internal, text, smallint, oid, internal)
 RETURNS double precision
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_distance$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_in(cstring)
 RETURNS gtrgm
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_in$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_options(internal)
 RETURNS void
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE
AS '$libdir/pg_trgm', $function$gtrgm_options$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_out(gtrgm)
 RETURNS cstring
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_out$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_penalty(internal, internal, internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_penalty$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_picksplit(internal, internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_picksplit$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_same(gtrgm, gtrgm, internal)
 RETURNS internal
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_same$function$

;

CREATE OR REPLACE FUNCTION public.gtrgm_union(internal, internal)
 RETURNS gtrgm
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$gtrgm_union$function$

;

CREATE OR REPLACE FUNCTION public.is_promotion_active_now(p_id uuid, p_current_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    promo RECORD;
    current_day INTEGER;
    current_time_only TIME;
    is_active BOOLEAN := false;
BEGIN
    -- Get promotion details
    SELECT * INTO promo FROM promotions WHERE id = p_id;

    IF NOT FOUND OR NOT promo.active THEN
        RETURN false;
    END IF;

    -- Convert timestamp to timezone-aware time
    current_day := EXTRACT(DOW FROM p_current_time AT TIME ZONE promo.timezone);
    current_time_only := (p_current_time AT TIME ZONE promo.timezone)::TIME;

    -- Check 1: Date range
    IF promo.start_date > p_current_time THEN
        RETURN false;
    END IF;

    IF NOT promo.is_continuous AND promo.end_date IS NOT NULL AND promo.end_date < p_current_time THEN
        RETURN false;
    END IF;

    -- Check 2: Day of week (if specified)
    IF promo.day_of_week IS NOT NULL AND array_length(promo.day_of_week, 1) > 0 THEN
        IF NOT (current_day = ANY(promo.day_of_week)) THEN
            RETURN false;
        END IF;
    END IF;

    -- Check 3: Time window (if specified)
    IF promo.time_start IS NOT NULL AND promo.time_end IS NOT NULL THEN
        IF NOT (current_time_only >= promo.time_start AND current_time_only <= promo.time_end) THEN
            RETURN false;
        END IF;
    END IF;

    RETURN true;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.is_store_open(p_store_id uuid, p_datetime timestamp without time zone)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_date DATE;
    v_time TIME;
    v_day_of_week INTEGER;
    v_is_holiday BOOLEAN;
    v_special_hours store_special_hours%ROWTYPE;
    v_regular_hours store_regular_hours%ROWTYPE;
BEGIN
    v_date := p_datetime::DATE;
    v_time := p_datetime::TIME;
    v_day_of_week := EXTRACT(DOW FROM v_date);
    
    -- Check special hours first
    SELECT * INTO v_special_hours 
    FROM store_special_hours 
    WHERE store_id = p_store_id AND date = v_date;
    
    IF FOUND THEN
        IF v_special_hours.is_closed THEN
            RETURN FALSE;
        END IF;
        RETURN v_time >= v_special_hours.open_time AND v_time <= v_special_hours.close_time;
    END IF;
    
    -- Check holidays
    -- (Simplified - would need more complex logic)
    
    -- Check regular hours
    SELECT * INTO v_regular_hours
    FROM store_regular_hours
    WHERE store_id = p_store_id AND day_of_week = v_day_of_week;
    
    IF v_regular_hours.is_closed THEN
        RETURN FALSE;
    END IF;
    
    -- Check against time slots
    -- (Would need to check JSON array of time slots)
    
    RETURN TRUE; -- Simplified
END;
$function$

;

CREATE OR REPLACE FUNCTION public.log_delivery_event(p_delivery_id uuid, p_event_type character varying, p_event_data jsonb DEFAULT '{}'::jsonb, p_user_id uuid DEFAULT NULL::uuid)
 RETURNS uuid
 LANGUAGE plpgsql
AS $function$
DECLARE
    event_id UUID;
BEGIN
    INSERT INTO delivery_events (delivery_id, event_type, event_data, performed_by)
    VALUES (p_delivery_id, p_event_type, p_event_data, p_user_id)
    RETURNING id INTO event_id;

    RETURN event_id;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.process_asn_to_purchase_order(p_session_id character varying, p_po_number character varying, p_supplier_id uuid, p_expected_date date, p_notes text DEFAULT NULL::text)
 RETURNS uuid
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_po_id UUID;
    v_shipment_id VARCHAR;
    v_container_id VARCHAR;
    v_vendor VARCHAR;
    v_total_amount DECIMAL(12,2);
    v_item RECORD;
BEGIN
    -- Get common values from staging
    SELECT DISTINCT 
        shipment_id, 
        container_id, 
        vendor 
    INTO v_shipment_id, v_container_id, v_vendor
    FROM asn_import_staging
    WHERE session_id = p_session_id
    LIMIT 1;
    
    -- Calculate total amount
    SELECT SUM(unit_price * shipped_qty) INTO v_total_amount
    FROM asn_import_staging
    WHERE session_id = p_session_id;
    
    -- Create purchase order
    INSERT INTO purchase_orders (
        po_number,
        supplier_id,
        total_amount,
        status,
        expected_date,
        notes,
        shipment_id,
        container_id,
        vendor
    ) VALUES (
        p_po_number,
        p_supplier_id,
        COALESCE(v_total_amount, 0),
        'pending',
        p_expected_date,
        p_notes,
        v_shipment_id,
        v_container_id,
        v_vendor
    ) RETURNING id INTO v_po_id;
    
    -- Create purchase order items
    FOR v_item IN 
        SELECT * FROM asn_import_staging 
        WHERE session_id = p_session_id
    LOOP
        INSERT INTO purchase_order_items (
            purchase_order_id,
            sku,
            item_name,
            quantity,
            unit_cost,
            total,
            batch_lot,
            expiry_date,
            case_gtin,
            gtin_barcode,
            each_gtin,
            shipped_qty,
            uom,
            uom_conversion,
            exists_in_inventory
        ) VALUES (
            v_po_id,
            v_item.sku,
            v_item.item_name,
            v_item.shipped_qty,
            v_item.unit_price,
            v_item.unit_price * v_item.shipped_qty,
            v_item.batch_lot,
            v_item.expiry_date,
            v_item.case_gtin,
            v_item.gtin_barcode,
            v_item.each_gtin,
            v_item.shipped_qty,
            v_item.uom,
            v_item.uom_conversion,
            v_item.exists_in_inventory
        );
    END LOOP;
    
    -- Clear staging data
    DELETE FROM asn_import_staging WHERE session_id = p_session_id;
    
    RETURN v_po_id;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.process_purchase_order_receipt(p_po_id uuid, p_items jsonb)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_item JSONB;
    v_sku VARCHAR(100);
    v_quantity INTEGER;
    v_unit_cost DECIMAL(10,2);
    v_batch_lot VARCHAR(100);
    v_result JSONB = '[]'::JSONB;
BEGIN
    -- Process each item in the purchase order
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_items)
    LOOP
        v_sku := v_item->>'sku';
        v_quantity := (v_item->>'quantity')::INTEGER;
        v_unit_cost := (v_item->>'unit_cost')::DECIMAL;
        v_batch_lot := v_item->>'batch_lot';
        
        -- Update or insert inventory record
        INSERT INTO inventory (sku, quantity_on_hand, quantity_available, unit_cost, last_restock_date)
        VALUES (v_sku, v_quantity, v_quantity, v_unit_cost, CURRENT_TIMESTAMP)
        ON CONFLICT (sku) DO UPDATE
        SET 
            quantity_on_hand = inventory.quantity_on_hand + v_quantity,
            quantity_available = inventory.quantity_available + v_quantity,
            unit_cost = ((inventory.quantity_on_hand * inventory.unit_cost) + (v_quantity * v_unit_cost)) 
                        / (inventory.quantity_on_hand + v_quantity),
            last_restock_date = CURRENT_TIMESTAMP;
        
        -- Record inventory transaction
        INSERT INTO inventory_transactions (
            sku, transaction_type, reference_id, reference_type, 
            batch_lot, quantity, unit_cost, running_balance
        )
        SELECT 
            v_sku, 'purchase', p_po_id, 'purchase_order',
            v_batch_lot, v_quantity, v_unit_cost, quantity_on_hand
        FROM inventory
        WHERE sku = v_sku;
        
        -- Track batch/lot
        IF v_batch_lot IS NOT NULL THEN
            INSERT INTO batch_tracking (
                batch_lot, sku, purchase_order_id, 
                quantity_received, quantity_remaining, unit_cost
            )
            VALUES (
                v_batch_lot, v_sku, p_po_id,
                v_quantity, v_quantity, v_unit_cost
            );
        END IF;
        
        v_result := v_result || jsonb_build_object('sku', v_sku, 'processed', true);
    END LOOP;
    
    -- Update purchase order status
    UPDATE purchase_orders
    SET status = 'received', received_date = CURRENT_TIMESTAMP
    WHERE id = p_po_id;
    
    RETURN v_result;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.receive_purchase_order(p_po_id uuid)
 RETURNS jsonb
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_item RECORD;
    v_result JSONB = '{"status": "success", "items_processed": []}'::JSONB;
    v_items_array JSONB = '[]'::JSONB;
BEGIN
    -- Update purchase order status
    UPDATE purchase_orders
    SET status = 'received',
        received_date = CURRENT_TIMESTAMP
    WHERE id = p_po_id;
    
    -- Process each item
    FOR v_item IN 
        SELECT * FROM purchase_order_items 
        WHERE purchase_order_id = p_po_id
    LOOP
        -- Update inventory
        INSERT INTO inventory (sku, quantity_on_hand, quantity_available, unit_cost, last_restock_date)
        VALUES (v_item.sku, v_item.shipped_qty, v_item.shipped_qty, v_item.unit_cost, CURRENT_TIMESTAMP)
        ON CONFLICT (sku) DO UPDATE
        SET 
            quantity_on_hand = inventory.quantity_on_hand + v_item.shipped_qty,
            quantity_available = inventory.quantity_available + v_item.shipped_qty,
            unit_cost = v_item.unit_cost,
            last_restock_date = CURRENT_TIMESTAMP;
        
        -- Update batch tracking WITH GTIN columns
        INSERT INTO batch_tracking (
            sku,
            batch_lot,
            purchase_order_id,
            quantity_received,
            quantity_remaining,
            unit_cost,
            expiry_date,
            case_gtin,
            gtin_barcode,
            each_gtin
        ) VALUES (
            v_item.sku,
            v_item.batch_lot,
            p_po_id,
            v_item.shipped_qty,
            v_item.shipped_qty,
            v_item.unit_cost,
            v_item.expiry_date,
            v_item.case_gtin,
            v_item.gtin_barcode,
            v_item.each_gtin
        );
        
        -- Record inventory transaction
        INSERT INTO inventory_transactions (
            sku,
            transaction_type,
            quantity,
            reference_type,
            reference_id,
            notes
        ) VALUES (
            v_item.sku,
            'purchase',
            v_item.shipped_qty,
            'purchase_order',
            p_po_id,
            'Received from PO'
        );
        
        -- Add item to result
        v_items_array = v_items_array || jsonb_build_object(
            'sku', v_item.sku,
            'quantity', v_item.shipped_qty,
            'status', 'received'
        );
    END LOOP;
    
    v_result = v_result || jsonb_build_object('items_processed', v_items_array);
    
    RETURN v_result;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.refresh_review_summary()
 RETURNS void
 LANGUAGE plpgsql
AS $function$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY review_summary_view;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.set_limit(real)
 RETURNS real
 LANGUAGE c
 STRICT
AS '$libdir/pg_trgm', $function$set_limit$function$

;

CREATE OR REPLACE FUNCTION public.show_limit()
 RETURNS real
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$show_limit$function$

;

CREATE OR REPLACE FUNCTION public.show_trgm(text)
 RETURNS text[]
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$show_trgm$function$

;

CREATE OR REPLACE FUNCTION public.similarity(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$similarity$function$

;

CREATE OR REPLACE FUNCTION public.similarity_dist(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$similarity_dist$function$

;

CREATE OR REPLACE FUNCTION public.similarity_op(text, text)
 RETURNS boolean
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$similarity_op$function$

;

CREATE OR REPLACE FUNCTION public.strict_word_similarity(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$strict_word_similarity$function$

;

CREATE OR REPLACE FUNCTION public.strict_word_similarity_commutator_op(text, text)
 RETURNS boolean
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$strict_word_similarity_commutator_op$function$

;

CREATE OR REPLACE FUNCTION public.strict_word_similarity_dist_commutator_op(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$strict_word_similarity_dist_commutator_op$function$

;

CREATE OR REPLACE FUNCTION public.strict_word_similarity_dist_op(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$strict_word_similarity_dist_op$function$

;

CREATE OR REPLACE FUNCTION public.strict_word_similarity_op(text, text)
 RETURNS boolean
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$strict_word_similarity_op$function$

;

CREATE OR REPLACE FUNCTION public.unaccent(regdictionary, text)
 RETURNS text
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/unaccent', $function$unaccent_dict$function$

;

CREATE OR REPLACE FUNCTION public.unaccent_init(internal)
 RETURNS internal
 LANGUAGE c
 PARALLEL SAFE
AS '$libdir/unaccent', $function$unaccent_init$function$

;

CREATE OR REPLACE FUNCTION public.unaccent_lexize(internal, internal, internal, internal)
 RETURNS internal
 LANGUAGE c
 PARALLEL SAFE
AS '$libdir/unaccent', $function$unaccent_lexize$function$

;

CREATE OR REPLACE FUNCTION public.update_checkout_session_timestamp()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_inventory_movements_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_inventory_timestamp()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_pricing_rules_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_product_catalog_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_product_rating()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_avg_rating DECIMAL(2,1);
    v_total_reviews INTEGER;
    v_rating_dist JSONB;
    v_verified_count INTEGER;
    v_recommended_pct DECIMAL(5,2);
BEGIN
    -- Calculate aggregated values for the product
    WITH review_stats AS (
        SELECT
            AVG(rating)::DECIMAL(2,1) as avg_rating,
            COUNT(*) as total_reviews,
            COUNT(*) FILTER (WHERE is_verified_purchase = true) as verified_count,
            (COUNT(*) FILTER (WHERE is_recommended = true) * 100.0 / NULLIF(COUNT(*), 0))::DECIMAL(5,2) as recommended_pct,
            jsonb_build_object(
                '5', COUNT(*) FILTER (WHERE rating = 5),
                '4', COUNT(*) FILTER (WHERE rating = 4),
                '3', COUNT(*) FILTER (WHERE rating = 3),
                '2', COUNT(*) FILTER (WHERE rating = 2),
                '1', COUNT(*) FILTER (WHERE rating = 1)
            ) as rating_distribution
        FROM customer_reviews
        WHERE sku = COALESCE(NEW.sku, OLD.sku)
            AND status = 'approved'
    )
    SELECT
        COALESCE(avg_rating, 0),
        COALESCE(total_reviews, 0),
        rating_distribution,
        COALESCE(verified_count, 0),
        COALESCE(recommended_pct, 0)
    INTO
        v_avg_rating,
        v_total_reviews,
        v_rating_dist,
        v_verified_count,
        v_recommended_pct
    FROM review_stats;

    -- Update or insert product rating
    INSERT INTO product_ratings (
        sku,
        average_rating,
        total_reviews,
        rating_distribution,
        verified_purchase_count,
        recommended_percentage,
        last_updated
    ) VALUES (
        COALESCE(NEW.sku, OLD.sku),
        v_avg_rating,
        v_total_reviews,
        v_rating_dist,
        v_verified_count,
        v_recommended_pct,
        CURRENT_TIMESTAMP
    )
    ON CONFLICT (sku) DO UPDATE SET
        average_rating = EXCLUDED.average_rating,
        total_reviews = EXCLUDED.total_reviews,
        rating_distribution = EXCLUDED.rating_distribution,
        verified_purchase_count = EXCLUDED.verified_purchase_count,
        recommended_percentage = EXCLUDED.recommended_percentage,
        last_updated = EXCLUDED.last_updated;

    RETURN COALESCE(NEW, OLD);
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_review_vote_counts()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    -- Update helpful and not_helpful counts
    UPDATE customer_reviews
    SET
        helpful_count = (
            SELECT COUNT(*)
            FROM review_votes
            WHERE review_id = COALESCE(NEW.review_id, OLD.review_id)
                AND vote_type = 'helpful'
        ),
        not_helpful_count = (
            SELECT COUNT(*)
            FROM review_votes
            WHERE review_id = COALESCE(NEW.review_id, OLD.review_id)
                AND vote_type = 'not_helpful'
        ),
        updated_at = CURRENT_TIMESTAMP
    WHERE id = COALESCE(NEW.review_id, OLD.review_id);

    RETURN COALESCE(NEW, OLD);
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_system_settings_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_translation_usage()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    UPDATE translations 
    SET usage_count = usage_count + 1,
        last_used_at = CURRENT_TIMESTAMP
    WHERE id = NEW.id;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_user_last_login()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    IF NEW.login_successful = true THEN
        UPDATE users 
        SET 
            last_login_ip = NEW.ip_address,
            last_login_at = NEW.login_timestamp,
            last_login_location = jsonb_build_object(
                'country', NEW.country,
                'region', NEW.region,
                'city', NEW.city,
                'postal_code', NEW.postal_code,
                'latitude', NEW.latitude,
                'longitude', NEW.longitude,
                'timezone', NEW.timezone,
                'isp', NEW.isp
            ),
            login_count = COALESCE(login_count, 0) + 1,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = NEW.user_id;
    END IF;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.update_user_payment_methods_updated_at()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.user_has_permission(user_id_param uuid, resource_type_param character varying, action_param character varying)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
DECLARE
    user_rec record;
    has_perm boolean := false;
BEGIN
    -- Get user info
    SELECT role, tenant_id, store_id, permissions_override
    INTO user_rec
    FROM users 
    WHERE id = user_id_param AND active = true;
    
    IF NOT FOUND THEN
        RETURN false;
    END IF;
    
    -- Check override permissions first
    IF user_rec.permissions_override ? (resource_type_param || ':' || action_param) THEN
        RETURN (user_rec.permissions_override->>(resource_type_param || ':' || action_param))::boolean;
    END IF;
    
    -- Check role-based permissions
    SELECT granted INTO has_perm
    FROM role_permissions 
    WHERE role = user_rec.role 
      AND (resource_type = resource_type_param OR resource_type = '*')
      AND (action = action_param OR action = '*')
    ORDER BY 
        CASE WHEN resource_type = '*' THEN 1 ELSE 0 END,
        CASE WHEN action = '*' THEN 1 ELSE 0 END
    LIMIT 1;
    
    RETURN COALESCE(has_perm, false);
END;
$function$

;

CREATE OR REPLACE FUNCTION public.uuid_generate_v1()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v1$function$

;

CREATE OR REPLACE FUNCTION public.uuid_generate_v1mc()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v1mc$function$

;

CREATE OR REPLACE FUNCTION public.uuid_generate_v3(namespace uuid, name text)
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v3$function$

;

CREATE OR REPLACE FUNCTION public.uuid_generate_v4()
 RETURNS uuid
 LANGUAGE c
 PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v4$function$

;

CREATE OR REPLACE FUNCTION public.uuid_generate_v5(namespace uuid, name text)
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_generate_v5$function$

;

CREATE OR REPLACE FUNCTION public.uuid_nil()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_nil$function$

;

CREATE OR REPLACE FUNCTION public.uuid_ns_dns()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_dns$function$

;

CREATE OR REPLACE FUNCTION public.uuid_ns_oid()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_oid$function$

;

CREATE OR REPLACE FUNCTION public.uuid_ns_url()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_url$function$

;

CREATE OR REPLACE FUNCTION public.uuid_ns_x500()
 RETURNS uuid
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/uuid-ossp', $function$uuid_ns_x500$function$

;

CREATE OR REPLACE FUNCTION public.validate_auth_token(p_token_hash character varying, p_token_type character varying, p_mark_as_used boolean DEFAULT false)
 RETURNS TABLE(is_valid boolean, user_id uuid, metadata jsonb)
 LANGUAGE plpgsql
AS $function$
BEGIN
    RETURN QUERY
    WITH token_check AS (
        SELECT
            at.user_id,
            at.metadata,
            at.expires_at > CURRENT_TIMESTAMP AND at.is_used = false as valid
        FROM auth_tokens at
        WHERE at.token_hash = p_token_hash
        AND at.token_type = p_token_type
    )
    SELECT
        COALESCE(tc.valid, false) as is_valid,
        tc.user_id,
        tc.metadata
    FROM token_check tc;

    -- Mark token as used if requested and valid
    IF p_mark_as_used THEN
        UPDATE auth_tokens
        SET is_used = true, used_at = CURRENT_TIMESTAMP
        WHERE token_hash = p_token_hash
        AND token_type = p_token_type
        AND expires_at > CURRENT_TIMESTAMP
        AND is_used = false;
    END IF;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.validate_verified_purchase()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
DECLARE
    v_has_purchase BOOLEAN;
BEGIN
    -- Check if the user has purchased this product
    IF NEW.order_id IS NOT NULL THEN
        SELECT EXISTS (
            SELECT 1
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.id = NEW.order_id
                AND o.user_id = NEW.user_id
                AND oi.sku = NEW.sku
                AND o.status IN ('completed', 'delivered')
        ) INTO v_has_purchase;

        NEW.is_verified_purchase := v_has_purchase;
    ELSE
        -- Check for any completed order with this product
        SELECT EXISTS (
            SELECT 1
            FROM order_items oi
            JOIN orders o ON o.id = oi.order_id
            WHERE o.user_id = NEW.user_id
                AND oi.sku = NEW.sku
                AND o.status IN ('completed', 'delivered')
        ) INTO v_has_purchase;

        NEW.is_verified_purchase := v_has_purchase;
    END IF;

    RETURN NEW;
END;
$function$

;

CREATE OR REPLACE FUNCTION public.word_similarity(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$word_similarity$function$

;

CREATE OR REPLACE FUNCTION public.word_similarity_commutator_op(text, text)
 RETURNS boolean
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$word_similarity_commutator_op$function$

;

CREATE OR REPLACE FUNCTION public.word_similarity_dist_commutator_op(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$word_similarity_dist_commutator_op$function$

;

CREATE OR REPLACE FUNCTION public.word_similarity_dist_op(text, text)
 RETURNS real
 LANGUAGE c
 IMMUTABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$word_similarity_dist_op$function$

;

CREATE OR REPLACE FUNCTION public.word_similarity_op(text, text)
 RETURNS boolean
 LANGUAGE c
 STABLE PARALLEL SAFE STRICT
AS '$libdir/pg_trgm', $function$word_similarity_op$function$

;

-- ============================================================================
SELECT 'Stage 5: Functions created' AS status;
