"""
Model Management API Endpoints
Hot-swap models, download new models, and monitor performance
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
import logging
import asyncio
from pathlib import Path
import subprocess
import json

from services.hot_swap_model_manager import get_hot_swap_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/models", tags=["model_management"])

class ModelSwapRequest(BaseModel):
    model_name: str = Field(..., description="Name of model to swap to")
    force: bool = Field(False, description="Force reload even if already loaded")

class ModelDownloadRequest(BaseModel):
    model_category: str = Field(..., description="Category (llama3, mistral, qwen, etc)")
    model_variant: str = Field(..., description="Variant (8b, 7b_v0.3, etc)")

class ModelTestRequest(BaseModel):
    prompt: str = Field("Hello, how are you?", description="Test prompt")
    max_tokens: int = Field(50, description="Maximum tokens to generate")
    temperature: float = Field(0.7, description="Temperature for generation")

@router.get("/available")
async def get_available_models():
    """Get list of available models for hot-swapping"""
    try:
        manager = get_hot_swap_manager()
        available = manager.get_available_models()
        current = manager.get_current_model_info()
        
        # Check which models are actually downloaded
        models_info = []
        for model_name in available:
            config = manager.config["hot_swap"]["models"][model_name]
            model_path = Path(config["path"])
            
            models_info.append({
                "name": model_name,
                "path": str(model_path),
                "exists": model_path.exists(),
                "size_gb": model_path.stat().st_size / (1024**3) if model_path.exists() else 0,
                "config": config,
                "is_current": model_name == current.get("name")
            })
        
        return {
            "current_model": current,
            "available_models": models_info,
            "total_models": len(models_info),
            "downloaded_models": sum(1 for m in models_info if m["exists"])
        }
    except Exception as e:
        logger.error(f"Failed to get available models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/swap")
async def swap_model(request: ModelSwapRequest):
    """Hot-swap to a different model"""
    try:
        manager = get_hot_swap_manager()
        
        logger.info(f"Swapping to model: {request.model_name}")
        
        # Perform swap
        success = manager.swap_model(request.model_name, force=request.force)
        
        if success:
            current = manager.get_current_model_info()
            return {
                "status": "success",
                "message": f"Successfully swapped to {request.model_name}",
                "current_model": current
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to swap to {request.model_name}"
            )
            
    except Exception as e:
        logger.error(f"Model swap failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test")
async def test_model(request: ModelTestRequest):
    """Test current model with a prompt"""
    try:
        manager = get_hot_swap_manager()
        
        if not manager.current_model:
            raise HTTPException(status_code=400, detail="No model loaded")
        
        # Generate response
        response = await manager.async_generate(
            request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        if response:
            return {
                "status": "success",
                "model": manager.current_model_name,
                "prompt": request.prompt,
                "response": response.get("choices", [{}])[0].get("text", ""),
                "metrics": manager.performance_metrics.get(manager.current_model_name, {})
            }
        else:
            raise HTTPException(status_code=500, detail="Generation failed")
            
    except Exception as e:
        logger.error(f"Model test failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance")
async def get_performance_metrics():
    """Get performance metrics for all models"""
    try:
        manager = get_hot_swap_manager()
        report = manager.get_performance_report()
        
        # Add system metrics
        import psutil
        report["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "memory_available_gb": psutil.virtual_memory().available / (1024**3),
            "disk_usage_percent": psutil.disk_usage("/").percent
        }
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/download")
async def download_model(request: ModelDownloadRequest, background_tasks: BackgroundTasks):
    """Download a new model in the background"""
    try:
        # Import the download script
        from scripts.download_latest_models import ModelDownloader, LATEST_MODELS
        
        # Validate request
        if request.model_category not in LATEST_MODELS:
            raise HTTPException(status_code=400, detail=f"Unknown category: {request.model_category}")
        
        if request.model_variant not in LATEST_MODELS[request.model_category]:
            raise HTTPException(status_code=400, detail=f"Unknown variant: {request.model_variant}")
        
        model_info = LATEST_MODELS[request.model_category][request.model_variant]
        
        # Check if already exists
        downloader = ModelDownloader()
        dest_path = Path("models/base") / model_info["name"]
        
        if dest_path.exists():
            return {
                "status": "exists",
                "message": f"Model {model_info['name']} already downloaded",
                "path": str(dest_path),
                "size_gb": dest_path.stat().st_size / (1024**3)
            }
        
        # Start download in background
        background_tasks.add_task(
            downloader.download_model,
            request.model_category,
            request.model_variant
        )
        
        return {
            "status": "downloading",
            "message": f"Download started for {model_info['name']}",
            "expected_size": model_info.get("size"),
            "description": model_info["description"]
        }
        
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="Download script not available"
        )
    except Exception as e:
        logger.error(f"Download initiation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/status")
async def get_download_status():
    """Check status of model downloads"""
    try:
        # Check for running wget/curl processes
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        
        downloads = []
        for line in result.stdout.split("\n"):
            if "wget" in line or "curl" in line:
                if ".gguf" in line:
                    # Extract model name from command
                    parts = line.split()
                    for part in parts:
                        if ".gguf" in part:
                            downloads.append({
                                "file": Path(part).name,
                                "status": "downloading"
                            })
        
        return {
            "active_downloads": len(downloads),
            "downloads": downloads
        }
        
    except Exception as e:
        logger.error(f"Failed to check download status: {e}")
        return {"active_downloads": 0, "downloads": []}

@router.post("/auto-optimize")
async def enable_auto_optimization(enable: bool = True):
    """Enable/disable automatic model optimization based on performance"""
    try:
        manager = get_hot_swap_manager()
        manager.config["hot_swap"]["enabled"] = enable
        
        # Save config
        config_path = Path("config/model_hot_swap.json")
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(manager.config, f, indent=2)
        
        return {
            "status": "success",
            "auto_optimization": enable,
            "message": f"Auto-optimization {'enabled' if enable else 'disabled'}"
        }
        
    except Exception as e:
        logger.error(f"Failed to update auto-optimization: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommended")
async def get_recommended_model():
    """Get recommended model based on current system resources"""
    try:
        import psutil
        import os
        
        # Check available resources
        memory_gb = psutil.virtual_memory().available / (1024**3)
        cpu_count = os.cpu_count()
        
        # Check for GPU
        has_gpu = False
        try:
            import torch
            has_gpu = torch.cuda.is_available()
            if has_gpu:
                vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        except:
            vram_gb = 0
        
        # Recommend based on resources
        if has_gpu and vram_gb >= 24:
            recommended = "llama3_70b"
            reason = f"GPU with {vram_gb:.1f}GB VRAM can handle large models"
        elif has_gpu and vram_gb >= 8:
            recommended = "llama3_8b"
            reason = f"GPU with {vram_gb:.1f}GB VRAM suitable for 8B models"
        elif memory_gb >= 32:
            recommended = "mistral_7b"
            reason = f"{memory_gb:.1f}GB RAM available for 7B models"
        elif memory_gb >= 16:
            recommended = "qwen_7b"
            reason = f"{memory_gb:.1f}GB RAM suitable for efficient 7B models"
        else:
            recommended = "phi_mini"
            reason = f"Limited resources ({memory_gb:.1f}GB RAM) - using compact model"
        
        return {
            "recommended_model": recommended,
            "reason": reason,
            "system_info": {
                "memory_gb": memory_gb,
                "cpu_cores": cpu_count,
                "has_gpu": has_gpu,
                "vram_gb": vram_gb if has_gpu else 0
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get recommendation: {e}")
        raise HTTPException(status_code=500, detail=str(e))