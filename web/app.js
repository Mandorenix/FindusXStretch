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
        "bloom", "delay", "chorus", "stereo_width", "autopan", "pitch_drift",
        "bitcrush", "sub_bass", "tremolo", "phaser"
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
        original: { stretch: 1, reverb: 0.0, shimmer: 0.0, lowpass: 12000, drive: 0.0, texture: 0.0, granular: 0.0, motion: 0.0, bloom: 0.0, delay: 0.0, chorus: 0.0, stereo_width: 1.0, autopan: 0.0, pitch_drift: 0.0, bitcrush: 0.0, sub_bass: 0.0, tremolo: 0.0, phaser: 0.0, reverse: false, freeze: false },
        default: { stretch: 4, reverb: 0.5, shimmer: 0.3, lowpass: 6000, drive: 0.0, texture: 0.0, granular: 0.0, motion: 0.0, bloom: 0.0, delay: 0.0, chorus: 0.0, stereo_width: 1.0, autopan: 0.0, pitch_drift: 0.0, bitcrush: 0.0, sub_bass: 0.0, tremolo: 0.0, phaser: 0.0, reverse: false, freeze: false },
        deep_ambient: { stretch: 12, reverb: 0.9, shimmer: 0.1, lowpass: 2000, drive: 0.1, texture: 0.2, granular: 0.0, motion: 0.1, bloom: 0.5, delay: 0.4, chorus: 0.2, stereo_width: 1.5, autopan: 0.3, pitch_drift: 0.1, bitcrush: 0.0, sub_bass: 0.4, tremolo: 0.2, phaser: 0.0, reverse: false, freeze: false },
        glitchy_tape: { stretch: 3, reverb: 0.2, shimmer: 0.0, lowpass: 4000, drive: 0.6, texture: 0.4, granular: 0.8, motion: 0.7, bloom: 0.0, delay: 0.2, chorus: 0.0, stereo_width: 0.8, autopan: 0.0, pitch_drift: 0.8, bitcrush: 0.5, sub_bass: 0.0, tremolo: 0.0, phaser: 0.3, reverse: false, freeze: false },
        shimmering_ice: { stretch: 8, reverb: 0.8, shimmer: 0.9, lowpass: 8000, drive: 0.0, texture: 0.5, granular: 0.2, motion: 0.4, bloom: 0.3, delay: 0.6, chorus: 0.5, stereo_width: 2.0, autopan: 0.5, pitch_drift: 0.0, bitcrush: 0.0, sub_bass: 0.0, tremolo: 0.4, phaser: 0.6, reverse: false, freeze: false }
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
        updateSlider('autopan', (Math.random()).toFixed(2));
        updateSlider('pitch_drift', (Math.random()).toFixed(2));
        updateSlider('bitcrush', (Math.random()).toFixed(2));
        updateSlider('sub_bass', (Math.random()).toFixed(2));
        updateSlider('tremolo', (Math.random()).toFixed(2));
        updateSlider('phaser', (Math.random()).toFixed(2));
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
        
        const controlsDiv = document.createElement("div");
        controlsDiv.style.display = "flex";
        controlsDiv.style.justifyContent = "space-between";
        controlsDiv.style.marginTop = "10px";
        
        const previewBtn = document.createElement("button");
        previewBtn.className = "btn-secondary";
        previewBtn.textContent = "▶ Preview";
        previewBtn.style.padding = "4px 12px";
        previewBtn.style.fontSize = "0.8rem";
        previewBtn.style.borderRadius = "var(--btn-radius)";
        previewBtn.style.border = "none";
        previewBtn.style.color = "var(--text-main)";
        previewBtn.style.cursor = "pointer";
        
        previewBtn.onclick = (e) => {
            e.stopPropagation();
            if (layer.wavesurfer.isPlaying()) {
                layer.wavesurfer.pause();
                previewBtn.textContent = "▶ Preview";
            } else {
                if (layer.currentRegion) {
                    layer.currentRegion.play();
                } else {
                    layer.wavesurfer.play();
                }
                previewBtn.textContent = "⏸ Pause";
            }
        };
        
        layer.previewBtn = previewBtn;
        
        const zoomControls = document.createElement("div");
        zoomControls.style.display = "flex";
        zoomControls.style.gap = "5px";
        
        const zoomOutBtn = document.createElement("button");
        zoomOutBtn.className = "btn-secondary";
        zoomOutBtn.textContent = "-";
        zoomOutBtn.style.padding = "4px 10px";
        zoomOutBtn.style.borderRadius = "var(--btn-radius)";
        zoomOutBtn.style.border = "none";
        zoomOutBtn.style.color = "var(--text-main)";
        zoomOutBtn.style.cursor = "pointer";
        
        const zoomInBtn = document.createElement("button");
        zoomInBtn.className = "btn-secondary";
        zoomInBtn.textContent = "+";
        zoomInBtn.style.padding = "4px 10px";
        zoomInBtn.style.borderRadius = "var(--btn-radius)";
        zoomInBtn.style.border = "none";
        zoomInBtn.style.color = "var(--text-main)";
        zoomInBtn.style.cursor = "pointer";
        
        zoomControls.appendChild(zoomOutBtn);
        zoomControls.appendChild(zoomInBtn);
        
        controlsDiv.appendChild(previewBtn);
        controlsDiv.appendChild(zoomControls);
        
        div.appendChild(header);
        div.appendChild(wfContainer);
        div.appendChild(controlsDiv);
        
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

        let currentZoom = 50;
        
        zoomInBtn.onclick = (e) => {
            e.stopPropagation();
            currentZoom += 10;
            if (currentZoom > 1000) currentZoom = 1000;
            layer.wavesurfer.zoom(currentZoom);
        };
        
        zoomOutBtn.onclick = (e) => {
            e.stopPropagation();
            currentZoom -= 10;
            if (currentZoom < 10) currentZoom = 10;
            layer.wavesurfer.zoom(currentZoom);
        };

        wfContainer.addEventListener('wheel', (e) => {
            e.preventDefault();
            if (e.deltaY < 0) {
                currentZoom += 10;
            } else {
                currentZoom -= 10;
            }
            if (currentZoom < 10) currentZoom = 10;
            if (currentZoom > 1000) currentZoom = 1000;
            layer.wavesurfer.zoom(currentZoom);
        }, { passive: false });

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
                color: 'rgba(167, 139, 250, 0.3)',
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
                    if (layer.previewBtn) layer.previewBtn.textContent = "▶ Preview";
                }
            }
        });

        layer.wavesurfer.on('pause', () => {
            if (layer.previewBtn) layer.previewBtn.textContent = "▶ Preview";
        });
        
        layer.wavesurfer.on('finish', () => {
            if (layer.previewBtn) layer.previewBtn.textContent = "▶ Preview";
        });
    }

    // Process Button Logic (Sequential Worker Processing)
    processBtn.addEventListener("click", async () => {
        if (layers.length === 0 || !isWorkerReady) return;
        
        // Stop any playing audio before processing
        if (isPlaying) {
            layers.forEach(l => {
                if (l.bufferSource) {
                    try { l.bufferSource.stop(); } catch(e) {}
                    l.bufferSource.disconnect();
                    l.bufferSource = null;
                }
            });
            isPlaying = false;
            masterPlayBtn.textContent = "▶ Play All Tracks";
            cancelAnimationFrame(playbackUpdateTimer);
        }
        
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
                        statusText.textContent = `Processing Track ${i+1}/${layers.length}: ${layer.name} (${pct}%)`;
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
                    bitcrush_amount: layer.settings.bitcrush,
                    bitcrush_enabled: layer.settings.bitcrush > 0,
                    sub_bass_amount: layer.settings.sub_bass,
                    sub_bass_enabled: layer.settings.sub_bass > 0,
                    tremolo_amount: layer.settings.tremolo,
                    tremolo_enabled: layer.settings.tremolo > 0,
                    phaser_amount: layer.settings.phaser,
                    phaser_enabled: layer.settings.phaser > 0,
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
    
    // Playback state for seeking
    let masterPlaybackOffset = 0;
    let masterPlaybackStartTime = 0;
    let masterPlaybackMaxDuration = 0;
    let playbackUpdateTimer;
    
    function formatTime(secs) {
        if (!isFinite(secs)) return "∞";
        const m = Math.floor(secs / 60);
        const s = Math.floor(secs % 60).toString().padStart(2, '0');
        return `${m}:${s}`;
    }
    
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
        analyser.smoothingTimeConstant = 0.85; // Smoother transitions
        
        automationFilter = audioCtx.createBiquadFilter();
        automationFilter.type = "lowpass";
        
        masterGain.connect(automationFilter);
        automationFilter.connect(analyser);
        analyser.connect(audioCtx.destination);
        
        // Clean up UI
        mixerContainer.innerHTML = '<h3 style="margin-top: 0; margin-bottom: 5px; color: var(--primary); font-size: 1.1rem; text-align: center;">Mixer</h3>';
        
        isInfiniteMix = layers.some(l => l.settings.infiniteMode);
        
        function updateMuteSolo() {
            const anySoloed = layers.some(l => l.isSoloed);
            layers.forEach(l => {
                if (l.gainNode) {
                    if (l.isMuted || (anySoloed && !l.isSoloed)) {
                        l.gainNode.gain.value = 0;
                    } else {
                        l.gainNode.gain.value = l.volume;
                    }
                }
            });
        }

        for (let i = 0; i < layers.length; i++) {
            const layer = layers[i];
            
            // Decode blob to AudioBuffer first to get duration
            const arrayBuffer = await layer.processedBlob.arrayBuffer();
            layer.audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
            
            const mins = Math.floor(layer.audioBuffer.duration / 60);
            const secs = Math.floor(layer.audioBuffer.duration % 60).toString().padStart(2, '0');
            const durationText = layer.settings.infiniteMode ? "∞ min" : `${mins}:${secs} min`;
            
            // Create mixer row
            const row = document.createElement("div");
            row.style.display = "flex";
            row.style.alignItems = "center";
            row.style.gap = "8px";
            row.style.flexWrap = "wrap";
            
            const label = document.createElement("span");
            label.textContent = layer.name;
            label.style.flex = "1";
            label.style.minWidth = "100px";
            label.style.overflow = "hidden";
            label.style.textOverflow = "ellipsis";
            label.style.whiteSpace = "nowrap";
            label.title = layer.name;
            
            const durLabel = document.createElement("span");
            durLabel.textContent = `(${durationText})`;
            durLabel.style.color = "var(--text-muted)";
            durLabel.style.fontSize = "0.8rem";
            durLabel.style.marginRight = "10px";
            
            layer.isMuted = false;
            layer.isSoloed = false;
            layer.volume = 0.8;
            
            const muteBtn = document.createElement("button");
            muteBtn.className = "btn-secondary";
            muteBtn.textContent = "M";
            muteBtn.style.padding = "4px 8px";
            muteBtn.style.borderRadius = "4px";
            muteBtn.style.fontWeight = "bold";
            muteBtn.onclick = () => {
                layer.isMuted = !layer.isMuted;
                muteBtn.style.background = layer.isMuted ? "var(--accent)" : "";
                updateMuteSolo();
            };
            
            const soloBtn = document.createElement("button");
            soloBtn.className = "btn-secondary";
            soloBtn.textContent = "S";
            soloBtn.style.padding = "4px 8px";
            soloBtn.style.borderRadius = "4px";
            soloBtn.style.fontWeight = "bold";
            soloBtn.onclick = () => {
                layer.isSoloed = !layer.isSoloed;
                soloBtn.style.background = layer.isSoloed ? "var(--primary)" : "";
                updateMuteSolo();
            };
            
            const volSlider = document.createElement("input");
            volSlider.type = "range";
            volSlider.min = "0";
            volSlider.max = "1";
            volSlider.step = "0.01";
            volSlider.value = "0.8"; // Default volume
            volSlider.style.flex = "2";
            volSlider.style.minWidth = "80px";
            
            layer.gainNode = audioCtx.createGain();
            layer.gainNode.gain.value = 0.8;
            layer.gainNode.connect(masterGain);
            
            volSlider.addEventListener("input", (e) => {
                layer.volume = parseFloat(e.target.value);
                updateMuteSolo();
            });
            
            row.appendChild(label);
            row.appendChild(durLabel);
            row.appendChild(muteBtn);
            row.appendChild(soloBtn);
            row.appendChild(volSlider);
            mixerContainer.appendChild(row);
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

        // Setup Seek Slider bounds
        masterPlaybackMaxDuration = 0;
        layers.forEach(l => {
            if (l.audioBuffer && l.audioBuffer.duration > masterPlaybackMaxDuration) {
                masterPlaybackMaxDuration = l.audioBuffer.duration;
            }
        });
        
        const slider = document.getElementById('masterSeekSlider');
        if (isInfiniteMix) {
            masterPlaybackMaxDuration = Infinity;
            slider.disabled = true;
            document.getElementById('totalTimeDisplay').textContent = "∞ min";
        } else {
            slider.disabled = false;
            slider.max = masterPlaybackMaxDuration;
            document.getElementById('totalTimeDisplay').textContent = formatTime(masterPlaybackMaxDuration);
        }
        
        masterPlaybackOffset = 0;
        slider.value = 0;
        document.getElementById('currentTimeDisplay').textContent = "0:00";
        cancelAnimationFrame(playbackUpdateTimer);

        init3DVisualizer();
        drawVisualizer();
        isPlaying = false;
        masterPlayBtn.textContent = "▶ Play All Tracks";
    }

    function updatePlaybackProgress() {
        if (!isPlaying) return;
        const current = masterPlaybackOffset + (audioCtx.currentTime - masterPlaybackStartTime);
        
        if (current >= masterPlaybackMaxDuration && !isInfiniteMix) {
            document.getElementById("masterPlayBtn").click(); // auto stop
            masterPlaybackOffset = masterPlaybackMaxDuration;
            document.getElementById('currentTimeDisplay').textContent = formatTime(masterPlaybackMaxDuration);
            document.getElementById('masterSeekSlider').value = masterPlaybackMaxDuration;
            return;
        }

        document.getElementById('currentTimeDisplay').textContent = formatTime(current);
        document.getElementById('masterSeekSlider').value = current;
        
        playbackUpdateTimer = requestAnimationFrame(updatePlaybackProgress);
    }
    
    document.getElementById('masterSeekSlider').addEventListener('input', (e) => {
        masterPlaybackOffset = parseFloat(e.target.value);
        document.getElementById('currentTimeDisplay').textContent = formatTime(masterPlaybackOffset);
        
        if (isPlaying) {
            layers.forEach(l => {
                if (l.bufferSource) {
                    l.bufferSource.stop();
                    l.bufferSource.disconnect();
                    l.bufferSource = null;
                }
            });
            masterPlaybackStartTime = audioCtx.currentTime;
            layers.forEach(l => {
                if (l.audioBuffer) {
                    l.bufferSource = audioCtx.createBufferSource();
                    l.bufferSource.buffer = l.audioBuffer;
                    l.bufferSource.loop = l.settings.infiniteMode;
                    l.bufferSource.connect(l.gainNode);
                    l.bufferSource.start(0, masterPlaybackOffset);
                }
            });
        }
    });

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
            masterPlaybackOffset += audioCtx.currentTime - masterPlaybackStartTime;
            cancelAnimationFrame(playbackUpdateTimer);
            masterPlayBtn.textContent = "▶ Play All Tracks";
        } else {
            // Play all
            if (masterPlaybackOffset >= masterPlaybackMaxDuration && !isInfiniteMix) {
                masterPlaybackOffset = 0; // restart if at end
            }
            layers.forEach(l => {
                if (l.audioBuffer) {
                    l.bufferSource = audioCtx.createBufferSource();
                    l.bufferSource.buffer = l.audioBuffer;
                    l.bufferSource.loop = l.settings.infiniteMode;
                    l.bufferSource.connect(l.gainNode);
                    l.bufferSource.start(0, masterPlaybackOffset);
                }
            });
            isPlaying = true;
            masterPlaybackStartTime = audioCtx.currentTime;
            updatePlaybackProgress();
            masterPlayBtn.textContent = "⏸ Stop All Tracks";
        }
    });

    // --- 3D & 2D Visualizer ---
    const visualizer3dContainer = document.getElementById("visualizer3d");
    const visualizer2dCanvas = document.getElementById("visualizer2d");
    const canvas2dCtx = visualizer2dCanvas ? visualizer2dCanvas.getContext("2d") : null;
    const toggleVisBtn = document.getElementById("toggleVisBtn");
    
    let visualizerMode = '3d';
    let current3DTheme = 'cosmic';
    let scene, camera, renderer, visualizerObjects = {};
    let is3DInitialized = false;

    const visThemeSelect = document.getElementById('visThemeSelect');
    if (visThemeSelect) {
        visThemeSelect.addEventListener('change', (e) => {
            const val = e.target.value; // e.g. "3d_cosmic"
            const parts = val.split('_');
            visualizerMode = parts[0];
            current3DTheme = parts[1];
            
            if (visualizerMode === '3d') {
                visualizer3dContainer.style.display = 'block';
                visualizer2dCanvas.style.display = 'none';
                if (is3DInitialized) {
                    setup3DScene(current3DTheme);
                }
            } else {
                visualizer3dContainer.style.display = 'none';
                visualizer2dCanvas.style.display = 'block';
            }
        });
    }

    function init3DVisualizer() {
        if (is3DInitialized || !visualizer3dContainer) return;
        
        scene = new THREE.Scene();
        scene.fog = new THREE.FogExp2(0x000000, 0.005);
        
        const width = visualizer3dContainer.clientWidth || 400;
        const height = visualizer3dContainer.clientHeight || 150;
        
        camera = new THREE.PerspectiveCamera(75, width / height, 0.1, 1000);
        camera.position.z = 100;
        
        renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(width, height);
        renderer.setPixelRatio(window.devicePixelRatio);
        visualizer3dContainer.appendChild(renderer.domElement);
        
        is3DInitialized = true;
        setup3DScene(current3DTheme);
        
        window.addEventListener('resize', () => {
            if (visualizer3dContainer.clientWidth > 0) {
                const w = visualizer3dContainer.clientWidth;
                const h = visualizer3dContainer.clientHeight || 150;
                camera.aspect = w / h;
                camera.updateProjectionMatrix();
                renderer.setSize(w, h);
            }
        });
    }

    function setup3DScene(theme) {
        while(scene.children.length > 0){ 
            scene.remove(scene.children[0]); 
        }
        visualizerObjects = {};
        
        const style = getComputedStyle(document.documentElement);
        const primaryHex = style.getPropertyValue('--primary').trim() || '#a78bfa';
        const accentHex = style.getPropertyValue('--accent').trim() || '#f472b6';
        const secondaryHex = style.getPropertyValue('--secondary').trim() || '#10b981';
        
        if (theme === 'cosmic') {
            camera.position.set(0, 0, 100);
            camera.lookAt(0, 0, 0);
            scene.fog.density = 0.005;
            
            const particleCount = 2000;
            const geom = new THREE.BufferGeometry();
            const pos = new Float32Array(particleCount * 3);
            for(let i = 0; i < particleCount; i++) {
                const r = 10 + Math.random() * 70;
                const theta = Math.random() * 2 * Math.PI;
                const phi = Math.acos(2 * Math.random() - 1);
                pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
                pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
                pos[i * 3 + 2] = r * Math.cos(phi);
            }
            geom.setAttribute('position', new THREE.BufferAttribute(pos, 3));
            const mat = new THREE.PointsMaterial({ color: new THREE.Color(primaryHex), size: 2.0, transparent: true, blending: THREE.AdditiveBlending });
            const particles = new THREE.Points(geom, mat);
            scene.add(particles);
            visualizerObjects.particles = particles;
        } 
        else if (theme === 'terrain') {
            camera.position.set(0, 30, 80);
            camera.lookAt(0, 0, 0);
            scene.fog.density = 0.015;
            
            const geom = new THREE.PlaneGeometry(200, 200, 32, 32);
            geom.rotateX(-Math.PI / 2);
            const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(secondaryHex), wireframe: true, transparent: true, opacity: 0.5 });
            const terrain = new THREE.Mesh(geom, mat);
            scene.add(terrain);
            visualizerObjects.terrain = terrain;
        }
        else if (theme === 'rings') {
            camera.position.set(0, 0, 120);
            camera.lookAt(0, 0, 0);
            scene.fog.density = 0.002;
            
            visualizerObjects.rings = [];
            const colors = [primaryHex, accentHex, secondaryHex];
            for(let i = 0; i < 3; i++) {
                const geom = new THREE.TorusGeometry(20 + i*15, 0.5, 16, 100);
                const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(colors[i]), wireframe: true });
                const ring = new THREE.Mesh(geom, mat);
                ring.rotation.x = Math.random() * Math.PI;
                ring.rotation.y = Math.random() * Math.PI;
                scene.add(ring);
                visualizerObjects.rings.push(ring);
            }
        }
        else if (theme === 'tunnel') {
            camera.position.set(0, 0, 50);
            camera.lookAt(0, 0, 0);
            scene.fog.density = 0.01;
            
            const geom = new THREE.CylinderGeometry(15, 15, 300, 32, 32, true);
            geom.rotateX(Math.PI / 2);
            const mat = new THREE.MeshBasicMaterial({ color: new THREE.Color(primaryHex), wireframe: true, transparent: true, opacity: 0.3 });
            const tunnel = new THREE.Mesh(geom, mat);
            scene.add(tunnel);
            visualizerObjects.tunnel = tunnel;
        }
        else if (theme === 'plasma') {
            camera.position.set(0, 0, 80);
            camera.lookAt(0, 0, 0);
            scene.fog.density = 0.005;
            
            const geom = new THREE.IcosahedronGeometry(20, 3);
            const mat = new THREE.PointsMaterial({ color: new THREE.Color(accentHex), size: 1.5, transparent: true, blending: THREE.AdditiveBlending });
            const plasma = new THREE.Points(geom, mat);
            scene.add(plasma);
            visualizerObjects.plasma = plasma;
            visualizerObjects.plasmaBasePositions = new Float32Array(geom.attributes.position.array);
        }
        else if (theme === 'grid') {
            camera.position.set(0, 10, 60);
            camera.lookAt(0, 5, 0);
            scene.fog.density = 0.02;
            scene.fog.color = new THREE.Color(0x000000);
            
            const geom = new THREE.PlaneGeometry(200, 200, 40, 40);
            geom.rotateX(-Math.PI / 2);
            const mat = new THREE.LineBasicMaterial({ color: new THREE.Color(accentHex), transparent: true, opacity: 0.6 });
            const grid = new THREE.LineSegments(new THREE.WireframeGeometry(geom), mat);
            scene.add(grid);
            visualizerObjects.grid = grid;
        }
    }

    function drawVisualizer() {
        requestAnimationFrame(drawVisualizer);
        if (!analyser) return;

        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        analyser.getByteFrequencyData(dataArray);

        if (visualizerMode === '3d' && is3DInitialized) {
            let sum = 0, bassSum = 0, midSum = 0;
            for(let i = 0; i < bufferLength; i++) {
                sum += dataArray[i];
                if (i < bufferLength * 0.1) bassSum += dataArray[i];
                else if (i < bufferLength * 0.5) midSum += dataArray[i];
            }
            const avgFreq = sum / bufferLength;
            const intensity = avgFreq / 255.0;
            const bassIntensity = (bassSum / (bufferLength * 0.1)) / 255.0 || 0;
            const midIntensity = (midSum / (bufferLength * 0.4)) / 255.0 || 0;

            const style = getComputedStyle(document.documentElement);
            const primaryHex = style.getPropertyValue('--primary').trim() || '#a78bfa';

            if (current3DTheme === 'cosmic' && visualizerObjects.particles) {
                visualizerObjects.particles.rotation.y += 0.001 + (intensity * 0.01);
                visualizerObjects.particles.rotation.x += 0.0005 + (intensity * 0.005);
                const scale = 1.0 + (intensity * 0.6);
                visualizerObjects.particles.scale.set(scale, scale, scale);
                visualizerObjects.particles.material.color.set(primaryHex);
                visualizerObjects.particles.material.opacity = 0.4 + (intensity * 0.6);
            }
            else if (current3DTheme === 'terrain' && visualizerObjects.terrain) {
                const positions = visualizerObjects.terrain.geometry.attributes.position.array;
                const count = visualizerObjects.terrain.geometry.attributes.position.count;
                
                for(let i = 0; i < count; i++) {
                    let z = positions[i*3 + 2];
                    z += 0.5 + (bassIntensity * 1.5);
                    if (z > 100) z -= 200;
                    positions[i*3 + 2] = z;
                    
                    const dataIdx = Math.floor(Math.abs(positions[i*3] / 100) * bufferLength);
                    const val = dataArray[dataIdx] || 0;
                    const targetY = (val / 255.0) * 30.0 * intensity;
                    positions[i*3 + 1] += (targetY - positions[i*3 + 1]) * 0.1;
                }
                visualizerObjects.terrain.geometry.attributes.position.needsUpdate = true;
            }
            else if (current3DTheme === 'rings' && visualizerObjects.rings) {
                visualizerObjects.rings.forEach((ring, i) => {
                    ring.rotation.x += 0.01 * (i+1) + (bassIntensity * 0.05);
                    ring.rotation.y += 0.005 * (i+1) + (midIntensity * 0.05);
                    const scale = 1.0 + (intensity * 0.3 * (i+1));
                    ring.scale.set(scale, scale, scale);
                });
            }
            else if (current3DTheme === 'tunnel' && visualizerObjects.tunnel) {
                visualizerObjects.tunnel.rotation.z += 0.005 + (midIntensity * 0.02);
                camera.position.z -= 0.5 + (bassIntensity * 2.0);
                if (camera.position.z < -50) camera.position.z = 50;
                
                const scale = 1.0 + (intensity * 0.2);
                visualizerObjects.tunnel.scale.set(scale, scale, 1.0);
                visualizerObjects.tunnel.material.color.set(primaryHex);
            }
            else if (current3DTheme === 'plasma' && visualizerObjects.plasma) {
                visualizerObjects.plasma.rotation.y += 0.005 + (midIntensity * 0.01);
                visualizerObjects.plasma.rotation.z += 0.002 + (bassIntensity * 0.01);
                
                const positions = visualizerObjects.plasma.geometry.attributes.position.array;
                const base = visualizerObjects.plasmaBasePositions;
                const count = visualizerObjects.plasma.geometry.attributes.position.count;
                
                for(let i=0; i<count; i++) {
                    const dataIdx = Math.floor((i / count) * bufferLength);
                    const val = dataArray[dataIdx] || 0;
                    const deform = 1.0 + ((val / 255.0) * bassIntensity * 1.5);
                    
                    positions[i*3] = base[i*3] * deform;
                    positions[i*3+1] = base[i*3+1] * deform;
                    positions[i*3+2] = base[i*3+2] * deform;
                }
                visualizerObjects.plasma.geometry.attributes.position.needsUpdate = true;
                visualizerObjects.plasma.material.color.set(Math.random() > 0.9 ? secondaryHex : accentHex);
            }
            else if (current3DTheme === 'grid' && visualizerObjects.grid) {
                visualizerObjects.grid.position.z += 0.5 + (bassIntensity * 2.0);
                if (visualizerObjects.grid.position.z > 20) visualizerObjects.grid.position.z = 0;
                
                const scale = 1.0 + (intensity * 0.1);
                visualizerObjects.grid.scale.set(1.0, scale, 1.0);
                visualizerObjects.grid.material.color.set(bassIntensity > 0.6 ? primaryHex : accentHex);
            }

            renderer.render(scene, camera);
        } else if (visualizerMode === '2d' && canvas2dCtx) {
            canvas2dCtx.clearRect(0, 0, visualizer2dCanvas.width, visualizer2dCanvas.height);
            const w = visualizer2dCanvas.width;
            const h = visualizer2dCanvas.height;
            
            const style = getComputedStyle(document.documentElement);
            const primaryHex = style.getPropertyValue('--primary').trim() || '#a78bfa';
            const accentHex = style.getPropertyValue('--accent').trim() || '#f472b6';
            
            canvas2dCtx.fillStyle = primaryHex;
            canvas2dCtx.strokeStyle = accentHex;
            canvas2dCtx.lineWidth = 2;
            canvas2dCtx.shadowBlur = 10;
            canvas2dCtx.shadowColor = primaryHex;

            if (current3DTheme === 'spectrum') {
                const barWidth = (w / bufferLength) * 2.5;
                let x = 0;
                for(let i = 0; i < bufferLength; i++) {
                    const barHeight = (dataArray[i] / 255.0) * h;
                    canvas2dCtx.fillRect(x, h - barHeight, barWidth - 1, barHeight);
                    x += barWidth;
                }
            }
            else if (current3DTheme === 'oscilloscope') {
                canvas2dCtx.beginPath();
                const sliceWidth = w * 1.0 / bufferLength;
                let x = 0;
                for(let i = 0; i < bufferLength; i++) {
                    const v = dataArray[i] / 128.0; 
                    const y = v * h / 2;
                    if(i === 0) canvas2dCtx.moveTo(x, y);
                    else canvas2dCtx.lineTo(x, y);
                    x += sliceWidth;
                }
                canvas2dCtx.stroke();
            }
            else if (current3DTheme === 'circular') {
                const centerX = w / 2;
                const centerY = h / 2;
                const radius = h / 4;
                
                canvas2dCtx.beginPath();
                for(let i = 0; i < bufferLength; i++) {
                    const rads = Math.PI * 2 / bufferLength;
                    const barHeight = (dataArray[i] / 255.0) * (h / 2);
                    const rx = centerX + Math.cos(rads * i) * (radius + barHeight);
                    const ry = centerY + Math.sin(rads * i) * (radius + barHeight);
                    
                    if (i === 0) canvas2dCtx.moveTo(rx, ry);
                    else canvas2dCtx.lineTo(rx, ry);
                }
                canvas2dCtx.closePath();
                canvas2dCtx.stroke();
            }
            else if (current3DTheme === 'symmetry') {
                const barWidth = (w / bufferLength) * 2;
                let x = 0;
                for(let i = 0; i < bufferLength; i++) {
                    const barHeight = (dataArray[i] / 255.0) * (h / 2);
                    const yCenter = h / 2;
                    canvas2dCtx.fillRect(x, yCenter - barHeight, barWidth - 1, barHeight * 2);
                    x += barWidth;
                }
            }
        }
    }

    function audioBufferToWav(buffer) {
        let numOfChan = buffer.numberOfChannels,
            length = buffer.length * numOfChan * 2 + 44,
            bufferArray = new ArrayBuffer(length),
            view = new DataView(bufferArray),
            channels = [], i, sample,
            offset = 0,
            pos = 0;

        setUint32(0x46464952); // "RIFF"
        setUint32(length - 8); // file length - 8
        setUint32(0x45564157); // "WAVE"
        setUint32(0x20746d66); // "fmt " chunk
        setUint32(16); // length = 16
        setUint16(1); // PCM (uncompressed)
        setUint16(numOfChan);
        setUint32(buffer.sampleRate);
        setUint32(buffer.sampleRate * 2 * numOfChan); // avg. bytes/sec
        setUint16(numOfChan * 2); // block-align
        setUint16(16); // 16-bit

        setUint32(0x61746164); // "data" - chunk
        setUint32(length - pos - 4); // chunk length

        for(i = 0; i < buffer.numberOfChannels; i++)
            channels.push(buffer.getChannelData(i));

        while(pos < buffer.length) {
            for(i = 0; i < numOfChan; i++) {
                sample = Math.max(-1, Math.min(1, channels[i][pos])); // clamp
                sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767)|0; // scale
                view.setInt16(offset, sample, true); // write 16-bit
                offset += 2;
            }
            pos++;
        }

        return new Blob([bufferArray], {type: "audio/wav"});

        function setUint16(data) {
            view.setUint16(offset, data, true);
            offset += 2;
        }

        function setUint32(data) {
            view.setUint32(offset, data, true);
            offset += 4;
        }
    }

    downloadBtn.addEventListener("click", async () => {
        if (layers.length === 0 || !layers[0].audioBuffer) return;
        
        const prevText = downloadBtn.innerHTML;
        downloadBtn.textContent = "Rendering Mix (Please Wait)...";
        downloadBtn.disabled = true;

        try {
            let maxDuration = 0;
            layers.forEach(l => {
                if (l.audioBuffer && l.audioBuffer.duration > maxDuration) {
                    maxDuration = l.audioBuffer.duration;
                }
            });
            
            const sampleRate = layers[0].audioBuffer.sampleRate;
            const offlineCtx = new OfflineAudioContext(2, sampleRate * maxDuration, sampleRate);
            
            const offlineMasterGain = offlineCtx.createGain();
            const offlineFilter = offlineCtx.createBiquadFilter();
            offlineFilter.type = "lowpass";
            
            offlineMasterGain.connect(offlineFilter);
            offlineFilter.connect(offlineCtx.destination);
            
            layers.forEach(l => {
                if (l.audioBuffer) {
                    const source = offlineCtx.createBufferSource();
                    source.buffer = l.audioBuffer;
                    source.loop = l.settings.infiniteMode;
                    
                    const gainNode = offlineCtx.createGain();
                    
                    const anySoloed = layers.some(lr => lr.isSoloed);
                    if (l.isMuted || (anySoloed && !l.isSoloed)) {
                        gainNode.gain.value = 0;
                    } else {
                        gainNode.gain.value = l.volume !== undefined ? l.volume : l.gainNode.gain.value;
                    }
                    
                    source.connect(gainNode);
                    gainNode.connect(offlineMasterGain);
                    
                    source.start(0);
                }
            });
            
            if (isInfiniteMix) {
                offlineFilter.frequency.value = 2500;
                const offlineLfo = offlineCtx.createOscillator();
                offlineLfo.type = 'sine';
                offlineLfo.frequency.value = 1 / 90;
                const offlineLfoGain = offlineCtx.createGain();
                offlineLfoGain.gain.value = 3500;
                offlineLfo.connect(offlineLfoGain);
                offlineLfoGain.connect(offlineFilter.detune);
                offlineLfo.start();
            } else {
                offlineFilter.frequency.value = 22000;
            }
            
            const renderedBuffer = await offlineCtx.startRendering();
            const wavBlob = audioBufferToWav(renderedBuffer);
            
            const a = document.createElement("a");
            a.href = URL.createObjectURL(wavBlob);
            a.download = "Findus_Multitrack_Mix.wav";
            a.click();
            
        } catch (err) {
            console.error(err);
            alert("Error rendering mix: " + err.message);
        }
        
        downloadBtn.innerHTML = prevText;
        downloadBtn.disabled = false;
    });

    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./sw.js')
            .catch(err => console.log('SW registration failed', err));

    }
});
