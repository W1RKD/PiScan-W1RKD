#!/usr/bin/env python3
"""Dependency-free local web control plane for PiScan scan-list planning."""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
RADIUS_OPTIONS = (5, 10, 25, 50, 100)
DEFAULT_STATE = {"location": {"latitude": None, "longitude": None}, "radius_miles": 25, "mode": "local", "channels": [], "watch_ids": []}


def number(value, default=None):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def distance_miles(a_lat, a_lon, b_lat, b_lon):
    values = (a_lat, a_lon, b_lat, b_lon)
    if any(value is None for value in values):
        return None
    radius = 3958.7613
    lat1, lon1, lat2, lon2 = map(math.radians, values)
    dlat, dlon = lat2 - lat1, lon2 - lon1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * radius * math.asin(math.sqrt(min(1, value)))


def clean_channel(raw):
    frequency = number(raw.get("frequency_mhz", raw.get("frequency")))
    if frequency is None and raw.get("freq") is not None:
        frequency = number(raw["freq"])
        if frequency and frequency > 2_000_000:
            frequency /= 1_000_000
    if frequency is None or not 0.01 <= frequency <= 3000:
        raise ValueError("frequency_mhz must be between 0.01 and 3000")
    tag = str(raw.get("tag", raw.get("name", "Untitled channel"))).strip()[:120]
    channel_id = str(raw.get("id", "")).strip() or re.sub(r"[^a-z0-9]+", "-", tag.lower()).strip("-")
    if not channel_id:
        raise ValueError("channel id or tag is required")
    return {"id": channel_id[:80], "tag": tag or channel_id, "frequency_mhz": round(frequency, 6), "modulation": str(raw.get("modulation", "FM")).upper()[:12], "tone": str(raw.get("tone", "")).strip()[:20], "latitude": number(raw.get("latitude")), "longitude": number(raw.get("longitude")), "enabled": bool(raw.get("enabled", True))}


class Store:
    def __init__(self, path, systems_path):
        self.path, self.systems_path = Path(path), Path(systems_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.state = json.loads(self.path.read_text()) if self.path.exists() else json.loads(json.dumps(DEFAULT_STATE))
        self.save()

    def save(self):
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.state, indent=2) + "\n")
        temporary.replace(self.path)

    def view(self):
        state = json.loads(json.dumps(self.state))
        location = state["location"]
        for channel in state["channels"]:
            channel["distance_miles"] = distance_miles(location.get("latitude"), location.get("longitude"), channel.get("latitude"), channel.get("longitude"))
        return state

    def export_systems(self):
        channels = [c for c in self.state["channels"] if c.get("enabled", True)]
        return {"systems": [{"systype": "analog", "tag": "Web scan list", "lockout": "false", "channels": [{"tag": c["tag"], "lockout": "false", "delay": "2000", "freq": str(round(c["frequency_mhz"] * 1_000_000)), "chantype": "amc" if c["modulation"] == "AM" else "fmc", **({"tone": c["tone"]} if c.get("tone") else {})} for c in channels]}]}

    def apply_systems(self):
        """Atomically write a PiScan-compatible database for the next scanner start."""
        self.systems_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.systems_path.with_suffix(self.systems_path.suffix + ".tmp")
        temporary.write_text(json.dumps(self.export_systems(), indent=4) + "\n")
        temporary.replace(self.systems_path)


class Handler(BaseHTTPRequestHandler):
    store = None

    def send_json(self, value, status=HTTPStatus.OK):
        payload = json.dumps(value).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/state": return self.send_json(self.store.view())
        if path == "/api/export": return self.send_json(self.store.export_systems())
        if path == "/api/options": return self.send_json({"radius_miles": RADIUS_OPTIONS, "modes": ["local", "broadcast"]})
        file_path = STATIC / ("index.html" if path == "/" else path.removeprefix("/"))
        if not file_path.is_file() or STATIC not in file_path.parents: return self.send_error(HTTPStatus.NOT_FOUND)
        payload = file_path.read_bytes()
        content_type = {".html": "text/html", ".css": "text/css", ".js": "application/javascript"}.get(file_path.suffix, "application/octet-stream")
        self.send_response(HTTPStatus.OK); self.send_header("Content-Type", content_type); self.send_header("Content-Length", str(len(payload))); self.end_headers(); self.wfile.write(payload)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            if path == "/api/settings":
                data = self.body(); radius = int(data.get("radius_miles", 25)); mode = data.get("mode", "local")
                if radius not in RADIUS_OPTIONS: raise ValueError("radius_miles must be 5, 10, 25, 50, or 100")
                if mode not in ("local", "broadcast"): raise ValueError("mode must be local or broadcast")
                self.store.state.update({"radius_miles": radius, "mode": mode, "location": {"latitude": number(data.get("latitude")), "longitude": number(data.get("longitude"))}})
            elif path == "/api/channel":
                channel = clean_channel(self.body()); self.store.state["channels"] = [c for c in self.store.state["channels"] if c["id"] != channel["id"]] + [channel]
            elif path == "/api/watch":
                channel_id = str(self.body().get("id", ""))
                if channel_id not in {c["id"] for c in self.store.state["channels"]}: raise ValueError("channel does not exist")
                watch = self.store.state["watch_ids"]; self.store.state["watch_ids"] = [x for x in watch if x != channel_id] if channel_id in watch else watch + [channel_id]
            elif path == "/api/import":
                data = self.body(); text = data.get("text", "")
                if data.get("format") == "csv": rows = list(csv.DictReader(io.StringIO(text)))
                else:
                    parsed = json.loads(text); rows = parsed.get("channels", parsed) if isinstance(parsed, dict) else parsed
                existing = {c["id"]: c for c in self.store.state["channels"]}; existing.update({c["id"]: clean_channel(row) for row in rows}); self.store.state["channels"] = list(existing.values())
            elif path == "/api/apply":
                self.store.apply_systems(); return self.send_json({"success": True, "path": str(self.store.systems_path)})
            else: return self.send_error(HTTPStatus.NOT_FOUND)
            self.store.save(); return self.send_json(self.store.view())
        except (ValueError, json.JSONDecodeError) as exc:
            return self.send_json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)


def main():
    parser = argparse.ArgumentParser(description="PiScan browser scan-list editor")
    parser.add_argument("--host", default="127.0.0.1"); parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--data", default=str(ROOT / "data" / "web_state.json")); parser.add_argument("--systems", default=str(ROOT / "data" / "systems.json"), help="output systems.json path")
    args = parser.parse_args(); Handler.store = Store(args.data, args.systems); server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"PiScan web UI: http://{args.host}:{args.port}")
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: server.server_close()


if __name__ == "__main__": main()
