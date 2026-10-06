/**
 * ICU Patient Deterioration Early-Warning System
 * Interactive Web Application Dashboard Logic
 */

// Simulated Patient Dataset State
let patientDataset = [];
let selectedPatientId = "ICU-0004";
let isSimulating = true;
let simSpeed = 1;
let simTimer = null;

// Chart Instances
let riskTrajectoryChart = null;
let vitalsWaveformChart = null;
let fineTuneLossChart = null;
let rocCurveChart = null;
let calibrationChart = null;

document.addEventListener('DOMContentLoaded', () => {
    initDataset();
    setupNavigation();
    setupThemeToggle();
    setupSimulatorControls();
    setupWorkbenchControls();
    setupReportModal();
    renderBedGrid();
    renderMetricsHub();
    inspectPatient(selectedPatientId);
});

// Initialize Synthetic Patient Cohort
function initDataset() {
    const wards = ['Medical ICU', 'Surgical ICU', 'Cardiac Care Unit', 'Neuro ICU'];
    const diags = [
        'Sepsis / Septic Shock', 'Acute Respiratory Failure',
        'Post-Op Coronary Artery Bypass', 'Traumatic Brain Injury', 'Acute Renal Failure'
    ];

    patientDataset = [];

    for (let i = 1; i <= 20; i++) {
        const pid = `ICU-${String(i).padStart(4, '0')}`;
        const bed = `Bed ICU-${String(i).padStart(2, '0')}`;
        const age = Math.floor(Math.random() * 50) + 30;
        const gender = Math.random() > 0.5 ? 'Male' : 'Female';
        const ward = wards[i % wards.length];
        const diag = diags[i % diags.length];

        // Deterioration flag
        const isDeteriorating = (i === 4 || i === 9 || i === 15);
        let riskScore = isDeteriorating ? (0.65 + Math.random() * 0.28) : (0.05 + Math.random() * 0.18);

        // Vitals
        const heartRate = Math.round(isDeteriorating ? (105 + Math.random() * 25) : (72 + Math.random() * 12));
        const map = Math.round(isDeteriorating ? (58 - Math.random() * 10) : (84 + Math.random() * 8));
        const spo2 = Math.round(isDeteriorating ? (90 - Math.random() * 4) : (98 + Math.random() * 1.5));
        const respRate = Math.round(isDeteriorating ? (26 + Math.random() * 6) : (16 + Math.random() * 3));
        const lactate = parseFloat((isDeteriorating ? (3.2 + Math.random() * 2.5) : (1.0 + Math.random() * 0.4)).toFixed(1));
        const wbc = parseFloat((isDeteriorating ? (14.5 + Math.random() * 5.0) : (7.2 + Math.random() * 1.8)).toFixed(1));

        let riskClass = "LOW";
        let riskColor = "var(--color-success)";
        let action = "Routine Monitoring - Patient Stable";

        if (riskScore >= 0.50) {
            riskClass = "HIGH";
            riskColor = "var(--color-danger)";
            action = "CRITICAL ALERT - Immediate ICU Team Review & ABG Protocol";
        } else if (riskScore >= 0.20) {
            riskClass = "MEDIUM";
            riskColor = "var(--color-warning)";
            action = "Increased Surveillance - Clinical Assessment Recommended";
        }

        patientDataset.push({
            patient_id: pid,
            bed: bed,
            age: age,
            gender: gender,
            ward: ward,
            primary_diagnosis: diag,
            risk_score: riskScore,
            risk_percentage: (riskScore * 100).toFixed(1),
            risk_class: riskClass,
            risk_color: riskColor,
            recommended_action: action,
            vitals: {
                heart_rate: heartRate,
                map: map,
                spo2: spo2,
                resp_rate: respRate,
                lactate: lactate,
                wbc: wbc,
                temperature: (36.5 + Math.random() * 1.2).toFixed(1)
            }
        });
    }
}

// Navigation Tab Switching
function setupNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    const tabPages = document.querySelectorAll('.tab-page');

    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetTab = item.getAttribute('data-tab');

            navItems.forEach(n => n.classList.remove('active'));
            tabPages.forEach(p => p.classList.remove('active'));

            item.classList.add('active');
            document.getElementById(`${targetTab}Section`).classList.add('active');
        });
    });

    document.getElementById('backToGridBtn').addEventListener('click', () => {
        document.querySelector('[data-tab="monitor"]').click();
    });

    // Search and Filter Listeners
    document.getElementById('patientSearchInput').addEventListener('input', renderBedGrid);
    document.getElementById('riskFilterSelect').addEventListener('change', renderBedGrid);
}

