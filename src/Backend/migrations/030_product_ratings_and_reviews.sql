-- =============================================
-- Migration: Product Ratings and Reviews System
-- Author: System
-- Date: 2025-01-16
-- Description: Comprehensive rating and review system for products
-- =============================================

-- Drop existing objects if they exist (for re-running migration)
DROP MATERIALIZED VIEW IF EXISTS review_summary_view CASCADE;
DROP TABLE IF EXISTS review_attributes CASCADE;
DROP TABLE IF EXISTS review_media CASCADE;
DROP TABLE IF EXISTS review_votes CASCADE;
DROP TABLE IF EXISTS customer_reviews CASCADE;
DROP TABLE IF EXISTS product_ratings CASCADE;

-- =============================================
-- 1. PRODUCT RATINGS TABLE (Aggregated ratings per product)
-- =============================================
CREATE TABLE product_ratings (
    sku VARCHAR(255) PRIMARY KEY,
    average_rating DECIMAL(2,1) DEFAULT 0.0 CHECK (average_rating >= 0 AND average_rating <= 5),
    total_reviews INTEGER DEFAULT 0 CHECK (total_reviews >= 0),
    rating_distribution JSONB DEFAULT '{"5": 0, "4": 0, "3": 0, "2": 0, "1": 0}'::jsonb,
    verified_purchase_count INTEGER DEFAULT 0 CHECK (verified_purchase_count >= 0),
    recommended_percentage DECIMAL(5,2) DEFAULT 0.00 CHECK (recommended_percentage >= 0 AND recommended_percentage <= 100),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    -- Note: No foreign key constraint as SKU is not unique in ocs_inventory (unique per store)
);

-- Create index for fast lookups
CREATE INDEX idx_product_ratings_sku ON product_ratings(sku);
CREATE INDEX idx_product_ratings_avg_rating ON product_ratings(average_rating DESC);

-- =============================================
-- 2. CUSTOMER REVIEWS TABLE (Individual customer reviews)
-- =============================================
CREATE TABLE customer_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sku VARCHAR(255) NOT NULL,
    user_id UUID NOT NULL,
    order_id UUID,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    title VARCHAR(200),
    review_text TEXT,
    is_recommended BOOLEAN DEFAULT true,
    is_verified_purchase BOOLEAN DEFAULT false,
    helpful_count INTEGER DEFAULT 0 CHECK (helpful_count >= 0),
    not_helpful_count INTEGER DEFAULT 0 CHECK (not_helpful_count >= 0),
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'flagged')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_reviews_product_ratings
        FOREIGN KEY (sku)
        REFERENCES product_ratings(sku)
        ON DELETE CASCADE,
    CONSTRAINT fk_reviews_users
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_reviews_orders
        FOREIGN KEY (order_id)
        REFERENCES orders(id)
        ON DELETE SET NULL
);

-- Create indexes for performance
CREATE INDEX idx_reviews_variant_rating ON customer_reviews(sku, rating);
CREATE INDEX idx_reviews_user ON customer_reviews(user_id);
CREATE INDEX idx_reviews_status_created ON customer_reviews(status, created_at DESC);
CREATE INDEX idx_reviews_order ON customer_reviews(order_id);
CREATE INDEX idx_reviews_helpful ON customer_reviews(helpful_count DESC);

