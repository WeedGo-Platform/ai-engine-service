-- =====================================================
-- SUBSCRIPTION TIERS DATABASE DESIGN
-- Based on existing definitions from Landing page
-- =====================================================

-- Main subscription tiers table
CREATE TABLE subscription_tiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,  -- e.g., 'community_and_new_business'
    name VARCHAR(100) NOT NULL,        -- e.g., 'Community and New Business'
    display_order INTEGER NOT NULL,    -- For ordering in UI

    -- Pricing
    price_monthly DECIMAL(10,2) NOT NULL,  -- Monthly price in CAD
    price_annual DECIMAL(10,2),            -- Annual price in CAD (optional discount)
    is_free BOOLEAN DEFAULT FALSE,

    -- Core limits
    max_stores INTEGER NOT NULL,
    max_languages INTEGER NOT NULL,
    max_ai_personalities_per_store INTEGER NOT NULL,

    -- Display properties
    is_popular BOOLEAN DEFAULT FALSE,  -- For "Most Popular" badge
    badge_text VARCHAR(50),            -- e.g., "Most Popular", "Best Value"
    description TEXT,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature categories for organizing features
CREATE TABLE feature_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    display_order INTEGER NOT NULL,
    icon VARCHAR(50),  -- Icon class name
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Master list of all features
CREATE TABLE features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category_id UUID REFERENCES feature_categories(id),
    code VARCHAR(100) UNIQUE NOT NULL,  -- e.g., 'pos_system'
    name VARCHAR(200) NOT NULL,         -- e.g., 'POS System'
    description TEXT,
    feature_type VARCHAR(50) DEFAULT 'boolean',  -- 'boolean', 'numeric', 'text'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Link features to tiers with specific values
CREATE TABLE tier_features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tier_id UUID REFERENCES subscription_tiers(id) ON DELETE CASCADE,
    feature_id UUID REFERENCES features(id) ON DELETE CASCADE,
    is_included BOOLEAN DEFAULT TRUE,
    value VARCHAR(200),  -- For numeric or text features (e.g., "Basic", "Advanced", "Full")
    display_text VARCHAR(200),  -- Override display text if needed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tier_id, feature_id)
);

-- =====================================================
-- INITIAL DATA BASED ON LANDING PAGE
-- =====================================================

-- Insert subscription tiers with correct pricing from Landing.tsx
INSERT INTO subscription_tiers (code, name, display_order, price_monthly, is_free, max_stores, max_languages, max_ai_personalities_per_store) VALUES
('community_and_new_business', 'Community and New Business', 1, 0.00, TRUE, 1, 2, 1),
('small_business', 'Small Business', 2, 99.00, FALSE, 5, 5, 2),
('professional_and_growing_business', 'Professional and Growing Business', 3, 149.00, FALSE, 12, 10, 3),
('enterprise', 'Enterprise', 4, 299.00, FALSE, 999, 25, 5);

-- Mark Professional as most popular
UPDATE subscription_tiers SET is_popular = TRUE, badge_text = 'Most Popular'
WHERE code = 'professional_and_growing_business';

-- Insert feature categories
INSERT INTO feature_categories (name, display_order, icon) VALUES
('Core Platform', 1, 'layers'),
('AI & Automation', 2, 'brain'),
('Commerce Features', 3, 'shopping-cart'),
('Security & Compliance', 4, 'shield'),
('Support & Service', 5, 'headphones');

-- Insert features
-- Core Platform features
INSERT INTO features (category_id, code, name, description) VALUES
((SELECT id FROM feature_categories WHERE name = 'Core Platform'), 'pos_system', 'POS System', 'Point of Sale system'),
((SELECT id FROM feature_categories WHERE name = 'Core Platform'), 'kiosk_mode', 'KIOSK Mode', 'Self-service kiosk functionality'),
((SELECT id FROM feature_categories WHERE name = 'Core Platform'), 'white_label', 'White Label Branding', 'Custom branding options'),
((SELECT id FROM feature_categories WHERE name = 'Core Platform'), 'api_access', 'API Access', 'Programmatic access to platform');

-- AI & Automation features
INSERT INTO features (category_id, code, name, description) VALUES
((SELECT id FROM feature_categories WHERE name = 'AI & Automation'), 'ai_budtender', 'AI Budtender Assistant', 'Intelligent customer assistance'),
((SELECT id FROM feature_categories WHERE name = 'AI & Automation'), 'voice_commerce', 'Voice Commerce', 'Voice-enabled shopping'),
((SELECT id FROM feature_categories WHERE name = 'AI & Automation'), 'voice_age_verification', 'Voice Age Verification', 'Automated age verification'),
((SELECT id FROM feature_categories WHERE name = 'AI & Automation'), 'predictive_analytics', 'Predictive Analytics', 'AI-driven insights'),
((SELECT id FROM feature_categories WHERE name = 'AI & Automation'), 'natural_language_search', 'Natural Language Search', 'Advanced search capabilities');

