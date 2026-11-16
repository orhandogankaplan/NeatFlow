import os, shutil, threading, time, winreg
from pathlib import Path
import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog

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
CAT_COLORS = {
    'Belgeler': '#388bfd',
    'Gorseller': '#a371f7',
    'Arsivler': '#d29922',
    'Kurulumlar': '#f85149',
    'Videolar': '#3fb950',
    'Diger': '#8b949e'
}
MANAGED_FOLDERS = list(CATEGORIES.keys()) + ['Diger']
IGNORE_EXT = {'.part', '.crdownload', '.tmp', '.ini', '.lnk', '.url'}

BG_MAIN = '#0d1117'
BG_CARD = '#161b22'
BG_INPUT = '#21262d'
BORDER = '#30363d'
FG_TEXT = '#f0f6fc'
FG_MUTED = '#8b949e'


class NeatFlowEngine:
    def __init__(self, watch_dir):
        self.watch_dir = Path(watch_dir)

    def organize_existing(self):
        if not self.watch_dir.exists():
            return 0
        moved = 0
        for item in self.watch_dir.iterdir():
            if not item.is_file() or item.suffix.lower() in IGNORE_EXT or item.name.startswith(('NeatFlow', '.')):
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

    def get_stats(self):
        sizes = {k: 0 for k in MANAGED_FOLDERS}
        total_files = 0
        if not self.watch_dir.exists():
            return total_files, sizes
        for item in self.watch_dir.iterdir():
            if item.is_file() and not item.name.startswith(('NeatFlow', '.')):
                ext = item.suffix.lower()
                if ext in IGNORE_EXT:
                    continue
                cat = next((c for c, exts in CATEGORIES.items() if ext in exts), 'Diger')
                try:
                    sizes[cat] += item.stat().st_size
                    total_files += 1
                except Exception:
                    pass
        for cat in MANAGED_FOLDERS:
            sub = self.watch_dir / cat
            if sub.exists():
                for f in sub.iterdir():
                    if f.is_file():
                        try:
                            sizes[cat] += f.stat().st_size
                            total_files += 1
                        except Exception:
                            pass
        return total_files, sizes

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
                    last_used = max(st.st_mtime, st.st_atime)
                    if last_used < cutoff and st.st_size > 0:
                        olds.append(f)
                except Exception:
                    pass
        olds.sort(key=lambda x: x.stat().st_size, reverse=True)
        return olds

    def get_installed_programs(self):
        programs = []
        reg_paths = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        ]
        seen = set()
        for root_key, sub_path in reg_paths:
            try:
                with winreg.OpenKey(root_key, sub_path) as key:
                    for i in range(winreg.QueryInfoKey(key)[0]):
                        try:
                            sub_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, sub_name) as sub_key:
                                name, _ = winreg.QueryValueEx(sub_key, "DisplayName")
                                if not name or name in seen or "Update for" in name:
                                    continue
                                seen.add(name)
                                try:
                                    size_kb, _ = winreg.QueryValueEx(sub_key, "EstimatedSize")
                                    size_mb = size_kb / 1024
                                except Exception:
                                    size_mb = 0
                                try:
                                    install_date, _ = winreg.QueryValueEx(sub_key, "InstallDate")
                                except Exception:
                                    install_date = "Bilinmiyor"
                                programs.append((size_mb, name, install_date))
                        except Exception:
                            continue
            except Exception:
                continue
        programs.sort(reverse=True)
        return programs


