"""Dosya kategorilendirme, kopya tespiti ve bildirimli temizleme motoru."""

from datetime import datetime, timedelta
import hashlib
import logging
from pathlib import Path
import shutil
from typing import Any, Callable, Dict, List

from tidydownloads.notifier import send_notification

logger = logging.getLogger("tidydownloads")


def _safe_delete(file_path: Path, use_trash: bool = True) -> None:
    """Dosyayı ayara göre Çöp Kutusuna taşır veya kalıcı olarak siler."""
    if use_trash:
        try:
            from send2trash import send2trash  # type: ignore

            send2trash(str(file_path))
            return
        except Exception as exc:
            logger.warning("send2trash başarısız, doğrudan siliniyor (%s): %s", file_path.name, exc)
    file_path.unlink(missing_ok=True)


def _file_sha256(file_path: Path) -> str:
    """Dosyanın SHA-256 özetini hesaplar."""
    hasher = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


class DownloadOrganizer:
    """İndirilenler klasörünü düzenleyen ve eski/kopya dosyaları temizleyen sınıf."""

    def __init__(
        self,
        config: Dict[str, Any],
        notifier: Callable[[str, str], bool] = send_notification,
    ) -> None:
        self.config = config
        self.watch_dir = Path(config["watch_dir"])
        self.notifier = notifier
        self.categories: Dict[str, List[str]] = config.get("categories", {})
        self.ignore_exts = {ext.lower() for ext in config.get("ignore_extensions", [])}
        self.use_trash = bool(config.get("use_trash", True))

    def get_category(self, file_path: Path) -> str | None:
        ext = file_path.suffix.lower()
        if ext in self.ignore_exts or not ext:
            return None
        for category, extensions in self.categories.items():
            if ext in [e.lower() for e in extensions]:
                return category
        return "Diger"

    def organize_file(self, file_path: Path) -> Path | None:
        """Tek bir dosyayı uygun kategori klasörüne taşır."""
        if not file_path.is_file() or file_path.name.startswith("."):
            return None

        category = self.get_category(file_path)
        if category is None:
            return None

        target_dir = self.watch_dir / category
        target_dir.mkdir(parents=True, exist_ok=True)
        dest = target_dir / file_path.name

        if dest.exists() and dest != file_path:
            if self.config.get("deduplicate", {}).get("enabled", True):
                if _file_sha256(file_path) == _file_sha256(dest):
                    _safe_delete(file_path, use_trash=self.use_trash)
                    if self.config.get("deduplicate", {}).get("notify_on_delete", True):
                        self.notifier(
                            "TidyDownloads - Kopya Dosya Silindi",
                            f"'{file_path.name}' dosyasının birebir kopyası temizlendi.",
                        )
                    return None
            stem, suffix = file_path.stem, file_path.suffix
            counter = 1
            while dest.exists():
                dest = target_dir / f"{stem} ({counter}){suffix}"
                counter += 1

        shutil.move(str(file_path), str(dest))
        logger.info("Taşındı: %s -> %s", file_path.name, category)
        return dest

    def organize_existing(self) -> int:
        """Klasördeki mevcut tüm dosyaları düzenler."""
        if not self.watch_dir.exists():
            return 0
        moved = 0
        for item in list(self.watch_dir.iterdir()):
            if item.is_file():
                if self.organize_file(item) is not None:
                    moved += 1
        return moved

    def cleanup_old_files(self, now: datetime | None = None) -> List[str]:
        """Belirlenen günden eski dosyaları siler ve kullanıcıya bildirim gönderir."""
        cleanup_cfg = self.config.get("cleanup", {})
        if not cleanup_cfg.get("enabled", True):
            return []

        max_age_days = int(cleanup_cfg.get("max_age_days", 30))
        target_categories = cleanup_cfg.get("target_categories", [])
        notify_on_delete = bool(cleanup_cfg.get("notify_on_delete", True))
        cutoff = (now or datetime.now()) - timedelta(days=max_age_days)

        deleted_files: List[str] = []
        search_dirs = (
            [self.watch_dir / cat for cat in target_categories]
            if target_categories
            else [p for p in self.watch_dir.iterdir() if p.is_dir()]
        )

        for folder in search_dirs:
            if not folder.exists():
                continue
            for file_path in list(folder.iterdir()):
                if not file_path.is_file():
                    continue
                mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                if mtime < cutoff:
                    _safe_delete(file_path, use_trash=self.use_trash)
                    deleted_files.append(file_path.name)
                    logger.info("Eski dosya silindi: %s", file_path.name)

        if deleted_files and notify_on_delete:
            preview = ", ".join(deleted_files[:3])
            extra = f" (+{len(deleted_files) - 3} diğer)" if len(deleted_files) > 3 else ""
            action_text = "Çöp Kutusuna taşındı" if self.use_trash else "kalıcı olarak silindi"
            self.notifier(
                "TidyDownloads - Otomatik Temizlik",
                f"{len(deleted_files)} eski dosya {action_text}: {preview}{extra}",
            )

        return deleted_files
