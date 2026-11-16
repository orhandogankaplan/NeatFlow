import os, shutil, threading, time
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext, messagebox

try:
    from send2trash import send2trash
except ImportError:
    send2trash = None

CATEGORIES = {
    'Belgeler': ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.pptx', '.csv'],
    'Gorseller': ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'],
    'Arsivler': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Kurulumlar': ['.exe', '.msi', '.dmg', '.pkg', '.deb'],
    'Videolar': ['.mp4', '.mkv', '.avi', '.mov']
}
MANAGED_FOLDERS = list(CATEGORIES.keys()) + ['Diger']
IGNORE_EXT = {'.part', '.crdownload', '.tmp', '.ini'}


class NeatFlowEngine:
    def __init__(self, watch_dir):
        self.watch_dir = Path(watch_dir)

    def organize_existing(self):
        if not self.watch_dir.exists():
            return 0
        moved = 0
        for item in self.watch_dir.iterdir():
            if not item.is_file() or item.suffix.lower() in IGNORE_EXT or item.name.startswith('NeatFlow'):
                continue
            ext = item.suffix.lower()
            target_cat = next((cat for cat, exts in CATEGORIES.items() if ext in exts), 'Diger')
            dest_dir = self.watch_dir / target_cat
            dest_dir.mkdir(exist_ok=True)
            dest_path = dest_dir / item.name
            counter = 1
            while dest_path.exists():
                dest_path = dest_dir / f'{item.stem}_{counter}{item.suffix}'
                counter += 1
            try:
                shutil.move(str(item), str(dest_path))
                moved += 1
            except Exception:
                pass
        return moved

    def find_old_files(self, max_age_days=30):
        if not self.watch_dir.exists():
            return []
        cutoff = time.time() - (max_age_days * 86400)
        olds = []
        scan_dirs = [self.watch_dir] + [self.watch_dir / d for d in MANAGED_FOLDERS]
        for folder in scan_dirs:
            if not folder.exists():
                continue
            for f in folder.iterdir():
                if not f.is_file() or f.suffix.lower() in IGNORE_EXT or f.name.startswith(('NeatFlow', '.')):
                    continue
                try:
                    st = f.stat()
                    if st.st_mtime < cutoff and st.st_size > 0:
                        olds.append(f)
                except Exception:
                    pass
        olds.sort(key=lambda x: x.stat().st_size, reverse=True)
        return olds


class NeatFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title('NeatFlow - Akilli Indirilenler Duzenleyici')
        self.root.geometry('580x390')
        self.running = False
        self.notified = set()
        watch_path = Path.home() / 'Downloads'
        self.engine = NeatFlowEngine(watch_path)

        tk.Label(root, text='NeatFlow Klasor Yoneticisi', font=('Segoe UI', 14, 'bold')).pack(pady=10)
        tk.Label(root, text=f'Izlenen Klasor: {watch_path}', fg='#555').pack()

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=12)
        self.btn_now = tk.Button(btn_frame, text='Simdi Duzenle', width=14, bg='#2ea44f', fg='white', command=self.run_once)
        self.btn_now.grid(row=0, column=0, padx=4)
        self.btn_toggle = tk.Button(btn_frame, text='Otomatik Izlemeyi Baslat', width=20, bg='#0969da', fg='white', command=self.toggle_watch)
        self.btn_toggle.grid(row=0, column=1, padx=4)
        self.btn_old = tk.Button(btn_frame, text='Eski Dosyalari Tara', width=18, bg='#e98b00', fg='white', command=lambda: self.check_old_files(True))
        self.btn_old.grid(row=0, column=2, padx=4)

        self.log_area = scrolledtext.ScrolledText(root, height=14, width=68, state='disabled', font=('Consolas', 9))
        self.log_area.pack(padx=10, pady=5)
        self.log('NeatFlow hazir. Yalnizca yonetilen klasorlerdeki 30 gunden eski dosyalar taranir.')

    def log(self, msg):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f'[{time.strftime("%H:%M:%S")}] {msg}\n')
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def run_once(self):
        moved = self.engine.organize_existing()
        self.log(f'Tarama tamamlandi -> Duzenlenen: {moved} dosya')
        self.check_old_files(False)

    def check_old_files(self, manual=False):
        olds = self.engine.find_old_files(30)
        if not olds:
            if manual:
                self.log('30 gunden eski dosya bulunamadi.')
            return
        if not manual and all(str(f) in self.notified for f in olds):
            return
        for f in olds:
            self.notified.add(str(f))
        mb = sum(f.stat().st_size for f in olds) / (1024 * 1024)
        lines = []
        for f in olds[:10]:
            f_mb = f.stat().st_size / (1024 * 1024)
            loc = 'Ana Klasor' if f.parent == self.engine.watch_dir else f.parent.name
            lines.append(f'- {f.name} [{loc}] ({f_mb:.1f} MB)')
        names = '\n'.join(lines)
        if len(olds) > 10:
            names += f'\n...ve {len(olds) - 10} dosya daha'
        self.log(f'BILDIRIM: {len(olds)} eski dosya bulundu ({mb:.1f} MB). Onay bekleniyor...')
        ans = messagebox.askyesno(
            'NeatFlow - Temizlik Bildirimi',
            f'30 gunden eski {len(olds)} dosya tespit edildi ({mb:.1f} MB yer kapliyor):\n\n{names}\n\nHepsi Geri Donusum Kutusuna gonderilsin mi?'
        )
        if ans:
            cnt = 0
            for f in olds:
                try:
                    if send2trash:
                        send2trash(str(f))
                    else:
                        f.unlink()
                    cnt += 1
                    self.notified.discard(str(f))
                except Exception:
                    pass
            self.log(f'ONAYLANDI: {cnt} dosya Geri Donusum Kutusuna tasindi ({mb:.1f} MB yer acildi).')
        else:
            self.log('IPTAL EDILDI: Kullanici onay vermedi, dosyalara dokunulmadi.')

    def toggle_watch(self):
        if not self.running:
            self.running = True
            self.btn_toggle.config(text='Izlemeyi Durdur', bg='#cf222e')
            self.log('Arka plan izleme baslatildi...')
            threading.Thread(target=self.watch_loop, daemon=True).start()
        else:
            self.running = False
            self.btn_toggle.config(text='Otomatik Izlemeyi Baslat', bg='#0969da')
            self.log('Otomatik izleme durduruldu.')

    def watch_loop(self):
        while self.running:
            moved = self.engine.organize_existing()
            if moved:
                self.root.after(0, self.log, f'Yeni indirilen {moved} dosya duzenlendi.')
            self.root.after(0, lambda: self.check_old_files(False))
            time.sleep(5)


def main():
    root = tk.Tk()
    app = NeatFlowApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()