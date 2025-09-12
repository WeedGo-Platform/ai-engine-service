"""
Hardware Management API Endpoints
Endpoints for detecting and managing POS hardware devices
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import logging
from pydantic import BaseModel

from services.hardware_detection import HardwareDetectionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/hardware", tags=["hardware"])


class ScannerConfig(BaseModel):
    """Scanner configuration model"""
    enable_beep: bool = True
    enable_vibrate: bool = True
    scan_mode: str = "continuous"  # continuous, single, trigger
    decode_1d: bool = True
    decode_2d: bool = True
    decode_qr: bool = True


@router.get("/scanners/detect")
async def detect_scanners() -> List[Dict[str, Any]]:
    """Detect all connected barcode scanners"""
    try:
        scanners = await HardwareDetectionService.detect_scanners()
        logger.info(f"Detected {len(scanners)} scanner(s)")
        return scanners
    except Exception as e:
        logger.error(f"Error detecting scanners: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scanners/{scanner_id}/test")
async def test_scanner(scanner_id: str) -> Dict[str, Any]:
    """Test a specific scanner connection"""
    try:
        result = await HardwareDetectionService.test_scanner(scanner_id)
        return result
    except Exception as e:
        logger.error(f"Error testing scanner {scanner_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scanners/{scanner_id}/configure")
async def configure_scanner(scanner_id: str, config: ScannerConfig) -> Dict[str, Any]:
    """Configure scanner settings"""
    try:
        success = await HardwareDetectionService.configure_scanner(
            scanner_id, 
            config.dict()
        )
        return {
            "success": success,
            "scanner_id": scanner_id,
            "message": "Scanner configured successfully" if success else "Configuration failed"
        }
    except Exception as e:
        logger.error(f"Error configuring scanner {scanner_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/printers/detect")
async def detect_printers() -> List[Dict[str, Any]]:
    """Detect all connected receipt printers"""
    # Mock implementation for now
    return [
        {
            "id": "PRINTER-001",
            "name": "Star TSP100",
            "type": "USB",
            "status": "ready",
            "paper_status": "ok",
            "capabilities": ["receipt", "barcode", "qr_code"]
        },
        {
            "id": "PRINTER-002",
            "name": "Epson TM-T88V",
            "type": "Network",
            "status": "ready",
            "ip_address": "192.168.1.101",
            "paper_status": "ok",
            "capabilities": ["receipt", "graphics", "barcode"]
        }
    ]


@router.get("/terminals/detect")
async def detect_payment_terminals() -> List[Dict[str, Any]]:
    """Detect all connected payment terminals"""
    # Mock implementation for now
    return [
        {
            "id": "TERM-001",
            "name": "Ingenico iCT250",
            "type": "USB",
            "status": "connected",
            "capabilities": ["chip", "tap", "swipe"]
        },
        {
            "id": "TERM-002",
            "name": "Verifone VX520",
            "type": "Network",
            "status": "connected",
            "ip_address": "192.168.1.102",
            "capabilities": ["chip", "tap", "swipe", "contactless"]
        }
    ]


@router.get("/cash-drawers/detect")
async def detect_cash_drawers() -> List[Dict[str, Any]]:
    """Detect all connected cash drawers"""
    # Mock implementation for now
    return [
        {
            "id": "DRAWER-001",
            "name": "APG Vasario Series",
            "type": "Printer-driven",
            "status": "connected",
            "locked": False
        }
    ]


@router.get("/all")
async def detect_all_hardware() -> Dict[str, Any]:
    """Detect all connected POS hardware"""
    try:
        scanners = await HardwareDetectionService.detect_scanners()
        printers = await detect_printers()
        terminals = await detect_payment_terminals()
        drawers = await detect_cash_drawers()
        
        return {
            "scanners": scanners,
            "printers": printers,
            "payment_terminals": terminals,
            "cash_drawers": drawers,
            "summary": {
                "total_devices": len(scanners) + len(printers) + len(terminals) + len(drawers),
                "scanners_count": len(scanners),
                "printers_count": len(printers),
                "terminals_count": len(terminals),
                "drawers_count": len(drawers)
            }
        }
    except Exception as e:
        logger.error(f"Error detecting hardware: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))