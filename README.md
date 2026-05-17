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

**Seçenek 1 (Önerilen - JSON Format):**
ESP32 kodunuz sensör verilerini şu formatta yazdırmalıdır:
```json
{"temperature": 25.0, "speed": 150, "diameter": 1.75, "status": "Extruding", "is_extruding": true}
```

**Seçenek 2 (Eski V1.2 Metin Format):**
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

---
<br><br>

# RecyPrint (Smart Bottle Waste-to-Filament System) 🌿⚙️ [English Version]

This repository contains the **Software & IoT (Internet of Things)** interface codes for the **RecyPrint** capstone project, which recycles plastic PET bottles to produce usable filament for 3D printers.

The project is an interdisciplinary machine automation system, fundamentally divided into two main branches: **Mechatronics** (hardware shredding, melting, pulling, and cooling processes) and **Software** (real-time monitoring, logging, and remote control of these processes via the cloud).

---

## 🎯 Current Status & Software Achievements
As the software team, we have accomplished all project objectives and successfully completed the hardware integration:
- **Cloud Database:** Transitioned from a local SQLite setup to a highly secure and professional **AWS Neon.tech (PostgreSQL)** database.
- **Modern Communication (MQTT & WebSocket):** Replaced basic REST APIs with a zero-latency, highly responsive **Native MQTT (broker.emqx.io)** and WebSocket architecture.
- **Smart Hardware Bridge (bridge.py):** Developed a smart Python bridge that automatically detects incoming data from the ESP32 (whether in JSON or plain text), parses it using Regex, and pushes it to the cloud.
- **Premium Dashboard:** Designed a professional interface with "Glassmorphism," Dark-Mode, and "Neon" accents, replacing a standard panel. Heater PWM and Motor speed ranges have been calibrated perfectly for the hardware (0-255).
- **Logging & Excel Export System:** Real-time chart data (Chart.js) is instantly tabulated in the `/history` route and can be exported as a **CSV (Excel)** file in seconds.

---

## 🏗️ System Architecture

Data flow in the project is designed according to Industry 4.0 IoT standards:
1. **Hardware (ESP32):** Controls the heater (via PID) and the motor (L298N). Sends sensor data to the PC via serial port (USB).
2. **Bridge Software (bridge.py):** Runs on the PC. Reads data from the ESP32, formats it, and publishes it to the **MQTT Cloud Broker**.
3. **Web Interface (Dashboard):** Connects to the cloud broker via WebSockets to fetch real-time data, draws charts, and transmits user commands (speed/temperature) back to the hardware via the cloud.
4. **Backend (app.py):** Serves the smart interface and periodically fetches data from MQTT to log into the Neon PostgreSQL database.

---

## 🔧 Hardware Integration Guide (For the Mechatronics Team)

For hardware integration, the mechatronics team simply needs to connect the ESP32 to the PC via USB and run the **`bridge.py`** script on the computer.

### What should the ESP32 Serial Output look like?
Our `bridge.py` software is highly intelligent and automatically detects two different scenarios:

**Option 1 (Recommended - JSON Format):**
Your ESP32 code should print the sensor data in this format:
```json
{"temperature": 25.0, "speed": 150, "diameter": 1.75, "status": "Extruding", "is_extruding": true}
```

**Option 2 (Legacy V1.2 Text Format):**
If the ESP32 is currently running the older code and printing plain text like the example below, `bridge.py` will detect it with Regex and automatically convert it to JSON. No code change is necessary!
```text
Temp: [25.0 / 0.0°C] | Heater Pwr: 0% | Motor Spd: 150
```

### Commands sent from the Dashboard to the ESP32
When you click buttons or drag sliders on the Dashboard, `bridge.py` sends the following direct machine commands to the ESP32:
- `T150` -> Set target temperature to 150°C.
- `M200` -> Set motor speed to 200 (PWM: 0-255).
- `0` -> Emergency Stop (E-STOP). Shuts down the entire system.

---

## ⚙️ Setup and Installation

To run the project on your local machine:

1. Install the required Python libraries:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the main Flask server (for database logging and UI hosting):
   ```bash
   python app.py
   ```
3. Connect the ESP32 to the computer via USB and launch the bridge script:
   ```bash
   python bridge.py
   ```
4. Access the interface from any web browser by navigating to:
   **http://localhost:5000**
