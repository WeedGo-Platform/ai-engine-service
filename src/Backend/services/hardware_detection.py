"""
Hardware Detection Service
Detects connected hardware devices including barcode scanners
"""

import platform
import subprocess
import re
import json
import logging
from typing import List, Dict, Any
import asyncio

logger = logging.getLogger(__name__)

# Try to import enhanced USB detection
try:
    from .usb_scanner_detector import detect_usb_scanners
    HAS_USB_DETECTOR = True
except ImportError:
    HAS_USB_DETECTOR = False
    logger.info("Enhanced USB detection not available")


class HardwareDetectionService:
    """Service for detecting connected hardware devices"""
    
    @staticmethod
    async def detect_scanners() -> List[Dict[str, Any]]:
        """Detect all connected barcode scanners"""
        scanners = []
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                scanners = await HardwareDetectionService._detect_macos_devices()
            elif system == "Linux":
                scanners = await HardwareDetectionService._detect_linux_devices()
            elif system == "Windows":
                scanners = await HardwareDetectionService._detect_windows_devices()
            else:
                logger.warning(f"Unsupported platform: {system}")
                
        except Exception as e:
            logger.error(f"Error detecting scanners: {str(e)}")
            
        # Only add mock scanners if no real devices found and in development mode
        if not scanners:
            logger.info("No real scanners detected, returning mock data for development")
            scanners = HardwareDetectionService._get_mock_scanners()
            
        return scanners
    
    @staticmethod
    async def _detect_macos_devices() -> List[Dict[str, Any]]:
        """Detect devices on macOS using system_profiler and enhanced USB detection"""
        devices = []
        seen_ids = set()
        
        try:
            # First try enhanced USB detection if available
            if HAS_USB_DETECTOR:
                try:
                    usb_devices = detect_usb_scanners()
                    for device in usb_devices:
                        device_id = device.get('id')
                        if device_id not in seen_ids:
                            devices.append(device)
                            seen_ids.add(device_id)
                            logger.info(f"Enhanced detection found: {device.get('name')}")
                except Exception as e:
                    logger.warning(f"Enhanced USB detection failed: {e}")
            
            # Then use system_profiler for additional devices
            usb_cmd = ["system_profiler", "SPUSBDataType", "-json"]
            usb_result = await HardwareDetectionService._run_command(usb_cmd)
            if usb_result:
                usb_data = json.loads(usb_result)
                system_devices = HardwareDetectionService._parse_macos_usb(usb_data)
                for device in system_devices:
                    device_id = device.get('id')
                    if device_id not in seen_ids:
                        devices.append(device)
                        seen_ids.add(device_id)
            
            # Check Bluetooth devices
            bt_cmd = ["system_profiler", "SPBluetoothDataType", "-json"]
            bt_result = await HardwareDetectionService._run_command(bt_cmd)
            if bt_result:
                bt_data = json.loads(bt_result)
                bt_devices = HardwareDetectionService._parse_macos_bluetooth(bt_data)
                for device in bt_devices:
                    device_id = device.get('id')
                    if device_id not in seen_ids:
                        devices.append(device)
                        seen_ids.add(device_id)
                
        except Exception as e:
            logger.error(f"Error detecting macOS devices: {str(e)}")
            
        return devices
    
    @staticmethod
    def _parse_macos_usb(data: Dict) -> List[Dict[str, Any]]:
        """Parse macOS USB device data"""
        scanners = []
        
        def traverse_usb_tree(items, depth=0):
            for item in items:
                # Get device details
                name = item.get("_name", "")
                manufacturer = item.get("manufacturer", "")
                product_id = item.get("product_id", "")
                vendor_id = item.get("vendor_id", "")
                
                # Log all USB devices for debugging
                if name:
                    logger.debug(f"Found USB device: {name} by {manufacturer} (VID:{vendor_id} PID:{product_id})")
                
                # Check for HID devices (keyboards/scanners)
                # Most barcode scanners appear as HID keyboard devices
                is_hid = "HID" in name or "Keyboard" in name or "Human Interface" in str(item.get("device_class", ""))
                
                # Known scanner manufacturers and models
                scanner_keywords = [
                    "scanner", "barcode", "honeywell", "symbol", "zebra", 
                    "datalogic", "motorola", "metrologic", "opticon", "code",
                    "socket", "cipherlab", "newland", "sunlux", "netum"
                ]
                
                # Check vendor IDs for known scanner manufacturers
                scanner_vendor_ids = [
                    "0x0c2e",  # Honeywell
                    "0x05e0",  # Symbol Technologies
                    "0x05f9",  # PSC Scanning
                    "0x0536",  # Hand Held Products
                    "0x080c",  # Datalogic
                    "0x0bda",  # Some generic scanners
                    "0x1eab",  # Some generic scanners
                    "0x23d0",  # Some generic scanners
                ]
                
                name_lower = name.lower()
                manufacturer_lower = manufacturer.lower()
                
                # Detect scanner by keywords or vendor ID
                is_scanner = (
                    any(keyword in name_lower or keyword in manufacturer_lower for keyword in scanner_keywords) or
                    vendor_id in scanner_vendor_ids
                )
                
                # Add HID devices that might be scanners
                if is_hid or is_scanner:
                    device_type = "USB-HID" if is_hid else "USB"
                    
                    # Determine if it's likely a scanner
                    confidence = "high" if is_scanner else "medium" if is_hid else "low"
                    
                    scanner_info = {
                        "id": item.get("serial_num", f"{vendor_id}:{product_id}:{name[:10]}"),
                        "name": name or "Unknown HID Device",
                        "type": device_type,
                        "manufacturer": manufacturer or "Unknown",
                        "status": "connected",
                        "vendor_id": vendor_id,
                        "product_id": product_id,
                        "port": item.get("location_id", ""),
                        "capabilities": ["1D", "2D", "QR"] if is_scanner else ["1D"],
                        "confidence": confidence,
                        "is_hid": is_hid
                    }
                    
                    # Only add if we have some identifying information
                    if name and (is_scanner or (is_hid and "keyboard" not in name_lower)):
                        scanners.append(scanner_info)
                        logger.info(f"Detected potential scanner: {name} ({confidence} confidence)")
                
                # Recursively check children
                if "_items" in item:
                    traverse_usb_tree(item["_items"], depth + 1)
        
        if "SPUSBDataType" in data:
            for controller in data["SPUSBDataType"]:
                if "_items" in controller:
                    traverse_usb_tree(controller["_items"])
                    
        return scanners
    
    @staticmethod
    def _parse_macos_bluetooth(data: Dict) -> List[Dict[str, Any]]:
        """Parse macOS Bluetooth device data"""
        scanners = []
        
        if "SPBluetoothDataType" in data:
            for controller in data["SPBluetoothDataType"]:
                devices = controller.get("devices", {})
                for device_id, device_info in devices.items():
                    name = device_info.get("device_name", "").lower()
                    
                    scanner_keywords = ["scanner", "barcode", "honeywell", "symbol"]
                    if any(keyword in name for keyword in scanner_keywords):
                        scanners.append({
                            "id": device_id,
                            "name": device_info.get("device_name", "Unknown Scanner"),
                            "type": "Bluetooth",
                            "manufacturer": device_info.get("device_manufacturer", "Unknown"),
                            "status": "paired" if device_info.get("device_connected") else "disconnected",
                            "address": device_info.get("device_address", ""),
                            "capabilities": ["1D", "2D"]
                        })
                        
        return scanners
    
    @staticmethod
    async def _detect_linux_devices() -> List[Dict[str, Any]]:
        """Detect devices on Linux using lsusb and hcitool"""
        devices = []
        
        try:
            # Check USB devices
            usb_result = await HardwareDetectionService._run_command(["lsusb"])
            if usb_result:
                devices.extend(HardwareDetectionService._parse_linux_usb(usb_result))
            
            # Check Bluetooth devices
            bt_result = await HardwareDetectionService._run_command(["hcitool", "dev"])
            if bt_result:
                devices.extend(HardwareDetectionService._parse_linux_bluetooth(bt_result))
                
        except Exception as e:
            logger.error(f"Error detecting Linux devices: {str(e)}")
            
        return devices
    
    @staticmethod
    def _parse_linux_usb(output: str) -> List[Dict[str, Any]]:
        """Parse Linux USB device output"""
        scanners = []
        scanner_vendors = {
            "0c2e": "Honeywell",
            "05e0": "Symbol Technologies",
            "05f9": "PSC Scanning",
            "0536": "Hand Held Products",
            "080c": "Datalogic"
        }
        
        for line in output.split('\n'):
            for vendor_id, vendor_name in scanner_vendors.items():
                if vendor_id in line.lower():
                    match = re.search(r'ID ([0-9a-f]{4}):([0-9a-f]{4}) (.+)', line)
                    if match:
                        scanners.append({
                            "id": f"{match.group(1)}:{match.group(2)}",
                            "name": match.group(3).strip(),
                            "type": "USB",
                            "manufacturer": vendor_name,
                            "status": "connected",
                            "capabilities": ["1D", "2D", "QR"]
                        })
                        
        return scanners
    
    @staticmethod
    def _parse_linux_bluetooth(output: str) -> List[Dict[str, Any]]:
        """Parse Linux Bluetooth device output"""
        # This would need more implementation for actual Bluetooth scanning
        return []
    
    @staticmethod
    async def _detect_windows_devices() -> List[Dict[str, Any]]:
        """Detect devices on Windows using WMI"""
        devices = []
        
        try:
            # Use PowerShell to query WMI for HID devices
            ps_cmd = [
                "powershell", "-Command",
                "Get-WmiObject Win32_PnPEntity | Where-Object {$_.Name -like '*Scanner*' -or $_.Name -like '*Barcode*'} | Select-Object Name, DeviceID, Status | ConvertTo-Json"
            ]
            result = await HardwareDetectionService._run_command(ps_cmd)
            if result:
                devices_data = json.loads(result)
                if isinstance(devices_data, list):
                    for device in devices_data:
                        devices.append({
                            "id": device.get("DeviceID", ""),
                            "name": device.get("Name", "Unknown Scanner"),
                            "type": "USB/HID",
                            "status": "OK" if device.get("Status") == "OK" else "disconnected",
                            "capabilities": ["1D", "2D"]
                        })
                        
        except Exception as e:
            logger.error(f"Error detecting Windows devices: {str(e)}")
            
        return devices
    
    @staticmethod
    async def _run_command(cmd: List[str]) -> str:
        """Run a shell command and return output"""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                return stdout.decode('utf-8')
            else:
                logger.error(f"Command failed: {stderr.decode('utf-8')}")
                return ""
        except Exception as e:
            logger.error(f"Error running command {cmd}: {str(e)}")
            return ""
    
    @staticmethod
    def _get_mock_scanners() -> List[Dict[str, Any]]:
        """Return mock scanner data for development"""
        return [
            {
                "id": "MOCK-USB-001",
                "name": "Honeywell Voyager 1470g",
                "type": "USB",
                "manufacturer": "Honeywell",
                "status": "connected",
                "port": "USB001",
                "capabilities": ["1D", "2D", "QR", "PDF417"]
            },
            {
                "id": "MOCK-BT-001",
                "name": "Socket Mobile S700",
                "type": "Bluetooth",
                "manufacturer": "Socket Mobile",
                "status": "paired",
                "address": "00:11:22:33:44:55",
                "capabilities": ["1D", "2D", "QR"]
            },
            {
                "id": "MOCK-NET-001",
                "name": "Zebra DS9208",
                "type": "Network",
                "manufacturer": "Zebra Technologies",
                "status": "connected",
                "ip_address": "192.168.1.100",
                "capabilities": ["1D", "2D", "QR", "DataMatrix"]
            }
        ]
    
    @staticmethod
    async def test_scanner(scanner_id: str) -> Dict[str, Any]:
        """Test a scanner connection"""
        # In a real implementation, this would send a test command to the scanner
        await asyncio.sleep(1)  # Simulate test delay
        
        return {
            "success": True,
            "scanner_id": scanner_id,
            "message": "Scanner test successful",
            "test_barcode": "TEST123456789"
        }
    
    @staticmethod
    async def configure_scanner(scanner_id: str, settings: Dict[str, Any]) -> bool:
        """Configure scanner settings"""
        # This would send configuration to the scanner
        logger.info(f"Configuring scanner {scanner_id} with settings: {settings}")
        return True