#!/usr/bin/env python3
"""
Complete Data Loading Pipeline
Loads OCS data, generates embeddings, and sets up Milvus collections
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_script(script_name, description):
    """Run a Python script and handle errors"""
    try:
        logger.info(f"Starting: {description}")
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=True, text=True, check=True)
        logger.info(f"Completed: {description}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Error: {e.stderr}")
        return False

def main():
    """Run complete data loading pipeline"""
    logger.info("=== WeedGo AI Engine Data Loading Pipeline ===")
    
    # Get script directory
    script_dir = Path(__file__).parent
    
    # Define pipeline steps
    pipeline_steps = [
        (script_dir / "analyze_ocs_data.py", "OCS Data Analysis"),
        (script_dir / "process_ocs_data.py", "OCS Data Processing and Database Loading"),
        (script_dir / "generate_embeddings.py", "Product Embeddings Generation"),
        (script_dir / "setup_milvus.py", "Milvus Vector Database Setup")
    ]
    
    # Execute pipeline steps
    success_count = 0
    for script_path, description in pipeline_steps:
        if script_path.exists():
            if run_script(str(script_path), description):
                success_count += 1
            else:
                logger.error(f"Pipeline failed at step: {description}")
                break
        else:
            logger.warning(f"Script not found: {script_path}")
    
    # Print results
    logger.info(f"\n=== Pipeline Complete ===")
    logger.info(f"Successfully completed {success_count}/{len(pipeline_steps)} steps")
    
    if success_count == len(pipeline_steps):
        logger.info("✅ All data loaded successfully!")
        logger.info("The WeedGo AI Engine is ready for use.")
        
        # Print usage information
        print("\n🚀 Next Steps:")
        print("1. Start the services: make up")
        print("2. Check health: curl http://localhost:8501/health")
        print("3. Test budtender: curl -X POST http://localhost:8501/budtender/chat -H 'Content-Type: application/json' -d '{\"message\": \"Hello, I need help finding a strain for relaxation\"}'")
        print("4. API documentation: http://localhost:5100/swagger")
        
    else:
        logger.error("❌ Pipeline failed. Check logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()