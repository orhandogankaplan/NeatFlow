"""Klasör değişikliklerini gerçek zamanlı izleyen servis."""

import logging
from pathlib import Path
import time

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from tidydownloads.organizer import DownloadOrganizer

logger = logging.getLogger("tidydownloads")


class _DownloadHandler(FileSystemEventHandler):
    def __init__(self, organizer: DownloadOrganizer) -> None:
        self.organizer = organizer

    def on_created(self, event) -> None:  # type: ignore[override]
        if not event.is_directory:
            time.sleep(0.5)
            self.organizer.organize_file(Path(event.src_path))

    def on_moved(self, event) -> None:  # type: ignore[override]
        if not event.is_directory:
            self.organizer.organize_file(Path(event.dest_path))


def start_watching(organizer: DownloadOrganizer, cleanup_interval_sec: int = 3600) -> None:
    """İndirilenler klasörünü sürekli izler ve periyodik temizlik yapar."""
    organizer.watch_dir.mkdir(parents=True, exist_ok=True)
    organizer.organize_existing()
    organizer.cleanup_old_files()

    observer = Observer()
    observer.schedule(_DownloadHandler(organizer), str(organizer.watch_dir), recursive=False)
    observer.start()
    logger.info("İzleme başlatıldı: %s", organizer.watch_dir)

    last_cleanup = time.monotonic()
    try:
        while True:
            time.sleep(5)
            if time.monotonic() - last_cleanup >= cleanup_interval_sec:
                organizer.cleanup_old_files()
                last_cleanup = time.monotonic()
    except KeyboardInterrupt:
        logger.info("TidyDownloads durduruluyor...")
        observer.stop()
    observer.join()
