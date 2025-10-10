# Code Cleanup - Quick Start Guide

## Overview

This guide provides step-by-step instructions for cleaning up the AI Engine Service codebase based on the comprehensive analysis in `CODE_CLEANUP_REPORT.md`.

---

## 🚀 Quick Start (5 minutes)

### Phase 1: Immediate Cleanup (Safe, Low-Risk)

Run the automated cleanup script:

```bash
cd src/Backend
./scripts/cleanup_phase1.sh
```

This will:
- ✅ Delete 2 orphaned frontend AGI files
- ✅ Delete 1 orphaned payment service duplicate
- ✅ Delete 1 backup file
- ✅ Remove ~200 Python cache directories
- ✅ Fix duplicate dependencies in requirements.txt
- ✅ Update .gitignore

**Estimated time:** 1-2 minutes

---

## 📂 Phase 2: Organization (Medium Risk)

### Step 1: Organize Test Files

Move 50 misplaced test files to proper `tests/` directory:

```bash
cd src/Backend
python3 scripts/organize_tests.py
```

This creates a structured test directory:
```
tests/
├── api/           # API endpoint tests
├── services/      # Service layer tests
├── integration/   # Integration tests
├── voice/         # Voice/audio tests
├── database/      # Database tests
├── communication/ # Email/OTP tests
└── unit/          # Other unit tests
```

**Estimated time:** 5 minutes

### Step 2: Archive Utility Scripts

Move 32 one-off utility scripts to archive:

```bash
cd src/Backend
python3 scripts/archive_utilities.py
```

This organizes scripts into:
```
scripts/archive/
├── migrations/        # Migration scripts
├── diagnostics/       # Check/verify scripts
├── debug/            # Debug scripts
├── data_manipulation/ # Add/update scripts
└── setup/            # Create/generate scripts
```

**Estimated time:** 3 minutes

---

## 🎯 Phase 3: Strategic Decision Required

### DDD Integration (231 Orphaned Files)

**The Situation:**
- 231 DDD domain model files exist in `ddd_refactored/`
- 0% are integrated with the API layer
- All APIs still use legacy `services/` architecture

**You Must Choose:**

#### Option A: Fast-Track Integration (Recommended)
- Dedicate 2-3 weeks to integrate DDD
- Follow `IMPLEMENTATION_PLAN.md`
- Start with one bounded context (e.g., Payment Processing)
- **Timeline:** 2-3 weeks full-time

#### Option B: Incremental Integration
- Pick ONE context per sprint
- Fully integrate before moving to next
- **Timeline:** 14 sprints (3-4 months)

#### Option C: Archive and Revisit
- Move `ddd_refactored/` to `ddd_refactored_archived/`
- Continue with current architecture
- Revisit when resources allow
- **Timeline:** TBD

**Action Required:**
1. Review `DDD_ARCHITECTURE_REFACTORING.md`
2. Review `IMPLEMENTATION_PLAN.md`
3. Schedule team discussion
4. Make decision and document it

---

## ✅ Verification Steps

After each phase:

### 1. Check Git Status
```bash
git status
```

### 2. Run Tests
```bash
# Backend tests
pytest tests/

# Frontend tests (if applicable)
cd src/Frontend/ai-admin-dashboard && npm test
cd src/Frontend/weedgo-commerce && npm test
```

### 3. Start Servers
```bash
# Backend
python main_server.py

# Frontend
npm run dev
```

### 4. Verify No Breaking Changes
- Check API endpoints still work
- Verify frontend loads
- Test critical user flows

---

## 📊 Expected Results

### After Phase 1:
- ✅ 4 orphaned files deleted (~500 lines)
- ✅ 200+ cache directories cleaned
- ✅ Clean .gitignore
- ✅ No duplicate dependencies

### After Phase 2:
- ✅ 50 test files properly organized
- ✅ 32 utility scripts archived
- ✅ Clean project root directory
- ✅ Better code organization

### After Phase 3:
- ✅ DDD integration complete OR
- ✅ Clear decision documented
- ✅ Reduced technical debt
- ✅ Cleaner architecture

---

## 🔄 Rollback Instructions

If something goes wrong:

### Phase 1 Rollback:
```bash
# Requirements.txt was backed up
cp requirements.txt.backup requirements.txt

# Use git to restore deleted files
git checkout HEAD -- <file_path>
```

### Phase 2 Rollback:
```bash
# Move files back
# (Scripts create backups automatically)

# Or use git
git checkout HEAD -- .
```

---

## 📝 Commit Messages

### After Phase 1:
```bash
git add .
git commit -m "chore: Phase 1 cleanup - remove orphaned files and clean cache

- Delete orphaned AGI files (agiService.ts, useAGIEngine.ts)
- Delete duplicate payment_service_v2.py
- Delete backup file kiosk_endpoints_backup.py
- Clean Python cache files (__pycache__, *.pyc)
- Fix duplicate dependencies in requirements.txt
- Update .gitignore

See CODE_CLEANUP_REPORT.md for details"
```

### After Phase 2 (Tests):
```bash
git add .
git commit -m "chore: organize test files into proper structure

- Move 50 test files from root to tests/ directory
- Create categorized test structure (api, services, integration, etc.)
- Add __init__.py to test modules

See CODE_CLEANUP_REPORT.md for details"
```

### After Phase 2 (Scripts):
```bash
git add .
git commit -m "chore: archive utility scripts

- Move 32 one-off scripts to scripts/archive/
- Categorize by purpose (migrations, diagnostics, debug, etc.)
- Add README files for each category

See CODE_CLEANUP_REPORT.md for details"
```

---

## 🛠️ Recommended Tools

Install these for ongoing maintenance:

```bash
# Dead code detection
pip install vulture
vulture src/Backend --min-confidence 80

# Unused imports
pip install autoflake
autoflake --remove-all-unused-imports --in-place --recursive src/Backend

# Code formatting (already installed)
black src/Backend

# Import sorting
pip install isort
isort src/Backend

# Type checking
mypy src/Backend
```

---

## 📞 Support

- **Full Report:** See `CODE_CLEANUP_REPORT.md`
- **Issues:** Check git history or ask team
- **Questions:** Review DDD_ARCHITECTURE_REFACTORING.md

---

## ⚠️ Important Notes

1. **Backup First:** All scripts create backups automatically
2. **Test Everything:** Run full test suite after each phase
3. **Incremental Commits:** Commit after each successful phase
4. **Team Communication:** Notify team before major changes
5. **Documentation:** Update relevant docs after cleanup

---

**Last Updated:** 2025-10-09
**Created By:** Claude Code Cleanup Analysis
