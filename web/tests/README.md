# Windows quick test flow

This project can be fully tested on a Windows desktop before any Pi hardware is involved.

## Install Python

Install Python 3.11+ from https://python.org and make sure `python` is on your PATH.

## Install test dependencies

From the repo root:

```powershell
python -m pip install -r web/requirements-dev.txt
```

## Run tests

```powershell
python -m pytest web/tests -q
```

Or simply:

```powershell
./run_windows_tests.ps1
```

## Run the local web app

```powershell
python web/server.py
```

Then open http://127.0.0.1:8080 in your browser.

This does not require a Raspberry Pi, SDR, Linux system, or Broadcastify account. It validates the browser control layer, import logic, distance filtering, and generated PiScan `systems.json` output before hardware integration.
