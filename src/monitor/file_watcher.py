"""
File monitoring system for Pensieve.
Watches Zoom folder for new meeting transcripts and queues them for processing.
"""

import time
import threading
from pathlib import Path
from typing import Callable, Optional, Set, Dict, Any
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileModifiedEvent

from ..utils.config import get_config
from ..utils.logger import get_logger


class TranscriptFileHandler(FileSystemEventHandler):
    """Handles file system events for Zoom transcript files."""
    
    def __init__(self, callback: Callable[[Path], None]):
        """
        Initialize the file handler.
        
        Args:
            callback: Function to call when a new transcript is detected.
        """
        super().__init__()
        self.callback = callback
        self.config = get_config()
        self.logger = get_logger("file_handler")
        
        # Track files we're already monitoring to avoid duplicates
        self.processing_files: Set[str] = set()
        self.file_timestamps: Dict[str, float] = {}
        
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory and self._is_transcript_file(event.src_path):
            self.logger.debug(f"File created: {event.src_path}")
            self._handle_transcript_file(event.src_path)
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory and self._is_transcript_file(event.src_path):
            self.logger.debug(f"File modified: {event.src_path}")
            self._handle_transcript_file(event.src_path)
    
    def _is_transcript_file(self, file_path: str) -> bool:
        """
        Check if a file matches our transcript patterns.
        
        Args:
            file_path: Path to the file.
            
        Returns:
            True if it's a transcript file we should process.
        """
        path = Path(file_path)
        
        # Check filename pattern
        if path.name != "meeting_saved_closed_caption.txt":
            return False
        
        # Check if it's in a meeting folder (has timestamp pattern)
        parent_name = path.parent.name
        if not self._is_meeting_folder(parent_name):
            return False
        
        return True
    
    def _is_meeting_folder(self, folder_name: str) -> bool:
        """
        Check if folder name matches Zoom meeting pattern.
        
        Args:
            folder_name: Name of the folder.
            
        Returns:
            True if it matches the pattern YYYY-MM-DD HH.MM.SS [Title]
        """
        # Basic pattern check - starts with date
        parts = folder_name.split(' ')
        if len(parts) < 3:
            return False
        
        # Check date format YYYY-MM-DD
        date_part = parts[0]
        if len(date_part) == 10 and date_part.count('-') == 2:
            try:
                datetime.strptime(date_part, '%Y-%m-%d')
                return True
            except ValueError:
                pass
        
        return False
    
    def _handle_transcript_file(self, file_path: str):
        """
        Handle a transcript file, ensuring it's stable before processing.
        
        Args:
            file_path: Path to the transcript file.
        """
        file_path = str(Path(file_path).resolve())
        
        # Skip if already processing
        if file_path in self.processing_files:
            return
        
        # Check file size
        try:
            file_size = Path(file_path).stat().st_size
            if file_size < self.config.monitoring.min_file_size:
                self.logger.debug(f"File too small, skipping: {file_path} ({file_size} bytes)")
                return
        except OSError:
            self.logger.debug(f"Cannot access file: {file_path}")
            return
        
        # Track this file and wait for stability
        current_time = time.time()
        self.file_timestamps[file_path] = current_time
        
        # Schedule stability check
        stability_delay = self.config.monitoring.file_stable_time
        threading.Timer(stability_delay, self._check_file_stability, args=[file_path]).start()
        
        self.logger.debug(f"Scheduled stability check for: {file_path}")
    
    def _check_file_stability(self, file_path: str):
        """
        Check if file is stable (not being written to) and queue for processing.
        
        Args:
            file_path: Path to check.
        """
        try:
            # Check if file still exists
            path = Path(file_path)
            if not path.exists():
                self.logger.debug(f"File no longer exists: {file_path}")
                self.file_timestamps.pop(file_path, None)
                return
            
            # Check if file size has changed recently
            current_size = path.stat().st_size
            current_time = time.time()
            
            # Wait a bit more if file was modified recently
            last_timestamp = self.file_timestamps.get(file_path, 0)
            if current_time - last_timestamp < self.config.monitoring.file_stable_time:
                self.logger.debug(f"File not stable yet, rechecking: {file_path}")
                threading.Timer(2, self._check_file_stability, args=[file_path]).start()
                return
            
            # File seems stable, queue for processing
            self.processing_files.add(file_path)
            self.logger.info(f"📄 New transcript detected: {path.parent.name}")
            
            try:
                self.callback(path)
            except Exception as e:
                self.logger.error(f"Error processing {file_path}: {e}")
            finally:
                # Clean up tracking
                self.processing_files.discard(file_path)
                self.file_timestamps.pop(file_path, None)
                
        except Exception as e:
            self.logger.error(f"Error checking file stability: {e}")


