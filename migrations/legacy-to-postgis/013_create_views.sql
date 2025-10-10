-- ============================================================================
-- Migration: Create Database Views
-- Description: Create all missing views for query optimization
-- Dependencies: 012_add_foreign_keys.sql
-- ============================================================================

-- ===========================
-- INVENTORY & PRODUCT VIEWS
-- ===========================

-- Comprehensive Product Inventory View (combines product catalog with inventory)
CREATE OR REPLACE VIEW comprehensive_product_inventory_view AS
SELECT
    opc.id AS product_id,
    opc.ocs_sku,
    opc.product_name,
    opc.brand,
    opc.category,
    opc.product_type,
    opc.thc_min,
    opc.thc_max,
    opc.cbd_min,
    opc.cbd_max,
    opc.weight,
    opc.weight_unit,
    opc.wholesale_price,
    opc.suggested_retail_price,
    opc.description,
    opc.image_url,
    opc.is_active AS product_is_active,
    oi.id AS inventory_id,
    oi.store_id,
    s.name AS store_name,
    s.store_code,
    oi.quantity,
    oi.reserved_quantity,
    oi.available_quantity,
    oi.reorder_point,
    oi.location_code,
    oi.last_received,
    oi.last_sold,
    pr.average_rating,
    pr.total_ratings,
    CASE
        WHEN oi.quantity <= 0 THEN 'out_of_stock'
        WHEN oi.quantity <= oi.reorder_point THEN 'low_stock'
        ELSE 'in_stock'
    END AS stock_status
FROM ocs_product_catalog opc
LEFT JOIN ocs_inventory oi ON opc.ocs_sku = oi.ocs_sku
LEFT JOIN stores s ON oi.store_id = s.id
LEFT JOIN product_ratings pr ON opc.ocs_sku = pr.ocs_sku
WHERE opc.is_active = true;

COMMENT ON VIEW comprehensive_product_inventory_view IS 'Complete view combining product catalog, inventory levels, and ratings';

-- Inventory Products View (simpler inventory + product join)
CREATE OR REPLACE VIEW inventory_products_view AS
SELECT
    oi.id AS inventory_id,
    oi.store_id,
    oi.ocs_sku,
    oi.quantity,
    oi.reserved_quantity,
    oi.available_quantity,
    oi.reorder_point,
    opc.product_name,
    opc.brand,
    opc.category,
    opc.wholesale_price,
    opc.suggested_retail_price,
    opc.image_url
FROM ocs_inventory oi
INNER JOIN ocs_product_catalog opc ON oi.ocs_sku = opc.ocs_sku
WHERE opc.is_active = true;

COMMENT ON VIEW inventory_products_view IS 'Inventory with basic product information';

-- ===========================
-- PROMOTION & USER VIEWS
-- ===========================

-- Active Promotions View
CREATE OR REPLACE VIEW active_promotions AS
SELECT
    p.*,
    s.name AS store_name,
    s.store_code
FROM promotions p
INNER JOIN stores s ON p.store_id = s.id
WHERE p.created_at IS NOT NULL  -- Placeholder condition, adjust based on actual promotion active logic
ORDER BY p.created_at DESC;

COMMENT ON VIEW active_promotions IS 'Currently active promotions with store details';

-- Admin Users View
CREATE OR REPLACE VIEW admin_users AS
SELECT
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.role,
    u.active,
    u.created_at,
    u.last_login,
    u.tenant_id,
    t.code AS tenant_code,
    u.store_id,
    s.name AS store_name,
    s.store_code
FROM users u
LEFT JOIN tenants t ON u.tenant_id = t.id
LEFT JOIN stores s ON u.store_id = s.id
WHERE u.role IN ('super_admin', 'tenant_admin', 'store_manager', 'staff')
ORDER BY u.created_at DESC;

COMMENT ON VIEW admin_users IS 'All administrative users with tenant and store context';

-- Recent Login Activity View
CREATE OR REPLACE VIEW recent_login_activity AS
SELECT
    ull.id,
    ull.user_id,
    u.email,
    u.first_name,
    u.last_name,
    u.role,
    ull.created_at AS login_time,
    u.last_login_ip,
    u.last_login_location
FROM user_login_logs ull
INNER JOIN users u ON ull.user_id = u.id
ORDER BY ull.created_at DESC
LIMIT 100;

