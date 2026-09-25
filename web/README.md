# PiScan Web Control Plane

This directory contains the first, hardware-independent step of the PiScan modernization. It provides a browser-based scan-list editor that runs on any computer with Python 3. It does not require an RTL-SDR, Raspberry Pi, C++ build, or Broadcastify account.

## Run it

From the repository root:

```bash
python3 web/server.py
```

Open <http://127.0.0.1:8080>.

The server stores its working data in `data/web_state.json` by default. Override the path and port when needed:

```bash
python3 web/server.py --data data/my-state.json --port 8080
```

## Import formats

CSV columns:

```text
id,tag,frequency_mhz,modulation,tone,latitude,longitude
fire-dispatch,Fire Dispatch,154.070,FM,,42.10,-72.60
```

JSON can be either an array of channels or an object containing `channels`.

The editor accepts frequencies in MHz and exports PiScan-compatible `systems.json` with frequencies in Hz.

## Current scope

- scan-list and watch-list editing
- 5, 10, 25, 50, and 100 mile radius filters
- CSV/JSON import
- PiScan `systems.json` export
- local and broadcast planning modes
- no external dependencies

The broadcast mode currently records configuration only. It deliberately does not pretend to upload audio to Broadcastify. The scanner engine and an approved Broadcastify-compatible encoder will be connected in a later phase.
