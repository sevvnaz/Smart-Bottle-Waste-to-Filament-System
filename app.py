import time
import threading
import sqlite3
import random
import csv
import json
from io import StringIO
from flask import Flask, render_template, jsonify, Response
import paho.mqtt.client as mqtt

app = Flask(__name__)
DB_NAME = 'recyprint.db'

# === MQTT CONFIGURATION ===
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPIC_TELEMETRY = "recyprint/test/sensor_data" # Unique public topics to avoid collision
TOPIC_CONTROL = "recyprint/test/control"
TOPIC_ALERTS = "recyprint/test/alerts"

mqtt_client = mqtt.Client(client_id="recyprint_backend_logger", protocol=mqtt.MQTTv311)

# System State (Mocked ESP32 values)
system_state = {
    'temperature': 25.0,
    'speed': 0.0,
    'diameter': 0.0,
    'target_temperature': 214.0,
    'target_speed': 60.0,
    'is_extruding': False,
    'status': 'Standby'
}

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temperature REAL,
            speed REAL,
            diameter REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_sensor_data(temp, speed, diameter):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('INSERT INTO sensor_data (temperature, speed, diameter) VALUES (?, ?, ?)', (temp, speed, diameter))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")


# === MQTT CALLBACKS (Backend acting as a listener & commander) ===
def on_connect(client, userdata, flags, rc):
    print("Connected to Global MQTT Broker successfully!")
    client.subscribe(TOPIC_CONTROL)
    client.subscribe(TOPIC_TELEMETRY) # We subscribe to sensor topic to LOG data to SQLite

