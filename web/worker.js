importScripts("https://cdn.jsdelivr.net/pyodide/v0.25.0/full/pyodide.js");

let pyodide;
let isReady = false;

async function initPyodide() {
    try {
        postMessage({ type: 'STATUS', message: 'Downloading Engine Core...', progress: 10 });
        pyodide = await loadPyodide();
        
        postMessage({ type: 'STATUS', message: 'Downloading DSP Libraries...', progress: 50 });
        await pyodide.loadPackage(['numpy', 'scipy']);
        
        postMessage({ type: 'STATUS', message: 'Initializing Ambient Engine...', progress: 90 });
        // Fetch and load dsp.py
        const dspResponse = await fetch("dsp.py");
        const dspCode = await dspResponse.text();
        pyodide.FS.writeFile("dsp.py", dspCode);
        
        // Fetch and load web_wrapper.py
        const wrapperResponse = await fetch("web_wrapper.py");
        const wrapperCode = await wrapperResponse.text();
        pyodide.FS.writeFile("web_wrapper.py", wrapperCode);
        
        // Run the wrapper to make functions available
        await pyodide.runPythonAsync(`
            import web_wrapper
        `);
        
        isReady = true;
        postMessage({ type: 'READY', progress: 100 });
    } catch (err) {
        postMessage({ type: 'ERROR', error: err.message });
    }
}

self.onmessage = async (e) => {
    if (!isReady) {
        console.warn("Pyodide not ready yet.");
        return;
    }
    
    if (e.data.type === 'PROCESS') {
        const { wavBytes } = e.data;
        const stretchFactor = e.data.stretchFactor || 8.0;
        const effectsJson = e.data.effectsJson || "{}";
        const windowSize = e.data.windowSize || 8192;
        const regionStart = e.data.regionStart || 0.0;
        const regionEnd = e.data.regionEnd || -1.0;

        self.postMessage({ type: 'progress', message: 'Processing audio through Python...' });
        
        try {
            // Load bytes into Pyodide
            const js_array = new Uint8Array(wavBytes);
            
            // Create a JS proxy for Python to call
            const progressCallback = (progress, message) => {
                postMessage({ type: 'progress', progress: progress, message: message });
            };

            // Call Python function
            const web_wrapper = pyodide.globals.get('web_wrapper');
            const resultBytes = web_wrapper.process_audio(js_array, stretchFactor, effectsJson, windowSize, regionStart, regionEnd, progressCallback);
            
            const jsArray = resultBytes.toJs();
            
            postMessage({
                type: 'DONE',
                wavBytes: jsArray
            });
            
            // Clean up pyodide objects if needed
            if (typeof resultBytes.destroy === 'function') {
                resultBytes.destroy(); 
            }
        } catch (err) {
            console.error(err);
            postMessage({ type: 'ERROR', error: err.message });
        }
    }
};

initPyodide();
