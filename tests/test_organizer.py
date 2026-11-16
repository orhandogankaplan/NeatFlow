"""TidyDownloads birim testleri."""

from datetime import datetime, timedelta
import os
from pathlib import Path
import tempfile
import unittest

from tidydownloads.organizer import DownloadOrganizer


class TestDownloadOrganizer(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.watch_dir = Path(self.tmp_dir.name)
        self.notifications: list[tuple[str, str]] = []

        def fake_notifier(title: str, message: str) -> bool:
            self.notifications.append((title, message))
            return True

        self.config = {
            "watch_dir": str(self.watch_dir),
            "use_trash": False,
            "cleanup": {
                "enabled": True,
                "max_age_days": 30,
                "target_categories": ["Kurulumlar"],
                "notify_on_delete": True,
            },
            "deduplicate": {
                "enabled": True,
                "notify_on_delete": True,
            },
            "categories": {
                "Belgeler": [".pdf", ".txt"],
                "Kurulumlar": [".exe", ".deb"],
            },
            "ignore_extensions": [".part", ".crdownload"],
        }
        self.organizer = DownloadOrganizer(self.config, notifier=fake_notifier)

    def tearDown(self) -> None:
        self.tmp_dir.cleanup()

    def test_organize_and_ignore(self) -> None:
        pdf = self.watch_dir / "rapor.pdf"
        part = self.watch_dir / "indirme.part"
        pdf.write_text("test pdf", encoding="utf-8")
        part.write_text("partial", encoding="utf-8")

        moved = self.organizer.organize_existing()
        self.assertEqual(moved, 1)
        self.assertTrue((self.watch_dir / "Belgeler" / "rapor.pdf").exists())
        self.assertTrue(part.exists())

    def test_duplicate_file_triggers_notification(self) -> None:
        f1 = self.watch_dir / "not.txt"
        f1.write_text("aynı içerik", encoding="utf-8")
        self.organizer.organize_existing()

        f2 = self.watch_dir / "not.txt"
        f2.write_text("aynı içerik", encoding="utf-8")
        self.organizer.organize_existing()

        self.assertEqual(len(self.notifications), 1)
        self.assertIn("Kopya Dosya Silindi", self.notifications[0][0])

    def test_old_file_cleanup_triggers_notification(self) -> None:
        installers_dir = self.watch_dir / "Kurulumlar"
        installers_dir.mkdir()
        old_file = installers_dir / "eski_program.deb"
        old_file.write_text("binary", encoding="utf-8")

        old_time = (datetime.now() - timedelta(days=45)).timestamp()
        os.utime(old_file, (old_time, old_time))

        deleted = self.organizer.cleanup_old_files()
        self.assertEqual(deleted, ["eski_program.deb"])
        self.assertFalse(old_file.exists())
        self.assertEqual(len(self.notifications), 1)
        self.assertIn("Otomatik Temizlik", self.notifications[0][0])


if __name__ == "__main__":
    unittest.main()