COMMENT ON VIEW recent_login_activity IS 'Recent 100 login events with user details';

-- Store Settings View
CREATE OR REPLACE VIEW store_settings_view AS
SELECT
    s.id AS store_id,
    s.name AS store_name,
    s.store_code,
    s.status AS store_status,
    s.timezone,
    s.delivery_enabled,
    s.pickup_enabled,
    s.ecommerce_enabled,
    s.pos_enabled,
    s.kiosk_enabled,
    json_agg(
        json_build_object(
            'key', ss.key,
            'value', ss.value,
            'description', ss.description
        )
    ) FILTER (WHERE ss.id IS NOT NULL) AS settings
FROM stores s
LEFT JOIN store_settings ss ON s.id = ss.store_id
GROUP BY s.id, s.name, s.store_code, s.status, s.timezone,
         s.delivery_enabled, s.pickup_enabled, s.ecommerce_enabled,
         s.pos_enabled, s.kiosk_enabled;

COMMENT ON VIEW store_settings_view IS 'Stores with aggregated settings';

-- ===========================
-- WISHLIST & TRANSLATION VIEWS
-- ===========================

-- Wishlist Details View
CREATE OR REPLACE VIEW wishlist_details AS
SELECT
    w.id AS wishlist_id,
    w.user_id,
    u.email AS user_email,
    u.first_name,
    u.last_name,
    w.ocs_sku,
    opc.product_name,
    opc.brand,
    opc.category,
    opc.suggested_retail_price,
    opc.image_url,
    w.added_at,
    w.notes,
    w.notify_on_sale,
    w.notify_on_restock,
    pr.average_rating,
    pr.total_ratings
FROM wishlist w
INNER JOIN users u ON w.user_id = u.id
INNER JOIN ocs_product_catalog opc ON w.ocs_sku = opc.ocs_sku
LEFT JOIN product_ratings pr ON w.ocs_sku = pr.ocs_sku
WHERE opc.is_active = true
ORDER BY w.added_at DESC;

COMMENT ON VIEW wishlist_details IS 'Wishlist items with complete product and user information';

-- Hot Translations View (frequently accessed translations)
CREATE OR REPLACE VIEW v_hot_translations AS
SELECT
    t.translation_key,
    t.language_code,
    t.translation_value,
    t.context,
    t.is_approved
FROM translations t
WHERE t.is_approved = true
  AND t.translation_key IN (
      -- Common UI elements
      'common.submit', 'common.cancel', 'common.save', 'common.delete',
      'common.edit', 'common.add', 'common.search', 'common.filter',
      'nav.home', 'nav.products', 'nav.cart', 'nav.account',
      'checkout.title', 'checkout.payment', 'checkout.delivery'
  )
ORDER BY t.translation_key, t.language_code;

COMMENT ON VIEW v_hot_translations IS 'Frequently accessed translations for caching';

-- Translation Stats View
CREATE OR REPLACE VIEW v_translation_stats AS
SELECT
    language_code,
    COUNT(*) AS total_translations,
    COUNT(*) FILTER (WHERE is_approved = true) AS approved_translations,
    COUNT(*) FILTER (WHERE is_approved = false) AS pending_translations,
    ROUND(
        (COUNT(*) FILTER (WHERE is_approved = true)::NUMERIC / COUNT(*)::NUMERIC) * 100,
        2
    ) AS approval_percentage
FROM translations
GROUP BY language_code
ORDER BY total_translations DESC;

COMMENT ON VIEW v_translation_stats IS 'Translation completion statistics by language';

-- ===========================
-- GRANT PERMISSIONS
-- ===========================

-- Grant SELECT permissions on views to weedgo user (adjust as needed)
GRANT SELECT ON comprehensive_product_inventory_view TO weedgo;
GRANT SELECT ON inventory_products_view TO weedgo;
GRANT SELECT ON active_promotions TO weedgo;
GRANT SELECT ON admin_users TO weedgo;
GRANT SELECT ON recent_login_activity TO weedgo;
GRANT SELECT ON store_settings_view TO weedgo;
GRANT SELECT ON wishlist_details TO weedgo;
GRANT SELECT ON v_hot_translations TO weedgo;
GRANT SELECT ON v_translation_stats TO weedgo;
