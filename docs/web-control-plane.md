# Web control plane roadmap

The initial web control plane is intentionally independent from the radio hardware. It is a browser-based scan-list planner and PiScan `systems.json` exporter.

## Why this is separate initially

The current PiScan server loads `systems.json` into an in-memory `SystemList` at startup and scans from pre-built frequency bins. Runtime database mutation is not implemented yet. The web editor therefore writes a separate state file and exports a validated `systems.json`; it does not silently modify the running C++ scanner.

## Next integration step

Add a C++ `ScanListManager` that can safely pause scanning, replace the in-memory list, rebuild bins, and persist `systems.json`. Then replace the web editor's export-only path with a localhost API or Protocol Buffer scan-list request.

Do not expose the legacy unauthenticated TCP control port to the internet. When remote access is added, put the web service behind authentication and HTTPS.

## Broadcastify

The current `broadcast` mode is a planning flag only. It does not upload audio. A future `BroadcastSink` should feed an approved Broadcastify-compatible encoder or ingest client using credentials supplied through the appropriate approval process. Do not implement an undocumented direct upload endpoint.