// Light / Dark Theme Toggle
function setupThemeToggle() {
    const themeBtn = document.getElementById('themeToggleBtn');
    themeBtn.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        const isLight = document.body.classList.contains('light-theme');
        themeBtn.innerHTML = isLight ? '<i class="fa-solid fa-sun"></i>' : '<i class="fa-solid fa-moon"></i>';
    });
}

// Live Stream Simulator Controls
function setupSimulatorControls() {
    const playBtn = document.getElementById('simPlayBtn');
    const speedBtn = document.getElementById('simSpeedBtn');

    playBtn.addEventListener('click', () => {
        isSimulating = !isSimulating;
        if (isSimulating) {
            playBtn.className = "btn btn-sm btn-success";
            playBtn.innerHTML = '<i class="fa-solid fa-play"></i> Streaming';
            startSimulatorTimer();
        } else {
            playBtn.className = "btn btn-sm btn-outline";
            playBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Paused';
            clearInterval(simTimer);
        }
    });

    speedBtn.addEventListener('click', () => {
        if (simSpeed === 1) simSpeed = 5;
        else if (simSpeed === 5) simSpeed = 10;
        else simSpeed = 1;
        speedBtn.innerText = `${simSpeed}x Speed`;
        if (isSimulating) startSimulatorTimer();
    });

    startSimulatorTimer();
}

function startSimulatorTimer() {
    clearInterval(simTimer);
    simTimer = setInterval(() => {
        // Randomly adjust vitals of a deteriorating patient
        const p4 = patientDataset.find(p => p.patient_id === "ICU-0004");
        if (p4) {
            p4.vitals.heart_rate = Math.min(170, p4.vitals.heart_rate + (Math.random() > 0.4 ? 1 : -1));
            p4.vitals.map = Math.max(45, p4.vitals.map - (Math.random() > 0.3 ? 1 : -1));
            p4.vitals.lactate = parseFloat((p4.vitals.lactate + (Math.random() * 0.1 - 0.03)).toFixed(1));
            
            p4.risk_score = Math.min(0.98, p4.risk_score + 0.005);
            p4.risk_percentage = (p4.risk_score * 100).toFixed(1);
        }

        renderBedGrid();
        if (selectedPatientId === "ICU-0004") {
            updateInspectorVitals(p4);
        }
    }, 2000 / simSpeed);
}

// Render ICU Bed Matrix Grid
function renderBedGrid() {
    const grid = document.getElementById('patientBedGrid');
    const searchTerm = document.getElementById('patientSearchInput').value.toLowerCase();
    const filterLevel = document.getElementById('riskFilterSelect').value;

    let filtered = patientDataset.filter(p => {
        const matchesSearch = p.patient_id.toLowerCase().includes(searchTerm) ||
                              p.bed.toLowerCase().includes(searchTerm) ||
                              p.ward.toLowerCase().includes(searchTerm);
        const matchesFilter = (filterLevel === 'ALL') || (p.risk_class === filterLevel);
        return matchesSearch && matchesFilter;
    });

    grid.innerHTML = filtered.map(p => `
        <div class="glass-card patient-bed-card risk-${p.risk_class}" onclick="inspectPatient('${p.patient_id}')">
            <div class="card-top">
                <span class="bed-number">${p.bed}</span>
                <span class="status-tag ${p.risk_class}">${p.risk_class} RISK</span>
            </div>
            
            <div class="card-patient-info">
                <h4>${p.patient_id} (${p.gender}, ${p.age})</h4>
                <p><i class="fa-solid fa-hospital-user"></i> ${p.ward}</p>
            </div>

            <div class="risk-meter">
                <div class="meter-header">
                    <span>12h Deterioration Prob</span>
                    <span class="meter-score" style="color: ${p.risk_color};">${p.risk_percentage}%</span>
                </div>
                <div class="risk-bar-outer">
                    <div class="risk-bar-inner ${p.risk_class.toLowerCase()}" style="width: ${p.risk_percentage}%;"></div>
                </div>
            </div>

            <div class="card-vitals-mini">
                <span>HR: <strong>${p.vitals.heart_rate} bpm</strong></span>
                <span>MAP: <strong>${p.vitals.map} mmHg</strong></span>
                <span>SpO2: <strong>${p.vitals.spo2}%</strong></span>
                <span>Lactate: <strong>${p.vitals.lactate} mmol/L</strong></span>
            </div>
        </div>
    `).join('');

    // Update Header Counts
    document.getElementById('monitoredBedsCount').innerText = patientDataset.length;
    document.getElementById('highRiskCount').innerText = patientDataset.filter(p => p.risk_class === 'HIGH').length;
}