class NeatFlowApp:
    def __init__(self, root):
        self.root = root
        self.root.title('NeatFlow v1.1 - Akilli Klasor ve Sistem Yoneticisi')
        self.root.geometry('760x540')
        self.root.configure(bg=BG_MAIN)
        self.root.resizable(False, False)

        self.running = False
        self.notified = set()
        self.watch_path = Path.home() / 'Downloads'
        self.engine = NeatFlowEngine(self.watch_path)

        # Üst Başlık Kartı
        header = tk.Frame(root, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        header.pack(fill=tk.X, padx=16, pady=(14, 8))

        title_row = tk.Frame(header, bg=BG_CARD)
        title_row.pack(fill=tk.X, padx=14, pady=(10, 4))
        tk.Label(title_row, text='⚡ NeatFlow', font=('Segoe UI', 16, 'bold'), bg=BG_CARD, fg='#58a6ff').pack(side=tk.LEFT)
        tk.Label(title_row, text='Akilli Dosya Duzenleyici & Temizlik Asistani', font=('Segoe UI', 10), bg=BG_CARD, fg=FG_MUTED).pack(side=tk.LEFT, padx=10)

        self.status_badge = tk.Label(title_row, text='● BEKLEMEDE', font=('Segoe UI', 8, 'bold'), bg='#21262d', fg=FG_MUTED, padx=8, pady=3)
        self.status_badge.pack(side=tk.RIGHT)

        # Klasör Seçim Satırı
        dir_row = tk.Frame(header, bg=BG_CARD)
        dir_row.pack(fill=tk.X, padx=14, pady=(4, 12))
        self.lbl_dir = tk.Label(dir_row, text=f'📁 {self.watch_path}', font=('Consolas', 9), bg=BG_INPUT, fg=FG_TEXT, padx=10, pady=5, anchor='w')
        self.lbl_dir.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        self._make_btn(dir_row, 'Indirilenler', BG_INPUT, FG_TEXT, lambda: self.set_folder(Path.home() / 'Downloads')).pack(side=tk.LEFT, padx=2)
        self._make_btn(dir_row, 'Masaustu', BG_INPUT, FG_TEXT, lambda: self.set_folder(Path.home() / 'Desktop')).pack(side=tk.LEFT, padx=2)
        self._make_btn(dir_row, 'Klasor Sec...', '#1f6feb', '#ffffff', self.pick_folder).pack(side=tk.LEFT, padx=(4, 0))

        # İstatistik Kartları
        stats_frame = tk.Frame(root, bg=BG_MAIN)
        stats_frame.pack(fill=tk.X, padx=16, pady=4)

        self.card_files = self._make_stat_card(stats_frame, 'TOPLAM DOSYA', '0')
        self.card_files.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))

        self.card_size = self._make_stat_card(stats_frame, 'TOPLAM BOYUT', '0 MB')
        self.card_size.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        self.card_old = self._make_stat_card(stats_frame, 'TEMIZLENEBILIR (30G+)', '0 MB')
        self.card_old.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(6, 0))

        # Görsel Kategori Dağılım Çubuğu
        bar_card = tk.Frame(root, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        bar_card.pack(fill=tk.X, padx=16, pady=8)

        tk.Label(bar_card, text='Kategori Depolama Dagilimi', font=('Segoe UI', 9, 'bold'), bg=BG_CARD, fg=FG_MUTED).pack(anchor='w', padx=12, pady=(8, 4))
        self.canvas = tk.Canvas(bar_card, height=16, bg=BG_INPUT, highlightthickness=0)
        self.canvas.pack(fill=tk.X, padx=12, pady=(0, 6))

        legend_row = tk.Frame(bar_card, bg=BG_CARD)
        legend_row.pack(fill=tk.X, padx=12, pady=(0, 8))
        for cat, col in CAT_COLORS.items():
            item_f = tk.Frame(legend_row, bg=BG_CARD)
            item_f.pack(side=tk.LEFT, padx=(0, 14))
            tk.Label(item_f, text='■', fg=col, bg=BG_CARD, font=('Segoe UI', 9)).pack(side=tk.LEFT)
            tk.Label(item_f, text=cat, fg=FG_MUTED, bg=BG_CARD, font=('Segoe UI', 8)).pack(side=tk.LEFT, padx=3)

        # Ana Aksiyon Butonları
        btn_frame = tk.Frame(root, bg=BG_MAIN)
        btn_frame.pack(fill=tk.X, padx=16, pady=6)

        self.btn_now = self._make_btn(btn_frame, '▶ Simdi Duzenle', '#238636', '#ffffff', self.run_once, font=('Segoe UI', 9, 'bold'), pady=7)
        self.btn_now.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        self.btn_toggle = self._make_btn(btn_frame, '◉ Otomatik Izle', '#1f6feb', '#ffffff', self.toggle_watch, font=('Segoe UI', 9, 'bold'), pady=7)
        self.btn_toggle.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.btn_old = self._make_btn(btn_frame, '🧹 Eski Dosyalari Tara', '#9e6a03', '#ffffff', lambda: self.check_old_files(True), font=('Segoe UI', 9, 'bold'), pady=7)
        self.btn_old.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.btn_prog = self._make_btn(btn_frame, '📦 Yuklu Programlar', '#8957e5', '#ffffff', self.show_programs, font=('Segoe UI', 9, 'bold'), pady=7)
        self.btn_prog.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

        # İşlem Günlüğü (Terminal Görünümlü)
        log_card = tk.Frame(root, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
        log_card.pack(fill=tk.BOTH, expand=True, padx=16, pady=(4, 14))

        self.log_area = scrolledtext.ScrolledText(
            log_card, height=10, bg=BG_CARD, fg=FG_TEXT, insertbackground=FG_TEXT,
            relief=tk.FLAT, font=('Consolas', 9), state='disabled', padx=8, pady=6
        )
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.tag_config('ok', foreground='#3fb950')
        self.log_area.tag_config('warn', foreground='#d29922')
        self.log_area.tag_config('info', foreground='#58a6ff')

        self.refresh_dashboard()
        self.log('NeatFlow modern arayuzu hazir. Klasor secip duzenleme veya temizlik baslatabilirsiniz.', 'info')

    def _make_btn(self, parent, text, bg, fg, cmd, font=('Segoe UI', 8, 'bold'), pady=4):
        return tk.Button(
            parent, text=text, bg=bg, fg=fg, activebackground=bg, activeforeground=fg,
            relief=tk.FLAT, cursor='hand2', font=font, padx=10, pady=pady, command=cmd
        )

    def _make_stat_card(self, parent, title, val):
        card = tk.Frame(parent, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1, padx=12, pady=8)
        tk.Label(card, text=title, font=('Segoe UI', 8, 'bold'), bg=BG_CARD, fg=FG_MUTED).pack(anchor='w')
        lbl_val = tk.Label(card, text=val, font=('Segoe UI', 14, 'bold'), bg=BG_CARD, fg=FG_TEXT)
        lbl_val.pack(anchor='w', pady=(2, 0))
        card.val_label = lbl_val
        return card

    def refresh_dashboard(self):
        total_files, sizes = self.engine.get_stats()
        total_bytes = sum(sizes.values())
        olds = self.engine.find_old_files(30)
        old_mb = sum(f.stat().st_size for f in olds) / (1024 * 1024)

        self.card_files.val_label.config(text=f'{total_files} dosya')
        self.card_size.val_label.config(text=f'{total_bytes / (1024 * 1024):.1f} MB')
        self.card_old.val_label.config(text=f'{old_mb:.1f} MB ({len(olds)})', fg='#d29922' if olds else '#3fb950')

        self.root.update_idletasks()
        w = self.canvas.winfo_width() or 700
        self.canvas.delete('all')
        if total_bytes > 0:
            x = 0
            for cat in MANAGED_FOLDERS:
                sz = sizes.get(cat, 0)
                if sz > 0:
                    bar_w = max(4, int((sz / total_bytes) * w))
                    self.canvas.create_rectangle(x, 0, x + bar_w, 16, fill=CAT_COLORS[cat], width=0)
                    x += bar_w

    def set_folder(self, path):
        self.watch_path = Path(path)
        self.engine = NeatFlowEngine(self.watch_path)
        self.notified.clear()
        self.lbl_dir.config(text=f'📁 {self.watch_path}')
        self.refresh_dashboard()
        self.log(f'Hedef klasor degistirildi: {self.watch_path}', 'info')

    def pick_folder(self):
        chosen = filedialog.askdirectory(initialdir=str(self.watch_path), title='Duzenlenecek Klasoru Secin')
        if chosen:
            self.set_folder(chosen)

    def log(self, msg, tag=None):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, f'[{time.strftime("%H:%M:%S")}] {msg}\n', tag)
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def run_once(self):
        moved = self.engine.organize_existing()
        self.refresh_dashboard()
        self.log(f'Tarama tamamlandi -> {moved} dosya kategorilere ayrildi.', 'ok')
        self.check_old_files(False)

    def check_old_files(self, manual=False):
        olds = self.engine.find_old_files(30)
        if not olds:
            if manual:
                self.log(f'[{self.watch_path.name}] icinde 30 gunden eski kullanilmayan dosya bulunamadi.', 'ok')
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
        self.log(f'BILDIRIM: {len(olds)} eski dosya tespit edildi ({mb:.1f} MB). Onay bekleniyor...', 'warn')
        ans = messagebox.askyesno(
            'NeatFlow - Temizlik Bildirimi',
            f'"{self.watch_path.name}" konumunda 30 gunden eski {len(olds)} dosya bulundu ({mb:.1f} MB):\n\n{names}\n\nHepsi Geri Donusum Kutusuna gonderilsin mi?'
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
            self.refresh_dashboard()
            self.log(f'ONAYLANDI: {cnt} dosya Geri Donusum Kutusuna tasindi ({mb:.1f} MB yer acildi).', 'ok')
        else:
            self.log('IPTAL EDILDI: Kullanici onay vermedi, dosyalara dokunulmadi.', 'warn')

    def show_programs(self):
        progs = self.engine.get_installed_programs()
        self.log(f'Sistemde {len(progs)} yuklu program bulundu. En cok yer kaplayan ilk 12 program:', 'info')
        for size_mb, name, date in progs[:12]:
            sz = f'{size_mb:.0f} MB' if size_mb > 0 else 'Boyut bilinmiyor'
            self.log(f'  • {name} ({sz}) - Kurulum: {date}')
        if messagebox.askyesno('NeatFlow - Program Kaldirma', 'Kullanmadiginiz programlari kaldirmak icin Windows Program Ekle/Kaldir penceresi acilsin mi?'):
            os.system('start appwiz.cpl')

    def toggle_watch(self):
        if not self.running:
            self.running = True
            self.btn_toggle.config(text='■ Izlemeyi Durdur', bg='#da3633')
            self.status_badge.config(text='● AKTIF IZLEME', bg='#1f3a2c', fg='#3fb950')
            self.log('Arka plan canli izleme baslatildi...', 'ok')
            threading.Thread(target=self.watch_loop, daemon=True).start()
        else:
            self.running = False
            self.btn_toggle.config(text='◉ Otomatik Izle', bg='#1f6feb')
            self.status_badge.config(text='● BEKLEMEDE', bg='#21262d', fg=FG_MUTED)
            self.log('Otomatik izleme durduruldu.', 'warn')

    def watch_loop(self):
        while self.running:
            moved = self.engine.organize_existing()
            if moved:
                self.root.after(0, self.refresh_dashboard)
                self.root.after(0, lambda m=moved: self.log(f'Yeni eklenen {m} dosya duzenlendi.', 'ok'))
            self.root.after(0, lambda: self.check_old_files(False))
            time.sleep(5)


def main():
    root = tk.Tk()
    app = NeatFlowApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
