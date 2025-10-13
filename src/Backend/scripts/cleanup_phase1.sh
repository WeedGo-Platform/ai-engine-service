#!/bin/bash
# Phase 1: Immediate Cleanup Script
# Safe, low-risk cleanup operations
# Run from: src/Backend/

set -e  # Exit on error

echo "========================================="
echo "Code Cleanup - Phase 1: Immediate Actions"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track what we're doing
DELETED_FILES=()
CLEANED_ITEMS=0

echo -e "${YELLOW}Step 1: Delete Orphaned Frontend AGI Files${NC}"
echo "-------------------------------------------"

if [ -f "../Frontend/weedgo-commerce/src/services/agiService.ts" ]; then
    echo "Deleting: src/Frontend/weedgo-commerce/src/services/agiService.ts"
    rm -f "../Frontend/weedgo-commerce/src/services/agiService.ts"
    DELETED_FILES+=("agiService.ts")
    ((CLEANED_ITEMS++))
else
    echo "  Already deleted or not found: agiService.ts"
fi

if [ -f "../Frontend/weedgo-commerce/src/hooks/useAGIEngine.ts" ]; then
    echo "Deleting: src/Frontend/weedgo-commerce/src/hooks/useAGIEngine.ts"
    rm -f "../Frontend/weedgo-commerce/src/hooks/useAGIEngine.ts"
    DELETED_FILES+=("useAGIEngine.ts")
    ((CLEANED_ITEMS++))
else
    echo "  Already deleted or not found: useAGIEngine.ts"
fi

echo ""
echo -e "${YELLOW}Step 2: Delete Orphaned Payment Service${NC}"
echo "----------------------------------------"

if [ -f "services/payments/payment_service_v2.py" ]; then
    echo "Deleting: services/payments/payment_service_v2.py (orphaned duplicate)"
    rm -f "services/payments/payment_service_v2.py"
    DELETED_FILES+=("payment_service_v2.py")
    ((CLEANED_ITEMS++))
else
    echo "  Already deleted or not found: payment_service_v2.py"
fi

echo ""
echo -e "${YELLOW}Step 3: Delete Backup File${NC}"
echo "---------------------------"

if [ -f "api/kiosk_endpoints_backup.py" ]; then
    echo "Deleting: api/kiosk_endpoints_backup.py"
    rm -f "api/kiosk_endpoints_backup.py"
    DELETED_FILES+=("kiosk_endpoints_backup.py")
    ((CLEANED_ITEMS++))
else
    echo "  Already deleted or not found: kiosk_endpoints_backup.py"
fi

echo ""
echo -e "${YELLOW}Step 4: Clean Python Cache Files${NC}"
echo "---------------------------------"

echo "Finding and removing __pycache__ directories..."
CACHE_COUNT=$(find . -type d -name "__pycache__" 2>/dev/null | wc -l | tr -d ' ')
echo "Found $CACHE_COUNT __pycache__ directories"

if [ "$CACHE_COUNT" -gt 0 ]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    echo "  Deleted __pycache__ directories"
    ((CLEANED_ITEMS++))
fi

echo ""
echo "Finding and removing .pyc files..."
PYC_COUNT=$(find . -name "*.pyc" 2>/dev/null | wc -l | tr -d ' ')
echo "Found $PYC_COUNT .pyc files"

if [ "$PYC_COUNT" -gt 0 ]; then
    find . -name "*.pyc" -delete 2>/dev/null || true
    echo "  Deleted .pyc files"
    ((CLEANED_ITEMS++))
fi

echo ""
echo -e "${YELLOW}Step 5: Fix Duplicate Dependencies${NC}"
echo "-----------------------------------"

echo "Checking requirements.txt for duplicates..."

if [ -f "requirements.txt" ]; then
    # Create backup
    cp requirements.txt requirements.txt.backup
    echo "  Created backup: requirements.txt.backup"

    # Remove duplicate asyncpg and redis entries
    # Keep first occurrence, remove second
    sed -i.tmp '/^asyncpg==0.29.0$/{ :a; n; /^asyncpg==0.29.0$/d; ba }' requirements.txt 2>/dev/null || true
    sed -i.tmp '/^redis\[hiredis\]==5.0.1$/{ :a; n; /^redis\[hiredis\]==5.0.1$/d; ba }' requirements.txt 2>/dev/null || true
    rm -f requirements.txt.tmp 2>/dev/null || true

    echo "  Removed duplicate dependencies"
    ((CLEANED_ITEMS++))
else
    echo "  requirements.txt not found"
fi

echo ""
echo -e "${YELLOW}Step 6: Update .gitignore${NC}"
echo "-----------------------------"

if [ -f ".gitignore" ]; then
    # Check if __pycache__ is already in .gitignore
    if ! grep -q "__pycache__" .gitignore; then
        echo "Adding Python cache patterns to .gitignore..."
        cat >> .gitignore << 'EOF'

# Python cache
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
*.pyc
EOF
        echo "  Updated .gitignore"
        ((CLEANED_ITEMS++))
    else
        echo "  .gitignore already has cache patterns"
    fi
else
    echo "  .gitignore not found"
fi

echo ""
echo "========================================="
echo -e "${GREEN}Phase 1 Cleanup Complete!${NC}"
echo "========================================="
echo ""
echo "Summary:"
echo "  Files deleted: ${#DELETED_FILES[@]}"
if [ ${#DELETED_FILES[@]} -gt 0 ]; then
    for file in "${DELETED_FILES[@]}"; do
        echo "    - $file"
    done
fi
echo "  Cache directories cleaned: $CACHE_COUNT"
echo "  .pyc files removed: $PYC_COUNT"
echo "  Total cleanup actions: $CLEANED_ITEMS"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Review the changes with: git status"
echo "  2. Test that nothing broke: npm run dev / python api_server.py"
echo "  3. Commit changes: git add . && git commit -m 'chore: Phase 1 cleanup - remove orphaned files'"
echo "  4. Review CODE_CLEANUP_REPORT.md for Phase 2 recommendations"
echo ""
echo "Backup created: requirements.txt.backup"
echo ""
