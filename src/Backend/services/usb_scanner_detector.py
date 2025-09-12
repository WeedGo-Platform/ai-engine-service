"""
Enhanced USB Scanner Detection using pyusb and hid libraries
Detects barcode scanners that appear as HID devices
"""

import logging
import platform
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Try to import USB libraries
try:
    import usb.core
    import usb.util
    HAS_PYUSB = True
except ImportError:
    HAS_PYUSB = False
    logger.warning("pyusb not installed. Install with: pip install pyusb")

try:
    import hid
    HAS_HID = True
except ImportError:
    HAS_HID = False
    logger.warning("hidapi not installed. Install with: pip install hidapi")


class USBScannerDetector:
    """Enhanced USB scanner detection"""
    
    # Known barcode scanner vendor IDs
    SCANNER_VENDORS = {
        0x0c2e: "Honeywell",
        0x05e0: "Symbol Technologies", 
        0x05f9: "PSC Scanning",
        0x0536: "Hand Held Products",
        0x080c: "Datalogic",
        0x0bda: "Generic Scanner",
        0x1eab: "Generic Scanner",
        0x23d0: "Generic Scanner",
        0x0451: "Texas Instruments",
        0x04b4: "Cypress",
        0x0c42: "Metrologic",
        0x065a: "Opticon",
        0x0581: "Code Corporation",
        0x1234: "Brain Corp",
        0x05fe: "Chic Technology",
        0x1a86: "QinHeng Electronics",
        0x0483: "STMicroelectronics",
        0x0416: "Winbond",
        0x28e9: "GD32 MCU",
        0x1a2c: "China USB",
    }
    
    # Keywords that indicate a scanner
    SCANNER_KEYWORDS = [
        "scanner", "barcode", "reader", "scan", "hid kbd",
        "keyboard device", "hid keyboard", "usb input device"
    ]
    
    @classmethod
    def detect_with_pyusb(cls) -> List[Dict[str, Any]]:
        """Detect USB devices using pyusb"""
        if not HAS_PYUSB:
            return []
            
        scanners = []
        
        try:
            # Find all USB devices
            devices = usb.core.find(find_all=True)
            
            for device in devices:
                try:
                    # Get device info
                    vendor_id = device.idVendor
                    product_id = device.idProduct
                    
                    # Try to get manufacturer and product strings
                    manufacturer = "Unknown"
                    product_name = "Unknown Device"
                    
                    try:
                        manufacturer = usb.util.get_string(device, device.iManufacturer) or "Unknown"
                        product_name = usb.util.get_string(device, device.iProduct) or "Unknown Device"
                    except:
                        pass
                    
                    # Check if it's a HID device
                    is_hid = False
                    for cfg in device:
                        for intf in cfg:
                            if intf.bInterfaceClass == 0x03:  # HID class
                                is_hid = True
                                break
                    
                    # Check if it's a known scanner
                    is_scanner = (
                        vendor_id in cls.SCANNER_VENDORS or
                        any(kw in product_name.lower() for kw in cls.SCANNER_KEYWORDS) or
                        any(kw in manufacturer.lower() for kw in cls.SCANNER_KEYWORDS)
                    )
                    
                    # Add if it's HID or scanner
                    if is_hid or is_scanner:
                        confidence = "high" if is_scanner else "medium" if is_hid else "low"
                        
                        scanner_info = {
                            "id": f"{vendor_id:04x}:{product_id:04x}",
                            "name": product_name,
                            "type": "USB-HID" if is_hid else "USB",
                            "manufacturer": cls.SCANNER_VENDORS.get(vendor_id, manufacturer),
                            "vendor_id": f"0x{vendor_id:04x}",
                            "product_id": f"0x{product_id:04x}",
                            "status": "connected",
                            "capabilities": ["1D", "2D", "QR"] if is_scanner else ["1D"],
                            "confidence": confidence,
                            "is_hid": is_hid
                        }
                        
                        scanners.append(scanner_info)
                        logger.info(f"Found USB device: {product_name} ({confidence} confidence)")
                        
                except Exception as e:
                    logger.debug(f"Error reading device: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error detecting USB devices with pyusb: {e}")
            
        return scanners
    
    @classmethod
    def detect_with_hidapi(cls) -> List[Dict[str, Any]]:
        """Detect HID devices using hidapi"""
        if not HAS_HID:
            return []
            
        scanners = []
        
        try:
            # Enumerate all HID devices
            for device_info in hid.enumerate():
                vendor_id = device_info['vendor_id']
                product_id = device_info['product_id']
                product_name = device_info.get('product_string', 'Unknown HID Device')
                manufacturer = device_info.get('manufacturer_string', 'Unknown')
                
                # Check if it's a known scanner
                is_scanner = (
                    vendor_id in cls.SCANNER_VENDORS or
                    any(kw in product_name.lower() for kw in cls.SCANNER_KEYWORDS) or
                    any(kw in manufacturer.lower() for kw in cls.SCANNER_KEYWORDS)
                )
                
                # Most barcode scanners appear as keyboards
                is_keyboard = (
                    device_info.get('usage_page', 0) == 0x01 and
                    device_info.get('usage', 0) == 0x06
                )
                
                if is_scanner or is_keyboard:
                    confidence = "high" if is_scanner else "medium"
                    
                    scanner_info = {
                        "id": f"{vendor_id:04x}:{product_id:04x}",
                        "name": product_name,
                        "type": "USB-HID",
                        "manufacturer": cls.SCANNER_VENDORS.get(vendor_id, manufacturer),
                        "vendor_id": f"0x{vendor_id:04x}",
                        "product_id": f"0x{product_id:04x}",
                        "status": "connected",
                        "capabilities": ["1D", "2D", "QR"] if is_scanner else ["1D"],
                        "confidence": confidence,
                        "is_hid": True,
                        "path": device_info['path'].decode() if isinstance(device_info['path'], bytes) else device_info['path']
                    }
                    
                    scanners.append(scanner_info)
                    logger.info(f"Found HID device: {product_name} ({confidence} confidence)")
                    
        except Exception as e:
            logger.error(f"Error detecting HID devices with hidapi: {e}")
            
        return scanners
    
    @classmethod
    def detect_all(cls) -> List[Dict[str, Any]]:
        """Detect all USB scanners using available methods"""
        all_scanners = []
        seen_ids = set()
        
        # Try pyusb first
        pyusb_scanners = cls.detect_with_pyusb()
        for scanner in pyusb_scanners:
            scanner_id = scanner['id']
            if scanner_id not in seen_ids:
                all_scanners.append(scanner)
                seen_ids.add(scanner_id)
        
        # Then try hidapi for additional HID devices
        hid_scanners = cls.detect_with_hidapi()
        for scanner in hid_scanners:
            scanner_id = scanner['id']
            if scanner_id not in seen_ids:
                all_scanners.append(scanner)
                seen_ids.add(scanner_id)
        
        return all_scanners


def detect_usb_scanners() -> List[Dict[str, Any]]:
    """Main function to detect USB scanners"""
    detector = USBScannerDetector()
    return detector.detect_all()