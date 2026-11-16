"""Komut satırı ve uygulama giriş noktası."""

import argparse
import logging
from pathlib import Path

from tidydownloads.config import load_config
from tidydownloads.organizer import DownloadOrganizer
from tidydownloads.watcher import start_watching


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="tidydownloads",
        description="Akıllı İndirilenler klasörü düzenleyicisi ve bildirimli temizleyici.",
    )
    parser.add_argument(
        "-c",
        "--config",
        default="config.yaml",
        help="Yapılandırma dosyası yolu (varsayılan: config.yaml)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Arka planda beklemeden klasörü bir kez düzenle ve temizle",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Detaylı log çıktısı göster",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )

    cfg_path = Path(args.config)
    config = load_config(cfg_path if cfg_path.exists() else None)
    organizer = DownloadOrganizer(config)

    if args.once:
        moved = organizer.organize_existing()
        deleted = organizer.cleanup_old_files()
        print(f"Tamamlandı: {moved} dosya düzenlendi, {len(deleted)} eski dosya temizlendi.")
    else:
        start_watching(organizer)


if __name__ == "__main__":
    main()
