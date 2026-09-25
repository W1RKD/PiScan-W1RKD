## Stage 2: scanner integration groundwork

The web layer remains the easiest part to develop in Python: it has no hardware dependencies and can use the standard library for the current prototype. The radio engine should remain C++ because it already owns SDR, demodulation, scanning, RTSP, and the existing Protocol Buffer/TCP stack.

This stage adds:

- `proto/scanlist.proto`, defining a versioned scan-list request/response contract.
- New scan-list message fields in `proto/messages.proto`.
- A safe `Write systems.json` action in the local web UI.
- Atomic file replacement so a partially written database is not left behind.

The `Write systems.json` action prepares the database for the next PiScan start. It does not claim to hot-reload the running C++ scanner yet. That is intentional: `SystemList` currently owns mutable in-memory bins and must gain a coordinated pause/rebuild/swap operation before runtime updates are enabled.

## Run locally

```bash
python3 web/server.py
```

The default output is `data/systems.json`. To target another working directory:

```bash
python3 web/server.py --systems /path/to/data/systems.json
```

## Next C++ step

Implement `SystemList::replaceFromPropertyTree()` and a scanner-state-machine reload event. The operation must pause scanning, construct replacement systems and bins off to the side, swap them under a mutex, reset the bin cursor, and resume scanning. Only after that is tested should the web service send `ScanListRequest.REPLACE` over the localhost PiScan connection.

The browser service should remain bound to `127.0.0.1` until authentication and HTTPS are added. The legacy TCP control port must not be exposed publicly.
