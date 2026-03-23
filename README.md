# Demonlist Viewer

An interactive viewer for the [Pointercrate](https://pointercrate.com) Geometry Dash Demonlist — fully self-contained, no server required.

![Preview](https://i.ytimg.com/vi/CELNmHwln_c/mqdefault.jpg)

## Features

### 📋 Main List
The top 150 hardest demons, displayed as cards with thumbnail, tier badge, publisher and verifier. Filter by tier (Top 50 / 51–100 / 101–150) and search by name or player.

### 👹 All Demons
Every demon ever on the list (662 total), split into **Main List** and **Legacy** sections with search.

### 🔍 Demon Detail
Click any demon to open its detail page:
- Embedded YouTube video
- Publisher, verifier, GD level ID (links to GDBrowser)
- Top approved records with video links
- Creators list
- Position history scatter chart with clickable tooltips
- Vertical dashed line marking when the demon dropped to Legacy

### ⏰ Time Machine
Reconstruct the full demonlist — main + legacy — as it was on any date since **2017-01-14**. History is embedded locally for instant results with no API calls. Click any demon to open its detail page.

### 📊 Compare
Add up to 10 demons and overlay their position histories on a single chart. Each demon gets a distinct color. Click any dot to see the exact position and date. Remove demons individually or clear all.

### 📈 Stats & Records
Historical records across multiple categories, each showing the top 3 demons with medals:
- Longest reign at #1 (cumulative days)
- Longest time in top 10
- Oldest demons on the list
- Most stable (fewest position changes relative to time)
- Most volatile (most position changes)
- Complete history of every #1 reign since 2017 (clickable)
- List growth milestones (#50, #100, #150 … #600)
- Longest stays in the main list before going legacy
- Demons up vs. down since entry
- Survival by cohort — select a year and see which demons from that class are still in the main list today

### 📉 Charts
Visual analysis computed from the full position history:
- New demons added per year and per month
- Total days at #1 by demon (top 10)
- Entry position distribution
- Requirement % distribution
- #1 reign duration — toggle between number of changes per year and average days per reign
- Main list rotation rate per month
- Jump size distribution (how many positions demons move per change)
- Publisher average days on list
- Publisher dominance in the main list by year
- Entry position vs. longevity scatter (correlation)
- Current main list: year demons were added
- Top publishers and verifiers

### 🌙 Dark / Light mode
Toggle at any time. All charts and UI elements adapt to the selected theme.

### 📱 Mobile friendly
Responsive layout with a hamburger menu on small screens.

### ⬅️ Browser navigation
Back and forward buttons work correctly across tabs and demon detail pages.

---

## Files

```
index.html              # Main application — open this in your browser
demons_history.json     # Position history for all 662 demons (Time Machine data)
data/
  demons_listed.json    # Snapshot of the current demonlist
scripts/
  fetch_listed.py       # Downloads the current demonlist from the Pointercrate API
  fetch_history.py      # Downloads position history (incremental, resume-safe)
  build.py              # Rebuilds index.html with fresh data and recomputed stats
.github/
  workflows/
    update.yml          # GitHub Actions workflow — runs every Monday automatically
```

---

## Usage

Open `index.html` directly in your browser. Everything is embedded — no server, no dependencies.

---

## Updating the data

The demonlist changes regularly. Run these three commands to rebuild with fresh data:

```bash
cd scripts
pip install requests

python fetch_listed.py    # Update data/demons_listed.json
python fetch_history.py   # Update demons_history.json (incremental)
python build.py           # Rebuild index.html with fresh data and recomputed statistics
```

`fetch_history.py` is incremental by default — it only re-fetches demons that are new or have recent activity. Use `--full` to force a complete re-fetch:

```bash
python fetch_history.py --full
```

`build.py` recomputes **all statistics and charts** from scratch on every run, so Stats & Records and Charts are always up to date after a rebuild.

---

## Automatic updates

A GitHub Actions workflow runs every **Monday at 06:00 UTC** and automatically:
1. Fetches the updated demonlist
2. Updates position history (incremental)
3. Rebuilds `index.html` with fresh data and recomputed stats
4. Commits and pushes the changes if anything changed

You can also trigger it manually from the **Actions** tab → **Weekly Update** → **Run workflow**.

---

## Data sources

All data is fetched from the public [Pointercrate API](https://pointercrate.com/documentation):

| Endpoint | Used for |
|---|---|
| `GET /api/v2/demons/listed/?limit=100&after=<pos>` | Current ranked list |
| `GET /api/v2/demons/<id>/audit/movement` | Position history per demon |
| `GET /api/v2/demons/<id>/` | Full detail (video, records, creators) — live on click |

Position history is available from **2017-01-14** onwards.

---

## Tech stack

Pure HTML + CSS + JavaScript — no frameworks, no build tools, no runtime dependencies.  
Python scripts use only the standard library plus `requests` for data fetching.
