import time
import threading
import random
import csv
import json
from io import StringIO

from flask import Flask, render_template, jsonify, Response
import paho.mqtt.client as mqtt
import psycopg2

app = Flask(__name__)

DB_CONFIG = {
    "host": "ep-weathered-feather-amar8dcw-pooler.c-5.us-east-1.aws.neon.tech",
    "port": 5432,
    "database": "neondb",
    "user": "neondb_owner",
    "password": "npg_yjHJ8UOgCu0t",
    "sslmode": "require"
}


def get_db_connection():
    return psycopg2.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        database=DB_CONFIG["database"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        sslmode=DB_CONFIG["sslmode"]
    )


# === MQTT CONFIGURATION ===
MQTT_BROKER = "broker.emqx.io"
MQTT_PORT = 1883
TOPIC_TELEMETRY = "recyprint/test/sensor_data"
TOPIC_CONTROL = "recyprint/test/control"
TOPIC_ALERTS = "recyprint/test/alerts"

mqtt_client = mqtt.Client(client_id="recyprint_backend_logger", protocol=mqtt.MQTTv311)

# System State (Mocked ESP32 values)
system_state = {
    'temperature': 25.0,
    'speed': 0.0,
    'diameter': 0.0,
    'target_temperature': 150.0,
    'target_speed': 150.0,
    'is_extruding': False,
    'status': 'Standby'
}


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id SERIAL PRIMARY KEY,
            temperature REAL,
            speed REAL,
            diameter REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()


def log_sensor_data(temp, speed, diameter):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO sensor_data (temperature, speed, diameter) VALUES (%s, %s, %s)',
            (temp, speed, diameter)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")


# === MQTT CALLBACKS ===
def on_connect(client, userdata, flags, rc):
    print("Connected to Global MQTT Broker successfully!")
    client.subscribe(TOPIC_CONTROL)
    client.subscribe(TOPIC_TELEMETRY)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode('utf-8'))

        if msg.topic == TOPIC_CONTROL:
            cmd = payload.get("type")
            if cmd == 'update_targets':
                if 'target_temperature' in payload:
                    system_state['target_temperature'] = float(payload['target_temperature'])
                    system_state['status'] = 'Standby' if system_state['target_temperature'] == 0 else 'Heating'
                if 'target_speed' in payload:
                    system_state['target_speed'] = float(payload['target_speed'])
            elif cmd == 'start_extrusion':
                system_state['is_extruding'] = True
                client.publish(TOPIC_ALERTS, json.dumps({
                    'type': 'info',
                    'message': 'Üretim başlatıldı (Güvenlik kilidi devre dışı).'
                }))
            elif cmd == 'stop_extrusion':
                system_state['is_extruding'] = False

        elif msg.topic == TOPIC_TELEMETRY:
            if random.random() < 0.2:  # Log 1 in 5 messages
                log_sensor_data(
                    payload.get('temperature', 0),
                    payload.get('speed', 0),
                    payload.get('diameter', 0)
                )

    except Exception as e:
        print(f"MQTT Parsing Error: {e}")


mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message


# === LOCAL ESP32 SIMULATOR THREAD ===
def esp32_simulator_thread():
    CRITICAL_TEMP = 180.0
    time.sleep(2)

    while True:
        if system_state['temperature'] >= CRITICAL_TEMP and system_state['is_extruding']:
            system_state['is_extruding'] = False
            system_state['status'] = 'Error'
            system_state['target_temperature'] = 0.0
            system_state['target_speed'] = 0.0
            mqtt_client.publish(TOPIC_ALERTS, json.dumps({
                'type': 'emergency',
                'message': f"Kritik Sıcaklık ({system_state['temperature']:.1f}°C)! Heater kapatıldı, sistem güvenli moda alındı."
            }))

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
                    mqtt_client.publish(TOPIC_ALERTS, json.dumps({
                        'type': 'warning',
                        'message': "Sıcaklık hedef değerden çok saptı! Extrusion kalitesi etkilenebilir."
                    }))

        if system_state['is_extruding'] or system_state['status'] == 'Heating':
            diff_temp = system_state['target_temperature'] - system_state['temperature']
            system_state['temperature'] += diff_temp * 0.1 + random.uniform(-0.5, 0.5)

        if system_state['is_extruding']:
            diff_speed = system_state['target_speed'] - system_state['speed']
            system_state['speed'] += diff_speed * 0.2 + random.uniform(-1.0, 1.0)
            system_state['diameter'] = 1.75 + random.uniform(-0.04, 0.04)

            if abs(system_state['diameter'] - 1.75) > 0.05:
                mqtt_client.publish(TOPIC_ALERTS, json.dumps({
                    'type': 'warning',
                    'message': f"Çap tolerans dışı: {system_state['diameter']:.2f}mm. Motor hızı düzeltiliyor..."
                }))
                if system_state['diameter'] > 1.75:
                    system_state['target_speed'] += 2.0
                else:
                    system_state['target_speed'] -= 2.0
        else:
            if system_state['status'] != 'Heating' and system_state['temperature'] > 25.0:
                system_state['temperature'] -= 0.5 + random.uniform(0, 0.2)
            system_state['speed'] *= 0.5
            system_state['diameter'] = 0.0

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
        time.sleep(1.0)


# === FLASK ROUTES ===
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/history')
def history_page():
    return render_template('history.html')


@app.route('/api/logs')
def get_logs():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT temperature, speed, diameter, timestamp FROM sensor_data ORDER BY id DESC LIMIT 100'
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        logs = [
            {
                'temperature': r[0],
                'speed': r[1],
                'diameter': r[2],
                'timestamp': str(r[3])
            }
            for r in rows
        ]
        return jsonify(logs)
    except Exception as e:
        return jsonify(error=str(e)), 500


@app.route('/export/csv')
def export_csv():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT id, temperature, speed, diameter, timestamp FROM sensor_data ORDER BY id ASC'
        )
        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(['ID', 'Temperature (C)', 'Motor Speed (0-255)', 'Filament Diameter (mm)', 'Timestamp'])
        cw.writerows(rows)
        output = si.getvalue()
        si.close()

        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=recyprint_sensor_logs.csv"}
        )
    except Exception as e:
        return f"Export failed: {str(e)}", 500


if __name__ == '__main__':
    init_db()
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, 60)
    mqtt_client.loop_start()
    # threading.Thread(target=esp32_simulator_thread, daemon=True).start()

    print("Starting RecyPrint MQTT Integration Server on HTTP port 5000...")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)