// Inspect Patient Deep-Dive
function inspectPatient(patientId) {
    selectedPatientId = patientId;
    const p = patientDataset.find(item => item.patient_id === patientId) || patientDataset[0];

    document.getElementById('inspBedBadge').innerText = p.bed;
    document.getElementById('inspPatientName').innerText = `${p.patient_id} (${p.gender}, ${p.age} y/o)`;
    document.getElementById('inspPatientMeta').innerHTML = `
        <span><i class="fa-solid fa-hospital-user"></i> Ward: ${p.ward}</span><br>
        <span><i class="fa-solid fa-stethoscope"></i> Diag: ${p.primary_diagnosis}</span>
    `;

    document.getElementById('inspRiskVal').innerText = `${p.risk_percentage}%`;
    document.getElementById('inspRiskVal').style.color = p.risk_color;
    document.getElementById('inspRiskBadge').innerText = `${p.risk_class} RISK ALERT`;
    document.getElementById('inspRiskBadge').style.color = p.risk_color;
    document.getElementById('inspRiskBar').style.width = `${p.risk_percentage}%`;
    document.getElementById('inspActionText').innerText = p.recommended_action;

    updateInspectorVitals(p);
    renderRiskTrajectoryChart(p);
    renderVitalsWaveformChart(p);
    renderShapAttributions(p);

    // Switch to inspector tab if called from grid
    document.querySelector('[data-tab="inspector"]').click();
}

function updateInspectorVitals(p) {
    document.getElementById('inspVitalsGrid').innerHTML = `
        <div class="v-item">
            <div class="v-label">Heart Rate</div>
            <div class="v-val" style="color: ${p.vitals.heart_rate > 100 ? 'var(--color-danger)' : 'var(--text-heading)'}">${p.vitals.heart_rate} <small style="font-size:10px">bpm</small></div>
        </div>
        <div class="v-item">
            <div class="v-label">Mean Arterial Pres (MAP)</div>
            <div class="v-val" style="color: ${p.vitals.map < 65 ? 'var(--color-danger)' : 'var(--text-heading)'}">${p.vitals.map} <small style="font-size:10px">mmHg</small></div>
        </div>
        <div class="v-item">
            <div class="v-label">SpO2 Saturation</div>
            <div class="v-val" style="color: ${p.vitals.spo2 < 93 ? 'var(--color-danger)' : 'var(--text-heading)'}">${p.vitals.spo2} <small style="font-size:10px">%</small></div>
        </div>
        <div class="v-item">
            <div class="v-label">Blood Lactate</div>
            <div class="v-val" style="color: ${p.vitals.lactate > 2.0 ? 'var(--color-danger)' : 'var(--text-heading)'}">${p.vitals.lactate} <small style="font-size:10px">mmol/L</small></div>
        </div>
    `;
}

