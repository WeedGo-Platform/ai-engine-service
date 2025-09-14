-- Migration: Remove product, search, inventory, and display settings from store_settings table
-- This migration removes settings that are no longer needed

DELETE FROM store_settings 
WHERE category IN ('product', 'search', 'inventory', 'display');