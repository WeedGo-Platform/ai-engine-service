"""
Translation Cache Warming Endpoint

Pre-warms translation cache with common UI strings in multiple languages.
This reduces initial load time for users by ensuring frequently used translations
are already cached in Redis/Memory.
"""

from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import logging
from datetime import datetime

# Import translation service
from services.translation_service import TranslationService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize translation service
translation_service = TranslationService()


class WarmupRequest(BaseModel):
    """Request model for cache warming"""
    languages: Optional[List[str]] = None  # If None, use default common languages
    namespaces: Optional[List[str]] = None  # If None, use all namespaces


class WarmupResponse(BaseModel):
    """Response model for cache warming"""
    success: bool
    message: str
    languages_processed: List[str]
    translations_cached: int
    duration_seconds: float
    errors: List[str] = []


# Common languages to warm up (most frequently used)
DEFAULT_WARMUP_LANGUAGES = ['es', 'fr', 'zh', 'ar', 'de', 'ja', 'pt', 'it', 'ko', 'ru']

# Common UI strings to pre-translate (from common.json)
COMMON_UI_STRINGS = [
    # Buttons
    "Send", "Close", "Cancel", "Save", "Delete", "Edit", "Create", "Update",
    "Confirm", "Back", "Next", "Submit", "Search", "Filter", "Export", "Import",
    "Refresh", "Settings", "Logout", "Change",
    
    # Labels
    "Email address", "Password", "Username", "Name", "Phone", "Address",
    "City", "Province", "Postal Code", "Country", "Status", "Actions",
    "Description", "Notes", "Date", "Time", "Total", "Subtotal", "Tax",
    "Quantity", "Price", "Language",
    
    # Placeholders
    "Enter your email", "Enter your password", "Search...", "Select an option",
    "Type your message...", "Enter name", "Enter phone number",
    
    # Messages
    "Loading...", "Saving...", "Success!", "An error occurred",
    "No data available", "Are you sure?", "You have unsaved changes",
    
    # Errors
    "This field is required", "Invalid email address", "Invalid phone number",
    "Network error. Please try again.", "Server error. Please try again later.",
    "Unauthorized access", "Not found", "Your session has expired. Please log in again.",
    
    # Common words
    "Yes", "No", "Today", "Yesterday", "Week", "Month", "Year",
    "All", "None", "Active", "Inactive", "Pending", "Completed", "Failed",
]

# Auth namespace strings
AUTH_STRINGS = [
    "Sign in to your account",
    "Email address",
    "Password",
    "Remember me",
    "Forgot password?",
    "Sign in",
    "Don't have an account?",
    "Sign up for WeedGo",
    "Secure admin access",
    "This is a protected area. All login attempts are monitored and logged.",
]

# Dashboard namespace strings
DASHBOARD_STRINGS = [
    "Dashboard",
    "Admin Dashboard",
    "System-wide overview",
    "Tenant overview",
    "Store performance metrics",
    "Total Revenue",
    "Total Orders",
    "Total Customers",
    "Total Inventory",
    "vs last week",
    "Recent Orders",
    "Low Stock Alerts",
    "Order ID",
    "Customer",
    "Amount",
    "View Details",
]


