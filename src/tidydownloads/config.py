"""Yapılandırma yükleme ve varsayılan ayar yönetimi."""

from pathlib import Path
from typing import Any, Dict
from ruamel.yaml import YAML

DEFAULT_CONFIG: Dict[str, Any] = {
    "watch_dir": "~/Downloads",
    "use_trash": True,
    "cleanup": {
        "enabled": True,
        "max_age_days": 30,
        "target_categories": ["Kurulumlar", "Arsivler"],
        "notify_on_delete": True,
    },
    "deduplicate": {
        "enabled": True,
        "notify_on_delete": True,
    },
    "categories": {
        "Belgeler": [".pdf", ".docx", ".doc", ".xlsx", ".pptx", ".txt", ".md", ".csv"],
        "Gorseller": [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"],
        "Kurulumlar": [".exe", ".msi", ".deb", ".rpm", ".AppImage", ".dmg", ".pkg"],
        "Arsivler": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "Videolar": [".mp4", ".mkv", ".avi", ".mov"],
        "Muzik": [".mp3", ".wav", ".flac", ".ogg"],
    },
    "ignore_extensions": [".crdownload", ".part", ".tmp", ".download"],
}


def load_config(config_path: str | Path | None = None) -> Dict[str, Any]:
    """YAML yapılandırmasını okur, yoksa varsayılanları döndürür."""
    config = {**DEFAULT_CONFIG}
    if config_path:
        path = Path(config_path).expanduser()
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                user_cfg = YAML(typ="safe").load(f) or {}
            config.update(user_cfg)
    config["watch_dir"] = str(Path(config["watch_dir"]).expanduser().resolve())
    return config
