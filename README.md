# RecyPrint (Smart Bottle Waste-to-Filament System) 🌿⚙️

Bu repo, plastik pet şişeleri geri dönüştürerek 3 boyutlu yazıcılar için kullanılabilir filament üreten **RecyPrint** bitirme (Capstone) projesinin **Yazılım & IoT (Internet of Things)** arayüz kodlarını barındırmaktadır.

Proje, temelde **Mekatronik** (donanımsal parçalama, eritme, çekme, soğutma işlemleri) ve **Yazılım** (bu süreçlerin anlık izlenmesi, loglanması ve uzaktan kontrol edilmesi) olmak üzere iki ana kola ayrılmış, disiplinlerarası bir makine otomasyon sistemidir.

---

## 🎯 Projenin Temel İsterleri
Proje raporunda sistemden beklenen yazılımsal gereksinimler şunlardır:
- **Haberleşme:** Sensör ve kontrolcünün (ESP32) bir bilgisayar/sunucu ile haberleşmesi.
- **Canlı Sensör Takibi:** Sıcaklık (Temperature), Motor Hızı (Speed) ve Çap (Filament Diameter) değerlerinin dashboard üzerinden okunması.
- **Otomatik Güvenlik Doğrulaması:** 180°C limitini veya belirlenen kritik sıcaklık eşiklerini geçince acil durum (Emergency Stop) başlatılması.
- **Uzaktan Kontrol (Remote Control):** Hedef sıcaklığın, motor hızının ayarlanabilmesi ve motorun başlatılıp (Start) durdurulabilmesi (Stop).
- **Loglama:** Geçmiş verilerin sonradan incelenebilmesi için kalıcı bir veritabanında (SQLite) tutulması ve listelenmesi.

---

## 🚀 Yazılım Ekibi Olarak Biz Ne Yaptık?
Mekatronik prototipi henüz hazır olmadığı halde yazılım tabanı **simülatör mekanizması ile %100 oranında tamamlanmış, Endüstri 4.0** normlarında çalışır hale getirilmiştir. 

**Öne Çıkan Geliştirmeler:**
1. **Modern Haberleşme (WebSocket):** Dokümandaki basit REST API yerine gecikmesiz, anında tepki veren gelişmiş **Flask-SocketIO** mimarisi kullanıldı.
2. **Premium Dashboard:** Sıradan bir panel yerine "Glassmorphism", Dark-Mode ve "Neon" aksan tasarımlarına sahip profesyonel ve duyarlı bir arayüz HTML/CSS dosyaları kodlandı.
3. **Simülatör & İş Zekası (İnterlok Mantığı):** Arka planda donanım varmış gibi davranan bir Python simülatörü(`esp32_simulator_thread`) yazıldı. *Uyarı*: Bu simülatör sayesinde hedef sıcaklığa gelmeden arayüz motorun başlatılmasına izin vermez, aşırı çap sapması(±0.05mm) algılarsa motor hızı ile oto-düzeltme sağlar ve kritik seviyede "Kırmızı Alarm" (Emergency Stop) vererek devreyi kapatır.
4. **Log & Excel Export Sistemi:** SQLite sayesinde anlık olarak yazılan grafik (Chart.js) noktaları, `/history` rotasında tablo ile listelenmiş ve saniyeler içerisinde **CSV(Excel)** formatında indirilerek dışarı aktarılabilir hale getirilmiştir.

---

## 🔧 Mekatronik Ekibi İçin Entegrasyon Rehberi: "Gerçek Cihaza Geçiş"
Donanım (Isıtıcı fişek, motor, sensörler) ve ESP32 mikrokontrolcü kablolamaları bittikten sonra yazılım ile mekatroniğin birleştirilmesi için şu **3 adım** uygulanmalıdır:

### 1- Simülatörü Devre Dışı Bırakmak
Kodda cihaz yokken anlık veri fırlatan fonkisyonu durdurmalısınız. 
`app.py` dosyasındaki dosyasının en altına gidin ve aşağıdaki kodu bulun:
```python
# socketio.start_background_task(esp32_simulator_thread)  <-- BAŞINA DİYEZ KOYARAK KAPATIN
```

### 2- ESP32'den Veri Göndermek
ESP32 (C++/ArduinoIDE) kodunuz içinden Socket.IO kütüphanesini kullanarak `sensor_update` olayına sensör ölçümlerini atmalısınız:
```json
{
  "temperature": 210.5,
  "speed": 60.0,
  "diameter": 1.76,
  "target_temperature": 215.0,
  "target_speed": 60.0,
  "is_extruding": true,
  "status": "Extruding",
  "timestamp": "14:30:22"
}
```
*(Alternatif olarak Socket istemiyorsanız `app.py`'da basit bir POST `/update` route'u da mevcuttur).*

### 3- Arayüzden Gelen Komutları Almak
Kullanıcı web sayfasından slider'ları çektiğinde veya **Start/Stop** bastığında Flask sunucusu size geri komut yollayacaktır. ESP32 tarafında bunu dinleyip Motor veya Relay'e güç verin/kapatın:
```json
{
  "type": "update_targets",
  "target_temperature": 214,
  "target_speed": 60
}
```

---

## ⚙️ Kurulum ve Çalıştırma

Projeyi lokal bilgisayarınızda çalıştırmak için:

1. Python yüklü olmalıdır. İlgili kütüphaneleri kurun:
   ```bash
   pip install -r requirements.txt
   ```
2. Ana Flask sunucu dosyasını başlatın:
   ```bash
   python app.py
   ```
3. Herhangi bir internet tarayıcısından (Chrome, Safari vs.) adrese gidin:
   **http://localhost:5000**