-- =============================================
-- 3. REVIEW VOTES TABLE (Helpful/Not helpful votes)
-- =============================================
CREATE TABLE review_votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL,
    user_id UUID NOT NULL,
    vote_type VARCHAR(20) NOT NULL CHECK (vote_type IN ('helpful', 'not_helpful')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_votes_reviews
        FOREIGN KEY (review_id)
        REFERENCES customer_reviews(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_votes_users
        FOREIGN KEY (user_id)
        REFERENCES users(id)
        ON DELETE CASCADE,
    CONSTRAINT unique_user_review_vote
        UNIQUE (review_id, user_id)
);

-- Create indexes for performance
CREATE INDEX idx_votes_review ON review_votes(review_id);
CREATE INDEX idx_votes_user ON review_votes(user_id);

-- =============================================
-- 4. REVIEW MEDIA TABLE (Photos/videos attached to reviews)
-- =============================================
CREATE TABLE review_media (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    review_id UUID NOT NULL,
    media_type VARCHAR(10) NOT NULL CHECK (media_type IN ('image', 'video')),
    media_url VARCHAR(500) NOT NULL,
    thumbnail_url VARCHAR(500),
    caption VARCHAR(500),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_media_reviews
        FOREIGN KEY (review_id)
        REFERENCES customer_reviews(id)
        ON DELETE CASCADE
);

-- Create indexes for performance
CREATE INDEX idx_media_review ON review_media(review_id);
CREATE INDEX idx_media_order ON review_media(review_id, display_order);

-- =============================================
-- 5. REVIEW ATTRIBUTES TABLE (Cannabis-specific attributes)
-- =============================================
CREATE TABLE review_attributes (
    review_id UUID NOT NULL,
    attribute_name VARCHAR(50) NOT NULL,
    attribute_value VARCHAR(100),
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    CONSTRAINT pk_review_attributes
        PRIMARY KEY (review_id, attribute_name),
    CONSTRAINT fk_attributes_reviews
        FOREIGN KEY (review_id)
        REFERENCES customer_reviews(id)
        ON DELETE CASCADE,
    CONSTRAINT chk_attribute_name
        CHECK (attribute_name IN ('effects', 'flavor', 'potency', 'aroma', 'value', 'quality'))
);

-- Create index for performance
CREATE INDEX idx_attributes_review ON review_attributes(review_id);

-- =============================================
-- 6. FUNCTIONS AND TRIGGERS
-- =============================================

-- Function to update product ratings when a review is added/updated/deleted
CREATE OR REPLACE FUNCTION update_product_rating()
RETURNS TRIGGER AS $$
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
$$ LANGUAGE plpgsql;

-- Create trigger for review changes
CREATE TRIGGER trigger_update_product_rating
AFTER INSERT OR UPDATE OR DELETE ON customer_reviews
FOR EACH ROW
EXECUTE FUNCTION update_product_rating();

-- Function to update review vote counts
CREATE OR REPLACE FUNCTION update_review_vote_counts()
RETURNS TRIGGER AS $$
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
$$ LANGUAGE plpgsql;

-- Create trigger for vote changes
CREATE TRIGGER trigger_update_review_vote_counts
AFTER INSERT OR UPDATE OR DELETE ON review_votes
FOR EACH ROW
EXECUTE FUNCTION update_review_vote_counts();

-- Function to validate verified purchase
CREATE OR REPLACE FUNCTION validate_verified_purchase()
RETURNS TRIGGER AS $$
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
$$ LANGUAGE plpgsql;

-- Create trigger to validate verified purchase
CREATE TRIGGER trigger_validate_verified_purchase
BEFORE INSERT OR UPDATE ON customer_reviews
FOR EACH ROW
EXECUTE FUNCTION validate_verified_purchase();

-- =============================================
-- 7. MATERIALIZED VIEW FOR REVIEW SUMMARIES
-- =============================================
CREATE MATERIALIZED VIEW review_summary_view AS
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
        (rr.recent_reviews_data)[1:3],
        '[]'::jsonb
    ) as recent_reviews,
    MAX(CASE WHEN tr.review_type = 'positive' THEN tr.review_data END) as top_positive_review,
    MAX(CASE WHEN tr.review_type = 'critical' THEN tr.review_data END) as top_critical_review,
    pr.last_updated
FROM product_ratings pr
LEFT JOIN recent_reviews rr ON rr.sku = pr.sku
LEFT JOIN top_reviews tr ON tr.sku = pr.sku
GROUP BY
    pr.sku,
    pr.average_rating,
    pr.total_reviews,
    pr.rating_distribution,
    pr.verified_purchase_count,
    pr.recommended_percentage,
    pr.last_updated,
    rr.recent_reviews_data;

-- Create indexes on materialized view
CREATE INDEX idx_review_summary_variant ON review_summary_view(sku);
CREATE INDEX idx_review_summary_rating ON review_summary_view(average_rating DESC);

-- =============================================
-- 8. MIGRATE EXISTING OCS RATING DATA
-- =============================================

-- Insert existing ratings from OCS inventory
INSERT INTO product_ratings (
    sku,
    average_rating,
    total_reviews,
    created_at,
    last_updated
)
SELECT
    sku,
    COALESCE(rating, 0),
    COALESCE(rating_count, 0),
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
FROM ocs_inventory
WHERE sku IS NOT NULL
ON CONFLICT (sku) DO UPDATE SET
    average_rating = EXCLUDED.average_rating,
    total_reviews = EXCLUDED.total_reviews,
    last_updated = EXCLUDED.last_updated
WHERE product_ratings.total_reviews = 0; -- Only update if no real reviews exist

-- =============================================
-- 9. PERMISSIONS
-- =============================================

-- Grant appropriate permissions
GRANT SELECT ON product_ratings TO PUBLIC;
GRANT SELECT ON customer_reviews TO PUBLIC;
GRANT SELECT ON review_media TO PUBLIC;
GRANT SELECT ON review_attributes TO PUBLIC;
GRANT SELECT ON review_summary_view TO PUBLIC;

GRANT INSERT, UPDATE ON customer_reviews TO authenticated;
GRANT INSERT, UPDATE, DELETE ON review_votes TO authenticated;
GRANT INSERT ON review_media TO authenticated;
GRANT INSERT, UPDATE ON review_attributes TO authenticated;

-- =============================================
-- 10. COMMENTS
-- =============================================

COMMENT ON TABLE product_ratings IS 'Aggregated product ratings and review statistics';
COMMENT ON TABLE customer_reviews IS 'Individual customer product reviews';
COMMENT ON TABLE review_votes IS 'Helpful/not helpful votes on reviews';
COMMENT ON TABLE review_media IS 'Media attachments (photos/videos) for reviews';
COMMENT ON TABLE review_attributes IS 'Cannabis-specific review attributes (effects, flavor, etc.)';
COMMENT ON MATERIALIZED VIEW review_summary_view IS 'Pre-computed review summaries for fast product page loading';

-- =============================================
-- 11. REFRESH MATERIALIZED VIEW FUNCTION
-- =============================================

CREATE OR REPLACE FUNCTION refresh_review_summary()
RETURNS void AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY review_summary_view;
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job to refresh the view (requires pg_cron extension)
-- This would be run separately if pg_cron is available:
-- SELECT cron.schedule('refresh-review-summary', '*/15 * * * *', 'SELECT refresh_review_summary();');

-- =============================================
-- END OF MIGRATION
-- =============================================