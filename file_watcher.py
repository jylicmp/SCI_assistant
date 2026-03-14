#!/usr/bin/env python3
"""
File Watcher - Monitor data_md/ directory for changes

Watches for file additions and modifications in the data_md/ directory
and automatically syncs changes to Notion.

Features:
- Debounce to avoid frequent triggers
- Background execution support
- Logging to file

Usage:
    python file_watcher.py              # Start watching (foreground)
    python file_watcher.py --background # Start watching (background)
    python file_watcher.py --stop       # Stop background watcher
"""

import os
import sys
import time
import signal
import logging
import argparse
from pathlib import Path
from datetime import datetime
from threading import Timer

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configuration
DATA_MD_DIR = Path(__file__).parent / "data_md"
LOG_FILE = Path(__file__).parent / "file_watcher.log"
PID_FILE = Path(__file__).parent / ".file_watcher.pid"
DEBOUNCE_SECONDS = 2.0  # Wait time after file change before syncing

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MarkdownFileHandler(FileSystemEventHandler):
    """Handle file system events for markdown files."""

    def __init__(self, sync_callback):
        super().__init__()
        self.sync_callback = sync_callback
        self._debounce_timers = {}

    def _debounce(self, file_path: Path):
        """Debounce file changes to avoid frequent syncing."""
        # Cancel existing timer for this file
        if file_path in self._debounce_timers:
            self._debounce_timers[file_path].cancel()

        # Create new timer
        timer = Timer(
            DEBOUNCE_SECONDS,
            self._trigger_sync,
            args=[file_path]
        )
        timer.daemon = True
        timer.start()
        self._debounce_timers[file_path] = timer

        logger.info(f"Detected change: {file_path.name} (debouncing {DEBOUNCE_SECONDS}s)")

    def _trigger_sync(self, file_path: Path):
        """Trigger sync for a file after debounce period."""
        try:
            logger.info(f"Syncing: {file_path}")
            self.sync_callback(file_path)
        except Exception as e:
            logger.error(f"Error syncing {file_path}: {e}")

    def on_created(self, event):
        """Handle file creation events."""
        if isinstance(event, FileCreatedEvent):
            file_path = Path(event.src_path)
            if file_path.suffix == ".md" and "data_md" in str(file_path):
                self._debounce(file_path)

    def on_modified(self, event):
        """Handle file modification events."""
        if isinstance(event, FileModifiedEvent):
            file_path = Path(event.src_path)
            if file_path.suffix == ".md" and "data_md" in str(file_path):
                self._debounce(file_path)

    def on_moved(self, event):
        """Handle file move events (treat as creation)."""
        if hasattr(event, 'dest_path'):
            file_path = Path(event.dest_path)
            if file_path.suffix == ".md" and "data_md" in str(file_path):
                self._debounce(file_path)


class FileWatcher:
    """Main file watcher class."""

    def __init__(self):
        self.observer = None
        self.syncer = None
        self._running = False

    def _get_syncer(self):
        """Lazy import syncer to avoid circular imports."""
        if self.syncer is None:
            from notion_sync import NotionSync
            self.syncer = NotionSync()
        return self.syncer

    def start(self):
        """Start watching the data_md directory."""
        # Ensure data_md directory exists
        if not DATA_MD_DIR.exists():
            logger.error(f"Directory not found: {DATA_MD_DIR}")
            sys.exit(1)

        # Create event handler
        def sync_callback(file_path: Path):
            try:
                self._get_syncer().sync_file(file_path)
            except Exception as e:
                logger.error(f"Sync failed for {file_path}: {e}")

        event_handler = MarkdownFileHandler(sync_callback)

        # Create observer
        self.observer = Observer()
        self.observer.schedule(
            event_handler,
            str(DATA_MD_DIR),
            recursive=False
        )

        # Start observing
        self.observer.start()
        self._running = True

        logger.info(f"Started watching: {DATA_MD_DIR}")
        logger.info(f"Log file: {LOG_FILE}")
        logger.info(f"Press Ctrl+C to stop")

        # Save PID for background mode
        self._save_pid()

        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the file watcher."""
        logger.info("Stopping file watcher...")
        self._running = False

        if self.observer:
            self.observer.stop()
            self.observer.join()

        self._remove_pid()
        logger.info("File watcher stopped")

    def _save_pid(self):
        """Save PID to file for background mode."""
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))

    def _remove_pid(self):
        """Remove PID file."""
        if PID_FILE.exists():
            PID_FILE.unlink()


def is_running():
    """Check if a watcher is already running."""
    if not PID_FILE.exists():
        return False

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())

        # Check if process is running
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError):
        # Process not running, clean up PID file
        PID_FILE.unlink()
        return False


def stop_watcher():
    """Stop a running background watcher."""
    if not PID_FILE.exists():
        logger.info("No background watcher is running")
        return

    try:
        with open(PID_FILE, "r") as f:
            pid = int(f.read().strip())

        os.kill(pid, signal.SIGTERM)
        logger.info(f"Sent stop signal to process {pid}")

        # Wait for process to stop
        for _ in range(10):
            if not is_running():
                logger.info("Background watcher stopped")
                return
            time.sleep(0.5)

        logger.warning("Process did not stop gracefully")

    except ProcessLookupError:
        logger.info("Process was not running (cleaned up PID file)")
        PID_FILE.unlink()
    except Exception as e:
        logger.error(f"Error stopping watcher: {e}")


def run_background():
    """Run the watcher as a background process."""
    if is_running():
        logger.info("File watcher is already running in background")
        return

    # Fork to background
    pid = os.fork()
    if pid > 0:
        logger.info(f"Started background watcher (PID: {pid})")
        return

    # Child process - detach from parent
    os.setsid()

    # Redirect stdout/stderr
    sys.stdout = open("/dev/null", "w")
    sys.stderr = open("/dev/null", "w")

    # Start watcher
    watcher = FileWatcher()
    watcher.start()


def main():
    parser = argparse.ArgumentParser(description="Watch data_md/ for changes")
    parser.add_argument(
        "--background",
        action="store_true",
        help="Run in background"
    )
    parser.add_argument(
        "--stop",
        action="store_true",
        help="Stop background watcher"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Check if watcher is running"
    )

    args = parser.parse_args()

    if args.stop:
        stop_watcher()
    elif args.status:
        if is_running():
            logger.info("File watcher is running")
        else:
            logger.info("File watcher is not running")
    elif args.background:
        run_background()
    else:
        # Foreground mode
        watcher = FileWatcher()
        watcher.start()


if __name__ == "__main__":
    main()
