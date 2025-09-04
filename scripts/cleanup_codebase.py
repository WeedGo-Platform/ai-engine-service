#!/usr/bin/env python3
"""
Codebase Cleanup Script
Removes duplicates, organizes files, and restructures the codebase
"""
import os
import shutil
import json
from pathlib import Path
from typing import List, Set, Dict
import hashlib

class CodebaseCleanup:
    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.docs_to_move = []
        self.tests_to_move = []
        self.training_data_to_move = []
        self.duplicates_to_remove = []
        self.orphaned_files = []
        
    def find_duplicate_files(self) -> Dict[str, List[Path]]:
        """Find duplicate files based on content hash"""
        file_hashes = {}
        
        # Skip certain directories and file types
        skip_dirs = {'node_modules', '.git', '.venv', '__pycache__', 'models', '.next', 'dist', 'build'}
        skip_extensions = {'.pyc', '.pyo', '.so', '.dylib', '.dll', '.gguf'}
        
        for file_path in self.base_path.rglob("*"):
            # Skip if in excluded directory
            if any(skip_dir in str(file_path) for skip_dir in skip_dirs):
                continue
                
            # Skip if has excluded extension
            if file_path.suffix in skip_extensions:
                continue
                
            if file_path.is_file() and not str(file_path.name).startswith('.'):
                try:
                    # Only check Python, JSON, MD files for duplicates
                    if file_path.suffix in ['.py', '.json', '.md', '.txt', '.yml', '.yaml']:
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        
                        if file_hash not in file_hashes:
                            file_hashes[file_hash] = []
                        file_hashes[file_hash].append(file_path)
                except:
                    pass
        
        # Return only duplicates
        return {k: v for k, v in file_hashes.items() if len(v) > 1}
    
    def identify_files_to_move(self):
        """Identify files that should be moved to proper directories"""
        
        # Documentation files in root
        for file in self.base_path.glob("*.md"):
            self.docs_to_move.append(file)
        
        # Test files in root
        for file in self.base_path.glob("test_*.py"):
            self.tests_to_move.append(file)
        
        # Training data in root
        for file in self.base_path.glob("*training*.json"):
            self.training_data_to_move.append(file)
        for file in self.base_path.glob("cannabis_*.json"):
            if "training" in str(file).lower():
                self.training_data_to_move.append(file)
    
    def identify_orphaned_files(self):
        """Identify orphaned and unused files"""
        orphaned_patterns = [
            "*_old.py",
            "*_backup.py",
            "*_deprecated.py",
            "*.log",
            "*_test.json",
            "test_output_*",
        ]
        
        for pattern in orphaned_patterns:
            for file in self.base_path.rglob(pattern):
                self.orphaned_files.append(file)
    
    def create_new_structure(self):
        """Create the new folder structure"""
        new_dirs = [
            "src/api",
            "src/services", 
            "src/models",
            "src/middleware",
            "src/utils",
            "tests/unit",
            "tests/integration",
            "tests/e2e",
            "training/datasets",
            "training/models",
            "training/results",
            "docs/api",
            "docs/architecture",
            "docs/deployment",
            "docs/guides",
            "docs/status",
            "logs"
        ]
        
        for dir_path in new_dirs:
            full_path = self.base_path / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
    
    def move_files(self, dry_run=True):
        """Move files to their proper locations"""
        moves = []
        
        # Move documentation
        for doc in self.docs_to_move:
            if "STATUS" in doc.name.upper():
                dest = self.base_path / "docs" / "status" / doc.name
            elif "ARCHITECTURE" in doc.name.upper() or "DESIGN" in doc.name.upper():
                dest = self.base_path / "docs" / "architecture" / doc.name
            elif "DEPLOY" in doc.name.upper() or "SETUP" in doc.name.upper():
                dest = self.base_path / "docs" / "deployment" / doc.name
            elif "API" in doc.name.upper():
                dest = self.base_path / "docs" / "api" / doc.name
            else:
                dest = self.base_path / "docs" / "guides" / doc.name
            
            moves.append((doc, dest))
        
        # Move tests
        for test in self.tests_to_move:
            if "integration" in test.name.lower():
                dest = self.base_path / "tests" / "integration" / test.name
            elif "e2e" in test.name.lower():
                dest = self.base_path / "tests" / "e2e" / test.name
            else:
                dest = self.base_path / "tests" / "unit" / test.name
            
            moves.append((test, dest))
        
        # Move training data
        for data in self.training_data_to_move:
            dest = self.base_path / "training" / "datasets" / data.name
            moves.append((data, dest))
        
        # Execute moves
        for src, dest in moves:
            if dry_run:
                print(f"Would move: {src.name} -> {dest.relative_to(self.base_path)}")
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dest))
                print(f"Moved: {src.name} -> {dest.relative_to(self.base_path)}")
        
        return len(moves)
    
    def remove_duplicates(self, dry_run=True):
        """Remove duplicate files, keeping the most recent"""
        duplicates = self.find_duplicate_files()
        removed_count = 0
        
        for file_hash, files in duplicates.items():
            # Sort by modification time, keep the newest
            files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            for file_to_remove in files[1:]:  # Keep first (newest), remove others
                if dry_run:
                    print(f"Would remove duplicate: {file_to_remove.relative_to(self.base_path)}")
                else:
                    file_to_remove.unlink()
                    print(f"Removed duplicate: {file_to_remove.relative_to(self.base_path)}")
                removed_count += 1
        
        return removed_count
    
    def remove_orphaned(self, dry_run=True):
        """Remove orphaned files"""
        removed_count = 0
        
        for file in self.orphaned_files:
            if dry_run:
                print(f"Would remove orphaned: {file.relative_to(self.base_path)}")
            else:
                file.unlink()
                print(f"Removed orphaned: {file.relative_to(self.base_path)}")
            removed_count += 1
        
        return removed_count
    
    def reorganize_services(self, dry_run=True):
        """Move services to src/services"""
        services_dir = self.base_path / "services"
        if services_dir.exists():
            dest = self.base_path / "src" / "services"
            if dry_run:
                print(f"Would move: services/ -> src/services/")
            else:
                shutil.move(str(services_dir), str(dest))
                print(f"Moved: services/ -> src/services/")
    
    def cleanup_root_directory(self, dry_run=True):
        """Move Python files from root to appropriate src subdirectories"""
        api_files = ["api_server.py", "llm_api.py", "rag_api.py"]
        
        for file_name in api_files:
            file_path = self.base_path / file_name
            if file_path.exists():
                dest = self.base_path / "src" / "api" / file_name
                if dry_run:
                    print(f"Would move: {file_name} -> src/api/{file_name}")
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(file_path), str(dest))
                    print(f"Moved: {file_name} -> src/api/{file_name}")
    
    def generate_cleanup_report(self) -> Dict:
        """Generate a report of what will be cleaned up"""
        self.identify_files_to_move()
        self.identify_orphaned_files()
        duplicates = self.find_duplicate_files()
        
        report = {
            "documentation_files": len(self.docs_to_move),
            "test_files": len(self.tests_to_move),
            "training_data_files": len(self.training_data_to_move),
            "duplicate_files": sum(len(files) - 1 for files in duplicates.values()),
            "orphaned_files": len(self.orphaned_files),
            "total_files_to_process": (
                len(self.docs_to_move) + 
                len(self.tests_to_move) + 
                len(self.training_data_to_move) +
                sum(len(files) - 1 for files in duplicates.values()) +
                len(self.orphaned_files)
            )
        }
        
        return report
    
    def execute_cleanup(self, dry_run=True):
        """Execute the full cleanup process"""
        print("\n" + "="*60)
        print("CODEBASE CLEANUP SCRIPT")
        print("="*60)
        
        if dry_run:
            print("\n[DRY RUN MODE - No actual changes will be made]\n")
        
        # Generate report
        report = self.generate_cleanup_report()
        print("\nCleanup Summary:")
        print(f"  Documentation files to move: {report['documentation_files']}")
        print(f"  Test files to move: {report['test_files']}")
        print(f"  Training data files to move: {report['training_data_files']}")
        print(f"  Duplicate files to remove: {report['duplicate_files']}")
        print(f"  Orphaned files to remove: {report['orphaned_files']}")
        print(f"  Total files to process: {report['total_files_to_process']}")
        
        if not dry_run:
            response = input("\nProceed with cleanup? (yes/no): ")
            if response.lower() != 'yes':
                print("Cleanup cancelled.")
                return
        
        print("\n" + "-"*60)
        print("Creating new directory structure...")
        self.create_new_structure()
        
        print("\n" + "-"*60)
        print("Moving files to proper locations...")
        moved = self.move_files(dry_run)
        
        print("\n" + "-"*60)
        print("Removing duplicate files...")
        removed_dups = self.remove_duplicates(dry_run)
        
        print("\n" + "-"*60)
        print("Removing orphaned files...")
        removed_orphaned = self.remove_orphaned(dry_run)
        
        print("\n" + "-"*60)
        print("Reorganizing services...")
        self.reorganize_services(dry_run)
        
        print("\n" + "-"*60)
        print("Cleaning up root directory...")
        self.cleanup_root_directory(dry_run)
        
        print("\n" + "="*60)
        print("CLEANUP COMPLETE")
        print(f"  Files moved: {moved}")
        print(f"  Duplicates removed: {removed_dups}")
        print(f"  Orphaned files removed: {removed_orphaned}")
        print("="*60 + "\n")

if __name__ == "__main__":
    import sys
    
    # Get the base path
    base_path = "/Users/charrcy/projects/WeedGo/microservices/ai-engine-service"
    
    # Check for --execute flag
    dry_run = "--execute" not in sys.argv
    
    cleanup = CodebaseCleanup(base_path)
    cleanup.execute_cleanup(dry_run=dry_run)
    
    if dry_run:
        print("\nTo execute the cleanup, run:")
        print("  python scripts/cleanup_codebase.py --execute\n")