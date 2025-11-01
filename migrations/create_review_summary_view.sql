-- Create review_summary_view materialized view
-- This view aggregates review data for fast querying

CREATE MATERIALIZED VIEW IF NOT EXISTS review_summary_view AS
SELECT
    cr.ocs_sku as sku,
    ROUND(AVG(cr.rating)::numeric, 2) as average_rating,
    COUNT(cr.id) as total_reviews,
    COUNT(CASE WHEN cr.rating = 5 THEN 1 END) as five_star_count,
    COUNT(CASE WHEN cr.rating = 4 THEN 1 END) as four_star_count,
    COUNT(CASE WHEN cr.rating = 3 THEN 1 END) as three_star_count,
    COUNT(CASE WHEN cr.rating = 2 THEN 1 END) as two_star_count,
    COUNT(CASE WHEN cr.rating = 1 THEN 1 END) as one_star_count,
    ROUND((COUNT(CASE WHEN cr.is_verified_purchase = true THEN 1 END)::numeric / NULLIF(COUNT(cr.id), 0)) * 100, 2) as verified_percentage,
    ROUND((COUNT(CASE WHEN cr.rating >= 4 THEN 1 END)::numeric / NULLIF(COUNT(cr.id), 0)) * 100, 2) as recommended_percentage,
    json_agg(
        json_build_object(
            'id', cr.id,
            'rating', cr.rating,
            'title', cr.title,
            'review_text', cr.review_text,
            'created_at', cr.created_at,
            'helpful_count', cr.helpful_count
        ) ORDER BY cr.created_at DESC
    ) FILTER (WHERE cr.is_approved = true) as recent_reviews,
    (
        SELECT json_build_object(
            'id', r.id,
            'rating', r.rating,
            'title', r.title,
            'review_text', r.review_text,
            'helpful_count', r.helpful_count
        )
        FROM customer_reviews r
        WHERE r.ocs_sku = cr.ocs_sku
          AND r.is_approved = true
          AND r.rating >= 4
        ORDER BY r.helpful_count DESC, r.created_at DESC
        LIMIT 1
    ) as top_positive_review,
    (
        SELECT json_build_object(
            'id', r.id,
            'rating', r.rating,
            'title', r.title,
            'review_text', r.review_text,
            'helpful_count', r.helpful_count
        )
        FROM customer_reviews r
        WHERE r.ocs_sku = cr.ocs_sku
          AND r.is_approved = true
          AND r.rating <= 2
        ORDER BY r.helpful_count DESC, r.created_at DESC
        LIMIT 1
    ) as top_critical_review
FROM customer_reviews cr
WHERE cr.is_approved = true
GROUP BY cr.ocs_sku;

-- Create indexes on the materialized view
CREATE UNIQUE INDEX IF NOT EXISTS idx_review_summary_sku_unique ON review_summary_view (sku);
CREATE INDEX IF NOT EXISTS idx_review_summary_rating ON review_summary_view (average_rating DESC);
CREATE INDEX IF NOT EXISTS idx_review_summary_total ON review_summary_view (total_reviews DESC);

-- Refresh function
CREATE OR REPLACE FUNCTION refresh_review_summary()
RETURNS void
LANGUAGE plpgsql
AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY review_summary_view;
END;
$$;

COMMENT ON MATERIALIZED VIEW review_summary_view IS 'Aggregated review statistics for products';
COMMENT ON FUNCTION refresh_review_summary() IS 'Refresh the review summary materialized view';
