#!/usr/bin/env python3
"""
Reorganize AI Engine Codebase
Focus on removing hardcoded content and organizing structure
"""
import os
import shutil
from pathlib import Path
import json

def reorganize():
    base_path = Path("/Users/charrcy/projects/WeedGo/microservices/ai-engine-service")
    
    # Create organized structure
    print("Creating organized directory structure...")
    
    # Move all documentation to docs folder
    docs_dir = base_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    
    # Categories for documentation
    doc_categories = {
        "architecture": ["ARCHITECTURE", "DESIGN", "SYSTEM", "FLOW"],
        "deployment": ["DEPLOY", "SETUP", "INSTALL", "CONFIG"],
        "api": ["API", "ENDPOINT", "REST", "GRAPHQL"],
        "guides": ["GUIDE", "TUTORIAL", "WALKTHROUGH", "README"],
        "status": ["STATUS", "PROGRESS", "COMPLETE", "FINAL"]
    }
    
    # Create subdirectories
    for category in doc_categories.keys():
        (docs_dir / category).mkdir(exist_ok=True)
    
    # Move .md files to appropriate folders
    moved_docs = 0
    for md_file in base_path.glob("*.md"):
        moved = False
        for category, keywords in doc_categories.items():
            if any(keyword in md_file.name.upper() for keyword in keywords):
                dest = docs_dir / category / md_file.name
                shutil.move(str(md_file), str(dest))
                print(f"Moved {md_file.name} to docs/{category}/")
                moved_docs += 1
                moved = True
                break
        
        if not moved:
            # Default to guides
            dest = docs_dir / "guides" / md_file.name
            shutil.move(str(md_file), str(dest))
            print(f"Moved {md_file.name} to docs/guides/")
            moved_docs += 1
    
    print(f"Moved {moved_docs} documentation files")
    
    # Move test files to tests directory
    tests_dir = base_path / "tests"
    tests_dir.mkdir(exist_ok=True)
    
    moved_tests = 0
    for test_file in base_path.glob("test_*.py"):
        dest = tests_dir / test_file.name
        shutil.move(str(test_file), str(dest))
        print(f"Moved {test_file.name} to tests/")
        moved_tests += 1
    
    print(f"Moved {moved_tests} test files")
    
    # Move training data
    training_dir = base_path / "training_data"
    training_dir.mkdir(exist_ok=True)
    
    moved_training = 0
    for pattern in ["*training*.json", "cannabis_*.json", "joint_*.json"]:
        for training_file in base_path.glob(pattern):
            dest = training_dir / training_file.name
            shutil.move(str(training_file), str(dest))
            print(f"Moved {training_file.name} to training_data/")
            moved_training += 1
    
    print(f"Moved {moved_training} training data files")
    
    # Clean up log files
    removed_logs = 0
    for log_file in base_path.glob("*.log"):
        if log_file.name not in ["api_server.log", "system.log"]:  # Keep active logs
            log_file.unlink()
            print(f"Removed {log_file.name}")
            removed_logs += 1
    
    print(f"Removed {removed_logs} log files")
    
    # Remove deprecated UI translations service (replaced with model-based)
    deprecated_files = [
        "services/ui_translations.py",  # Hardcoded translations
        "services/language_manager.py",  # Hardcoded language content
        "scripts/setup_multilingual_database.py",  # Hardcoded translations
    ]
    
    removed_deprecated = 0
    for file_path in deprecated_files:
        full_path = base_path / file_path
        if full_path.exists():
            # Archive it first
            archive_dir = base_path / "archive"
            archive_dir.mkdir(exist_ok=True)
            archive_path = archive_dir / full_path.name
            shutil.move(str(full_path), str(archive_path))
            print(f"Archived {file_path} (contained hardcoded translations)")
            removed_deprecated += 1
    
    print(f"Archived {removed_deprecated} deprecated files")
    
    # Create a clean prompts structure
    prompts_dir = base_path / "prompts"
    clean_prompt_structure = {
        "system": {},
        "templates": {},
        "multilingual": {},
        "personalities": {}
    }
    
    # Consolidate all prompt files
    for prompt_file in prompts_dir.glob("*.json"):
        try:
            with open(prompt_file, 'r') as f:
                data = json.load(f)
            
            # Categorize prompts
            if "system" in prompt_file.name.lower() or "role" in data:
                clean_prompt_structure["system"][prompt_file.stem] = data
            elif "template" in prompt_file.name.lower():
                clean_prompt_structure["templates"][prompt_file.stem] = data
            elif "multilingual" in prompt_file.name.lower():
                clean_prompt_structure["multilingual"][prompt_file.stem] = data
            elif "personality" in prompt_file.name.lower():
                clean_prompt_structure["personalities"][prompt_file.stem] = data
        except:
            pass
    
    # Save consolidated prompts
    consolidated_prompts_file = prompts_dir / "consolidated_prompts.json"
    with open(consolidated_prompts_file, 'w') as f:
        json.dump(clean_prompt_structure, f, indent=2)
    
    print(f"Created consolidated prompts file")
    
    # Summary
    print("\n" + "="*60)
    print("REORGANIZATION COMPLETE")
    print("="*60)
    print(f"Documentation files moved: {moved_docs}")
    print(f"Test files moved: {moved_tests}")
    print(f"Training data files moved: {moved_training}")
    print(f"Log files removed: {removed_logs}")
    print(f"Deprecated files archived: {removed_deprecated}")
    print("\nNext steps:")
    print("1. Update import paths in Python files")
    print("2. Remove hardcoded translations from remaining files")
    print("3. Use ModelTranslationService for all translations")
    print("4. Load prompts from consolidated_prompts.json")
    print("="*60)

if __name__ == "__main__":
    reorganize()