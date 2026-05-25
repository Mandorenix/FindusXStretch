# FINDUS>x<STRETCHING

An offline ambient/drone workstation for extreme time-stretching with a Paulstretch-inspired engine.

## Features

- drag-select a preview/export region directly in the waveform
- microphone recording straight to WAV, with optional auto-load into the app
- recent-takes list for quickly reloading recorded material
- recent-takes management for loading, renaming, deleting, and reopening take folders
- recording controls for sample rate, mono/stereo selection, live level and peak hold
- keyboard shortcuts for core transport, tabs, and waveform navigation
- preview the selected region in-app with loop playback
- stretch from `2x` to `64x`
- quality profiles for performance vs. fidelity
- effect chain with low-pass, reverb, shimmer, delay, stereo width, reverse, freeze, and wet/dry
- factory presets plus user presets saved to local JSON
- autosave of the latest app state between launches
- compact tabbed workspace with a toolbar for common actions
- float WAV export

## Requirements

- Python 3.11+
- `numpy`
- `scipy`
- `soundfile`
- `PySide6`

Install dependencies:

```bash
pip install -r requirements.txt
```

Optional recommended packages:

```bash
pip install -r requirements-optional.txt
```

What they are for:

- `pyqtgraph` for future waveform and plotting upgrades in the GUI
- `pyinstaller` for building a Windows executable
- `sounddevice` for advanced Windows audio routing, host API selection, and non-default input/output device control

Run the automated test suite:

```bash
python -m pytest -q
```

## Start the app

```bash
python app.py
```

On Windows you can also use `start.bat` for a launcher that can install dependencies, run tests, open a venv shell, build releases, and start the app.
It can also install the optional recommended package set and explain the menu options directly inside the launcher.

Launcher menu summary:

- `1` start the app directly
- `2` quick start: install base deps, run tests, start the app
- `3` install base dependencies from `requirements.txt`
- `4` install optional recommended extras from `requirements-optional.txt`
- `5` run the test suite
- `6` create `.venv`
- `7` open a new shell with `.venv` activated
- `8` open a Python REPL
- `9` run a compile check over the codebase
- `10` build the Windows app with PyInstaller
- `11` create a release zip from the built app
- `12` build a Windows installer with Inno Setup
- `13` show installed Python packages
- `14` open the project folder in Explorer
- `15` open `README.md`
- `16` explain the optional extras
- `17` full release: patch-bump version, test, build exe, build installer, create zip, update logs
- `18` clean generated `build/` and `dist/` folders
- `19` minor release: minor-bump version, then run the full release flow
- `20` explain all launcher choices in plain language

## Build a Windows executable

Install the optional packaging tools first:

```bash
pip install -r requirements-optional.txt
```

Then either:

- use option `10` in `start.bat`
- or run PyInstaller manually:

```bash
python -m PyInstaller --noconfirm --clean findus_stretching.spec
```

The packaged app will be written to:

```text
dist/findus_stretching
```

Packaging assets included in the repo:

- `findus_stretching.spec` for repeatable PyInstaller builds
- `findus_stretching_installer.iss` for building a Windows installer with Inno Setup
- `assets/findus_stretching_icon.ico` as the Windows app icon
- `assets/findus_stretching_icon.png` as the source artwork preview
- `assets/version_info.txt` for Windows `.exe` metadata such as product name and version

## Build a Windows installer

Install Inno Setup 6, then use:

- option `12` in `start.bat`
- or compile manually with:

```bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" findus_stretching_installer.iss
```

The installer will be written to:

```text
dist/installer
```

For testing on another computer, the simplest shareable files are:

- `dist/installer/findus_stretching_setup_v0.1.1.exe`
- or `dist/release/findus_stretching_v0.1.1.zip`

## Release workflow

Recommended release flow for Windows:

1. Install base dependencies:

```bash
pip install -r requirements.txt
```

2. Install optional packaging tools:

```bash
pip install -r requirements-optional.txt
```

3. Run tests:

```bash
python -m pytest -q
```

4. Build the app:

```bash
python -m PyInstaller --noconfirm --clean findus_stretching.spec
```

5. Optionally create a shareable zip from the packaged folder.

In `start.bat`, use option `11`, `17`, or `19`.

6. Smoke test the packaged app from:

```text
dist/findus_stretching/findus_stretching.exe
```

7. If the release is meant for users, ship either:

- the whole `dist/findus_stretching` folder
- or the generated zip from `dist/release`

Notes:

- `build/` and `dist/` are generated artifacts and should not be committed.
- local autosave and user preset JSON files are ignored so development state does not leak into releases.
- `start.bat` can now bump patch or minor version automatically during release.
- release shortcuts also write `dist/release/release_log.txt`, update `CHANGELOG_RELEASES.md`, and copy the latest installer/zip to stable filenames.
- current packaged app version is `0.1.1` until the next release command is run.

## Workflow

- Load an audio file.
- Or record a new WAV from your selected input device.
- Drag a region in the waveform to define the source area.
- Use the toolbar for fast open/record/preview/render actions.
- Use recent takes in the `Source` tab to reload recordings or derive render filenames quickly.
- Use `Zoom To Selection`, `Show Full`, or `Reset Selection` to navigate.
- Switch between the `Source`, `Stretch`, `Effects`, and `Presets` tabs to work without crowding the main view.
- Adjust stretch, quality, preview length, and effects.
- Turn on `Freeze selection` to build a sustained drone from the chosen region.
- Increase `Shimmer` for a pitch-up ambient reverb layer.
- Use `Loop` when auditioning textures repeatedly.
- Save your own presets with `Save New`, update them later, or duplicate/delete user presets.
- If autosaved files or presets are missing on launch, the app falls back safely and reports it in the status bar.
- Export the current sound with `Render WAV`.

## Local data files

- user presets are stored in `findus_stretching_presets.json`
- autosaved app state is stored in `findus_stretching_state.json`

## Project structure

- `app.py` starts the GUI
- `paulstretch_light/gui.py` contains the desktop UI, waveform editor, and playback flow
- `paulstretch_light/renderer.py` handles preview/export rendering and waveform loading
- `paulstretch_light/dsp.py` contains stretching, freeze, shimmer, and the effect chain
- `paulstretch_light/preset_library.py` manages user presets and autosaved state
- `paulstretch_light/waveform.py` contains waveform overview models
