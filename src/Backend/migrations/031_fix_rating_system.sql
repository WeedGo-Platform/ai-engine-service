-- =============================================
-- Migration: Fix Rating System Issues
-- Author: System
-- Date: 2025-01-16
-- Description: Fix materialized view and data migration for rating system
-- =============================================

-- =============================================
-- 1. CREATE MATERIALIZED VIEW (Fixed version)
-- =============================================
CREATE MATERIALIZED VIEW IF NOT EXISTS review_summary_view AS
WITH recent_reviews AS (
    SELECT
        cr.sku,
        jsonb_agg(
            jsonb_build_object(
                'id', cr.id,
                'rating', cr.rating,
                'title', cr.title,
                'review_text', cr.review_text,
                'user_name', u.first_name || ' ' || LEFT(u.last_name, 1) || '.',
                'is_verified_purchase', cr.is_verified_purchase,
                'helpful_count', cr.helpful_count,
                'created_at', cr.created_at
            ) ORDER BY cr.created_at DESC
        ) FILTER (WHERE cr.status = 'approved') as recent_reviews_data
    FROM customer_reviews cr
    JOIN users u ON u.id = cr.user_id
    WHERE cr.created_at >= CURRENT_DATE - INTERVAL '30 days'
    GROUP BY cr.sku
),
top_reviews AS (
    SELECT DISTINCT ON (sku, review_type)
        sku,
        CASE
            WHEN rating >= 4 THEN 'positive'
            ELSE 'critical'
        END as review_type,
        jsonb_build_object(
            'id', id,
            'rating', rating,
            'title', title,
            'review_text', review_text,
            'is_verified_purchase', is_verified_purchase,
            'helpful_count', helpful_count,
            'created_at', created_at
        ) as review_data
    FROM customer_reviews
    WHERE status = 'approved'
        AND review_text IS NOT NULL
        AND LENGTH(review_text) > 50
    ORDER BY sku, review_type, helpful_count DESC, created_at DESC
)
SELECT
    pr.sku,
    pr.average_rating,
    pr.total_reviews,
    (pr.rating_distribution->>'5')::INTEGER as five_star_count,
    (pr.rating_distribution->>'4')::INTEGER as four_star_count,
    (pr.rating_distribution->>'3')::INTEGER as three_star_count,
    (pr.rating_distribution->>'2')::INTEGER as two_star_count,
    (pr.rating_distribution->>'1')::INTEGER as one_star_count,
    CASE
        WHEN pr.total_reviews > 0
        THEN ROUND((pr.verified_purchase_count::DECIMAL / pr.total_reviews) * 100, 2)
        ELSE 0
    END as verified_percentage,
    pr.recommended_percentage,
    COALESCE(
        CASE
            WHEN jsonb_array_length(rr.recent_reviews_data) >= 3
            THEN jsonb_build_array(
                rr.recent_reviews_data->0,
                rr.recent_reviews_data->1,
                rr.recent_reviews_data->2
            )
            ELSE rr.recent_reviews_data
        END,
        '[]'::jsonb
    ) as recent_reviews,
    (SELECT review_data FROM top_reviews WHERE sku = pr.sku AND review_type = 'positive' LIMIT 1) as top_positive_review,
    (SELECT review_data FROM top_reviews WHERE sku = pr.sku AND review_type = 'critical' LIMIT 1) as top_critical_review,
    pr.last_updated
FROM product_ratings pr
LEFT JOIN recent_reviews rr ON rr.sku = pr.sku;

-- Create indexes on materialized view
CREATE INDEX IF NOT EXISTS idx_review_summary_sku ON review_summary_view(sku);
CREATE INDEX IF NOT EXISTS idx_review_summary_rating ON review_summary_view(average_rating DESC);

-- =============================================
-- 2. MIGRATE EXISTING OCS RATING DATA (if columns exist)
-- =============================================
DO $$
BEGIN
    -- Check if rating columns exist in ocs_inventory
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'ocs_inventory'
        AND column_name = 'rating'
    ) THEN
        -- Migrate existing ratings from OCS inventory
        INSERT INTO product_ratings (
            sku,
            average_rating,
            total_reviews,
            created_at,
            last_updated
        )
        SELECT DISTINCT
            sku,
            COALESCE(MAX(rating), 0),
            COALESCE(MAX(rating_count), 0),
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM ocs_inventory
        WHERE sku IS NOT NULL
        GROUP BY sku
        ON CONFLICT (sku) DO UPDATE SET
            average_rating = EXCLUDED.average_rating,
            total_reviews = EXCLUDED.total_reviews,
            last_updated = EXCLUDED.last_updated
        WHERE product_ratings.total_reviews = 0; -- Only update if no real reviews exist
    ELSE
        -- If rating columns don't exist, just initialize with zero values for all products
        INSERT INTO product_ratings (
            sku,
            average_rating,
            total_reviews,
            created_at,
            last_updated
        )
        SELECT DISTINCT
            sku,
            0,
            0,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
        FROM ocs_inventory
        WHERE sku IS NOT NULL
        GROUP BY sku
        ON CONFLICT (sku) DO NOTHING;
    END IF;
END $$;

-- =============================================
-- 3. GRANT PERMISSIONS (Create role if it doesn't exist)
-- =============================================
DO $$
BEGIN
    -- Check if authenticated role exists
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'authenticated') THEN
        CREATE ROLE authenticated;
    END IF;

    -- Grant permissions
    GRANT INSERT, UPDATE ON customer_reviews TO authenticated;
    GRANT INSERT, UPDATE, DELETE ON review_votes TO authenticated;
    GRANT INSERT ON review_media TO authenticated;
    GRANT INSERT, UPDATE ON review_attributes TO authenticated;
END $$;

-- Grant public read permissions
GRANT SELECT ON product_ratings TO PUBLIC;
GRANT SELECT ON customer_reviews TO PUBLIC;
GRANT SELECT ON review_media TO PUBLIC;
GRANT SELECT ON review_attributes TO PUBLIC;
GRANT SELECT ON review_summary_view TO PUBLIC;

-- =============================================
-- 4. REFRESH MATERIALIZED VIEW
-- =============================================
REFRESH MATERIALIZED VIEW review_summary_view;

-- =============================================
-- END OF FIX MIGRATION
-- =============================================