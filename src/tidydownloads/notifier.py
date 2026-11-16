"""Çapraz platform masaüstü bildirim modülü."""

import logging
import platform
import shutil
import subprocess

logger = logging.getLogger("tidydownloads")


def send_notification(title: str, message: str) -> bool:
    """Kullanıcıya işletim sistemine uygun masaüstü bildirimi gönderir."""
    system = platform.system()

    # 1. Öncelik: plyer (Windows / macOS / Linux ortak)
    try:
        from plyer import notification  # type: ignore

        notification.notify(
            title=title,
            message=message,
            app_name="TidyDownloads",
            timeout=6,
        )
        return True
    except Exception:
        pass

    # 2. İşletim sistemine özel yerel yedekler
    try:
        if system == "Linux" and shutil.which("notify-send"):
            subprocess.run(
                ["notify-send", "-a", "TidyDownloads", title, message],
                check=False,
                timeout=5,
            )
            return True
        if system == "Darwin" and shutil.which("osascript"):
            escaped_msg = message.replace('"', '\"')
            escaped_title = title.replace('"', '\"')
            script = f'display notification "{escaped_msg}" with title "{escaped_title}"'
            subprocess.run(["osascript", "-e", script], check=False, timeout=5)
            return True
        if system == "Windows":
            ps_script = (
                "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, "
                "ContentType = WindowsRuntime] > $null; "
                f"$msg = '{title}: {message}'; Write-Output $msg"
            )
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                check=False,
                timeout=5,
            )
            return True
    except Exception as exc:
        logger.debug("Yerel bildirim gönderilemedi: %s", exc)

    # 3. Son çare: konsol çıktısı
    print(f"[BİLDİRİM] {title} -> {message}")
    return False
