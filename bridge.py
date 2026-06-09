import serial
import json
import time
import re
import paho.mqtt.client as mqtt

# --- AYARLAR ---
SERIAL_PORT = 'COM6' 
BAUD_RATE = 115200
MQTT_BROKER = "broker.emqx.io"
TOPIC_TELEMETRY = "recyprint/test/sensor_data"
TOPIC_CONTROL = "recyprint/test/control"
TOPIC_ALERTS = "recyprint/test/alerts"

# --- OTOMATİK ÇAP KONTROL SİSTEMİ DEĞİŞKENLERİ ---
auto_mode = False
current_target_speed = 125.0  # Başlangıç motor hızı
TARGET_DIAMETER = 1.75        # Hedef filaman çapı (mm)
MIN_SPEED = 50.0              # Motorun inebileceği en düşük hız
MAX_SPEED = 250.0             # Motorun çıkabileceği en yüksek hız
KP_SPEED = 150.0              # Oransal kontrolcü kazancı (Kp)

# paho-mqtt v2.0+ ve v1.x ile tam uyumluluk için Callback API sürümünü belirliyoruz
try:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
except AttributeError:
    # Eski paho-mqtt sürümü kullanılıyorsa fallback
    client = mqtt.Client()

def on_connect(client, userdata, flags, rc, properties=None):
    """
    Bağlantı kurulduğunda çağrılır. 
    Abonelikleri burada yapmak bağlantı kopup tekrar kurulduğunda (reconnect) aboneliklerin kaybolmasını önler.
    """
    print("MQTT Broker bağlantısı başarıyla kuruldu!")
    client.subscribe(TOPIC_CONTROL)
    print(f"Abone olunan kanal: {TOPIC_CONTROL}")

def update_automatic_control(diameter):
    """
    Filaman çapına göre motor hızını otomatik ayarlayan kapalı döngü kontrolcü.
    """
    global auto_mode, current_target_speed
    if not auto_mode:
        return
    
    if diameter > 1.0:
        # Hata değeri (Mevcut çap - Hedef çap)
        error = diameter - TARGET_DIAMETER
        
        # Yeni hız hesabı: Çap büyükse motor hızlanır (error > 0), küçükse yavaşlar (error < 0)
        new_speed = current_target_speed + (error * KP_SPEED)
        new_speed = max(MIN_SPEED, min(MAX_SPEED, new_speed))
        
        # Seri portu ve cihazı yormamak için sadece tamsayı seviyesinde değişim varsa komut yolla
        if int(new_speed) != int(current_target_speed):
            old_speed = int(current_target_speed)
            current_target_speed = new_speed
            cmd = f"M{int(new_speed)}\n"
            if ser.is_open:
                ser.write(cmd.encode())
                print(f"[OTOMATİK KONTROL] Çap: {diameter:.2f}mm | Hata: {error:+.2f}mm | Yeni Hız: {int(new_speed)} (Değişim: {int(new_speed) - old_speed:+d})")
    else:
        # Çap 1.0mm altındaysa filaman henüz sensöre ulaşmamıştır. Başlangıç hızını (125) koru.
        if int(current_target_speed) != 125:
            current_target_speed = 125.0
            cmd = "M125\n"
            if ser.is_open:
                ser.write(cmd.encode())
                print("[OTOMATİK KONTROL] Filaman bekleniyor... Hız 125 olarak sabitlendi.")

def check_temperature_safety(current_temp):
    """
    Sıcaklık 200°C limitini aşarsa sistemi otomatik durduran ve alarm veren koruma fonksiyonu.
    """
    global auto_mode
    if current_temp > 200.0:
        auto_mode = False
        # ESP32'ye acil durdurma yolla (M0, T0)
        if ser.is_open:
            ser.write(b"M0\n")
            time.sleep(0.1)
            ser.write(b"T0\n")
            print(f"[ACİL DURDURMA] Sıcaklık {current_temp}°C (Limit: 200°C) aşıldı! Sistem kapatıldı.")
        
        # Arayüze (dashboard) kırmızı acil durum uyarısı gönder
        alert_payload = {
            "type": "emergency",
            "message": f"Kritik Sıcaklık Limiti Aşıldı ({current_temp:.1f}°C)! Isıtıcı ve motor acil olarak kapatıldı."
        }
        client.publish(TOPIC_ALERTS, json.dumps(alert_payload))
        return True
    return False

def on_message(client, userdata, msg):
    global auto_mode, current_target_speed
    try:
        payload = json.loads(msg.payload.decode())
        commands = []
        
        # DASHBOARD KOMUTLARINI ESP32 DİLİNE ÇEVİR
        if payload.get('type') == 'start_extrusion':
            print("[OTOMATİK SİSTEM] Üretim Başlatıldı! Hedef: 185°C | Başlangıç Hızı: 125")
            auto_mode = True
            current_target_speed = 125.0
            
            # ESP32'ye başlangıç komutlarını gönder
            commands.append("T185\n")
            commands.append("M125\n")
            
        elif payload.get('type') == 'update_targets':
            # Arayüzden sürgüleri kaldırdık ama manuel olarak MQTT'den istek gelirse koruma
            if 'target_temperature' in payload:
                commands.append(f"T{int(payload['target_temperature'])}\n")
            if 'target_speed' in payload:
                esp_speed = int(float(payload['target_speed']))
                current_target_speed = float(esp_speed)
                commands.append(f"M{esp_speed}\n")
                
        elif payload.get('type') in ['stop_extrusion', 'emergency_stop']:
            print("[OTOMATİK SİSTEM] Üretim Durduruldu! Cihazlar kapatılıyor...")
            auto_mode = False
            commands.append("M0\n")
            commands.append("T0\n")
            
        elif payload.get('type') == 'tare_gauge':
            commands.append("Z\n")

        # Komutları sırayla gönder
        for command in commands:
            if command and ser.is_open:
                ser.write(command.encode())
                print(f">>> ESP32'YE GİDEN: {command.strip()}")
                time.sleep(0.1)
            
    except Exception as e:
        print(f"Kontrol Hatası: {e}")

