// Pure Native MQTT connection via WebSockets (Browser -> Public MQTT Broker)
const mqttClient = mqtt.connect('ws://broker.emqx.io:8083/mqtt');

const TOPIC_TELEMETRY = "recyprint/test/sensor_data";
const TOPIC_CONTROL   = "recyprint/test/control";
const TOPIC_ALERTS    = "recyprint/test/alerts";

// UI Elements
const dot = document.getElementById('connection-dot');
const statusText = document.getElementById('connection-status');

const liveTemp = document.getElementById('live-temp');
const liveSpeed = document.getElementById('live-speed');
const liveDiameter = document.getElementById('live-diameter');

const sliderTemp = document.getElementById('target-temp');
const valTemp = document.getElementById('val-target-temp');

const sliderSpeed = document.getElementById('target-speed');
const valSpeed = document.getElementById('val-target-speed');

const btnStart = document.getElementById('btn-start');
const btnStop = document.getElementById('btn-stop');

// Chart Setup
const ctx = document.getElementById('tempChart').getContext('2d');
Chart.defaults.color = "rgba(148, 163, 184, 0.8)";
Chart.defaults.font.family = "'Inter', sans-serif";

const tempChart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: [], // Timestamps
        datasets: [{
            label: 'Extrusion Temp (°C)',
            data: [],
            borderColor: '#0ea5e9',
            backgroundColor: 'rgba(14, 165, 233, 0.1)',
            borderWidth: 2,
            tension: 0.4, // Smooth curve
            fill: true,
            pointRadius: 0
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: { beginAtZero: false, grid: { color: 'rgba(255, 255, 255, 0.05)' } },
            x: { grid: { display: false } }
        },
        plugins: { legend: { labels: { font: { family: "'Orbitron', sans-serif" } } } },
        animation: { duration: 0 }
    }
});

function addData(chart, label, data) {
    chart.data.labels.push(label);
    chart.data.datasets.forEach((dataset) => { dataset.data.push(data); });
    if(chart.data.labels.length > 30) {
        chart.data.labels.shift();
        chart.data.datasets.forEach((dataset) => { dataset.data.shift(); });
    }
    chart.update();
}

// === MQTT EVENT LISTENERS ===
mqttClient.on('connect', () => {
    dot.classList.add('connected');
    statusText.innerText = "Connected to MQTT Broker";
    statusText.style.color = "var(--success)";
    
    // Subscribe to appropriate RecyPrint topics
    mqttClient.subscribe(TOPIC_TELEMETRY);
    mqttClient.subscribe(TOPIC_ALERTS);
    console.log("MQTT Client Subscribed successfully.");
});

mqttClient.on('error', (err) => {
    dot.classList.remove('connected');
    statusText.innerText = "MQTT Error / Disconnected";
    statusText.style.color = "var(--danger)";
    console.error(err);
});

// Handling incoming Publishes
mqttClient.on('message', (topic, message) => {
    try {
        const payload = JSON.parse(message.toString());
        
        if (topic === TOPIC_TELEMETRY) {
            liveTemp.innerText = payload.temperature.toFixed(1);
            liveSpeed.innerText = payload.speed.toFixed(1);
            liveDiameter.innerText = payload.diameter.toFixed(3);

            // Update Status Badge
            const badge = document.getElementById('system-badge');
            badge.innerText = payload.status;
            if(payload.status === 'Heating') badge.style.color = '#f59e0b';
            else if(payload.status === 'Ready') badge.style.color = 'var(--success)';
            else if(payload.status === 'Extruding') badge.style.color = 'var(--accent-primary)';
            else if(payload.status === 'Error') badge.style.color = 'var(--danger)';
            else badge.style.color = 'var(--text-muted)';
            
            if(payload.timestamp) { addData(tempChart, payload.timestamp, payload.temperature); }
            
            if(payload.is_extruding) {
                btnStart.style.opacity = '0.5';
                btnStart.innerText = "EXTRUDING...";
                btnStop.style.opacity = '1';
            } else {
                btnStart.style.opacity = '1';
                btnStart.innerText = "START EXTRUSION";
                btnStop.style.opacity = '0.5';
            }
        } 
        else if (topic === TOPIC_ALERTS) {
            const toastContainer = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = 'toast';
            
            if(payload.type === 'emergency') {
                toast.style.borderLeft = '6px solid #b91c1c';
                toast.style.background = 'rgba(239, 68, 68, 0.95)';
                toast.innerHTML = `🚨 <strong>EMERGENCY:</strong> ${payload.message}`;
            } else {
                toast.style.background = 'rgba(245, 158, 11, 0.9)'; // Warning Orange
                toast.style.borderLeft = '6px solid #d97706';
                toast.innerHTML = `⚠️ <strong>Uyarı:</strong> ${payload.message}`;
            }
            
            toastContainer.appendChild(toast);
            setTimeout(() => { toast.remove(); }, 8000);
        }
    } catch(err) {
        console.error("Payload decode error:", err);
    }
});


// === USER INTERACTIONS -> PUBLISHING TO MQTT ===
sliderTemp.addEventListener('change', (e) => {
    const val = e.target.value;
    valTemp.innerText = val;
    mqttClient.publish(TOPIC_CONTROL, JSON.stringify({ type: 'update_targets', target_temperature: val }));
});
// Using slider input for pure visual, but change for publishing limits network usage
sliderTemp.addEventListener('input', (e) => { valTemp.innerText = e.target.value; });

sliderSpeed.addEventListener('change', (e) => {
    const val = e.target.value;
    valSpeed.innerText = val;
    mqttClient.publish(TOPIC_CONTROL, JSON.stringify({ type: 'update_targets', target_speed: val }));
});
sliderSpeed.addEventListener('input', (e) => { valSpeed.innerText = e.target.value; });

btnStart.addEventListener('click', () => {
    mqttClient.publish(TOPIC_CONTROL, JSON.stringify({ type: 'start_extrusion' }));
});

btnStop.addEventListener('click', () => {
    mqttClient.publish(TOPIC_CONTROL, JSON.stringify({ type: 'stop_extrusion' }));
});
