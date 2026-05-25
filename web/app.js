document.addEventListener("DOMContentLoaded", () => {
    const audioInput = document.getElementById("audioInput");
    const dropZone = document.getElementById("dropZone");
    const uploadPrompt = document.getElementById("uploadPrompt");
    const waveformEl = document.getElementById("waveform");
    const processBtn = document.getElementById("processBtn");
    const statusText = document.getElementById("statusText");
    const playerContainer = document.getElementById("playerContainer");
    const player = document.getElementById("player");
    const downloadBtn = document.getElementById("downloadBtn");
    const themeSelect = document.getElementById("themeSelect");
    const qualitySelect = document.getElementById("qualitySelect");
    
    // Sliders & Vals
    const binds = [
        "stretch", "reverb", "shimmer",
        "lowpass", "drive", "texture", "granular", "motion"
    ];
    const ui = {};
    binds.forEach(b => {
        ui[b + 'Slider'] = document.getElementById(b + "Slider");
        ui[b + 'Val'] = document.getElementById(b + "Val");
        if(ui[b + 'Slider']) {
            ui[b + 'Slider'].addEventListener("input", (e) => {
                let val = e.target.value;
                if (b === 'stretch') val += "x";
                if (b === 'lowpass') val += " Hz";
                ui[b + 'Val'].textContent = val;
            });
        }
    });

    const advancedToggle = document.getElementById("advancedToggle");
    const advancedPanel = document.getElementById("advancedPanel");
    advancedToggle.addEventListener("click", () => {
        if (advancedPanel.style.display === "none") {
            advancedPanel.style.display = "block";
            advancedToggle.textContent = "⚙️ Hide Advanced Settings";
        } else {
            advancedPanel.style.display = "none";
            advancedToggle.textContent = "⚙️ Advanced Settings";
        }
    });

    let worker = new Worker("worker.js");
    let isWorkerReady = false;
    let fileBuffer = null;
    let currentBlob = null;
    let wavesurfer = null;

    // Theme loading and switching
    function applyTheme(themeName) {
        document.documentElement.setAttribute('data-theme', themeName);
        localStorage.setItem('findusTheme', themeName);
        if (wavesurfer) {
            // Read CSS variables
            const style = getComputedStyle(document.documentElement);
            const waveColor = style.getPropertyValue('--waveform-wave').trim() || 'rgba(255, 255, 255, 0.4)';
            const progressColor = style.getPropertyValue('--waveform-progress').trim() || '#8b5cf6';
            
            wavesurfer.setOptions({
                waveColor: waveColor,
                progressColor: progressColor
            });
        }
    }

    const savedTheme = localStorage.getItem('findusTheme') || 'default';
    themeSelect.value = savedTheme;
    // We apply it immediately to document, but wavesurfer isn't created yet
    document.documentElement.setAttribute('data-theme', savedTheme);

    themeSelect.addEventListener('change', (e) => {
        applyTheme(e.target.value);
    });

    // Init Wavesurfer
    const initialStyle = getComputedStyle(document.documentElement);
    wavesurfer = WaveSurfer.create({
        container: '#waveform',
        waveColor: initialStyle.getPropertyValue('--waveform-wave').trim() || 'rgba(255, 255, 255, 0.4)',
        progressColor: initialStyle.getPropertyValue('--waveform-progress').trim() || '#8b5cf6',
        cursorColor: 'transparent',
        barWidth: 2,
        barRadius: 3,
        responsive: true,
        height: 80,
    });

    // Worker messaging
    worker.onmessage = function(e) {
        const data = e.data;
        if (data.type === 'READY') {
            isWorkerReady = true;
            statusText.textContent = "Engine Ready. Upload audio to begin.";
            statusText.classList.remove("pulse");
            checkReadyState();
        } else if (data.type === 'STATUS') {
            statusText.textContent = data.message;
            statusText.classList.add("pulse");
        } else if (data.type === 'DONE') {
            statusText.textContent = "Processing Complete!";
            statusText.classList.remove("pulse");
            processBtn.disabled = false;
            
            // Create audio blob and play
            currentBlob = new Blob([data.wavBytes], { type: 'audio/wav' });
            const url = URL.createObjectURL(currentBlob);
            player.src = url;
            playerContainer.style.display = "block";
            player.play();
        } else if (data.type === 'ERROR') {
            statusText.textContent = "Error: " + data.error;
            statusText.classList.remove("pulse");
            processBtn.disabled = false;
        }
    };

    function checkReadyState() {
        if (isWorkerReady && fileBuffer) {
            processBtn.disabled = false;
        } else {
            processBtn.disabled = true;
        }
    }

    // File Input
    audioInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) {
            uploadPrompt.style.display = "none";
            waveformEl.style.display = "block";
            
            const reader = new FileReader();
            reader.onload = function() {
                fileBuffer = new Uint8Array(reader.result);
                wavesurfer.loadBlob(file);
                checkReadyState();
            };
            reader.readAsArrayBuffer(file);
        }
    });

    // Process Button
    processBtn.addEventListener("click", () => {
        if (!fileBuffer || !isWorkerReady) return;
        
        processBtn.disabled = true;
        playerContainer.style.display = "none";
        
        const lowpassHz = parseFloat(ui.lowpassSlider.value);
        const filterMode = lowpassHz < 12000 ? "Low-pass" : "Off";
        
        const effects = {
            reverb_amount: parseFloat(ui.reverbSlider.value),
            reverb_enabled: parseFloat(ui.reverbSlider.value) > 0,
            shimmer_amount: parseFloat(ui.shimmerSlider.value),
            shimmer_enabled: parseFloat(ui.shimmerSlider.value) > 0,
            filter_mode: filterMode,
            lowpass_hz: lowpassHz,
            drive_amount: parseFloat(ui.driveSlider.value),
            drive_enabled: parseFloat(ui.driveSlider.value) > 0,
            texture_amount: parseFloat(ui.textureSlider.value),
            texture_enabled: parseFloat(ui.textureSlider.value) > 0,
            granular_amount: parseFloat(ui.granularSlider.value),
            granular_enabled: parseFloat(ui.granularSlider.value) > 0,
            motion_amount: parseFloat(ui.motionSlider.value),
            motion_enabled: parseFloat(ui.motionSlider.value) > 0,
            chorus_amount: 0.0,
            pitch_drift_amount: 0.0,
            bloom_amount: 0.0,
            delay_amount: 0.0,
            autopan_amount: 0.0,
            stereo_width: 1.0,
            reverse: false,
            freeze_enabled: false,
            wet_dry: 1.0,
            input_gain_db: 0.0,
            limiter_enabled: true
        };
        
        worker.postMessage({
            type: 'PROCESS',
            wavBytes: fileBuffer,
            stretchFactor: parseFloat(ui.stretchSlider.value),
            windowSize: parseInt(qualitySelect.value),
            effectsJson: JSON.stringify(effects)
        });
    });

    // Download Button
    downloadBtn.addEventListener("click", () => {
        if (!currentBlob) return;
        const a = document.createElement("a");
        a.href = URL.createObjectURL(currentBlob);
        a.download = "Findus_Stretched.wav";
        a.click();
    });

    // Register Service Worker for PWA offline support
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./sw.js')
            .then(reg => console.log('SW registered!', reg))
            .catch(err => console.log('SW registration failed', err));
    }
});