async def warmup_translations_task(
    languages: List[str],
    namespaces: List[str]
) -> Dict:
    """
    Background task to warm up translation cache
    
    Args:
        languages: List of language codes to warm up
        namespaces: List of namespaces (common, auth, dashboard)
    
    Returns:
        Dictionary with warmup statistics
    """
    start_time = datetime.now()
    translations_cached = 0
    errors = []
    
    # Determine which strings to translate based on namespaces
    strings_to_translate = []
    if 'common' in namespaces or not namespaces:
        strings_to_translate.extend(COMMON_UI_STRINGS)
    if 'auth' in namespaces or not namespaces:
        strings_to_translate.extend(AUTH_STRINGS)
    if 'dashboard' in namespaces or not namespaces:
        strings_to_translate.extend(DASHBOARD_STRINGS)
    
    logger.info(f"🔥 Starting cache warmup for {len(languages)} languages, {len(strings_to_translate)} strings")
    
    # Translate each string for each language
    for lang in languages:
        for text in strings_to_translate:
            try:
                # Determine namespace based on which list the string came from
                if text in COMMON_UI_STRINGS:
                    namespace = 'common'
                elif text in AUTH_STRINGS:
                    namespace = 'auth'
                else:
                    namespace = 'dashboard'
                
                # Call translation service (will cache the result)
                result = await translation_service.translate_single(
                    text=text,
                    target_language=lang,
                    source_language='en',
                    context=f'ui_{namespace}',
                    namespace=namespace,
                    use_cache=True  # This will store in cache if not already cached
                )
                
                if result.get('success'):
                    translations_cached += 1
                    
            except Exception as e:
                error_msg = f"Failed to translate '{text}' to {lang}: {str(e)}"
                logger.warning(error_msg)
                errors.append(error_msg)
                
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    logger.info(f"✅ Cache warmup complete: {translations_cached} translations cached in {duration:.2f}s")
    
    return {
        'languages_processed': languages,
        'translations_cached': translations_cached,
        'duration_seconds': duration,
        'errors': errors
    }


@router.post("/warmup", response_model=WarmupResponse)
async def warmup_cache(
    request: WarmupRequest,
    background_tasks: BackgroundTasks
):
    """
    Warm up translation cache with common UI strings.
    
    This endpoint pre-translates common UI strings into multiple languages
    and stores them in the cache (Memory -> Redis -> Database).
    
    **Use Cases:**
    - Run on server startup to pre-populate cache
    - Run after deploying new UI strings
    - Run periodically to keep cache warm
    
    **Example:**
    ```bash
    # Warm up default languages (es, fr, zh, ar, de, ja)
    curl -X POST http://localhost:5024/api/translate/warmup
    
    # Warm up specific languages
    curl -X POST http://localhost:5024/api/translate/warmup \
      -H "Content-Type: application/json" \
      -d '{"languages": ["es", "fr", "zh"], "namespaces": ["common", "auth"]}'
    ```
    
    **Performance:**
    - Runs as background task (returns immediately)
    - Typical warmup time: 30-60 seconds for 6 languages
    - Caches 600-800 translations (100-120 strings × 6 languages)
    """
    try:
        # Use default languages if not specified
        languages = request.languages if request.languages else DEFAULT_WARMUP_LANGUAGES
        
        # Use all namespaces if not specified
        namespaces = request.namespaces if request.namespaces else ['common', 'auth', 'dashboard']
        
        # Validate languages
        valid_languages = ['es', 'fr', 'zh', 'ar', 'de', 'ja', 'pt', 'it', 'ko', 'ru', 
                          'hi', 'nl', 'pl', 'tr', 'vi', 'th', 'id', 'ms']
        invalid_languages = [lang for lang in languages if lang not in valid_languages]
        if invalid_languages:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid language codes: {', '.join(invalid_languages)}"
            )
        
        # Start warmup in background
        background_tasks.add_task(
            warmup_translations_task,
            languages=languages,
            namespaces=namespaces
        )
        
        return WarmupResponse(
            success=True,
            message=f"Cache warmup started for {len(languages)} languages in background",
            languages_processed=languages,
            translations_cached=0,  # Will be updated in background
            duration_seconds=0.0,  # Background task, returns immediately
            errors=[]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cache warmup failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache warmup failed: {str(e)}"
        )


@router.get("/warmup/status")
async def warmup_status():
    """
    Get cache warmup status and statistics.
    
    Returns information about cached translations and cache hit rates.
    """
    try:
        # Get cache statistics from translation service
        stats = await translation_service.get_cache_stats()
        
        return {
            "success": True,
            "cache_stats": stats,
            "message": "Cache statistics retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to retrieve cache statistics"
        }
