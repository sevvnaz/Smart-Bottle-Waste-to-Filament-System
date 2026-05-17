# RecyPrint (Smart Bottle Waste-to-Filament System) 🌿⚙️

Bu depo, plastik pet şişeleri geri dönüştürerek 3 boyutlu yazıcılar için kullanılabilir filament üreten **RecyPrint** bitirme (Capstone) projesinin **Yazılım & IoT (Internet of Things)** arayüz kodlarını barındırmaktadır.

Proje, temelde **Mekatronik** (donanımsal parçalama, eritme, çekme, soğutma işlemleri) ve **Yazılım** (bu süreçlerin anlık izlenmesi, loglanması ve bulut üzerinden uzaktan kontrol edilmesi) olmak üzere iki ana kola ayrılmış, disiplinlerarası bir makine otomasyon sistemidir.

---

## 🎯 Projenin Ulaştığı Son Nokta (Current Status)
Yazılım ekibi olarak projenin tüm hedeflerini tamamladık ve donanım entegrasyonunu başarıyla gerçekleştirdik:
- **Bulut Veritabanı (Cloud DB):** Lokal SQLite yerine çok daha güvenli ve profesyonel olan **AWS Neon.tech (PostgreSQL)** veritabanına geçiş yapıldı.
- **Modern Haberleşme (MQTT & WebSocket):** Basit REST API yerine gecikmesiz, anında tepki veren **Native MQTT (broker.emqx.io)** ve WebSocket mimarisi kullanıldı.
- **Akıllı Donanım Köprüsü (bridge.py):** ESP32'den gelen verileri (JSON veya düz metin fark etmeksizin) algılayıp, Regex ile ayrıştırarak buluta aktaran akıllı bir Python köprüsü yazıldı.
- **Premium Dashboard:** Sıradan bir panel yerine "Glassmorphism", Dark-Mode ve "Neon" aksan tasarımlarına sahip profesyonel bir arayüz kodlandı. Isıtıcı PWM değerleri ve Motor hızı donanıma uygun olarak (0-255) ayarlandı.
- **Log & Excel Export Sistemi:** Anlık olarak yazılan grafik (Chart.js) noktaları, `/history` rotasında tablo ile listelenmiş ve saniyeler içerisinde **CSV (Excel)** formatında indirilerek dışarı aktarılabilir hale getirilmiştir.

---

## 🏗️ Sistem Mimarisi (Architecture)

Projedeki veri akışı Endüstri 4.0 IoT standartlarına uygun olarak tasarlanmıştır:
1. **Donanım (ESP32):** Isıtıcıyı (PID ile) ve motoru (L298N) kontrol eder. Sensör verilerini seri porttan (USB) bilgisayara gönderir.
2. **Köprü Yazılımı (bridge.py):** Bilgisayarda çalışır. ESP32'den gelen verileri okur, formatlar ve **MQTT Bulut Sunucusuna** fırlatır.
3. **Web Arayüzü (Dashboard):** Bulut sunucusuna WebSocket ile bağlanarak verileri canlı (real-time) çeker, grafiğe döker ve kullanıcının girdiği hız/sıcaklık komutlarını bulut üzerinden donanıma iletir.
4. **Backend (app.py):** Akıllı arayüzü sunar ve periyodik olarak MQTT'den veri çekip Neon PostgreSQL veritabanına loglar.

---

## 🔧 Mekatronik Ekibi İçin Entegrasyon Rehberi

Donanım entegrasyonu için mekatronik ekibinin yapması gereken tek şey, ESP32'yi bilgisayara bağlayıp bilgisayarda **`bridge.py`** dosyasını çalıştırmaktır.

### ESP32 Kod Çıktısı (Serial Print) Ne Olmalı?
`bridge.py` yazılımımız oldukça akıllıdır ve iki farklı durumu da otomatik algılar:

**Seçenek 1 (Önerilen - JSON Formatı):**
ESP32 kodunuz sensör verilerini şu formatta yazdırmalıdır:
```json
{"temperature": 25.0, "speed": 150, "diameter": 1.75, "status": "Extruding", "is_extruding": true}
```

**Seçenek 2 (Eski V1.2 Metin Formatı):**
Eğer ESP32 şu an eski kodu çalıştırıyorsa ve ekrana aşağıdaki gibi düz metin basıyorsa, `bridge.py` bunu Regex ile algılayıp kendisi JSON'a çevirecektir. Kod değişikliğine gerek yoktur!
```text
Temp: [25.0 / 0.0°C] | Heater Pwr: 0% | Motor Spd: 150
```

### Dashboard'dan ESP32'ye Giden Komutlar
Siz Dashboard üzerinden butonlara bastığınızda veya kaydırıcıyı çektiğinizde, `bridge.py` ESP32'ye doğrudan makine dilinde şu komutları yollar:
- `T150` -> Hedef sıcaklığı 150°C yap.
- `M200` -> Motor hızını 200 (PWM: 0-255) yap.
- `0` -> Acil Durdurma (E-STOP). Tüm sistemi kapat.

---

## ⚙️ Kurulum ve Çalıştırma

Projeyi bilgisayarınızda çalıştırmak için:

1. Gerekli Python kütüphanelerini kurun:
   ```bash
   pip install -r requirements.txt
   ```
2. Ana Flask sunucu dosyasını başlatın (Veritabanı loglama ve arayüz sunumu için):
   ```bash
   python app.py
   ```
3. ESP32'yi USB ile bilgisayara bağlayın ve köprü yazılımını başlatın:
   ```bash
   python bridge.py
   ```
4. Herhangi bir internet tarayıcısından adres çubuğuna giderek arayüze ulaşın:
   **http://localhost:5000**