-- Commerce features
INSERT INTO features (category_id, code, name, description) VALUES
((SELECT id FROM feature_categories WHERE name = 'Commerce Features'), 'delivery_management', 'Delivery Management', 'Complete delivery system'),
((SELECT id FROM feature_categories WHERE name = 'Commerce Features'), 'inventory_optimization', 'Inventory Optimization', 'Smart inventory management'),
((SELECT id FROM feature_categories WHERE name = 'Commerce Features'), 'multi_payment', 'Multiple Payment Options', 'Various payment methods'),
((SELECT id FROM feature_categories WHERE name = 'Commerce Features'), 'promotions', 'Promotions & Discounts', 'Marketing tools');

-- Security & Compliance features
INSERT INTO features (category_id, code, name, description) VALUES
((SELECT id FROM feature_categories WHERE name = 'Security & Compliance'), 'fraud_protection', 'Fraud Protection', 'Advanced fraud detection'),
((SELECT id FROM feature_categories WHERE name = 'Security & Compliance'), 'compliance_tracking', 'Compliance Tracking', 'Regulatory compliance'),
((SELECT id FROM feature_categories WHERE name = 'Security & Compliance'), 'ocs_integration', 'OCS Integration', 'Ontario Cannabis Store integration'),
((SELECT id FROM feature_categories WHERE name = 'Security & Compliance'), 'cannsell_tracking', 'CannSell Tracking', 'Certification management');

-- Support features
INSERT INTO features (category_id, code, name, description) VALUES
((SELECT id FROM feature_categories WHERE name = 'Support & Service'), 'support_level', 'Support Level', 'Customer support tier'),
((SELECT id FROM feature_categories WHERE name = 'Support & Service'), 'training', 'Training & Onboarding', 'Platform training'),
((SELECT id FROM feature_categories WHERE name = 'Support & Service'), 'dedicated_account_manager', 'Dedicated Account Manager', 'Personal account management');

-- =====================================================
-- TIER FEATURES MAPPING
-- =====================================================

-- Community and New Business tier features
INSERT INTO tier_features (tier_id, feature_id, is_included, value, display_text) VALUES
-- Core Platform
((SELECT id FROM subscription_tiers WHERE code = 'community_and_new_business'),
 (SELECT id FROM features WHERE code = 'pos_system'), TRUE, 'Basic', 'Basic POS System'),
((SELECT id FROM subscription_tiers WHERE code = 'community_and_new_business'),
 (SELECT id FROM features WHERE code = 'kiosk_mode'), FALSE, NULL, NULL),
-- AI & Automation
((SELECT id FROM subscription_tiers WHERE code = 'community_and_new_business'),
 (SELECT id FROM features WHERE code = 'ai_budtender'), TRUE, 'Basic', 'Basic AI Assistant'),
((SELECT id FROM subscription_tiers WHERE code = 'community_and_new_business'),
 (SELECT id FROM features WHERE code = 'voice_commerce'), FALSE, NULL, NULL),
-- Support
((SELECT id FROM subscription_tiers WHERE code = 'community_and_new_business'),
 (SELECT id FROM features WHERE code = 'support_level'), TRUE, 'Standard', 'Standard Support');

-- Small Business tier features
INSERT INTO tier_features (tier_id, feature_id, is_included, value, display_text) VALUES
-- Core Platform
((SELECT id FROM subscription_tiers WHERE code = 'small_business'),
 (SELECT id FROM features WHERE code = 'pos_system'), TRUE, 'Advanced', 'Advanced POS System'),
((SELECT id FROM subscription_tiers WHERE code = 'small_business'),
 (SELECT id FROM features WHERE code = 'kiosk_mode'), TRUE, 'Full', 'KIOSK Mode'),
-- AI & Automation
((SELECT id FROM subscription_tiers WHERE code = 'small_business'),
 (SELECT id FROM features WHERE code = 'ai_budtender'), TRUE, 'Advanced', 'Advanced AI Assistant'),
((SELECT id FROM subscription_tiers WHERE code = 'small_business'),
 (SELECT id FROM features WHERE code = 'voice_commerce'), TRUE, 'Basic', 'Voice Commerce'),
-- Commerce
((SELECT id FROM subscription_tiers WHERE code = 'small_business'),
 (SELECT id FROM features WHERE code = 'delivery_management'), TRUE, 'Full', 'Delivery Management'),
-- Support
((SELECT id FROM subscription_tiers WHERE code = 'small_business'),
 (SELECT id FROM features WHERE code = 'support_level'), TRUE, 'Priority', 'Priority Support');

-- Professional and Growing Business tier features
INSERT INTO tier_features (tier_id, feature_id, is_included, value, display_text) VALUES
-- Core Platform
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'pos_system'), TRUE, 'Full', 'Full Platform Access'),
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'kiosk_mode'), TRUE, 'Full', 'Full KIOSK Mode'),
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'white_label'), TRUE, 'Full', 'White Label Branding'),
-- AI & Automation
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'ai_budtender'), TRUE, 'Full', 'Full AI Assistant'),
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'voice_commerce'), TRUE, 'Full', 'Full Voice Commerce'),
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'voice_age_verification'), TRUE, 'Full', 'Voice Age Verification'),
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'predictive_analytics'), TRUE, 'Full', 'Predictive Analytics'),
-- Commerce
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'delivery_management'), TRUE, 'Full', 'Full Delivery Management'),
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'inventory_optimization'), TRUE, 'Full', 'Inventory Optimization'),
-- Security
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'fraud_protection'), TRUE, 'Full', 'Fraud Protection'),
-- Support
((SELECT id FROM subscription_tiers WHERE code = 'professional_and_growing_business'),
 (SELECT id FROM features WHERE code = 'support_level'), TRUE, '24/7', '24/7 Support');

