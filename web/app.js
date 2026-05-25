document.addEventListener("DOMContentLoaded", () => {
    // --- UI Elements ---
    const audioInput = document.getElementById("audioInput");
    const layersContainer = document.getElementById("layersContainer");
    const processBtn = document.getElementById("processBtn");
    const statusText = document.getElementById("statusText");
    const playerContainer = document.getElementById("playerContainer");
    const downloadBtn = document.getElementById("downloadBtn");
    const presetSelect = document.getElementById("presetSelect");
    const surpriseBtn = document.getElementById("surpriseBtn");
    const themeSelect = document.getElementById("themeSelect");
    const qualitySelect = document.getElementById("qualitySelect");
    const masterPlayBtn = document.getElementById("masterPlayBtn");
    const mixerContainer = document.getElementById("mixerContainer");
    const infiniteToggle = document.getElementById("infiniteToggle");
    
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

    // Toggles
    const reverseToggle = document.getElementById("reverseToggle");
    const freezeToggle = document.getElementById("freezeToggle");

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
                
                // If a layer is active, update its settings
                if (activeLayerId !== null) {
                    const layer = layers.find(l => l.id === activeLayerId);
                    if (layer) {
                        layer.settings[b] = parseFloat(val);
                    }
                }
            });
        }
    });

    [reverseToggle, freezeToggle, infiniteToggle, qualitySelect].forEach(el => {
        if (el) {
            el.addEventListener("change", (e) => {
                if (activeLayerId !== null) {
                    const layer = layers.find(l => l.id === activeLayerId);
                    if (layer) {
                        if (el === reverseToggle) layer.settings.reverse = el.checked;
                        if (el === freezeToggle) layer.settings.freeze = el.checked;
                        if (el === infiniteToggle) layer.settings.infiniteMode = el.checked;
                        if (el === qualitySelect) layer.settings.windowSize = parseInt(el.value);
                    }
                }
            });
        }
    });

    const advancedToggle = document.getElementById("advancedToggle");
    const advancedPanel = document.getElementById("advancedPanel");
    
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

    function updateSlider(name, value) {
        if (ui[name + 'Slider']) {
            ui[name + 'Slider'].value = value;
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
    
    const savedPresets = JSON.parse(localStorage.getItem('findusPresets') || '{}');
    Object.assign(presets, savedPresets);
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
            if (preset.reverse !== undefined) {
                reverseToggle.checked = preset.reverse;
                reverseToggle.dispatchEvent(new Event('change'));
            }
            if (preset.freeze !== undefined) {
                freezeToggle.checked = preset.freeze;
                freezeToggle.dispatchEvent(new Event('change'));
            }
        }
    });

    const savePresetBtn = document.getElementById('savePresetBtn');
    if (savePresetBtn) {
        savePresetBtn.addEventListener('click', () => {
            const name = prompt("Enter a name for your preset:");
            if (!name) return;
            const currentSettings = getCurrentUISettings();
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

    surpriseBtn.addEventListener("click", () => {
        updateSlider('stretch', Math.floor(Math.random() * 15) + 2);
        updateSlider('reverb', (Math.random()).toFixed(2));
        updateSlider('shimmer', (Math.random()).toFixed(2));
        updateSlider('lowpass', Math.floor(Math.random() * 11500) + 500);
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
        reverseToggle.dispatchEvent(new Event('change'));
        freezeToggle.checked = Math.random() > 0.9;
        freezeToggle.dispatchEvent(new Event('change'));
        infiniteToggle.checked = Math.random() > 0.8;
        infiniteToggle.dispatchEvent(new Event('change'));
        presetSelect.value = "default";
    });

    // Theme logic
    function applyTheme(themeName) {
        document.documentElement.setAttribute('data-theme', themeName);
        localStorage.setItem('findusTheme', themeName);
        const style = getComputedStyle(document.documentElement);
        const waveColor = style.getPropertyValue('--waveform-wave').trim() || 'rgba(255, 255, 255, 0.4)';
        const progressColor = style.getPropertyValue('--waveform-progress').trim() || '#8b5cf6';
        
        layers.forEach(layer => {
            if (layer.wavesurfer) {
                layer.wavesurfer.setOptions({ waveColor, progressColor });
            }
        });
    }

    const savedTheme = localStorage.getItem('findusTheme') || 'default';
    themeSelect.value = savedTheme;
    document.documentElement.setAttribute('data-theme', savedTheme);
    themeSelect.addEventListener('change', (e) => applyTheme(e.target.value));

    // --- State & Worker ---
    let worker = new Worker("worker.js?t=" + Date.now());
    let isWorkerReady = false;
    
    let layers = [];
    let activeLayerId = null;

    function getCurrentUISettings() {
        const settings = {};
        binds.forEach(b => {
            if (ui[b + 'Slider']) settings[b] = parseFloat(ui[b + 'Slider'].value);
        });
        settings.reverse = reverseToggle.checked;
        settings.freeze = freezeToggle.checked;
        settings.infiniteMode = infiniteToggle.checked;
        settings.windowSize = parseInt(qualitySelect.value);
        return settings;
    }

    function syncUIToLayer(layer) {
        binds.forEach(b => {
            if (layer.settings[b] !== undefined) {
                updateSlider(b, layer.settings[b]);
            }
        });
        reverseToggle.checked = layer.settings.reverse || false;
        freezeToggle.checked = layer.settings.freeze || false;
        infiniteToggle.checked = layer.settings.infiniteMode || false;
        if (layer.settings.windowSize) {
            qualitySelect.value = layer.settings.windowSize.toString();
        }
    }

    function setActiveLayer(id) {
        activeLayerId = id;
        document.querySelectorAll('.layer-item').forEach(el => {
            if (el.dataset.id == id) {
                el.style.borderColor = 'var(--primary)';
                el.style.background = 'rgba(255, 255, 255, 0.1)';
            } else {
                el.style.borderColor = 'var(--glass-border)';
                el.style.background = 'rgba(0, 0, 0, 0.2)';
            }
        });
        const layer = layers.find(l => l.id === id);
        if (layer) {
            syncUIToLayer(layer);
        }
    }

    function checkReadyState() {
        if (isWorkerReady && layers.length > 0) {
            processBtn.disabled = false;
        } else {
            processBtn.disabled = true;
        }
    }

    worker.onmessage = function(e) {
        const data = e.data;
        if (data.type === 'READY') {
            isWorkerReady = true;
            statusText.textContent = "Engine Ready. Add layers to begin.";
            statusText.classList.remove("pulse");
            checkReadyState();
        } else if (data.type === 'STATUS') {
            statusText.textContent = data.message;
            statusText.classList.add("pulse");
            if (data.progress !== undefined) {
                document.getElementById("progressContainer").style.display = "block";
                document.getElementById("progressBar").style.width = data.progress + "%";
            }
        }
    };

    audioInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function() {
                const newLayer = {
                    id: Date.now(),
                    name: file.name,
                    fileBuffer: new Uint8Array(reader.result),
                    blob: file,
                    wavesurfer: null,
                    wsRegions: null,
                    currentRegion: null,
                    settings: getCurrentUISettings(),
                    processedBlob: null,
                    gainNode: null,
                    bufferSource: null
                };
                layers.push(newLayer);
                renderLayerElement(newLayer);
                setActiveLayer(newLayer.id);
                checkReadyState();
            };
            reader.readAsArrayBuffer(file);
        }
        // Reset input so the same file can be selected again
        e.target.value = '';
    });

    function renderLayerElement(layer) {
        const div = document.createElement("div");
        div.className = "layer-item";
        div.dataset.id = layer.id;
        div.style.border = "2px solid var(--glass-border)";
        div.style.borderRadius = "var(--btn-radius)";
        div.style.padding = "10px";
        div.style.background = "rgba(0,0,0,0.2)";
        div.style.cursor = "pointer";
        div.style.transition = "all 0.2s";

        const header = document.createElement("div");
        header.style.display = "flex";
        header.style.justifyContent = "space-between";
        header.style.alignItems = "center";
        header.style.marginBottom = "10px";
        
        const title = document.createElement("strong");
        title.style.color = "var(--text-main)";
        title.textContent = `🎵 ${layer.name}`;
        
        const deleteBtn = document.createElement("button");
        deleteBtn.textContent = "✖";
        deleteBtn.style.background = "none";
        deleteBtn.style.border = "none";
        deleteBtn.style.color = "var(--text-muted)";
        deleteBtn.style.cursor = "pointer";
        deleteBtn.onclick = (e) => {
            e.stopPropagation();
            layers = layers.filter(l => l.id !== layer.id);
            div.remove();
            if (activeLayerId === layer.id) {
                if (layers.length > 0) {
                    setActiveLayer(layers[0].id);
                } else {
                    activeLayerId = null;
                }
            }
            checkReadyState();
        };

        header.appendChild(title);
        header.appendChild(deleteBtn);
        
        const wfContainer = document.createElement("div");
        wfContainer.id = "waveform-" + layer.id;
        wfContainer.style.width = "100%";
        wfContainer.style.minHeight = "60px";
        
        div.appendChild(header);
        div.appendChild(wfContainer);
        
        div.onclick = () => setActiveLayer(layer.id);
        layersContainer.appendChild(div);

        // Init Wavesurfer for this layer
        const style = getComputedStyle(document.documentElement);
        layer.wavesurfer = WaveSurfer.create({
            container: '#' + wfContainer.id,
            waveColor: style.getPropertyValue('--waveform-wave').trim() || 'rgba(255, 255, 255, 0.4)',
            progressColor: style.getPropertyValue('--waveform-progress').trim() || '#8b5cf6',
            cursorColor: 'transparent',
            barWidth: 2,
            barRadius: 3,
            responsive: true,
            height: 60,
        });

        layer.wsRegions = layer.wavesurfer.registerPlugin(WaveSurfer.Regions.create());
        layer.wavesurfer.loadBlob(layer.blob);

        layer.wavesurfer.on('decode', () => {
            layer.wsRegions.clearRegions();
            const regionContent = document.createElement('div');
            regionContent.style.width = '100%';
            regionContent.style.height = '100%';
            regionContent.style.position = 'relative';
            regionContent.style.pointerEvents = 'none';
            const moveHandle = document.createElement('div');
            moveHandle.className = 'region-move-handle';
            moveHandle.style.pointerEvents = 'auto';
            regionContent.appendChild(moveHandle);

            layer.currentRegion = layer.wsRegions.addRegion({
                start: 0,
                end: layer.wavesurfer.getDuration(),
                content: regionContent,
                resize: true,
                drag: true
            });
        });
        
        layer.wsRegions.on('region-updated', (region) => {
            layer.currentRegion = region;
        });
        
        layer.wsRegions.on('region-out', (region) => {
            if (layer.wavesurfer && region === layer.currentRegion) {
                if (layer.wavesurfer.getCurrentTime() >= region.end - 0.05) {
                    layer.wavesurfer.pause();
                }
            }
        });
    }

    // Process Button Logic (Sequential Worker Processing)
    processBtn.addEventListener("click", async () => {
        if (layers.length === 0 || !isWorkerReady) return;
        
        processBtn.disabled = true;
        playerContainer.style.display = "none";
        document.getElementById("progressContainer").style.display = "block";
        document.getElementById("progressBar").style.width = "0%";
        statusText.classList.add("pulse");
        
        const oldOnMessage = worker.onmessage;
        
        for (let i = 0; i < layers.length; i++) {
            const layer = layers[i];
            statusText.textContent = `Processing Track ${i+1}/${layers.length}: ${layer.name}`;
            
            await new Promise((resolve, reject) => {
                worker.onmessage = function(e) {
                    const data = e.data;
                    if (data.type === 'STATUS') {
                        if (data.progress !== undefined) {
                            document.getElementById("progressBar").style.width = data.progress + "%";
                        }
                    } else if (data.type === 'progress') {
                        const pct = Math.round(data.progress * 100);
                        document.getElementById("progressBar").style.width = pct + "%";
                    } else if (data.type === 'DONE') {
                        layer.processedBlob = new Blob([data.wavBytes], { type: 'audio/wav' });
                        resolve();
                    } else if (data.type === 'ERROR') {
                        reject(data.error);
                    }
                };
                
                const filterMode = layer.settings.lowpass < 12000 ? "Low-pass" : "Off";
                const effects = {
                    reverb_amount: layer.settings.reverb,
                    reverb_enabled: layer.settings.reverb > 0,
                    shimmer_amount: layer.settings.shimmer,
                    shimmer_enabled: layer.settings.shimmer > 0,
                    filter_mode: filterMode,
                    lowpass_hz: layer.settings.lowpass,
                    drive_amount: layer.settings.drive,
                    drive_enabled: layer.settings.drive > 0,
                    texture_amount: layer.settings.texture,
                    texture_enabled: layer.settings.texture > 0,
                    granular_amount: layer.settings.granular,
                    granular_enabled: layer.settings.granular > 0,
                    motion_amount: layer.settings.motion,
                    motion_enabled: layer.settings.motion > 0,
                    chorus_amount: layer.settings.chorus,
                    pitch_drift_amount: layer.settings.pitch_drift,
                    bloom_amount: layer.settings.bloom,
                    delay_amount: layer.settings.delay,
                    autopan_amount: layer.settings.autopan,
                    stereo_width: layer.settings.stereo_width,
                    reverse: layer.settings.reverse,
                    freeze_enabled: layer.settings.freeze,
                    wet_dry: 1.0,
                    input_gain_db: 0.0,
                    limiter_enabled: true
                };
                
                worker.postMessage({
                    type: 'PROCESS',
                    wavBytes: layer.fileBuffer,
                    stretchFactor: layer.settings.stretch,
                    windowSize: layer.settings.windowSize,
                    regionStart: layer.currentRegion ? layer.currentRegion.start : 0,
                    regionEnd: layer.currentRegion ? layer.currentRegion.end : -1,
                    effectsJson: JSON.stringify(effects),
                    infiniteMode: layer.settings.infiniteMode
                });
            });
        }
        
        worker.onmessage = oldOnMessage;
        
        statusText.textContent = "All Tracks Processed!";
        statusText.classList.remove("pulse");
        document.getElementById("progressContainer").style.display = "none";
        processBtn.disabled = false;
        
        setupMixer();
        playerContainer.style.display = "block";
    });

    // --- Multitrack Web Audio Engine ---
    let audioCtx;
    let masterGain;
    let analyser;
    let isPlaying = false;
    let isInfiniteMix = false;
    
    // Automation variables
    let automationFilter;
    let lfoNode;
    let lfoGainNode;
    
    async function setupMixer() {
        if (!audioCtx) {
            audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
        
        if (masterGain) masterGain.disconnect();
        if (automationFilter) automationFilter.disconnect();
        
        masterGain = audioCtx.createGain();
        analyser = audioCtx.createAnalyser();
        analyser.fftSize = 128;
        
        automationFilter = audioCtx.createBiquadFilter();
        automationFilter.type = "lowpass";
        
        masterGain.connect(automationFilter);
        automationFilter.connect(analyser);
        analyser.connect(audioCtx.destination);
        
        // Clean up UI
        mixerContainer.innerHTML = '<h3 style="margin-top: 0; margin-bottom: 5px; color: var(--primary); font-size: 1.1rem; text-align: center;">Mixer</h3>';
        
        isInfiniteMix = layers.some(l => l.settings.infiniteMode);

        for (let i = 0; i < layers.length; i++) {
            const layer = layers[i];
            
            // Create mixer row
            const row = document.createElement("div");
            row.style.display = "flex";
            row.style.alignItems = "center";
            row.style.gap = "10px";
            
            const label = document.createElement("span");
            label.textContent = layer.name;
            label.style.flex = "1";
            label.style.overflow = "hidden";
            label.style.textOverflow = "ellipsis";
            label.style.whiteSpace = "nowrap";
            
            const volSlider = document.createElement("input");
            volSlider.type = "range";
            volSlider.min = "0";
            volSlider.max = "1";
            volSlider.step = "0.01";
            volSlider.value = "0.8"; // Default volume
            volSlider.style.flex = "2";
            
            layer.gainNode = audioCtx.createGain();
            layer.gainNode.gain.value = 0.8;
            layer.gainNode.connect(masterGain);
            
            volSlider.addEventListener("input", (e) => {
                layer.gainNode.gain.value = parseFloat(e.target.value);
            });
            
            row.appendChild(label);
            row.appendChild(volSlider);
            mixerContainer.appendChild(row);
            
            // Decode blob to AudioBuffer
            const arrayBuffer = await layer.processedBlob.arrayBuffer();
            layer.audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
        }
        
        if (isInfiniteMix) {
            automationFilter.frequency.value = 2500;
            if (lfoNode) lfoNode.stop();
            lfoNode = audioCtx.createOscillator();
            lfoNode.type = 'sine';
            lfoNode.frequency.value = 1 / 90;
            lfoGainNode = audioCtx.createGain();
            lfoGainNode.gain.value = 3500;
            lfoNode.connect(lfoGainNode);
            lfoGainNode.connect(automationFilter.detune);
            lfoNode.start();
        } else {
            automationFilter.frequency.value = 22000;
            if (lfoGainNode) lfoGainNode.gain.value = 0;
        }

        drawVisualizer();
        isPlaying = false;
        masterPlayBtn.textContent = "▶ Play All Tracks";
    }

    masterPlayBtn.addEventListener("click", () => {
        if (!audioCtx) return;
        
        if (audioCtx.state === 'suspended') {
            audioCtx.resume();
        }
        
        if (isPlaying) {
            // Stop all
            layers.forEach(l => {
                if (l.bufferSource) {
                    l.bufferSource.stop();
                    l.bufferSource.disconnect();
                    l.bufferSource = null;
                }
            });
            isPlaying = false;
            masterPlayBtn.textContent = "▶ Play All Tracks";
        } else {
            // Play all
            layers.forEach(l => {
                if (l.audioBuffer) {
                    l.bufferSource = audioCtx.createBufferSource();
                    l.bufferSource.buffer = l.audioBuffer;
                    l.bufferSource.loop = l.settings.infiniteMode;
                    l.bufferSource.connect(l.gainNode);
                    l.bufferSource.start(0);
                }
            });
            isPlaying = true;
            masterPlayBtn.textContent = "⏸ Stop All Tracks";
        }
    });

    // Visualizer drawing
    const visualizerCanvas = document.getElementById("visualizer");
    const canvasCtx = visualizerCanvas ? visualizerCanvas.getContext("2d") : null;

    function drawVisualizer() {
        requestAnimationFrame(drawVisualizer);
        if (!visualizerCanvas || !canvasCtx || !analyser) return;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyser.getByteFrequencyData(dataArray);

        canvasCtx.clearRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);

        const style = getComputedStyle(document.documentElement);
        const primaryColor = style.getPropertyValue('--primary').trim() || '#a78bfa';

        const barWidth = (visualizerCanvas.width / bufferLength) * 2;
        let x = 0;

        for(let i = 0; i < bufferLength; i++) {
            const barHeight = dataArray[i] / 2;
            
            canvasCtx.fillStyle = primaryColor;
            canvasCtx.shadowBlur = 10;
            canvasCtx.shadowColor = primaryColor;
            
            const y = (visualizerCanvas.height - barHeight) / 2;
            canvasCtx.fillRect(x, y, barWidth - 1, barHeight);

            x += barWidth;
        }
    }

    downloadBtn.addEventListener("click", () => {
        alert("Downloading a multi-track mix is not fully supported yet in this version. You can only download single tracks.");
    });

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./sw.js')
            .catch(err => console.log('SW registration failed', err));
    }
});
