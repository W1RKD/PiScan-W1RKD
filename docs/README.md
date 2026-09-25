## Web control plane (initial)

A hardware-independent browser scan-list editor is now included under `web/`. It supports the requested 5/10/25/50/100 mile options, channel import, watch-list planning, local mode, broadcast planning mode, and export to the existing PiScan `systems.json` format.

This is deliberately a fresh first step: it can be developed and tested without a Raspberry Pi or SDR. Start it with:

```bash
python3 web/server.py
```

Then open `http://127.0.0.1:8080`.

The web editor does not yet control a running C++ scanner. PiScan currently loads the scan database at startup, so runtime list replacement will be added in the next phase through a thread-safe `ScanListManager` and new Protocol Buffer messages.

The broadcast option is configuration/planning only until an approved Broadcastify-compatible encoder or ingest method is configured. No undocumented direct upload is attempted.
