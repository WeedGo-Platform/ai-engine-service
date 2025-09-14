"""
File Upload Handler for Tenant Resources
Handles logo uploads and other tenant assets
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, status
from fastapi.responses import FileResponse
from typing import Optional
from uuid import UUID
import os
import shutil
from pathlib import Path
import aiofiles
import hashlib
from PIL import Image
import io

from core.services.tenant_service import TenantService
from core.dependencies import get_tenant_service

router = APIRouter(prefix="/api/uploads", tags=["uploads"])

# Configuration
STORAGE_ROOT = Path("storage")
TENANTS_DIR = STORAGE_ROOT / "tenants"
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB
MAX_IMAGE_DIMENSION = 500  # Max width or height

# Logo specifications
LOGO_SPECS = {
    "max_size_mb": 2,
    "max_dimension": 500,
    "allowed_formats": ["PNG", "JPG", "JPEG", "WebP"],
    "recommended_dimension": "500x500",
    "aspect_ratio": "1:1 (square recommended)"
}


def create_storage_directories():
    """Create necessary storage directories if they don't exist"""
    TENANTS_DIR.mkdir(parents=True, exist_ok=True)


# Initialize storage on module load
create_storage_directories()


def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded image file
    
    Raises:
        HTTPException: If validation fails
    """
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Move to end of file
    file_size = file.file.tell()
    file.file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
        )


def process_and_save_logo(image_data: bytes, tenant_id: UUID, file_extension: str) -> str:
    """
    Process and save logo image
    
    Args:
        image_data: Raw image bytes
        tenant_id: Tenant UUID
        file_extension: File extension (e.g., '.png')
    
    Returns:
        Relative path to saved file
    """
    try:
        # Open and validate image
        img = Image.open(io.BytesIO(image_data))
        
        # Convert RGBA to RGB if necessary (for JPEG)
        if img.mode == 'RGBA' and file_extension in ['.jpg', '.jpeg']:
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3] if len(img.split()) > 3 else None)
            img = background
        
        # Resize if too large (maintain aspect ratio)
        if img.width > MAX_IMAGE_DIMENSION or img.height > MAX_IMAGE_DIMENSION:
            img.thumbnail((MAX_IMAGE_DIMENSION, MAX_IMAGE_DIMENSION), Image.Resampling.LANCZOS)
        
        # Create tenant directory
        tenant_dir = TENANTS_DIR / str(tenant_id)
        tenant_dir.mkdir(parents=True, exist_ok=True)
        
        # Save processed image
        logo_path = tenant_dir / f"logo{file_extension}"
        
        # Save with appropriate format
        save_format = 'JPEG' if file_extension in ['.jpg', '.jpeg'] else file_extension[1:].upper()
        img.save(logo_path, format=save_format, quality=95 if save_format == 'JPEG' else None)
        
        # Return relative path for database storage
        return f"tenants/{tenant_id}/logo{file_extension}"
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process image: {str(e)}"
        )


@router.post("/tenant/{tenant_id}/logo")
async def upload_tenant_logo(
    tenant_id: UUID,
    file: UploadFile = File(...),
    service: TenantService = Depends(get_tenant_service)
):
    """
    Upload a logo for a tenant
    
    Logo Specifications:
    - Max size: 2MB
    - Formats: PNG, JPG, JPEG, WebP
    - Max dimensions: 500x500px
    - Recommended: Square aspect ratio (1:1)
    """
    try:
        # Validate tenant exists
        tenant = await service.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Validate file
        validate_image_file(file)
        
        # Read file content
        content = await file.read()
        
        # Process and save logo
        file_ext = Path(file.filename).suffix.lower()
        logo_path = process_and_save_logo(content, tenant_id, file_ext)
        
        # Update tenant with logo path
        await service.update_tenant(
            tenant_id=tenant_id,
            logo_url=f"/api/uploads/{logo_path}"
        )
        
        return {
            "success": True,
            "message": "Logo uploaded successfully",
            "logo_url": f"/api/uploads/{logo_path}",
            "specs": LOGO_SPECS
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload logo: {str(e)}"
        )


@router.get("/tenants/{tenant_id}/logo{file_ext}")
async def get_tenant_logo(
    tenant_id: UUID,
    file_ext: str
):
    """
    Retrieve tenant logo
    """
    # Validate file extension
    if file_ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file extension"
        )
    
    # Build file path
    file_path = TENANTS_DIR / str(tenant_id) / f"logo{file_ext}"
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Logo not found"
        )
    
    # Determine media type
    media_types = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp"
    }
    
    return FileResponse(
        path=file_path,
        media_type=media_types.get(file_ext.lower(), "application/octet-stream"),
        headers={
            "Cache-Control": "public, max-age=3600"  # Cache for 1 hour
        }
    )


@router.delete("/tenant/{tenant_id}/logo")
async def delete_tenant_logo(
    tenant_id: UUID,
    service: TenantService = Depends(get_tenant_service)
):
    """
    Delete tenant logo
    """
    try:
        # Get tenant
        tenant = await service.get_tenant(tenant_id)
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Remove logo files
        tenant_dir = TENANTS_DIR / str(tenant_id)
        if tenant_dir.exists():
            for logo_file in tenant_dir.glob("logo.*"):
                logo_file.unlink()
        
        # Update tenant to remove logo reference
        await service.update_tenant(
            tenant_id=tenant_id,
            logo_url=None
        )
        
        return {
            "success": True,
            "message": "Logo deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete logo: {str(e)}"
        )


@router.get("/logo-specs")
async def get_logo_specifications():
    """
    Get logo upload specifications
    """
    return LOGO_SPECS