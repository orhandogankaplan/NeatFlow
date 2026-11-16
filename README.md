# NeatFlow

Zamanla karmaşaya dönen **İndirilenler (Downloads)** klasörünü arka planda sessizce düzenleyen, kopya ve eski kurulum dosyalarını Çöp Kutusuna taşıyarak kullanıcıya masaüstü bildirimi gönderen açık kaynaklı uygulama.

## Öne Çıkan Özellikler

* **Otomatik Kategorilendirme:** PDF, görsel, arşiv, kurulum ve doküman dosyalarını uzantılarına göre ilgili alt klasörlere taşır.
* **Akıllı Temizlik:** Belirlenen süreden (varsayılan 30 gün) eski kurulum dosyalarını kalıcı olarak silmek yerine güvenli şekilde Çöp Kutusuna gönderir.
* **Anlık Masaüstü Bildirimleri:** Düzenlenen veya temizlenen dosyalar hakkında sessiz bildirimler sunar.
* **Özelleştirilebilir Yapı:** `config.yaml` dosyası üzerinden klasör kuralları ve süre sınırları kolayca düzenlenebilir.

## Kurulum ve Kullanım

### 1. Kaynak Koddan Kurulum (Python 3.8+)
```bash
git clone [https://github.com/orhandogankaplan/NeatFlow.git](https://github.com/orhandogankaplan/NeatFlow.git)
cd NeatFlow
python -m pip install -r requirements.txt
python -m pip install -e .
```

Uygulamayı başlatmak için:
```bash
python -m neatflow
```

### 2. Hazır Çalıştırılabilir Dosya (Releases)
Python kurulumuyla uğraşmadan doğrudan kullanmak için sağ taraftaki **Releases** bölümünden işletim sisteminize uygun derlenmiş dosyayı indirip çalıştırabilirsiniz.
