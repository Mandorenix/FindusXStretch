# Release History

## 0.1.9 - 2026-03-17 08:11:50

- Promoted the latest UI refresh to its own patch release.
- Kept the new under-tab layout for Source, Stretch, and Presets, while returning Effects to one unified panel with clearer internal sections.
- Refreshed the built-in Help view so the tab structure and unified Effects workflow are described accurately.
- Artifacts: `dist\findus_stretching`, `dist\installer`, `dist\release`.

## 0.1.8 - 2026-03-16 20:14:22

- Built from the 0.1.8 workflow polish pass.
- Added labeled undo/redo tooltips and cleaner workflow-history action naming for source loads, project loads, preview-history loads, compare-slot loads, and effect shortcuts.
- Added `Store Active` and `Swap A/B` to the compare workflow, with clearer slot-state feedback and improved slot-toggle status messages.
- Added recent-source polish with `Open Folder`, `Clear List`, clearer unsupported-drop feedback, and an inline drop hint while dragging supported files into the app.
- Refreshed the built-in help text for polished compare controls, recent-source actions, drop flow, and history labeling.
- Artifacts: `dist\findus_stretching`, `dist\installer`, `dist\release`.

## 0.1.7 - 2026-03-16 19:27:30

- Built from the 0.1.7 workflow-speed release.
- Added snapshot-based undo/redo for the active stretch, region, effects, A/B, loop, and export workflow.
- Added fast Toggle A/B auditioning with active-slot feedback and cached-preview reuse when available.
- Added drag-and-drop for supported audio files and `.findusstretch.json` project files.
- Added recent source tracking in the Source tab, with quick reopen and missing-file cleanup.
- Refreshed the built-in help text for undo/redo, Toggle A/B, drag-and-drop, recent sources, and new shortcuts.
- Artifacts: `dist\findus_stretching`, `dist\installer`, `dist\release`.

## 0.1.6 - 2026-03-16 18:40:04

- Built from Advanced Sound Design Package 4.
- Added input trim before stretch/effects so weak or overly hot sources can be shaped earlier in the chain.
- Added an optional safety limiter stage with a soft output ceiling for aggressive combinations.
- Added loop crossfade for smoother repeated preview playback without invalidating cached previews.
- Refreshed the built-in help text for input trim, safety limiter, and loop crossfade behavior.
- Artifacts: `dist\findus_stretching`, `dist\installer`, `dist\release`.

## 0.1.5 - 2026-03-16 17:58:35

- Built from Session And Recall Package 3.
- Added explicit project save/load files for source, region, stretch, effects, A/B slots, and queued renders.
- Added launchable recent-project tracking in the Source tab and app-state restore.
- Added session-local preview history so recent rendered preview states can be loaded or replayed quickly.
- Refreshed the built-in help text for project workflow, recent projects, preview history, and new shortcuts.
- Artifacts: `dist\findus_stretching`, `dist\installer`, `dist\release`.

## 0.1.4 - 2026-03-16 17:28:39

- Built from Export And Production Package 2.
- Added wet-only, dry-only, and dry+wet render modes.
- Added a sequential render queue for saved render jobs.
- Added filtered preset batch queueing with safe preset-based output names.
- Refreshed the built-in help text for export modes, queue workflow, and batch rendering.
- Artifacts: `dist\findus_stretching`, `dist\installer`, `dist\release`.

## 0.1.3 - 2026-03-16 16:34:27

- Built from Creative Workflow Package 1.
- Added A/B compare slots for storing and loading two full working ideas.
- Added preset favorites, editable tags, and live preset search/filter controls.
- Refreshed the built-in help text for the new compare and preset-library workflow.
- Artifacts: `dist\findus_stretching`, `dist\installer`, `dist\release`.

## 0.1.2 - 2026-03-14 23:57:40

- Built from the updated UX and preview-flow pass.
- Artifacts: `dist\findus_stretching`, `dist\installer`, `dist\release`.
