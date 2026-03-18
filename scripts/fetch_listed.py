"""
fetch_listed.py
---------------
Downloads the current Pointercrate demonlist and saves it to
../data/demons_listed.json

Usage:
    pip install requests
    python fetch_listed.py
"""

import requests
import json
import time
import os

BASE   = "https://pointercrate.com"
OUTPUT = os.path.join(os.path.dirname(__file__), "..", "data", "demons_listed.json")
DELAY  = 0.4


def fetch_page(after=None):
    params = {"limit": 100}
    if after is not None:
        params["after"] = after
    r = requests.get(f"{BASE}/api/v2/demons/listed/", params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def main():
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    print("Fetching demonlist from Pointercrate API...")
    demons = []
    after  = None

    while True:
        batch = fetch_page(after)
        if not batch:
            break
        demons.extend(batch)
        after = batch[-1]["position"]
        print(f"  {len(demons)} demons fetched...")
        time.sleep(DELAY)

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(demons, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(demons)} demons to {OUTPUT}")
    main_list = [d for d in demons if d["position"] <= 150]
    legacy    = [d for d in demons if d["position"] > 150]
    print(f"  Main list (1-150): {len(main_list)}")
    print(f"  Legacy    (151+):  {len(legacy)}")


if __name__ == "__main__":
    main()
