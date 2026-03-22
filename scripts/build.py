"""
build.py
--------
Rebuilds demonlist.html by embedding fresh data from:
  - data/demons_listed.json   → demon list + positions
  - demons_history.json       → position history (for Time Machine)

Run this after updating either data file.

Usage:
    python build.py
"""

import json
import re
import os
import sys

ROOT         = os.path.dirname(os.path.abspath(__file__))
LISTED_FILE  = os.path.join(ROOT, "data", "demons_listed.json")
HISTORY_FILE = os.path.join(ROOT, "demons_history.json")
HTML_OUT     = os.path.join(ROOT, "index.html")


def yt_id(url):
    if not url:
        return None
    m = re.search(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})", url)
    return m.group(1) if m else None


def build_demons_data(demons):
    """Convert full demon objects to compact JS-friendly dicts."""
    compact = []
    for d in sorted(demons, key=lambda x: x["position"]):
        thumb = d.get("thumbnail")
        if thumb and "zebrafishes" in thumb:
            thumb = None
        compact.append({
            "id":    d["id"],
            "pos":   d["position"],
            "name":  d["name"],
            "req":   d["requirement"],
            "yt":    yt_id(d.get("video")),
            "thumb": thumb,
            "pub":   d["publisher"]["name"],
            "pubId": d["publisher"]["id"],
            "ver":   d["verifier"]["name"],
            "verId": d["verifier"]["id"],
            "lvl":   d["level_id"],
        })
    return compact


def main():
    # ── Check inputs ──────────────────────────────────────────────────────
    for path, label in [(LISTED_FILE, "demons_listed.json"), (HISTORY_FILE, "demons_history.json")]:
        if not os.path.exists(path):
            print(f"ERROR: {label} not found at {path}")
            print("Run scripts/fetch_listed.py and scripts/fetch_history.py first.")
            sys.exit(1)

    if not os.path.exists(HTML_OUT):
        print(f"ERROR: index.html not found at {HTML_OUT}")
        sys.exit(1)

    # ── Load data ─────────────────────────────────────────────────────────
    print("Loading data files...")
    demons  = json.load(open(LISTED_FILE,  encoding="utf-8"))
    history = json.load(open(HISTORY_FILE, encoding="utf-8"))

    demons_data    = build_demons_data(demons)
    demons_data_js = "const DEMONS_DATA = " + json.dumps(demons_data, separators=(",", ":"), ensure_ascii=False) + ";"

    # Convert history keys to ints for consistency
    hist_compact = {int(k): v for k, v in history["history"].items()}
    history_js   = "const DEMONS_HISTORY = " + json.dumps(hist_compact, separators=(",", ":"), ensure_ascii=False) + ";"

    print(f"  Demons:  {len(demons_data)}")
    print(f"  History: {len(hist_compact)} entries")

    # ── Patch HTML ────────────────────────────────────────────────────────
    print("Patching demonlist.html...")
    content = open(HTML_OUT, encoding="utf-8").read()

    # Replace first <script> block (DEMONS_DATA)
    content = re.sub(
        r"(<script>\s*)const DEMONS_DATA\s*=\s*\[.*?\];\s*(</script>)",
        r"\g<1>" + demons_data_js + r"\2",
        content, flags=re.DOTALL, count=1
    )

    # Replace second <script> block (DEMONS_HISTORY)
    content = re.sub(
        r"(<script>\s*)const DEMONS_HISTORY\s*=\s*\{.*?\};\s*(</script>)",
        r"\g<1>" + history_js + r"\2",
        content, flags=re.DOTALL, count=1
    )

    with open(HTML_OUT, "w", encoding="utf-8") as f:
        f.write(content)

    size_mb = os.path.getsize(HTML_OUT) / (1024 * 1024)
    print(f"\nDone. demonlist.html rebuilt ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
