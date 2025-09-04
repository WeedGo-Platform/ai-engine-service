#!/usr/bin/env python3
"""
Setup Model Directory Structure
Creates organized directories for different model categories
"""
import os
from pathlib import Path
import json
import shutil

def setup_model_directories():
    """Create organized model directory structure"""
    
    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / "models"
    
    # Define directory structure
    directories = {
        "base": "General purpose models (Mistral, Llama)",
        "multilingual": "Multilingual models (Qwen, Aya, BLOOM)",
        "specialized": "Task-specific models (Code, Medical, etc.)",
        "small": "Fast models for quick responses (Phi, TinyLlama)",
        "embeddings": "Embedding models for RAG",
        "translation": "Dedicated translation models",
        "experimental": "Testing new models",
        "deprecated": "Old models (archived)"
    }
    
    # Create directories
    for dir_name, description in directories.items():
        dir_path = models_dir / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create README in each directory
        readme_path = dir_path / "README.md"
        readme_content = f"""# {dir_name.title()} Models

{description}

## Models in this directory:
<!-- Auto-populated by model scanner -->

## Usage:
Models in this directory are automatically discovered at startup.
"""
        with open(readme_path, 'w') as f:
            f.write(readme_content)
        
        print(f"✓ Created {dir_path}")
    
    # Move existing models to appropriate directories
    existing_models = list(models_dir.glob("*.gguf"))
    
    for model_file in existing_models:
        name_lower = model_file.name.lower()
        
        # Determine target directory
        if "mistral" in name_lower or "llama" in name_lower:
            target_dir = "base"
        elif "qwen" in name_lower or "aya" in name_lower or "bloom" in name_lower:
            target_dir = "multilingual"
        elif "phi" in name_lower or "tiny" in name_lower:
            target_dir = "small"
        elif "embed" in name_lower or "bge" in name_lower or "e5" in name_lower:
            target_dir = "embeddings"
        else:
            target_dir = "experimental"
        
        # Move file
        target_path = models_dir / target_dir / model_file.name
        if model_file != target_path and not target_path.exists():
            shutil.move(str(model_file), str(target_path))
            print(f"→ Moved {model_file.name} to {target_dir}/")
    
    # Create model registry file
    registry_path = models_dir / "model_registry.json"
    registry = {
        "version": "1.0",
        "directories": directories,
        "models": {},
        "last_scan": ""
    }
    
    with open(registry_path, 'w') as f:
        json.dump(registry, f, indent=2)
    
    print(f"\n✓ Model directory structure created at {models_dir}")
    print("✓ Model registry initialized")
    
    return models_dir

if __name__ == "__main__":
    setup_model_directories()