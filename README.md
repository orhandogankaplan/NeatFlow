# TidyDownloads

Zamanla karmaşaya dönen **İndirilenler (`Downloads`)** klasörünü arka planda sessizce düzenleyen, kopya ve eski kurulum dosyalarını **Çöp Kutusuna** taşıyarak kullanıcıya **masaüstü bildirimi** gönderen açık kaynaklı uygulama.

## Öne Çıkan Özellikler

* **Otomatik Kategorilendirme:** PDF, görsel, arşiv ve kurulum dosyalarını (`watchdog` ile) anlık olarak ilgili alt klasörlere ayırır.
* **Bildirimli Eski Dosya Temizliği:** Belirlediğin günden (varsayılan 30 gün) eski kurulum/arşiv dosyalarını temizler ve silinen dosyaları masaüstü bildirimiyle haber verir.
* **Kopya Dosya Tespiti:** SHA-256 hash kontrolü ile birebir aynı olan mükerrer indirmeleri tespit edip temizler ve bildirim gönderir.
* **Güvenli Silme:** Varsayılan olarak dosyaları kalıcı silmez, işletim sisteminin Çöp Kutusuna (`send2trash`) taşır.
* **Tek Tıkla Uygulama Olarak İndirme:** GitHub Releases üzerinden `.exe` (Windows) veya Linux/macOS çalıştırılabilir dosyası olarak doğrudan indirilebilir.

## Kurulum ve Kullanım

### Seçenek 1: Hazır Uygulama Olarak (Geliştirici Olmayanlar İçin)
1. GitHub'daki **Releases** sayfasından işletim sistemine uygun `TidyDownloads` dosyasını indir.
2. İsteğe bağlı olarak yanına `config.yaml` dosyasını koyup kurallarını özelleştir.
3. Uygulamayı çalıştır; arka planda klasörünü izlemeye başlar.

### Seçenek 2: Python Paketi Olarak Kurulum
```bash
git clone https://github.com/KULLANICI_ADIN/tidydownloads.git
cd tidydownloads
pip install -r requirements.txt
pip install -e .
```

Uygulamayı başlatmak için:
```bash
# Arka planda sürekli izleme
tidydownloads

# Sadece bir kez düzenle ve temizle
tidydownloads --once
```

### Kendi Çalıştırılabilir Dosyanı (.exe / binary) Derleme
```bash
pip install pyinstaller
python build_app.py
```

## Testleri Çalıştırma
```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
