// Connect to standard Socket.IO namespace
const socket = io();

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
            y: {
                beginAtZero: false,
                grid: { color: 'rgba(255, 255, 255, 0.05)' }
            },
            x: {
                grid: { display: false }
            }
        },
        plugins: {
            legend: {
                labels: { font: { family: "'Orbitron', sans-serif" } }
            }
        },
        animation: {
            duration: 0 // Remove overall animation to make streaming smooth
        }
    }
});

function addData(chart, label, data) {
    chart.data.labels.push(label);
    chart.data.datasets.forEach((dataset) => {
        dataset.data.push(data);
    });
    // Keep max 30 points
    if(chart.data.labels.length > 30) {
        chart.data.labels.shift();
        chart.data.datasets.forEach((dataset) => {
            dataset.data.shift();
        });
    }
    chart.update();
}

// Socket IO Event Listeners

socket.on('connect', () => {
    dot.classList.add('connected');
    statusText.innerText = "Connected (Real-time)";
    statusText.style.color = "var(--success)";
});

socket.on('disconnect', () => {
    dot.classList.remove('connected');
    statusText.innerText = "Disconnected";
    statusText.style.color = "var(--danger)";
});

socket.on('sensor_update', (data) => {
    // 1. Update metric displays quickly
    liveTemp.innerText = data.temperature.toFixed(1);
    liveSpeed.innerText = data.speed.toFixed(1);
    liveDiameter.innerText = data.diameter.toFixed(3);

    // Update Status Badge
    const badge = document.getElementById('system-badge');
    badge.innerText = data.status;
    if(data.status === 'Heating') badge.style.color = '#f59e0b';
    else if(data.status === 'Ready') badge.style.color = 'var(--success)';
    else if(data.status === 'Extruding') badge.style.color = 'var(--accent-primary)';
    else if(data.status === 'Error') badge.style.color = 'var(--danger)';
    else badge.style.color = 'var(--text-muted)';
    
    // 2. Update chart
    if(data.timestamp) {
        addData(tempChart, data.timestamp, data.temperature);
    }
    
    // 3. Update buttons visual state based on backend truthful state
    if(data.is_extruding) {
        btnStart.style.opacity = '0.5';
        btnStart.innerText = "EXTRUDING...";
        btnStop.style.opacity = '1';
    } else {
        btnStart.style.opacity = '1';
        btnStart.innerText = "START EXTRUSION";
        btnStop.style.opacity = '0.5';
    }
});

socket.on('command_ack', (res) => {
    console.log("Command acknowledged:", res);
});

socket.on('emergency_stop', (data) => {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.borderLeft = '6px solid #b91c1c';
    toast.innerHTML = `🚨 <strong>EMERGENCY:</strong> ${data.message}`;
    toastContainer.appendChild(toast);
    
    setTimeout(() => { toast.remove(); }, 8000);
});

socket.on('warning', (data) => {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.background = 'rgba(245, 158, 11, 0.9)'; // Warning Orange
    toast.style.borderLeft = '6px solid #d97706';
    toast.innerHTML = `⚠️ <strong>Uyarı:</strong> ${data.message}`;
    toastContainer.appendChild(toast);
    
    setTimeout(() => { toast.remove(); }, 6000);
});

// User Interactions -> Emitting Events to Server

// Sliders updating DOM instantly, but sending to server on 'change' (when user lets go) or 'input'
sliderTemp.addEventListener('input', (e) => {
    const val = e.target.value;
    valTemp.innerText = val;
    socket.emit('control_command', {
        type: 'update_targets',
        target_temperature: val
    });
});

sliderSpeed.addEventListener('input', (e) => {
    const val = e.target.value;
    valSpeed.innerText = val;
    socket.emit('control_command', {
        type: 'update_targets',
        target_speed: val
    });
});

btnStart.addEventListener('click', () => {
    socket.emit('control_command', { type: 'start_extrusion' });
});

btnStop.addEventListener('click', () => {
    socket.emit('control_command', { type: 'stop_extrusion' });
});
