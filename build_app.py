"""PyInstaller ile tek dosyalık çalıştırılabilir uygulama (.exe / binary) üretir."""

import subprocess
import sys


def build() -> None:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "TidyDownloads",
        "--add-data",
        "config.yaml:.",
        "src/tidydownloads/cli.py",
    ]
    print("Uygulama derleniyor:", " ".join(cmd))
    subprocess.run(cmd, check=True)
    print("Derleme tamamlandı! Çıktı: dist/TidyDownloads")


if __name__ == "__main__":
    build()