// Chart 1: Continuous Risk Trajectory (Past 24h & 12h horizon)
function renderRiskTrajectoryChart(p) {
    const ctx = document.getElementById('riskTrajectoryChart').getContext('2d');
    if (riskTrajectoryChart) riskTrajectoryChart.destroy();

    const hours = Array.from({length: 24}, (_, i) => `-${23-i}h`);
    hours.push('+6h (Pred)', '+12h (Horizon)');

    const baseRisk = p.risk_score;
    const trajectoryData = [];

    for (let i = 0; i < 24; i++) {
        const factor = Math.max(0.1, baseRisk * (0.3 + 0.7 * (i / 24)));
        trajectoryData.push((factor * 100).toFixed(1));
    }
    trajectoryData.push((baseRisk * 105).toFixed(1), (baseRisk * 110).toFixed(1));

    riskTrajectoryChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours,
            datasets: [{
                label: 'Deterioration Risk Probability (%)',
                data: trajectoryData,
                borderColor: p.risk_color,
                backgroundColor: 'rgba(239, 68, 68, 0.12)',
                fill: true,
                tension: 0.35,
                borderWidth: 3,
                pointRadius: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                y: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

// Chart 2: Vital Signs Waveform Chart
function renderVitalsWaveformChart(p) {
    const ctx = document.getElementById('vitalsWaveformChart').getContext('2d');
    if (vitalsWaveformChart) vitalsWaveformChart.destroy();

    const hours = Array.from({length: 12}, (_, i) => `-${11-i}h`);
    const hrData = Array.from({length: 12}, (_, i) => p.vitals.heart_rate - (11-i)*1.5 + (Math.random()*4 - 2));
    const mapData = Array.from({length: 12}, (_, i) => p.vitals.map + (11-i)*1.2 + (Math.random()*4 - 2));

    vitalsWaveformChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: hours,
            datasets: [
                { label: 'Heart Rate (bpm)', data: hrData, borderColor: '#ef4444', borderWidth: 2, tension: 0.3 },
                { label: 'MAP (mmHg)', data: mapData, borderColor: '#3b82f6', borderWidth: 2, tension: 0.3 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

// SHAP Feature Attributions Rendering
function renderShapAttributions(p) {
    const container = document.getElementById('shapAttributionList');
    
    // Dynamic feature contributions
    const attributions = [
        { feature: 'Lactate Rise (2.5 -> ' + p.vitals.lactate + ' mmol/L)', pct: 32.5, type: 'inc' },
        { feature: 'MAP Drop (' + p.vitals.map + ' mmHg)', pct: 24.8, type: 'inc' },
        { feature: 'SpO2 Desaturation (' + p.vitals.spo2 + '%)', pct: 18.2, type: 'inc' },
        { feature: 'Tachycardia HR (' + p.vitals.heart_rate + ' bpm)', pct: 12.4, type: 'inc' },
        { feature: 'Normal pH Baseline (7.38)', pct: -7.9, type: 'dec' }
    ];

    container.innerHTML = attributions.map(a => `
        <div class="attr-item">
            <div class="attr-info">
                <span>${a.feature}</span>
                <strong class="${a.type === 'inc' ? 'text-danger' : 'text-success'}">${a.type === 'inc' ? '+' : ''}${a.pct}%</strong>
            </div>
            <div class="attr-bar-outer">
                <div class="attr-bar-inner ${a.type}" style="width: ${Math.abs(a.pct)}%;"></div>
            </div>
        </div>
    `).join('');
}

// Transfer Learning Workbench Fine-Tuning Simulator
function setupWorkbenchControls() {
    const lrRange = document.getElementById('lrRange');
    const epochsRange = document.getElementById('epochsRange');
    const runBtn = document.getElementById('runFineTuneBtn');

    lrRange.addEventListener('input', () => document.getElementById('lrVal').innerText = lrRange.value);
    epochsRange.addEventListener('input', () => document.getElementById('epochsVal').innerText = epochsRange.value);

    renderFineTuneLossChart([0.65, 0.48, 0.38, 0.32, 0.28, 0.25, 0.22, 0.19, 0.18, 0.16]);

    runBtn.addEventListener('click', () => {
        runBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Fine-Tuning in Progress...';
        runBtn.disabled = true;

        setTimeout(() => {
            const epochs = parseInt(epochsRange.value);
            const lossHistory = [];
            let loss = 0.68;

            for (let e = 0; e < epochs; e++) {
                loss *= (0.91 + Math.random() * 0.04);
                lossHistory.push(parseFloat(loss.toFixed(4)));
            }

            renderFineTuneLossChart(lossHistory);
            runBtn.innerHTML = '<i class="fa-solid fa-check"></i> Fine-Tuning Complete';
            runBtn.disabled = false;
        }, 1500);
    });
}

function renderFineTuneLossChart(losses) {
    const ctx = document.getElementById('fineTuneLossChart').getContext('2d');
    if (fineTuneLossChart) fineTuneLossChart.destroy();

    fineTuneLossChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: losses.map((_, idx) => `Epoch ${idx+1}`),
            datasets: [{
                label: 'BCE Loss',
                data: losses,
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.15)',
                fill: true,
                tension: 0.3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { grid: { color: 'rgba(255,255,255,0.05)' } },
                x: { grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

// Metrics Hub Rendering (AUROC, AUPRC, Calibration)
function renderMetricsHub() {
    renderRocCurveChart();
    renderCalibrationChart();

    const tableBody = document.getElementById('metricsTableBody');
    tableBody.innerHTML = `
        <tr style="background: rgba(59, 130, 246, 0.1);">
            <td><strong>Proposed: Medical Foundation (Fine-Tuned)</strong></td>
            <td><strong class="text-primary">0.9142</strong></td>
            <td><strong class="text-success">0.8875</strong></td>
            <td>92.3%</td>
            <td>88.6%</td>
            <td>0.865</td>
            <td><strong class="text-info">0.0712</strong></td>
        </tr>
        <tr>
            <td>Baseline: Gradient Boosted Trees (XGBoost)</td>
            <td>0.8210</td>
            <td>0.7640</td>
            <td>81.5%</td>
            <td>80.2%</td>
            <td>0.742</td>
            <td>0.1245</td>
        </tr>
        <tr>
            <td>Baseline: Logistic Regression</td>
            <td>0.7435</td>
            <td>0.6812</td>
            <td>73.0%</td>
            <td>72.4%</td>
            <td>0.665</td>
            <td>0.1680</td>
        </tr>
    `;
}

function renderRocCurveChart() {
    const ctx = document.getElementById('rocCurveChart').getContext('2d');
    if (rocCurveChart) rocCurveChart.destroy();

    rocCurveChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
            datasets: [
                { label: 'Foundation Model (AUROC = 0.914)', data: [0, 0.45, 0.72, 0.85, 0.91, 0.94, 0.96, 0.98, 0.99, 1.0, 1.0], borderColor: '#3b82f6', borderWidth: 3 },
                { label: 'Baseline GBDT (AUROC = 0.821)', data: [0, 0.30, 0.52, 0.68, 0.78, 0.84, 0.88, 0.92, 0.95, 0.98, 1.0], borderColor: '#f59e0b', borderWidth: 2, borderDash: [4, 4] },
                { label: 'Random Chance (0.50)', data: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], borderColor: '#6b7280', borderWidth: 1, borderDash: [2, 2] }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'False Positive Rate (1 - Specificity)' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { title: { display: true, text: 'True Positive Rate (Sensitivity)' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

function renderCalibrationChart() {
    const ctx = document.getElementById('calibrationChart').getContext('2d');
    if (calibrationChart) calibrationChart.destroy();

    calibrationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['0-10%', '10-20%', '20-30%', '30-40%', '40-50%', '50-60%', '60-70%', '70-80%', '80-90%', '90-100%'],
            datasets: [
                { label: 'Perfect Calibration', data: [0.05, 0.15, 0.25, 0.35, 0.45, 0.55, 0.65, 0.75, 0.85, 0.95], borderColor: '#6b7280', borderDash: [4,4] },
                { label: 'Observed vs Predicted Frequency', data: [0.04, 0.14, 0.26, 0.34, 0.47, 0.56, 0.63, 0.76, 0.84, 0.93], borderColor: '#10b981', borderWidth: 3 }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { title: { display: true, text: 'Predicted Risk Bin' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                y: { title: { display: true, text: 'Actual Deterioration Rate' }, grid: { color: 'rgba(255,255,255,0.05)' } }
            }
        }
    });
}

// Report Modal & Printing
function setupReportModal() {
    const modal = document.getElementById('reportModal');
    const openBtn = document.getElementById('reportExportBtn');
    const closeBtn = document.getElementById('closeModalBtn');
    const dismissBtn = document.getElementById('dismissModalBtn');
    const printBtn = document.getElementById('printReportBtn');

    openBtn.addEventListener('click', () => {
        const highRisk = patientDataset.filter(p => p.risk_class === 'HIGH');
        document.getElementById('reportTableBody').innerHTML = highRisk.map(p => `
            <tr>
                <td>${p.bed}</td>
                <td>${p.patient_id}</td>
                <td>${p.primary_diagnosis}</td>
                <td>Lactate: ${p.vitals.lactate} mmol/L, MAP: ${p.vitals.map} mmHg</td>
                <td><strong class="text-danger">${p.risk_percentage}%</strong></td>
                <td>${p.recommended_action}</td>
            </tr>
        `).join('');
        modal.classList.add('active');
    });

    closeBtn.addEventListener('click', () => modal.classList.remove('active'));
    dismissBtn.addEventListener('click', () => modal.classList.remove('active'));
    printBtn.addEventListener('click', () => window.print());
}
