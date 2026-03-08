#!/usr/bin/env python3
"""
Probe the device REST API to discover which siid/piid properties are supported.

Sweeps configurable siid/piid ranges by sending batched get_properties requests
and reports which ones return code=0 (supported) vs error codes.

Usage:
    .venv/bin/python dev/probe_rest_properties.py
    .venv/bin/python dev/probe_rest_properties.py --siid-max 10 --piid-max 30
    .venv/bin/python dev/probe_rest_properties.py --siid 2 --piid-max 100

Results are printed to stdout and saved to dev/logs/probe_<TIMESTAMP>.json
"""
from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from custom_components.dreame_mower.dreame.cloud.cloud_device import DreameMowerCloudDevice

BATCH_SIZE = 20  # properties per get_properties call


def load_creds_from_launch() -> dict[str, str] | None:
    launch_path = ROOT_DIR / ".vscode" / "launch.json"
    try:
        raw = launch_path.read_text(encoding="utf-8")
        raw = re.sub(r"//[^\n]*", "", raw)
        cfg = json.loads(raw)
        configs = cfg.get("configurations", [])
        debug = next((c for c in configs if "CLI" in c.get("name", "")), None)
        if not debug:
            return None
        args = debug.get("args", [])

        def get_arg(flag: str, default: str = "") -> str:
            return args[args.index(flag) + 1] if flag in args else default

        username = get_arg("--username")
        password = get_arg("--password")
        device_id = get_arg("--device_id")
        country = get_arg("--country", "eu") or "eu"
        if username and password and device_id:
            return {"username": username, "password": password, "device_id": device_id, "country": country}
    except Exception:
        pass
    return None


def prompt_creds() -> dict[str, str]:
    username = input("Username (email): ").strip()
    password = getpass.getpass("Password: ")
    device_id = input("Device ID (e.g. -112149257): ").strip()
    country = input("Country [eu]: ").strip() or "eu"
    return {"username": username, "password": password, "device_id": device_id, "country": country}


def probe(
    device: DreameMowerCloudDevice,
    siid_range: range,
    piid_range: range,
) -> list[dict[str, Any]]:
    """Sweep all (siid, piid) pairs and return a list of result dicts."""
    pairs = [(s, p) for s in siid_range for p in piid_range]
    results: list[dict[str, Any]] = []

    for batch_start in range(0, len(pairs), BATCH_SIZE):
        batch = pairs[batch_start : batch_start + BATCH_SIZE]
        params = [{"siid": s, "piid": p} for s, p in batch]
        label = f"siid {batch[0][0]}:{batch[0][1]} .. {batch[-1][0]}:{batch[-1][1]}"
        print(f"  Probing {label} ...", end="", flush=True)
        try:
            result_list = device.get_properties(params)
        except TimeoutError as e:
            print(f" TIMEOUT ({e})")
            # Mark whole batch as timeout
            for s, p in batch:
                results.append({"siid": s, "piid": p, "code": None, "status": "timeout"})
            time.sleep(2)
            continue
        except Exception as e:
            print(f" ERROR ({e})")
            for s, p in batch:
                results.append({"siid": s, "piid": p, "code": None, "status": f"exception: {e}"})
            continue

        if not isinstance(result_list, list):
            print(f" unexpected response: {result_list!r}")
            continue

        ok_count = 0
        for item in result_list:
            siid = item.get("siid")
            piid = item.get("piid")
            code = item.get("code", -1)
            if code == 0:
                ok_count += 1
                results.append({
                    "siid": siid,
                    "piid": piid,
                    "code": code,
                    "status": "ok",
                    "value": item.get("value"),
                })
            else:
                results.append({
                    "siid": siid,
                    "piid": piid,
                    "code": code,
                    "status": "error",
                })
        print(f" {ok_count}/{len(batch)} ok")
        time.sleep(0.3)  # avoid hammering the API

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe Dreame device REST properties")
    parser.add_argument("--username", default=None)
    parser.add_argument("--password", default=None)
    parser.add_argument("--device-id", default=None)
    parser.add_argument("--country", default=None)
    parser.add_argument("--siid", type=int, default=None, help="Probe only this siid")
    parser.add_argument("--siid-min", type=int, default=1, help="First siid to probe (default: 1)")
    parser.add_argument("--siid-max", type=int, default=8, help="Last siid to probe (default: 8)")
    parser.add_argument("--piid-min", type=int, default=1, help="First piid to probe (default: 1)")
    parser.add_argument("--piid-max", type=int, default=120, help="Last piid to probe (default: 120)")
    args = parser.parse_args()

    # Credentials: CLI args > launch.json > interactive prompt
    creds = load_creds_from_launch()
    if args.username:
        creds = creds or {}
        creds["username"] = args.username
    if args.password:
        creds = creds or {}
        creds["password"] = args.password
    if args.device_id:
        creds = creds or {}
        creds["device_id"] = args.device_id
    if args.country:
        creds = creds or {}
        creds["country"] = args.country

    if not creds or not all(creds.get(k) for k in ("username", "password", "device_id")):
        print("No credentials in launch.json — please enter them:")
        creds = prompt_creds()

    print(f"Connecting as {creds['username']} (device {creds['device_id']}, {creds['country']}) ...")
    device = DreameMowerCloudDevice(
        username=creds["username"],
        password=creds["password"],
        country=creds["country"],
        account_type="dreame",
        device_id=creds["device_id"],
    )
    # _initialize_mqtt_connection_state fetches the device's host/uid/model, which
    # send() needs to build the correct API relay URL — without it every call returns None.
    if not device._initialize_mqtt_connection_state():
        print("Connection / device init failed.")
        sys.exit(1)
    print(f"Connected. host={device._host}\n")

    siid_range = range(args.siid, args.siid + 1) if args.siid else range(args.siid_min, args.siid_max + 1)
    piid_range = range(args.piid_min, args.piid_max + 1)

    print(f"Probing siid={list(siid_range)}, piid={args.piid_min}..{args.piid_max} "
          f"({len(siid_range) * len(piid_range)} pairs in batches of {BATCH_SIZE})\n")

    results = probe(device, siid_range, piid_range)

    # Summary
    supported = [r for r in results if r["status"] == "ok"]
    print(f"\n{'='*60}")
    print(f"Supported properties ({len(supported)} found):")
    print(f"{'='*60}")
    for r in supported:
        val = r["value"]
        val_str = json.dumps(val, ensure_ascii=False)
        if len(val_str) > 80:
            val_str = val_str[:77] + "..."
        print(f"  {r['siid']:>2}:{r['piid']:<3}  {val_str}")

    # Save full results
    out_dir = ROOT_DIR / "dev" / "logs"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"probe_{ts}.json"
    out_path.write_text(
        json.dumps(
            {
                "timestamp": datetime.now().astimezone().isoformat(),
                "device_id": creds["device_id"],
                "siid_range": [siid_range.start, siid_range.stop - 1],
                "piid_range": [piid_range.start, piid_range.stop - 1],
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    print(f"\nFull results saved to {out_path.relative_to(ROOT_DIR)}")


if __name__ == "__main__":
    main()