# Callback'leri tanımla
try:
    client.on_connect = on_connect
    client.on_message = on_message
except Exception:
    # Eski v1.x paho-mqtt imza uyumluluğu için fallback
    def on_connect_v1(client, userdata, flags, rc):
        print("MQTT Broker bağlantısı başarıyla kuruldu (v1)!")
        client.subscribe(TOPIC_CONTROL)
    client.on_connect = on_connect_v1
    client.on_message = on_message

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    client.connect(MQTT_BROKER, 1883, 60)
    client.loop_start()
    
    print(f"FİNAL SİSTEM AKTİF: {SERIAL_PORT} üzerinden iletişim kuruldu...")
    print("Sıcaklık Koruması: 200°C Üstü Acil Kapatma Aktif!")

    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line: continue
            
            # 1. DURUM: ESP32 DOĞRUDAN JSON GÖNDERİYORSA
            if line.startswith("{"):
                try:
                    payload_data = json.loads(line)
                    current_temp = float(payload_data.get('temperature', 0))
                    
                    # 200 Derece Üstü Acil Durum Kontrolü
                    is_emergency = check_temperature_safety(current_temp)
                    if is_emergency:
                        payload_data['status'] = 'Error'
                        payload_data['speed'] = 0
                        payload_data['is_extruding'] = False
                    
                    if 'is_extruding' not in payload_data:
                        payload_data['is_extruding'] = (payload_data.get('speed', 0) > 0)
                        
                    client.publish(TOPIC_TELEMETRY, json.dumps(payload_data))
                    print(f"📡 MQTT İLETİLDİ (JSON) -> Sıcaklık: {current_temp}°C")
                    
                    # Eğer acil durum yoksa otomatik çap kontrolünü çalıştır
                    if not is_emergency and 'diameter' in payload_data:
                        update_automatic_control(float(payload_data['diameter']))
                except Exception as e:
                    print(f"JSON Çevirme Hatası: {e}")
            
            # 2. DURUM: ESP32 METİN FORMATINDA VERİ GÖNDERİYORSA (Örn: TEMP: 30.5 / 0.0 C...)
            elif line.upper().startswith("TEMP:"):
                try:
                    # Sıcaklık Değerlerini Al (TEMP: 30.5 / 0.0 C)
                    temp_match = re.search(r'(?:TEMP|Temp):\s*\[?([\d\.]+)\s*/\s*([\d\.]+)', line, re.IGNORECASE)
                    
                    # Motor Hızını Al (SPD: 0% veya Motor Spd: 150)
                    speed_match = re.search(r'(?:SPD|Motor Spd):\s*(\-?\d+)\s*%?', line, re.IGNORECASE)
                    
                    # Çap Değerini Al (DIA: 0.00 mm)
                    dia_match = re.search(r'(?:DIA|Diameter):\s*([\d\.]+)', line, re.IGNORECASE)
                    
                    if temp_match and speed_match:
                        current_temp = float(temp_match.group(1))
                        target_temp = float(temp_match.group(2))
                        
                        raw_speed_str = speed_match.group(1)
                        motor_speed = int(raw_speed_str)
                        
                        # Eğer hız yüzdelik verilmişse (%50 gibi), 0-255 PWM aralığına ölçekle
                        is_percent = '%' in speed_match.group(0) or 'SPD:' in line.upper()
                        if is_percent and 0 <= motor_speed <= 100:
                            motor_speed = int(motor_speed * 2.55)
                        
                        diameter = 1.75
                        if dia_match:
                            diameter = float(dia_match.group(1))
                            
                        # 200 Derece Üstü Acil Durum Kontrolü
                        is_emergency = check_temperature_safety(current_temp)
                        if is_emergency:
                            status = "Error"
                            motor_speed = 0
                        else:
                            # Durumu (Status) tahmin et
                            if target_temp == 0 and motor_speed == 0:
                                status = "Idle"
                            elif current_temp < target_temp - 5.0:
                                status = "Heating"
                            elif motor_speed > 0:
                                status = "Extruding"
                            else:
                                status = "Ready"
                            
                        # Dashboard için JSON formatını oluştur
                        fake_json = {
                            "temperature": current_temp,
                            "speed": motor_speed,
                            "diameter": diameter,
                            "status": status,
                            "is_extruding": (motor_speed > 0)
                        }
                        
                        # Dashboard'a ve veritabanına loglanması için MQTT'ye fırlat
                        client.publish(TOPIC_TELEMETRY, json.dumps(fake_json))
                        print(f"📡 MQTT İLETİLDİ -> Sıcaklık: {current_temp}°C | Durum: {status} | Çap: {diameter}mm")
                        
                        # Acil durum yoksa otomatik çap kontrolünü çalıştır
                        if not is_emergency:
                            update_automatic_control(diameter)
                    else:
                        print(f"Ayrıştırma Hatası (Regex eşleşmedi): {line}")
                except Exception as e:
                    print(f"Metin Çevirme Hatası: {e}")
            
            # 3. DURUM: ESP32 BAŞKA BİR BİLGİ / LOG BASIYORSA
            else:
                print(f"ESP32 INFO: {line}")

except Exception as e:
    print(f"Bağlantı Hatası: {e}")
finally:
    client.loop_stop()
