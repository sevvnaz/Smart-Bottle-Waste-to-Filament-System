import time
import threading
import sqlite3
import random
import csv
from io import StringIO
from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'recyprint_secret!'
# Utilizing SocketIO for real-time WebSocket communication
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

DB_NAME = 'recyprint.db'

# System State (Mocked ESP32 values)
system_state = {
    'temperature': 25.0,  # Startup at room temp
    'speed': 0.0,
    'diameter': 0.0,
    'target_temperature': 180.0,
    'target_speed': 60.0,
    'is_extruding': False,
    'status': 'Standby' # Standby, Heating, Ready, Extruding, Error
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

def esp32_simulator_thread():
    """Background thread simulating ESP32 sensor values."""
    CRITICAL_TEMP = 180.0  # Safe threshold for automated shutdown as per PDF documentation

    while True:
        # Automated Safety Logic Verification (Emergency Stop)
        if system_state['temperature'] >= CRITICAL_TEMP and system_state['is_extruding']:
            system_state['is_extruding'] = False
            system_state['status'] = 'Error'
            system_state['target_temperature'] = 0.0
            system_state['target_speed'] = 0.0
            socketio.emit('emergency_stop', {
                'message': f"Kritik Sıcaklık ({system_state['temperature']:.1f}°C)! Heater kapatıldı, sistem güvenli moda alındı."
            })
        
        # Determine Status
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
                    socketio.emit('warning', {'message': "Sıcaklık hedef değerden çok saptı! Extrusion kalitesi etkilenebilir."})

        # Process Physics Simulation
        if system_state['is_extruding'] or system_state['status'] == 'Heating':
            # Simulate generic temperature approaching target (both during heating and extruding)
            diff_temp = system_state['target_temperature'] - system_state['temperature']
            system_state['temperature'] += diff_temp * 0.1 + random.uniform(-0.5, 0.5)

        if system_state['is_extruding']:
            # Simulate real speed
            diff_speed = system_state['target_speed'] - system_state['speed']
            system_state['speed'] += diff_speed * 0.2 + random.uniform(-1.0, 1.0)
            
            # Simulate diameter fluctuation
            system_state['diameter'] = 1.75 + random.uniform(-0.04, 0.04)
            
            # Check Tolerance && Auto-correct speed
            if abs(system_state['diameter'] - 1.75) > 0.05:
                # Issue Warning
                socketio.emit('warning', {'message': f"Çap tolerans dışı: {system_state['diameter']:.2f}mm. Motor hızı düzeltiliyor..."})
                # Auto correct
                if system_state['diameter'] > 1.75:
                    system_state['target_speed'] += 2.0 # Pull faster to make it thinner
                else:
                    system_state['target_speed'] -= 2.0 # Pull slower to make it thicker
        else:
            # Not extruding -> Cooling down and motor stopped
            if system_state['status'] != 'Heating':
                if system_state['temperature'] > 25.0:
                    system_state['temperature'] -= 0.5 + random.uniform(0, 0.2)
            system_state['speed'] *= 0.5
            system_state['diameter'] = 0.0

        # Log to DB occasionally (for history)
        if random.random() < 0.2: # ~ every 5 ticks
            log_sensor_data(system_state['temperature'], system_state['speed'], system_state['diameter'])

        # Emit standard real-time update via WebSocket
        socketio.emit('sensor_update', {
            'temperature': round(system_state['temperature'], 2),
            'speed': round(system_state['speed'], 1),
            'diameter': round(system_state['diameter'], 3),
            'target_temperature': system_state['target_temperature'],
            'target_speed': system_state['target_speed'],
            'is_extruding': system_state['is_extruding'],
            'status': system_state['status'],
            'timestamp': time.strftime('%H:%M:%S')
        })
        
        socketio.sleep(1) # Emit data every 1 second

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
        
        return Response(
            output,
            mimetype="text/csv",
            headers={"Content-disposition": "attachment; filename=recyprint_sensor_logs.csv"}
        )
    except Exception as e:
        return f"Export failed: {str(e)}", 500

# WebSocket Event Handlers
@socketio.on('connect')
def handle_connect():
    print("Client connected")
    # Send initial state
    emit('sensor_update', system_state)

@socketio.on('control_command')
def handle_control(data):
    """Handle commands from frontend to adjust ESP32 targets."""
    print("Received Control Command:", data)
    command_type = data.get('type')
    
    if command_type == 'update_targets':
        if 'target_temperature' in data:
            system_state['target_temperature'] = float(data['target_temperature'])
            system_state['status'] = 'Standby' if system_state['target_temperature'] == 0 else 'Heating'
        if 'target_speed' in data:
            system_state['target_speed'] = float(data['target_speed'])
    elif command_type == 'start_extrusion':
        # Safely constraint: Only start if temperature is hot enough!
        if system_state['temperature'] < (system_state['target_temperature'] - 5.0):
            emit('warning', {'message': 'Hedef sıcaklığa ulaşmadan motor başlatılamaz!'})
        else:
            system_state['is_extruding'] = True
    elif command_type == 'stop_extrusion':
        system_state['is_extruding'] = False

    # Acknowledge the command via WS broadcast
    socketio.emit('command_ack', {'status': 'success', 'state': system_state})

if __name__ == '__main__':
    init_db()
    # Start the simulator background task using socketio
    socketio.start_background_task(esp32_simulator_thread)
    print("Starting RecyPrint WebSocket Server on port 5000...")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)
