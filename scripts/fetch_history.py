"""
fetch_history.py
----------------
Downloads the position history (movement log) for every demon in the
demonlist and saves it to ../demons_history.json

The output file is used by the Time Machine feature in demonlist.html.

Usage:
    pip install requests
    python fetch_history.py

Resume support: if the output file already exists, only missing demons
are fetched. Safe to interrupt and re-run.

Output format:
    {
      "history": {
        "<demon_id>": [
          {"t": "2019-03-09T18:00:08", "p": 45, "a": false},
          ...
        ],
        ...
      }
    }
    Fields: t = time (ISO), p = new_position, a = true if reason is "Added"
"""

import requests
import json
import time
import os

BASE        = "https://pointercrate.com"
LISTED_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "demons_listed.json")
OUTPUT      = os.path.join(os.path.dirname(__file__), "..", "demons_history.json")
DELAY       = 0.4   # seconds between requests
SAVE_EVERY  = 50    # save progress every N demons


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
    """Convert raw API entries to compact format."""
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


def main():
    # Load demon list
    if not os.path.exists(LISTED_FILE):
        print(f"ERROR: {LISTED_FILE} not found.")
        print("Run fetch_listed.py first.")
        return

    demons = json.load(open(LISTED_FILE, encoding="utf-8"))
    demons.sort(key=lambda d: d["id"])
    total = len(demons)
    print(f"Loaded {total} demons from {LISTED_FILE}")

    # Load existing progress
    history = {}
    if os.path.exists(OUTPUT):
        existing = json.load(open(OUTPUT, encoding="utf-8"))
        history  = {int(k): v for k, v in existing.get("history", {}).items()}
        already  = sum(1 for v in history.values() if v is not None)
        print(f"Resuming — {already}/{total} already fetched\n")
    else:
        print("Starting fresh...\n")

    failed = []
    done   = 0

    for i, demon in enumerate(demons, 1):
        did  = demon["id"]
        name = demon["name"]

        if did in history:
            done += 1
            continue

        raw = fetch_movement(did)

        # Single retry on failure
        if raw is None:
            time.sleep(1.0)
            raw = fetch_movement(did)

        if raw is None:
            failed.append(did)
            history[did] = []
            print(f"  [{i:4d}/{total}] FAILED  id={did:4d}  {name}")
        else:
            history[did] = parse_entries(raw)
            n = len(history[did])
            print(f"  [{i:4d}/{total}]  {n:4d} entries  id={did:4d}  {name}")

        done += 1
        time.sleep(DELAY)

        # Save progress periodically
        if done % SAVE_EVERY == 0:
            _save(history, OUTPUT)
            print(f"\n  -- Progress saved ({done}/{total}) --\n")

    _save(history, OUTPUT)

    size_kb = os.path.getsize(OUTPUT) / 1024
    print(f"\n{'='*52}")
    print(f"Saved: {OUTPUT}  ({size_kb:.0f} KB)")
    print(f"Demons with history : {sum(1 for v in history.values() if v)}/{total}")
    print(f"Demons with no data : {len(failed)}")
    if failed:
        print(f"Failed IDs: {failed}")
    print(f"{'='*52}")


def _save(history, path):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    out = {"history": {str(k): v for k, v in history.items()}}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, separators=(",", ":"), ensure_ascii=False)


if __name__ == "__main__":
    main()