class ZoomMonitor:
    """Monitors Zoom folder for new meeting transcripts."""
    
    def __init__(self, callback: Callable[[Path], None]):
        """
        Initialize the Zoom monitor.
        
        Args:
            callback: Function to call when new transcript is detected.
        """
        self.callback = callback
        self.config = get_config()
        self.logger = get_logger("zoom_monitor")
        
        self.observer: Optional[Observer] = None
        self.is_running = False
        self._stop_event = threading.Event()
        
        # Validate Zoom folder exists
        self.zoom_folder = Path(self.config.monitoring.zoom_folder)
        if not self.zoom_folder.exists():
            raise FileNotFoundError(f"Zoom folder not found: {self.zoom_folder}")
    
    def start(self) -> bool:
        """
        Start monitoring the Zoom folder.
        
        Returns:
            True if monitoring started successfully.
        """
        if self.is_running:
            self.logger.warning("Monitor is already running")
            return True
        
        try:
            self.logger.info(f"🔍 Starting to monitor: {self.zoom_folder}")
            
            # Create file handler
            handler = TranscriptFileHandler(self.callback)
            
            # Set up observer
            self.observer = Observer()
            self.observer.schedule(handler, str(self.zoom_folder), recursive=True)
            
            # Start observer
            self.observer.start()
            self.is_running = True
            
            self.logger.info("✅ File monitoring started successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return False
    
    def stop(self):
        """Stop monitoring."""
        if not self.is_running:
            return
        
        self.logger.info("🛑 Stopping file monitoring...")
        
        self._stop_event.set()
        
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
        
        self.is_running = False
        self.logger.info("✅ File monitoring stopped")
    
    def run_forever(self):
        """
        Run the monitor indefinitely until stopped.
        Blocks the current thread.
        """
        if not self.start():
            return False
        
        try:
            self.logger.info("🔄 Running file monitor (Press Ctrl+C to stop)")
            
            # Keep running until stop event is set
            while not self._stop_event.is_set():
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.info("📱 Received interrupt signal")
        finally:
            self.stop()
        
        return True
    
    def scan_existing_files(self, max_age_hours: int = 24) -> list:
        """
        Scan for existing transcript files that might need processing.
        
        Args:
            max_age_hours: Only include files modified within this many hours.
            
        Returns:
            List of transcript file paths.
        """
        self.logger.info(f"🔍 Scanning for existing transcripts (max age: {max_age_hours}h)")
        
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        transcript_files = []
        
        try:
            # Find all transcript files
            pattern = "*/meeting_saved_closed_caption.txt"
            for file_path in self.zoom_folder.glob(pattern):
                try:
                    # Check file age
                    mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mod_time > cutoff_time:
                        # Check minimum size
                        file_size = file_path.stat().st_size
                        if file_size >= self.config.monitoring.min_file_size:
                            transcript_files.append(file_path)
                except OSError as e:
                    self.logger.debug(f"Cannot access {file_path}: {e}")
            
            self.logger.info(f"📄 Found {len(transcript_files)} recent transcript files")
            
        except Exception as e:
            self.logger.error(f"Error scanning existing files: {e}")
        
        return transcript_files
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current monitoring status.
        
        Returns:
            Dictionary with status information.
        """
        return {
            "is_running": self.is_running,
            "zoom_folder": str(self.zoom_folder),
            "zoom_folder_exists": self.zoom_folder.exists(),
            "observer_alive": self.observer.is_alive() if self.observer else False,
            "config": {
                "min_file_size": self.config.monitoring.min_file_size,
                "check_interval": self.config.monitoring.check_interval,
                "file_stable_time": self.config.monitoring.file_stable_time
            }
        } 