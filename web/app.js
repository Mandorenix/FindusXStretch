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
    const presetSelect = document.getElementById("presetSelect");
    const surpriseBtn = document.getElementById("surpriseBtn");
    const themeSelect = document.getElementById("themeSelect");
    const qualitySelect = document.getElementById("qualitySelect");
    
    // Help Modal Logic
    const openHelpBtn = document.getElementById('openHelpBtn');
    const closeHelpBtn = document.getElementById('closeHelpBtn');
    const helpModal = document.getElementById('helpModal');
    
    if (openHelpBtn && closeHelpBtn && helpModal) {
        openHelpBtn.addEventListener('click', () => helpModal.style.display = 'flex');
        closeHelpBtn.addEventListener('click', () => helpModal.style.display = 'none');
        helpModal.addEventListener('click', (e) => {
            if (e.target === helpModal) helpModal.style.display = 'none';
        });
    }
    
    // Sliders & Vals
    const binds = [
        "stretch", "reverb", "shimmer",
        "lowpass", "drive", "texture", "granular", "motion",
        "bloom", "delay", "chorus", "stereo_width", "autopan", "pitch_drift"
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
    
    // Toggles
    const reverseToggle = document.getElementById("reverseToggle");
    const freezeToggle = document.getElementById("freezeToggle");

    // Tab logic
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            tabContents.forEach(c => c.style.display = 'none');
            
            btn.classList.add('active');
            const target = btn.getAttribute('data-tab');
            document.getElementById(target).style.display = 'block';
        });
    });

    advancedToggle.addEventListener("click", () => {
        if (advancedPanel.style.display === "none") {
            advancedPanel.style.display = "block";
            advancedToggle.textContent = "⚙️ Hide Advanced Settings";
        } else {
            advancedPanel.style.display = "none";
            advancedToggle.textContent = "⚙️ Advanced Settings";
        }
    });

    // Helper to update slider and its display value
    function updateSlider(name, value) {
        if (ui[name + 'Slider']) {
            ui[name + 'Slider'].value = value;
            // Trigger input event to update label
            ui[name + 'Slider'].dispatchEvent(new Event('input'));
        }
    }

    // Presets
    const presets = {
        original: { stretch: 1, reverb: 0.0, shimmer: 0.0, lowpass: 12000, drive: 0.0, texture: 0.0, granular: 0.0, motion: 0.0, bloom: 0.0, delay: 0.0, chorus: 0.0, stereo_width: 1.0, autopan: 0.0, pitch_drift: 0.0, reverse: false, freeze: false },
        default: { stretch: 4, reverb: 0.5, shimmer: 0.3, lowpass: 6000, drive: 0.0, texture: 0.0, granular: 0.0, motion: 0.0, bloom: 0.0, delay: 0.0, chorus: 0.0, stereo_width: 1.0, autopan: 0.0, pitch_drift: 0.0, reverse: false, freeze: false },
        deep_ambient: { stretch: 12, reverb: 0.9, shimmer: 0.1, lowpass: 2000, drive: 0.1, texture: 0.2, granular: 0.0, motion: 0.1, bloom: 0.5, delay: 0.4, chorus: 0.2, stereo_width: 1.5, autopan: 0.3, pitch_drift: 0.1, reverse: false, freeze: false },
        glitchy_tape: { stretch: 3, reverb: 0.2, shimmer: 0.0, lowpass: 4000, drive: 0.6, texture: 0.4, granular: 0.8, motion: 0.7, bloom: 0.0, delay: 0.2, chorus: 0.0, stereo_width: 0.8, autopan: 0.0, pitch_drift: 0.8, reverse: false, freeze: false },
        shimmering_ice: { stretch: 8, reverb: 0.8, shimmer: 0.9, lowpass: 8000, drive: 0.0, texture: 0.5, granular: 0.2, motion: 0.4, bloom: 0.3, delay: 0.6, chorus: 0.5, stereo_width: 2.0, autopan: 0.5, pitch_drift: 0.0, reverse: false, freeze: false }
    };
    
    // Load custom presets
    const savedPresets = JSON.parse(localStorage.getItem('findusPresets') || '{}');
    Object.assign(presets, savedPresets);
    
    // Populate select with custom presets
    Object.keys(savedPresets).forEach(key => {
        const option = document.createElement('option');
        option.value = key;
        option.textContent = key;
        presetSelect.appendChild(option);
    });

    presetSelect.addEventListener("change", (e) => {
        const preset = presets[e.target.value];
        if (preset) {
            Object.keys(preset).forEach(key => {
                if (key !== 'reverse' && key !== 'freeze') {
                    updateSlider(key, preset[key]);
                }
            });
            if (preset.reverse !== undefined) reverseToggle.checked = preset.reverse;
            if (preset.freeze !== undefined) freezeToggle.checked = preset.freeze;
        }
    });

    const savePresetBtn = document.getElementById('savePresetBtn');
    if (savePresetBtn) {
        savePresetBtn.addEventListener('click', () => {
            const name = prompt("Enter a name for your preset:");
            if (!name) return;
            
            const currentSettings = {};
            binds.forEach(b => {
                if (ui[b + 'Slider']) {
                    currentSettings[b] = parseFloat(ui[b + 'Slider'].value);
                }
            });
            currentSettings.reverse = reverseToggle.checked;
            currentSettings.freeze = freezeToggle.checked;
            
            presets[name] = currentSettings;
            const customPresets = JSON.parse(localStorage.getItem('findusPresets') || '{}');
            customPresets[name] = currentSettings;
            localStorage.setItem('findusPresets', JSON.stringify(customPresets));
            
            const option = document.createElement('option');
            option.value = name;
            option.textContent = name;
            presetSelect.appendChild(option);
            presetSelect.value = name;
        });
    }

    // Surprise Me
    surpriseBtn.addEventListener("click", () => {
        updateSlider('stretch', Math.floor(Math.random() * 15) + 2); // 2 to 16
        updateSlider('reverb', (Math.random()).toFixed(2));
        updateSlider('shimmer', (Math.random()).toFixed(2));
        updateSlider('lowpass', Math.floor(Math.random() * 11500) + 500); // 500 to 12000
        updateSlider('drive', (Math.random()).toFixed(2));
        updateSlider('texture', (Math.random()).toFixed(2));
        updateSlider('granular', (Math.random()).toFixed(2));
        updateSlider('motion', (Math.random()).toFixed(2));
        updateSlider('bloom', (Math.random()).toFixed(2));
        updateSlider('delay', (Math.random()).toFixed(2));
        updateSlider('chorus', (Math.random()).toFixed(2));
        updateSlider('stereo_width', (Math.random() * 2).toFixed(2));
        updateSlider('autopan', (Math.random()).toFixed(2));
        updateSlider('pitch_drift', (Math.random()).toFixed(2));
        reverseToggle.checked = Math.random() > 0.8;
        freezeToggle.checked = Math.random() > 0.9;
        presetSelect.value = "default"; // Reset preset dropdown
    });

    let worker = new Worker("worker.js");
    let isWorkerReady = false;
    let fileBuffer = null;
    let currentBlob = null;
    let wavesurfer = null;
    let wsRegions = null;
    let currentRegion = null;

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

    // Initialize Regions Plugin
    wsRegions = wavesurfer.registerPlugin(WaveSurfer.Regions.create());
    
    wavesurfer.on('decode', () => {
        // Create default region over the whole file
        wsRegions.clearRegions();
        
        // Create visual drag handle for mobile
        const regionContent = document.createElement('div');
        regionContent.style.width = '100%';
        regionContent.style.height = '100%';
        regionContent.style.position = 'relative';
        regionContent.style.pointerEvents = 'none';
        
        const moveHandle = document.createElement('div');
        moveHandle.className = 'region-move-handle';
        moveHandle.style.pointerEvents = 'auto'; // allow touch
        
        regionContent.appendChild(moveHandle);

        currentRegion = wsRegions.addRegion({
            start: 0,
            end: wavesurfer.getDuration(),
            content: regionContent,
            resize: true,
            drag: true
        });
        currentZoom = waveformEl.clientWidth / wavesurfer.getDuration();
    });

    let currentZoom = 50;
    
    // Zoom Buttons
    const zoomInBtn = document.getElementById('zoomInBtn');
    const zoomOutBtn = document.getElementById('zoomOutBtn');
    
    if (zoomInBtn) {
        zoomInBtn.addEventListener('click', () => {
            if (!wavesurfer) return;
            currentZoom = Math.min(currentZoom * 1.5, 2000);
            wavesurfer.zoom(currentZoom);
        });
    }
    
    if (zoomOutBtn) {
        zoomOutBtn.addEventListener('click', () => {
            if (!wavesurfer) return;
            currentZoom = Math.max(10, currentZoom / 1.5);
            wavesurfer.zoom(currentZoom);
        });
    }
    
    // Preview Button
    const playRegionBtn = document.getElementById('playRegionBtn');
    if (playRegionBtn) {
        playRegionBtn.addEventListener('click', () => {
            if (!wavesurfer) return;
            if (wavesurfer.isPlaying()) {
                wavesurfer.pause();
            } else {
                if (currentRegion) {
                    currentRegion.play();
                } else {
                    wavesurfer.play();
                }
            }
        });
    }

    wavesurfer.on('pause', () => {
        if (playRegionBtn) playRegionBtn.innerHTML = "▶ Preview";
    });
    wavesurfer.on('play', () => {
        if (playRegionBtn) playRegionBtn.innerHTML = "⏸ Pause";
    });

    waveformEl.addEventListener('wheel', (e) => {
        if (!wavesurfer) return;
        e.preventDefault();
        // zoom in if scrolling up, out if scrolling down
        const delta = e.deltaY < 0 ? 1.2 : 0.8;
        currentZoom = Math.max(10, Math.min(currentZoom * delta, 2000));
        wavesurfer.zoom(currentZoom);
    }, { passive: false });

    wsRegions.on('region-updated', (region) => {
        currentRegion = region;
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
            if (data.progress !== undefined) {
                document.getElementById("progressContainer").style.display = "block";
                document.getElementById("progressBar").style.width = data.progress + "%";
            }
        } else if (data.type === 'progress') {
            const pct = Math.round(data.progress * 100);
            document.getElementById("progressContainer").style.display = "block";
            document.getElementById("progressBar").style.width = pct + "%";
            statusText.textContent = data.message + " (" + pct + "%)";
        } else if (data.type === 'DONE') {
            statusText.textContent = "Processing Complete!";
            statusText.classList.remove("pulse");
            document.getElementById("progressContainer").style.display = "none";
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
            document.getElementById("progressContainer").style.display = "none";
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
            document.getElementById("uploadPromptText").textContent = "Tap to Upload a Different File";
            document.getElementById("fileName").textContent = file.name;
            document.getElementById("waveformContainer").style.display = "block";
            
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
        document.getElementById("progressContainer").style.display = "block";
        document.getElementById("progressBar").style.width = "0%";
        
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
            chorus_amount: parseFloat(ui.chorusSlider.value),
            pitch_drift_amount: parseFloat(ui.pitch_driftSlider.value),
            bloom_amount: parseFloat(ui.bloomSlider.value),
            delay_amount: parseFloat(ui.delaySlider.value),
            autopan_amount: parseFloat(ui.autopanSlider.value),
            stereo_width: parseFloat(ui.stereo_widthSlider.value),
            reverse: reverseToggle.checked,
            freeze_enabled: freezeToggle.checked,
            wet_dry: 1.0,
            input_gain_db: 0.0,
            limiter_enabled: true
        };
        
        worker.postMessage({
            type: 'PROCESS',
            wavBytes: fileBuffer,
            stretchFactor: parseFloat(ui.stretchSlider.value),
            windowSize: parseInt(qualitySelect.value),
            regionStart: currentRegion ? currentRegion.start : 0,
            regionEnd: currentRegion ? currentRegion.end : -1,
            effectsJson: JSON.stringify(effects)
        });
    });

    // Share / Download Button
    downloadBtn.addEventListener("click", async () => {
        if (!currentBlob) return;
        
        const file = new File([currentBlob], "Findus_Stretched.wav", { type: 'audio/wav' });

        if (navigator.share && navigator.canShare && navigator.canShare({ files: [file] })) {
            try {
                await navigator.share({
                    title: 'FindusXStretch Audio',
                    text: 'Check out this stretched audio I made!',
                    files: [file]
                });
                return;
            } catch (err) {
                console.log("Share failed or cancelled:", err);
                // Fallback to download below
            }
        }
        
        // Fallback standard download
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
