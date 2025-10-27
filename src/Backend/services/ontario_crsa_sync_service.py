"""
Ontario CRSA Sync Service
Handles automated synchronization of AGCO cannabis retail store data
"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
import asyncpg
import aiohttp
import schedule
import time
from threading import Thread

logger = logging.getLogger(__name__)


class CRSASyncService:
    """
    Service for automated CRSA data synchronization

    Features:
    - Downloads latest CSV from AGCO (when available)
    - Runs import script automatically
    - Tracks sync history
    - Sends notifications on failures
    - Scheduled daily execution
    """

    def __init__(
        self,
        csv_download_dir: str = "data/crsa",
        agco_csv_url: Optional[str] = None,
        db_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize CRSA sync service

        Args:
            csv_download_dir: Directory to store downloaded CSVs
            agco_csv_url: URL to download CSV (if available from AGCO)
            db_config: Database configuration
        """
        self.csv_download_dir = Path(csv_download_dir)
        self.csv_download_dir.mkdir(parents=True, exist_ok=True)

        # AGCO doesn't provide a direct CSV download URL yet
        # For now, we'll support manual CSV placement in the directory
        self.agco_csv_url = agco_csv_url

        self.db_config = db_config or {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', 5434)),
            'user': os.getenv('DB_USER', 'weedgo'),
            'password': os.getenv('DB_PASSWORD', 'your_password_here'),
            'database': os.getenv('DB_NAME', 'ai_engine')
        }

        self.last_sync_time: Optional[datetime] = None
        self.is_running = False
        self.scheduler_thread: Optional[Thread] = None

    async def run_download_scraper(self) -> Optional[Path]:
        """
        Run the download_agco_crsa.py scraper to get latest data

        Returns:
            Path to downloaded CSV file, or None if scraping failed
        """
        try:
            logger.info("Running AGCO scraper to download latest CRSA data...")

            # Path to the scraper script
            script_dir = Path(__file__).parent.parent / "scripts"
            scraper_script = script_dir / "download_agco_crsa.py"

            if not scraper_script.exists():
                logger.error(f"Scraper script not found: {scraper_script}")
                return None

            # Run the scraper asynchronously
            proc = await asyncio.create_subprocess_exec(
                "python3", str(scraper_script),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(script_dir)
            )

            stdout, stderr = await proc.communicate()

            if proc.returncode != 0:
                logger.error(f"Scraper failed with code {proc.returncode}")
                logger.error(f"Error output: {stderr.decode()}")
                return None

            # Parse output to find CSV path
            output = stdout.decode()
            logger.info(f"Scraper output:\n{output}")

            # Find the most recent CSV file in the download directory
            csv_files = list(self.csv_download_dir.glob("crsa_data_*.csv"))
            if not csv_files:
                logger.error("No CSV files found after scraper run")
                return None

            # Get the most recent file
            latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)
            logger.info(f"Using latest scraped CSV: {latest_csv}")

            return latest_csv

        except Exception as e:
            logger.error(f"Error running scraper: {e}")
            return None

    async def download_csv(self) -> Optional[Path]:
        """
        Download CSV from AGCO website

        Returns:
            Path to downloaded CSV file, or None if download failed
        """
        if not self.agco_csv_url:
            logger.warning("AGCO CSV URL not configured. Manual CSV placement required.")
            return None

        try:
            logger.info(f"Downloading CRSA CSV from: {self.agco_csv_url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(self.agco_csv_url, timeout=60) as response:
                    if response.status != 200:
                        logger.error(f"Failed to download CSV: HTTP {response.status}")
                        return None

                    # Save with timestamp
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"crsa_data_{timestamp}.csv"
                    file_path = self.csv_download_dir / filename

                    content = await response.read()
                    file_path.write_bytes(content)

                    logger.info(f"CSV downloaded successfully: {file_path}")
                    return file_path

        except Exception as e:
            logger.error(f"Error downloading CSV: {e}")
            return None

    async def get_latest_csv(self) -> Optional[Path]:
        """
        Get the latest CSV file from the download directory

        Returns:
            Path to latest CSV file, or None if no CSV found
        """
        csv_files = list(self.csv_download_dir.glob("*.csv"))

        if not csv_files:
            logger.warning(f"No CSV files found in {self.csv_download_dir}")
            return None

        # Sort by modification time (newest first)
        latest_csv = max(csv_files, key=lambda p: p.stat().st_mtime)

        logger.info(f"Found latest CSV: {latest_csv}")
        return latest_csv

    async def import_csv(self, csv_path: Path) -> Dict[str, Any]:
        """
        Import CSV data into database

        Args:
            csv_path: Path to CSV file

        Returns:
            Dictionary with import statistics
        """
        try:
            # Import the CSV import function
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent))

            from scripts.import_crsa_data import import_csv

            logger.info(f"Starting CSV import: {csv_path}")

            # Run import
            success = await import_csv(str(csv_path), is_initial_load=False)

            if success:
                logger.info("CSV import completed successfully")
                return {
                    'success': True,
                    'csv_path': str(csv_path),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.error("CSV import failed")
                return {
                    'success': False,
                    'error': 'Import function returned False',
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Error importing CSV: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def record_sync_history(
        self,
        success: bool,
        records_processed: int = 0,
        error_message: Optional[str] = None
    ):
        """
        Record sync history in database

        Args:
            success: Whether sync was successful
            records_processed: Number of records processed
            error_message: Error message if sync failed
        """
        try:
            conn = await asyncpg.connect(**self.db_config)

            await conn.execute("""
                INSERT INTO crsa_sync_history (
                    sync_date,
                    success,
                    records_processed,
                    error_message,
                    created_at
                ) VALUES ($1, $2, $3, $4, NOW())
            """, datetime.now(), success, records_processed, error_message)

            await conn.close()

            logger.info(f"Sync history recorded: success={success}, records={records_processed}")

        except Exception as e:
            logger.error(f"Failed to record sync history: {e}")

    async def get_sync_statistics(self) -> Dict[str, Any]:
        """
        Get sync statistics from database

        Returns:
            Dictionary with sync statistics
        """
        try:
            conn = await asyncpg.connect(**self.db_config)

            stats = await conn.fetchrow("""
                SELECT
                    COUNT(*) as total_syncs,
                    COUNT(*) FILTER (WHERE success = TRUE) as successful_syncs,
                    COUNT(*) FILTER (WHERE success = FALSE) as failed_syncs,
                    MAX(sync_date) as last_sync_date,
                    SUM(records_processed) as total_records_processed
                FROM crsa_sync_history
                WHERE sync_date > NOW() - INTERVAL '30 days'
            """)

            await conn.close()

            return {
                'total_syncs': stats['total_syncs'],
                'successful_syncs': stats['successful_syncs'],
                'failed_syncs': stats['failed_syncs'],
                'last_sync_date': stats['last_sync_date'].isoformat() if stats['last_sync_date'] else None,
                'total_records_processed': stats['total_records_processed']
            }

        except Exception as e:
            logger.error(f"Failed to get sync statistics: {e}")
            return {
                'error': str(e),
                'total_syncs': 0,
                'successful_syncs': 0,
                'failed_syncs': 0
            }

    async def run_sync(self) -> Dict[str, Any]:
        """
        Run a complete sync operation

        Returns:
            Dictionary with sync results
        """
        logger.info("=== Starting CRSA Sync ===")
        start_time = datetime.now()

        try:
            # Step 1: Run the download scraper to get latest data from AGCO
            csv_path = await self.run_download_scraper()

            # Step 2: If scraper failed, try to use latest existing CSV as fallback
            if not csv_path:
                logger.warning("Scraper failed, trying to use latest existing CSV")
                csv_path = await self.get_latest_csv()

            if not csv_path:
                error_msg = "No CSV file available for sync"
                logger.error(error_msg)
                await self.record_sync_history(success=False, error_message=error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'duration_seconds': (datetime.now() - start_time).total_seconds()
                }

            # Step 3: Import CSV
            import_result = await self.import_csv(csv_path)

            # Step 4: Record sync history
            await self.record_sync_history(
                success=import_result.get('success', False),
                records_processed=import_result.get('records_processed', 0),
                error_message=import_result.get('error')
            )

            # Update last sync time
            self.last_sync_time = datetime.now()

            duration = (datetime.now() - start_time).total_seconds()

            logger.info(f"=== CRSA Sync Completed in {duration:.2f}s ===")

            return {
                'success': import_result.get('success', False),
                'csv_path': str(csv_path),
                'records_processed': import_result.get('records_processed', 0),
                'duration_seconds': duration,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Sync failed with exception: {e}")
            await self.record_sync_history(success=False, error_message=str(e))

            return {
                'success': False,
                'error': str(e),
                'duration_seconds': (datetime.now() - start_time).total_seconds()
            }

    def schedule_daily_sync(self, hour: int = 3, minute: int = 0):
        """
        Schedule daily sync at specified time

        Args:
            hour: Hour to run sync (0-23), default 3 AM
            minute: Minute to run sync (0-59), default 0
        """
        def sync_job():
            """Wrapper to run async sync in sync context"""
            try:
                asyncio.run(self.run_sync())
            except Exception as e:
                logger.error(f"Scheduled sync failed: {e}")

        # Schedule daily at specified time
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(sync_job)

        logger.info(f"Scheduled daily CRSA sync at {hour:02d}:{minute:02d}")

    def start_scheduler(self, hour: int = 3, minute: int = 0):
        """
        Start the sync scheduler in a background thread

        Args:
            hour: Hour to run sync (0-23)
            minute: Minute to run sync (0-59)
        """
        if self.is_running:
            logger.warning("Scheduler already running")
            return

        # Schedule the sync
        self.schedule_daily_sync(hour, minute)

        # Run scheduler in background thread
        def run_scheduler():
            self.is_running = True
            logger.info("CRSA sync scheduler started")

            while self.is_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute

            logger.info("CRSA sync scheduler stopped")

        self.scheduler_thread = Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()

    def stop_scheduler(self):
        """Stop the sync scheduler"""
        if not self.is_running:
            logger.warning("Scheduler not running")
            return

        self.is_running = False

        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)

        logger.info("CRSA sync scheduler stopped")

    async def manual_sync(self, csv_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Trigger a manual sync

        Args:
            csv_path: Optional path to specific CSV file to import

        Returns:
            Dictionary with sync results
        """
        logger.info("=== Manual CRSA Sync Triggered ===")

        if csv_path:
            # Use specified CSV
            import_result = await self.import_csv(Path(csv_path))

            await self.record_sync_history(
                success=import_result.get('success', False),
                error_message=import_result.get('error')
            )

            return import_result
        else:
            # Run full sync
            return await self.run_sync()


# Global sync service instance
_sync_service: Optional[CRSASyncService] = None


def get_sync_service() -> CRSASyncService:
    """Get or create global sync service instance"""
    global _sync_service

    if _sync_service is None:
        _sync_service = CRSASyncService()

    return _sync_service


async def initialize_sync_service(start_scheduler: bool = True) -> CRSASyncService:
    """
    Initialize and optionally start the sync service

    Args:
        start_scheduler: Whether to start the background scheduler

    Returns:
        Initialized sync service
    """
    sync_service = get_sync_service()

    if start_scheduler:
        # Start scheduler to run daily at 3 AM
        sync_service.start_scheduler(hour=3, minute=0)

    return sync_service
