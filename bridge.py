import serial, json, time, re
import paho.mqtt.client as mqtt

# --- AYARLAR ---
SERIAL_PORT = 'COM6' 
BAUD_RATE = 115200
MQTT_BROKER = "broker.emqx.io"
TOPIC_TELEMETRY = "recyprint/test/sensor_data"
TOPIC_CONTROL = "recyprint/test/control"

client = mqtt.Client(protocol=mqtt.MQTTv311)

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        command = ""
        
        # DASHBOARD KOMUTLARINI ESP32 DİLİNE ÇEVİR (T, M, 0)
        if payload.get('type') == 'start_extrusion':
            speed = payload.get('target_speed', 150)
            command = f"M{speed}\n" 
        elif payload.get('type') == 'update_targets':
            if 'target_temperature' in payload:
                command = f"T{int(payload['target_temperature'])}\n"
            if 'target_speed' in payload:
                esp_speed = int(float(payload['target_speed']))
                command = f"M{esp_speed}\n"
        elif payload.get('type') == 'stop_extrusion' or payload.get('type') == 'emergency_stop':
            command = "0\n"

        if command and ser.is_open:
            ser.write(command.encode())
            print(f">>> ESP32'YE GİDEN: {command.strip()}")
            
    except Exception as e:
        print(f"Kontrol Hatası: {e}")

client.on_message = on_message

try:
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    client.connect(MQTT_BROKER, 1883, 60)
    client.subscribe(TOPIC_CONTROL)
    client.loop_start()
    print(f"FİNAL SİSTEM AKTİF: {SERIAL_PORT} üzerinden iletişim kuruldu...")
    print("Mekatronik ekibinin kodu ne olursa olsun otomatik çevrilip Dashboard'a aktarılacak!")

    while True:
        if ser.in_waiting > 0:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
            if not line: continue
            
            # 1. DURUM: ESP32 DOĞRUDAN JSON GÖNDERİYORSA
            if line.startswith("{"):
                try:
                    payload_data = json.loads(line)
                    # Eğer Dashboard'un beklediği 'is_extruding' eksikse biz ekleyelim
                    if 'is_extruding' not in payload_data:
                        payload_data['is_extruding'] = (payload_data.get('speed', 0) > 0)
                    client.publish(TOPIC_TELEMETRY, json.dumps(payload_data))
                except Exception as e:
                    print(f"JSON Çevirme Hatası: {e}")
            
            # 2. DURUM: ESP32 ESKİ V1.2 (DÜZ METİN) KODUNU GÖNDERİYORSA
            elif line.startswith("Temp:"):
                # Gelen Örnek: Temp: [25.0 / 0.0°C] | Heater Pwr: 0% | Motor Spd: 150
                try:
                    # Regex ile sayıları ayıklıyoruz (Cımbızla çekiyoruz)
                    match = re.search(r'Temp:\s*\[([\d\.]+)\s*/\s*([\d\.]+)°C\]\s*\|\s*Heater Pwr:\s*(\d+)%\s*\|\s*Motor Spd:\s*(\-?\d+)', line)
                    if match:
                        current_temp = float(match.group(1))
                        target_temp = float(match.group(2))
                        motor_speed = int(match.group(4))
                        
                        # Durumu (Status) o anki sıcaklık ve hıza bakarak biz tahmin ediyoruz
                        if target_temp == 0 and motor_speed == 0:
                            status = "Idle"
                        elif current_temp < target_temp - 5.0:
                            status = "Heating"
                        elif motor_speed > 0:
                            status = "Extruding"
                        else:
                            status = "Ready"
                            
                        # Python tarafında Dashboard'un tam beklediği JSON'ı biz oluşturuyoruz!
                        fake_json = {
                            "temperature": current_temp,
                            "speed": motor_speed,
                            "diameter": 1.75, # Eski Arduino kodunda çap ölçümü olmadığı için sabit ideal değer
                            "status": status,
                            "is_extruding": (motor_speed > 0)
                        }
                        
                        # Oluşturduğumuz bu muazzam JSON'ı Dashboard'a fırlatıyoruz
                        client.publish(TOPIC_TELEMETRY, json.dumps(fake_json))
                except Exception as e:
                    print(f"Metin Çevirme Hatası: {e}")
            
            # 3. DURUM: ESP32 BAŞKA BİR INFO / LOG BASIYORSA
            else:
                # Sadece terminale bilgi olarak bas, MQTT'yi yorma
                print(f"ESP32 INFO: {line}")

except Exception as e:
    print(f"Bağlantı Hatası: {e}")
finally:
    client.loop_stop()
