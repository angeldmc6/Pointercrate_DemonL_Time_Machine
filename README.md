# Demonlist Viewer

An interactive viewer for the [Pointercrate](https://pointercrate.com) Geometry Dash Demonlist, built as a single self-contained HTML file.

![Preview](https://i.ytimg.com/vi/CELNmHwln_c/mqdefault.jpg)

## Features

- **Main List** — The top 150 hardest demons, with tier filters (Top 50 / 51–100 / 101–150) and live search
- **All Demons** — All 662 demons ever on the list, split into Main List and Legacy sections
- **Demon Detail** — Click any demon to see its embedded YouTube video, publisher, verifier, GD level link, top records, creators, and a position history scatter chart with clickable tooltips
- **Time Machine** — Reconstruct the full demonlist (main + legacy) as it was on any date since 2017-01-14, using a local history file for instant results
- **Dark / Light mode** — Toggle at any time

## Files

```
demonlist.html          # Main application — open this in your browser
demons_history.json     # Position history for all 662 demons (required for Time Machine)
data/
  demons_listed.json    # Snapshot of the current demonlist (used to build the app)
scripts/
  fetch_history.py      # Downloads position history from the Pointercrate API
  fetch_listed.py       # Downloads the current demonlist from the Pointercrate API
```

## Usage

### Option A — Open directly (recommended)

Just open `demonlist.html` in your browser. The demon list and position history are embedded — no server needed.

### Option B — With a local server

If you want the Time Machine to load `demons_history.json` as a separate file (e.g. after updating it), serve the folder with Python:

```bash
python -m http.server 8000
# then open http://localhost:8000/demonlist.html
```

## Updating the data

The demonlist changes regularly. To rebuild with fresh data:

**1. Re-fetch the current list:**
```bash
cd scripts
pip install requests
python fetch_listed.py
```
This overwrites `data/demons_listed.json`.

**2. Re-fetch position history:**
```bash
python fetch_history.py
```
This overwrites `demons_history.json`. It resumes automatically if interrupted.

**3. Rebuild the HTML:**
```bash
python build.py
```
This re-embeds the updated data into `demonlist.html`.

## Data sources

All data is fetched from the public [Pointercrate API](https://pointercrate.com/documentation):

| Endpoint | Used for |
|---|---|
| `GET /api/v2/demons/listed/?limit=100&after=<pos>` | Current ranked list |
| `GET /api/v2/demons/` | All demons (including legacy) |
| `GET /api/v2/demons/<id>/audit/movement` | Position history per demon |
| `GET /api/v2/demons/<id>/` | Full detail (video, records, creators) |

The detail endpoint is called live when you click a demon — it is not cached locally.

## History coverage

Position history is available from **2017-01-14** onwards. Demons added before the Pointercrate tracking system was introduced may show `~ est.` in the Time Machine, indicating their position is estimated from current data.

## Tech stack

Pure HTML + CSS + JavaScript — no frameworks, no build tools, no dependencies.
Data is fetched from the Pointercrate public API and embedded at build time.
