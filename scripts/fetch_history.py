"""
fetch_history.py
----------------
Downloads the position history (movement log) for every demon in the
demonlist and saves it to ../demons_history.json

Incremental mode (default): only fetches demons that are new or whose
last recorded entry is older than 8 days. Weekly runs are fast.

Full mode (--full): re-fetches every demon regardless of cache.

Usage:
    pip install requests
    python fetch_history.py           # incremental (recommended)
    python fetch_history.py --full    # full re-fetch

Output format:
    {
      "history": {
        "<demon_id>": [
          {"t": "2019-03-09T18:00:08", "p": 45, "a": false},
          ...
        ]
      }
    }
    Fields: t = time (ISO), p = new_position, a = true if reason is "Added"
"""

import requests
import json
import time
import os
import sys
from datetime import datetime, timezone, timedelta

BASE        = "https://pointercrate.com"
LISTED_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "demons_listed.json")
OUTPUT      = os.path.join(os.path.dirname(__file__), "..", "demons_history.json")
DELAY       = 0.4
SAVE_EVERY  = 50


def fetch_movement(demon_id):
    url = f"{BASE}/api/v2/demons/{demon_id}/audit/movement"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.json()
        print(f"    HTTP {r.status_code} for id={demon_id}")
        return None
    except Exception as e:
        print(f"    Error for id={demon_id}: {e}")
        return None


def parse_entries(raw):
    result = []
    for m in raw:
        if not isinstance(m.get("new_position"), int):
            continue
        result.append({
            "t": m["time"],
            "p": m["new_position"],
            "a": m.get("reason") == "Added",
        })
    return result


def last_entry_date(entries):
    if not entries:
        return None
    try:
        ts = entries[-1]["t"].replace("Z", "+00:00")
        return datetime.fromisoformat(ts).replace(tzinfo=timezone.utc)
    except Exception:
        return None


def needs_update(demon_id, history, full_mode, threshold):
    if full_mode:
        return True
    if demon_id not in history:
        return True          # new demon, never fetched
    entries = history[demon_id]
    if not entries:
        return True          # previously failed, retry
    last = last_entry_date(entries)
    return last is None or last < threshold


def _save(history, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    out = {"history": {str(k): v for k, v in history.items()}}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"), ensure_ascii=False)


def main():
    full_mode = "--full" in sys.argv

    if not os.path.exists(LISTED_FILE):
        print(f"ERROR: {LISTED_FILE} not found. Run fetch_listed.py first.")
        sys.exit(1)

    demons = json.load(open(LISTED_FILE, encoding="utf-8"))
    demons.sort(key=lambda d: d["id"])
    total = len(demons)
    print(f"Loaded {total} demons")

    history = {}
    if os.path.exists(OUTPUT):
        raw     = json.load(open(OUTPUT, encoding="utf-8"))
        history = {int(k): v for k, v in raw.get("history", {}).items()}
        print(f"Existing history: {len(history)} demons cached")

    threshold  = datetime.now(timezone.utc) - timedelta(days=8)
    to_update  = [d for d in demons if needs_update(d["id"], history, full_mode, threshold)]
    mode_label = "FULL" if full_mode else "INCREMENTAL"

    print(f"\nMode: {mode_label}")
    print(f"Demons to fetch: {len(to_update)} / {total}\n")

    if not to_update:
        print("Everything is up to date.")
        return

    failed = []
    done   = 0

    for i, demon in enumerate(to_update, 1):
        did  = demon["id"]
        name = demon["name"]

        raw = fetch_movement(did)
        if raw is None:
            time.sleep(1.0)
            raw = fetch_movement(did)

        if raw is None:
            failed.append(did)
            if did not in history:
                history[did] = []
            print(f"  [{i:4d}/{len(to_update)}] FAILED  id={did:4d}  {name}")
        else:
            history[did] = parse_entries(raw)
            n = len(history[did])
            print(f"  [{i:4d}/{len(to_update)}]  {n:4d} entries  id={did:4d}  {name}")

        done += 1
        time.sleep(DELAY)

        if done % SAVE_EVERY == 0:
            _save(history, OUTPUT)
            print(f"\n  -- Progress saved ({done}/{len(to_update)}) --\n")

    _save(history, OUTPUT)

    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"\n{'='*52}")
    print(f"Saved: {OUTPUT}  ({size_kb:.0f} KB)")
    print(f"Updated : {len(to_update) - len(failed)}")
    print(f"Failed  : {len(failed)}")
    if failed:
        print(f"Failed IDs: {failed}")
    print(f"{'='*52}")


if __name__ == "__main__":
    main()