-- Enterprise tier features (everything included)
INSERT INTO tier_features (tier_id, feature_id, is_included, value, display_text) VALUES
-- Core Platform
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'pos_system'), TRUE, 'Enterprise', 'Enterprise POS System'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'kiosk_mode'), TRUE, 'Enterprise', 'Enterprise KIOSK Mode'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'white_label'), TRUE, 'Enterprise', 'Full White Label'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'api_access'), TRUE, 'Full', 'Full API Access'),
-- All AI features
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'ai_budtender'), TRUE, 'Enterprise', 'Enterprise AI Assistant'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'voice_commerce'), TRUE, 'Enterprise', 'Enterprise Voice Commerce'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'voice_age_verification'), TRUE, 'Enterprise', 'Voice Age Verification'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'predictive_analytics'), TRUE, 'Enterprise', 'Advanced Analytics'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'natural_language_search'), TRUE, 'Enterprise', 'Natural Language Search'),
-- All Commerce features
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'delivery_management'), TRUE, 'Enterprise', 'Enterprise Delivery'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'inventory_optimization'), TRUE, 'Enterprise', 'Advanced Inventory'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'multi_payment'), TRUE, 'All', 'All Payment Methods'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'promotions'), TRUE, 'Advanced', 'Advanced Promotions'),
-- All Security features
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'fraud_protection'), TRUE, 'Enterprise', 'Enterprise Fraud Protection'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'compliance_tracking'), TRUE, 'Full', 'Full Compliance Suite'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'ocs_integration'), TRUE, 'Full', 'OCS Integration'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'cannsell_tracking'), TRUE, 'Full', 'CannSell Management'),
-- Premium Support
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'support_level'), TRUE, 'Dedicated', 'Dedicated Support'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'training'), TRUE, 'Custom', 'Custom Training'),
((SELECT id FROM subscription_tiers WHERE code = 'enterprise'),
 (SELECT id FROM features WHERE code = 'dedicated_account_manager'), TRUE, 'Yes', 'Dedicated Account Manager');

-- =====================================================
-- HELPER VIEWS
-- =====================================================

-- View to get all features for a tier
CREATE VIEW tier_features_view AS
SELECT
    st.code as tier_code,
    st.name as tier_name,
    st.price_monthly,
    st.max_stores,
    st.max_languages,
    st.max_ai_personalities_per_store,
    fc.name as category,
    f.name as feature_name,
    tf.is_included,
    tf.value,
    COALESCE(tf.display_text, f.name) as display_text
FROM subscription_tiers st
LEFT JOIN tier_features tf ON st.id = tf.tier_id
LEFT JOIN features f ON tf.feature_id = f.id
LEFT JOIN feature_categories fc ON f.category_id = fc.id
ORDER BY st.display_order, fc.display_order, f.name;

-- View to compare tiers
CREATE VIEW tier_comparison_view AS
SELECT
    f.name as feature,
    fc.name as category,
    MAX(CASE WHEN st.code = 'community_and_new_business' THEN COALESCE(tf.display_text, tf.value, CASE WHEN tf.is_included THEN '✓' ELSE '✗' END) END) as community,
    MAX(CASE WHEN st.code = 'small_business' THEN COALESCE(tf.display_text, tf.value, CASE WHEN tf.is_included THEN '✓' ELSE '✗' END) END) as small_business,
    MAX(CASE WHEN st.code = 'professional_and_growing_business' THEN COALESCE(tf.display_text, tf.value, CASE WHEN tf.is_included THEN '✓' ELSE '✗' END) END) as professional,
    MAX(CASE WHEN st.code = 'enterprise' THEN COALESCE(tf.display_text, tf.value, CASE WHEN tf.is_included THEN '✓' ELSE '✗' END) END) as enterprise
FROM features f
JOIN feature_categories fc ON f.category_id = fc.id
CROSS JOIN subscription_tiers st
LEFT JOIN tier_features tf ON f.id = tf.feature_id AND st.id = tf.tier_id
GROUP BY f.name, fc.name, fc.display_order
ORDER BY fc.display_order, f.name;

-- =====================================================
-- SAMPLE QUERIES
-- =====================================================

-- Get all features for a specific tier
-- SELECT * FROM tier_features_view WHERE tier_code = 'professional_and_growing_business';

-- Compare all tiers
-- SELECT * FROM tier_comparison_view;

-- Get tier limits
-- SELECT code, name, price_monthly, max_stores, max_languages, max_ai_personalities_per_store
-- FROM subscription_tiers
-- ORDER BY display_order;