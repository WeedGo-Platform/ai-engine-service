#!/bin/bash
# Quick setup script for CRSA sync system

set -e

echo "================================================"
echo "  Ontario CRSA Sync System - Quick Setup"
echo "================================================"
echo ""

# Step 1: Install dependencies
echo "📦 Step 1: Installing required Python packages..."
pip install aiohttp beautifulsoup4 lxml schedule

# Step 2: Create data directory
echo "📁 Step 2: Creating data directory..."
mkdir -p data/crsa

# Step 3: Download AGCO data
echo "🌐 Step 3: Downloading latest AGCO CRSA data..."
python scripts/download_agco_crsa.py

# Step 4: Import to database
echo "💾 Step 4: Importing data to database..."
LATEST_CSV=$(ls -t data/crsa/crsa_data_*.csv 2>/dev/null | head -1)

if [ -z "$LATEST_CSV" ]; then
    echo "❌ Error: No CSV file found in data/crsa/"
    echo "Please download AGCO data manually or check download script"
    exit 1
fi

echo "Found CSV: $LATEST_CSV"
python scripts/import_crsa_data.py "$LATEST_CSV" --initial

# Step 5: Verify database
echo "🔍 Step 5: Verifying database..."
psql -h localhost -p 5434 -U weedgo -d ai_engine -c "
SELECT 
    COUNT(*) as total_records,
    COUNT(*) FILTER (WHERE is_active = true) as active,
    COUNT(*) FILTER (WHERE store_application_status LIKE '%Authorized%') as authorized
FROM ontario_crsa_status;
"

echo ""
echo "================================================"
echo "  ✅ Setup Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Restart the API server to initialize sync service"
echo "2. Test validation with a real license number"
echo "3. Check sync runs daily at 3:00 AM"
echo ""
echo "Test validation:"
echo "curl -X POST http://localhost:5024/api/crsa/validate \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"license_number\":\"CRSA-123456\",\"email\":\"test@example.com\"}'"
echo ""