def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
        
        # 1. Received Control Array from Dashboard
        if msg.topic == TOPIC_CONTROL:
            cmd = payload.get("type")
            if cmd == 'update_targets':
                if 'target_temperature' in payload:
                    system_state['target_temperature'] = float(payload['target_temperature'])
                    system_state['status'] = 'Standby' if system_state['target_temperature'] == 0 else 'Heating'
                if 'target_speed' in payload:
                    system_state['target_speed'] = float(payload['target_speed'])
            elif cmd == 'start_extrusion':
                if system_state['temperature'] < (system_state['target_temperature'] - 5.0):
                    client.publish(TOPIC_ALERTS, json.dumps({'type': 'warning', 'message': 'Hedef sıcaklığa ulaşmadan motor başlatılamaz!'}))
                else:
                    system_state['is_extruding'] = True
            elif cmd == 'stop_extrusion':
                system_state['is_extruding'] = False

        # 2. Received Real Telemetry Data (Log to Database randomly to save space)
        elif msg.topic == TOPIC_TELEMETRY:
            if random.random() < 0.2: # Log 1 in 5 messages
                log_sensor_data(payload.get('temperature', 0), payload.get('speed', 0), payload.get('diameter', 0))

    except Exception as e:
        print(f"MQTT Parsing Error: {e}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


# === LOCAL ESP32 SIMULATOR THREAD ===
def esp32_simulator_thread():
    """Background thread acting strictly as an ESP32 sending MQTT payloads."""
    CRITICAL_TEMP = 180.0  # Safe threshold for automated shutdown as per PDF documentation
    time.sleep(2) # Give broker time to connect
    
    while True:
        # Emergency Stop Logic
        if system_state['temperature'] >= CRITICAL_TEMP and system_state['is_extruding']:
            system_state['is_extruding'] = False
            system_state['status'] = 'Error'
            system_state['target_temperature'] = 0.0
            system_state['target_speed'] = 0.0
            mqtt_client.publish(TOPIC_ALERTS, json.dumps({
                'type': 'emergency',
                'message': f"Kritik Sıcaklık ({system_state['temperature']:.1f}°C)! Heater kapatıldı, sistem güvenli moda alındı."
            }))
        
        # Determine Process Mode
        temp_error = abs(system_state['temperature'] - system_state['target_temperature'])
        if system_state['status'] != 'Error':
            if not system_state['is_extruding']:
                if system_state['target_temperature'] > 30.0 and temp_error > 5.0:
                    system_state['status'] = 'Heating'
                elif system_state['target_temperature'] > 30.0 and temp_error <= 5.0:
                    system_state['status'] = 'Ready'
                else:
                    system_state['status'] = 'Standby'
            else:
                system_state['status'] = 'Extruding'
                if temp_error > 10.0:
                    mqtt_client.publish(TOPIC_ALERTS, json.dumps({'type': 'warning', 'message': "Sıcaklık hedef değerden çok saptı! Extrusion kalitesi etkilenebilir."}))

        # Heat Physics Simulation
        if system_state['is_extruding'] or system_state['status'] == 'Heating':
            diff_temp = system_state['target_temperature'] - system_state['temperature']
            system_state['temperature'] += diff_temp * 0.1 + random.uniform(-0.5, 0.5)

        # Output / Motor Physics Simulation
        if system_state['is_extruding']:
            diff_speed = system_state['target_speed'] - system_state['speed']
            system_state['speed'] += diff_speed * 0.2 + random.uniform(-1.0, 1.0)
            system_state['diameter'] = 1.75 + random.uniform(-0.04, 0.04)
            
            # Auto-correct tolerances (PID Simulation)
            if abs(system_state['diameter'] - 1.75) > 0.05:
                mqtt_client.publish(TOPIC_ALERTS, json.dumps({'type': 'warning', 'message': f"Çap tolerans dışı: {system_state['diameter']:.2f}mm. Motor hızı düzeltiliyor..."}))
                if system_state['diameter'] > 1.75: system_state['target_speed'] += 2.0
                else: system_state['target_speed'] -= 2.0
        else:
            if system_state['status'] != 'Heating' and system_state['temperature'] > 25.0:
                system_state['temperature'] -= 0.5 + random.uniform(0, 0.2)
            system_state['speed'] *= 0.5
            system_state['diameter'] = 0.0

        # MOCK ESP32 Publishes to MQTT
        telemetry_payload = {
            'temperature': round(system_state['temperature'], 2),
            'speed': round(system_state['speed'], 1),
            'diameter': round(system_state['diameter'], 3),
            'target_temperature': system_state['target_temperature'],
            'target_speed': system_state['target_speed'],
            'is_extruding': system_state['is_extruding'],
            'status': system_state['status'],
            'timestamp': time.strftime('%H:%M:%S')
        }
        mqtt_client.publish(TOPIC_TELEMETRY, json.dumps(telemetry_payload))
        
        time.sleep(1.0) # Clock tick

# === FLASK ROUTES (Frontend Serves & History APIs) ===
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history_page():
    return render_template('history.html')

@app.route('/api/logs')
def get_logs():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT temperature, speed, diameter, timestamp FROM sensor_data ORDER BY id DESC LIMIT 100')
        rows = cursor.fetchall()
        conn.close()
        logs = [{'temperature': r[0], 'speed': r[1], 'diameter': r[2], 'timestamp': r[3]} for r in rows]
        return jsonify(logs)
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route('/export/csv')
def export_csv():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute('SELECT id, temperature, speed, diameter, timestamp FROM sensor_data ORDER BY id ASC')
        rows = cursor.fetchall()
        conn.close()

        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['ID', 'Temperature (C)', 'Motor Speed (%)', 'Filament Diameter (mm)', 'Timestamp'])
        cw.writerows(rows)
        output = si.getvalue()
        si.close()
        
        return Response(output, mimetype="text/csv", headers={"Content-disposition": "attachment; filename=recyprint_sensor_logs.csv"})
    except Exception as e:
        return f"Export failed: {str(e)}", 500

if __name__ == '__main__':
    init_db()
    
    # Connect and loop MQTT in the background threading natively
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    
    # Start the simulator thread simulating ESP32
    threading.Thread(target=esp32_simulator_thread, daemon=True).start()
    
    print("Starting RecyPrint MQTT Integration Server on HTTP port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
