import json
import tempfile
from pathlib import Path

from web.server import Store, clean_channel, distance_miles


def test_clean_channel_handles_mhz_value():
    channel = clean_channel({
        "id": "fire-dispatch",
        "tag": "Fire Dispatch",
        "frequency_mhz": 154.07,
        "modulation": "FM",
        "tone": "103.5",
        "latitude": 42.1,
        "longitude": -72.6,
    })

    assert channel["id"] == "fire-dispatch"
    assert channel["tag"] == "Fire Dispatch"
    assert channel["frequency_mhz"] == 154.07
    assert channel["modulation"] == "FM"
    assert channel["tone"] == "103.5"
    assert channel["latitude"] == 42.1
    assert channel["longitude"] == -72.6


def test_clean_channel_rejects_invalid_frequency():
    try:
        clean_channel({"tag": "Bad", "frequency_mhz": 0})
        assert False, "Expected ValueError for an invalid frequency"
    except ValueError:
        pass


def test_distance_miles_returns_positive_value_for_close_points():
    distance = distance_miles(42.10, -72.60, 42.11, -72.59)
    assert distance is not None
    assert distance > 0
    assert distance < 5


def test_store_export_systems_uses_hz_values():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        state_path = root / "web_state.json"
        systems_path = root / "systems.json"
        store = Store(str(state_path), str(systems_path))

        store.state["channels"] = [{
            "id": "fire-dispatch",
            "tag": "Fire Dispatch",
            "frequency_mhz": 154.07,
            "modulation": "FM",
            "tone": "103.5",
            "latitude": 42.10,
            "longitude": -72.60,
            "enabled": True,
        }]

        export = store.export_systems()
        channels = export["systems"][0]["channels"]

        assert channels[0]["freq"] == "154070000"
        assert channels[0]["chantype"] == "fmc"
        assert channels[0]["tone"] == "103.5"


def test_store_apply_systems_writes_file():
    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        state_path = root / "web_state.json"
        systems_path = root / "systems.json"
        store = Store(str(state_path), str(systems_path))

        store.state["channels"] = [{
            "id": "airport",
            "tag": "Airport Ground",
            "frequency_mhz": 121.9,
            "modulation": "AM",
            "latitude": 42.05,
            "longitude": -72.68,
            "enabled": True,
        }]

        store.apply_systems()

        payload = json.loads(systems_path.read_text())
        assert payload["systems"][0]["channels"][0]["chantype"] == "amc"
        assert payload["systems"][0]["channels"][0]["freq"] == "121900000"
