-- Populate Canadian provinces and territories
INSERT INTO provinces_territories (id, code, name, type, tax_rate, delivery_allowed, pickup_allowed, created_at, updated_at) VALUES
(gen_random_uuid(), 'AB', 'Alberta', 'province', 0.05, true, true, NOW(), NOW()),
(gen_random_uuid(), 'BC', 'British Columbia', 'province', 0.12, true, true, NOW(), NOW()),
(gen_random_uuid(), 'MB', 'Manitoba', 'province', 0.12, true, true, NOW(), NOW()),
(gen_random_uuid(), 'NB', 'New Brunswick', 'province', 0.15, true, true, NOW(), NOW()),
(gen_random_uuid(), 'NL', 'Newfoundland and Labrador', 'province', 0.15, true, true, NOW(), NOW()),
(gen_random_uuid(), 'NS', 'Nova Scotia', 'province', 0.15, true, true, NOW(), NOW()),
(gen_random_uuid(), 'NT', 'Northwest Territories', 'territory', 0.05, true, true, NOW(), NOW()),
(gen_random_uuid(), 'NU', 'Nunavut', 'territory', 0.05, true, true, NOW(), NOW()),
(gen_random_uuid(), 'ON', 'Ontario', 'province', 0.13, true, true, NOW(), NOW()),
(gen_random_uuid(), 'PE', 'Prince Edward Island', 'province', 0.15, true, true, NOW(), NOW()),
(gen_random_uuid(), 'QC', 'Quebec', 'province', 0.14975, true, true, NOW(), NOW()),
(gen_random_uuid(), 'SK', 'Saskatchewan', 'province', 0.11, true, true, NOW(), NOW()),
(gen_random_uuid(), 'YT', 'Yukon', 'territory', 0.05, true, true, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;