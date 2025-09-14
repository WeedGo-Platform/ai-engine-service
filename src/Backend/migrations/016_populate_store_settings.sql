-- Migration: Populate default store settings categories and values
-- This migration adds default store settings for all stores using the store_settings table

-- Location & Delivery Settings
INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'location',
    'deliveryZones',
    '[]'::jsonb,
    'Delivery zones configuration'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'location',
    'deliveryFees',
    '{"base": 5.00, "free_threshold": 100.00}'::jsonb,
    'Delivery fee structure'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'location',
    'deliveryTimeSlots',
    '["9:00-12:00", "12:00-15:00", "15:00-18:00", "18:00-21:00"]'::jsonb,
    'Available delivery time slots'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'location',
    'pickupTimeSlots',
    '["9:00-12:00", "12:00-15:00", "15:00-18:00", "18:00-21:00"]'::jsonb,
    'Available pickup time slots'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'location',
    'minimumDeliveryOrder',
    '30.00'::jsonb,
    'Minimum order amount for delivery'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'location',
    'expressDeliveryEnabled',
    'false'::jsonb,
    'Enable express delivery option'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'location',
    'expressDeliveryFee',
    '15.00'::jsonb,
    'Express delivery fee'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

-- Compliance Settings
INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'compliance',
    'ageVerificationRequired',
    'true'::jsonb,
    'Require age verification'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'compliance',
    'minimumAge',
    '19'::jsonb,
    'Minimum age for purchase'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'compliance',
    'dailyPurchaseLimit',
    '30'::jsonb,
    'Daily purchase limit in grams'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'compliance',
    'monthlyPurchaseLimit',
    '150'::jsonb,
    'Monthly purchase limit in grams'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'compliance',
    'requireIdVerification',
    'true'::jsonb,
    'Require ID verification for all purchases'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'compliance',
    'trackPurchaseHistory',
    'true'::jsonb,
    'Track customer purchase history for compliance'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'compliance',
    'warningMessages',
    '{"pregnancy": "Cannabis use during pregnancy may harm the fetus", "driving": "Do not drive or operate machinery", "health": "Keep out of reach of children and pets"}'::jsonb,
    'Required warning messages'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;

INSERT INTO store_settings (store_id, category, key, value, description)
SELECT 
    s.id,
    'compliance',
    'requireMedicalCard',
    'false'::jsonb,
    'Require medical cannabis card'
FROM stores s
ON CONFLICT (store_id, category, key) DO NOTHING;