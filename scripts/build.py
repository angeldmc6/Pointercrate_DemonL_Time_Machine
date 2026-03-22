"""
build.py
--------
Rebuilds index.html by:
  1. Embedding fresh DEMONS_DATA from data/demons_listed.json
  2. Embedding fresh DEMONS_HISTORY from demons_history.json
  3. Recomputing and embedding STATS_DATA and STATS2_DATA from the same sources

Run this after updating either data file:
    python build.py
"""

import json, re, os, sys
from datetime import datetime, timezone, timedelta
from collections import defaultdict

ROOT         = os.path.dirname(os.path.abspath(__file__))
LISTED_FILE  = os.path.join(ROOT, '..', 'data', 'demons_listed.json')
HISTORY_FILE = os.path.join(ROOT, '..', 'demons_history.json')
HTML_FILE    = os.path.join(ROOT, '..', 'index.html')

# ── Helpers ───────────────────────────────────────────────────────────────
def yt_id(url):
    if not url: return None
    m = re.search(r'(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})', url or '')
    return m.group(1) if m else None

def parse_date(s):
    if not s: return None
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00')).replace(tzinfo=timezone.utc)
    except Exception:
        return None

def compact_json(obj):
    return json.dumps(obj, separators=(',', ':'), ensure_ascii=False)

# ── Load data ─────────────────────────────────────────────────────────────
for path, label in [(LISTED_FILE, 'demons_listed.json'),
                    (HISTORY_FILE, 'demons_history.json'),
                    (HTML_FILE,    'index.html')]:
    if not os.path.exists(path):
        print(f'ERROR: {label} not found at {path}')
        sys.exit(1)

print('Loading data files...')
listed  = json.load(open(LISTED_FILE,  encoding='utf-8'))
history = {int(k): v for k, v in json.load(open(HISTORY_FILE, encoding='utf-8'))['history'].items()}
demons_by_id = {d['id']: d for d in listed}
now = datetime.now(timezone.utc)

# ── Build DEMONS_DATA ─────────────────────────────────────────────────────
def build_demons_data(demons):
    compact = []
    for d in sorted(demons, key=lambda x: x['position']):
        thumb = d.get('thumbnail')
        if thumb and 'zebrafishes' in thumb: thumb = None
        compact.append({
            'id':    d['id'],      'pos':   d['position'],
            'name':  d['name'],    'req':   d['requirement'],
            'yt':    yt_id(d.get('video')),
            'thumb': thumb,
            'pub':   d['publisher']['name'], 'pubId': d['publisher']['id'],
            'ver':   d['verifier']['name'],  'verId': d['verifier']['id'],
            'lvl':   d['level_id'],
        })
    return compact

# ── Build STATS_DATA + STATS2_DATA ────────────────────────────────────────
def build_stats(listed, history, demons_by_id, now):
    def demon_info(did):
        d = demons_by_id.get(did, {})
        thumb = d.get('thumbnail')
        if thumb and 'zebrafishes' in thumb: thumb = None
        return {
            'id':    did,
            'name':  d.get('name', 'Unknown'),
            'pos':   d.get('position', 999),
            'pub':   d.get('publisher', {}).get('name', '?'),
            'ver':   d.get('verifier',  {}).get('name', '?'),
            'yt':    yt_id(d.get('video')),
            'thumb': thumb,
        }

    # ── Per-demon pre-processing ──────────────────────────────────────────
    time_at1 = defaultdict(float)
    time_top10 = defaultdict(float)
    entry_date = {}; entry_pos = {}; exit_date = {}
    total_moves = defaultdict(int)
    moves_list  = defaultdict(list)
    longevity   = {}
    top1_events = []

    for did, entries in history.items():
        if not entries: continue
        pts = sorted(entries, key=lambda x: x['t'])

        added = [e for e in pts if e.get('a')]
        if added:
            d = parse_date(added[0]['t'])
            if d:
                entry_date[did] = d
                entry_pos[did]  = added[0]['p']
                longevity[did]  = (now - d).days

        total_moves[did] = len(pts) - 1
        for i in range(1, len(pts)):
            delta = abs(pts[i]['p'] - pts[i-1]['p'])
            if delta > 0: moves_list[did].append(delta)

        for i in range(1, len(pts)):
            if pts[i-1]['p'] <= 150 and pts[i]['p'] > 150:
                d = parse_date(pts[i]['t'])
                if d: exit_date[did] = d; break

        for i, e in enumerate(pts):
            d1 = parse_date(e['t'])
            d2 = parse_date(pts[i+1]['t']) if i+1 < len(pts) else now
            if not d1 or not d2: continue
            days = (d2 - d1).total_seconds() / 86400
            if e['p'] == 1:
                time_at1[did] += days
                if days > 0.5:
                    top1_events.append({'id': did, 'start': d1, 'end': d2, 'days': days})
            if e['p'] <= 10:
                time_top10[did] += days

    # ── Merge top1 reigns ─────────────────────────────────────────────────
    top1_events.sort(key=lambda x: x['start'])
    reigns = []
    for ev in top1_events:
        if (reigns and reigns[-1]['id'] == ev['id'] and
                (ev['start'] - reigns[-1]['end']).total_seconds() < 86400 * 2):
            reigns[-1]['end']  = ev['end']
            reigns[-1]['days'] = (reigns[-1]['end'] - reigns[-1]['start']).total_seconds() / 86400
        else:
            reigns.append({'id': ev['id'], 'start': ev['start'], 'end': ev['end'], 'days': ev['days']})

    # ── STATS_DATA ────────────────────────────────────────────────────────
    def top3(d_iter, extra_fn):
        return [{**demon_info(did), **extra_fn(did, v)}
                for did, v in sorted(d_iter, key=lambda x: -x[1])[:3]]

    by_month = defaultdict(int); by_year_new = defaultdict(int)
    for did, d in entry_date.items():
        by_month[f'{d.year}-{d.month:02d}'] += 1
        by_year_new[d.year] += 1

    pub_count = defaultdict(list); pub_top50 = defaultdict(int)
    ver_count = defaultdict(list)
    req_dist  = {'<50': 0, '50-74': 0, '75-89': 0, '90-99': 0, '100': 0}
    for d in listed:
        pub = d['publisher']['name']; ver = d['verifier']['name']
        pub_count[pub].append(d['id']); ver_count[ver].append(d['id'])
        if d['position'] <= 50: pub_top50[pub] += 1
        r = d['requirement']
        if r == 100: req_dist['100'] += 1
        elif r >= 90: req_dist['90-99'] += 1
        elif r >= 75: req_dist['75-89'] += 1
        elif r >= 50: req_dist['50-74'] += 1
        else: req_dist['<50'] += 1

    main_entry_years = defaultdict(int)
    for d in listed:
        if d['position'] > 150: continue
        entries = history.get(d['id'], [])
        if not entries: continue
        added = [e for e in entries if e.get('a')]
        if added:
            dt = parse_date(added[0]['t'])
            if dt: main_entry_years[dt.year] += 1

    entry_dist = {'1-10': 0, '11-50': 0, '51-100': 0, '101-150': 0}
    for did, pos in entry_pos.items():
        if   pos <= 10:  entry_dist['1-10']    += 1
        elif pos <= 50:  entry_dist['11-50']   += 1
        elif pos <= 100: entry_dist['51-100']  += 1
        elif pos <= 150: entry_dist['101-150'] += 1

    top1_acc = defaultdict(float)
    for r in reigns:
        top1_acc[r['id']] += r['days']

    stable_candidates = [
        (did, total_moves[did], longevity.get(did, 1))
        for did in longevity
        if longevity.get(did, 0) > 365 and total_moves[did] < 50
    ]
    stable_candidates.sort(key=lambda x: x[1] / max(x[2], 1))

    stats = {
        'longestTop1':   top3(time_at1.items(),   lambda did, v: {'days': round(v)}),
        'longestTop10':  top3(time_top10.items(),  lambda did, v: {'days': round(v)}),
        'longestInList': top3(longevity.items(),   lambda did, v: {'days': v}),
        'mostMoves':     top3(total_moves.items(), lambda did, v: {'moves': v}),
        'mostStable': [{**demon_info(did), 'moves': moves, 'days': days}
                       for did, moves, days in stable_candidates[:3]],
        'top1Reigns': [
            {'id': r['id'], 'name': demons_by_id.get(r['id'], {}).get('name', '?'),
             'start': r['start'].strftime('%Y-%m-%d'),
             'end':   r['end'].strftime('%Y-%m-%d'),
             'days':  round(r['days'])}
            for r in reigns if r['days'] >= 1
        ],
        'byMonth':        [[m, c] for m, c in sorted(by_month.items())],
        'byYear':         [[yr, c] for yr, c in sorted(by_year_new.items())],
        'mainListByYear': [[yr, c] for yr, c in sorted(main_entry_years.items())],
        'top1TotalDays':  [{'id': did, 'name': demons_by_id.get(did, {}).get('name', '?'), 'days': round(d)}
                           for did, d in sorted(top1_acc.items(), key=lambda x: -x[1])[:10]],
        'entryDistribution': entry_dist,
        'publisherRanking':  [[p, len(ids)] for p, ids in sorted(pub_count.items(), key=lambda x: -len(x[1]))[:10]],
        'verifierRanking':   [[v, len(ids)] for v, ids in sorted(ver_count.items(), key=lambda x: -len(x[1]))
                              if v != '-'][:10],
        'requirementDist': req_dist,
    }

    # ── STATS2_DATA ───────────────────────────────────────────────────────
    reigns_by_year = defaultdict(list)
    for r in reigns:
        reigns_by_year[r['start'].year].append(r['days'])

    all_entries = sorted([(d, did) for did, d in entry_date.items()])
    milestones  = [50, 100, 150, 200, 300, 400, 500, 600]
    growth = []
    for ms in milestones:
        if ms <= len(all_entries):
            dt, did = all_entries[ms - 1]
            growth.append({'count': ms, 'date': dt.strftime('%Y-%m-%d'),
                           'demon': demons_by_id.get(did, {}).get('name', '?')})

    pub_dom = []
    for yr in range(2017, now.year + 1):
        year_end = datetime(yr, 12, 31, 23, 59, 59, tzinfo=timezone.utc)
        if year_end > now: year_end = now
        pc = defaultdict(int)
        for did, entries in history.items():
            if not entries: continue
            pts = sorted(entries, key=lambda x: x['t'])
            last = None
            for e in pts:
                d = parse_date(e['t'])
                if d and d <= year_end: last = e
                else: break
            if last and last['p'] <= 150:
                pub = demons_by_id.get(did, {}).get('publisher', {}).get('name', '?')
                if pub and pub != '?': pc[pub] += 1
        if pc:
            top3p = sorted(pc.items(), key=lambda x: -x[1])[:3]
            pub_dom.append({'year': yr, 'top': [[p, c] for p, c in top3p]})

    pub_days = defaultdict(list)
    for did, d in entry_date.items():
        pub = demons_by_id.get(did, {}).get('publisher', {}).get('name', '?')
        if pub and pub != '?':
            pub_days[pub].append((now - d).days)
    pub_avg = [[pub, round(sum(v)/len(v)), len(v)]
               for pub, v in pub_days.items() if len(v) >= 3]
    pub_avg.sort(key=lambda x: -x[1])

    months_rot = defaultdict(lambda: {'new': 0, 'exit': 0})
    for did, d in entry_date.items():
        if entry_pos.get(did, 999) <= 150:
            months_rot[f'{d.year}-{d.month:02d}']['new'] += 1
    for did, d in exit_date.items():
        months_rot[f'{d.year}-{d.month:02d}']['exit'] += 1

    dur = [(did, (exit_date[did] - entry_date[did]).days)
           for did in exit_date if did in entry_date]
    dur.sort(key=lambda x: -x[1])

    survival = {}
    for yr in range(2017, now.year + 1):
        cohort = [(did, entry_date[did]) for did in entry_date if entry_date[did].year == yr]
        total = len(cohort)
        still = sum(1 for did, _ in cohort if demons_by_id.get(did, {}).get('position', 999) <= 150)
        survival[str(yr)] = {
            'total': total, 'mainNow': still, 'pct': round(still / max(total, 1) * 100),
            'demons': [{**demon_info(did),
                        'entryDate': entry_date[did].strftime('%Y-%m-%d'),
                        'inMain':    demons_by_id.get(did, {}).get('position', 999) <= 150}
                       for did, _ in sorted(cohort, key=lambda x: x[1])]
        }

    corr = [{'x': entry_pos[did], 'y': (now - entry_date[did]).days,
              'id': did, 'name': demons_by_id.get(did, {}).get('name', '?')}
             for did in entry_pos
             if (now - entry_date[did]).days > 30]

    all_jumps = [j for jumps in moves_list.values() for j in jumps]
    jd = {'1': 0, '2-5': 0, '6-20': 0, '21-50': 0, '51+': 0,
          'total': len(all_jumps),
          'avg': round(sum(all_jumps) / max(len(all_jumps), 1), 2)}
    for j in all_jumps:
        if   j == 1:  jd['1']    += 1
        elif j <= 5:  jd['2-5']  += 1
        elif j <= 20: jd['6-20'] += 1
        elif j <= 50: jd['21-50'] += 1
        else:         jd['51+']  += 1

    went_up = went_down = stayed = 0
    for did in entry_pos:
        ep = entry_pos[did]
        cp = demons_by_id.get(did, {}).get('position', ep)
        if cp < ep: went_up += 1
        elif cp > ep: went_down += 1
        else: stayed += 1

    stats2 = {
        'top1Reigns': [{**demon_info(r['id']),
                        'start': r['start'].strftime('%Y-%m-%d'),
                        'end':   r['end'].strftime('%Y-%m-%d'),
                        'days':  round(r['days'])}
                       for r in reigns if r['days'] >= 1],
        'avgReignByYear':   [[yr, round(sum(v)/len(v))] for yr, v in sorted(reigns_by_year.items())],
        'reignCountByYear': [[yr, len(v)] for yr, v in sorted(reigns_by_year.items())],
        'listGrowth':       growth,
        'pubDominanceByYear': pub_dom,
        'pubAvgDays':   pub_avg[:12],
        'rotationByMonth': [[m, round((v['new'] + v['exit']) / 150 * 100, 1)]
                             for m, v in sorted(months_rot.items())],
        'avgDaysBeforeLegacy': round(sum(d for _, d in dur) / max(len(dur), 1)),
        'longestMainStay': [{**demon_info(did), 'days': days} for did, days in dur[:5]],
        'survivalCohorts': survival,
        'entryVsLongevity': corr,
        'jumpDist': jd,
        'upVsDown': {'up': went_up, 'down': went_down, 'same': stayed,
                     'total': went_up + went_down + stayed},
    }

    return stats, stats2


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    demons_data      = build_demons_data(listed)
    stats, stats2    = build_stats(listed, history, demons_by_id, now)

    demons_data_js  = 'const DEMONS_DATA = '   + compact_json(demons_data)  + ';'
    history_js      = 'const DEMONS_HISTORY = ' + compact_json({int(k): v for k, v in
                       {str(k): v for k, v in history.items()}.items()}) + ';'
    stats_js        = 'const STATS_DATA = '    + compact_json(stats)   + ';'
    stats2_js       = 'const STATS2_DATA = '   + compact_json(stats2)  + ';'

    print(f'  DEMONS_DATA:    {len(listed)} demons')
    print(f'  DEMONS_HISTORY: {len(history)} demons')
    print(f'  STATS_DATA:     {len(stats_js)//1024} KB')
    print(f'  STATS2_DATA:    {len(stats2_js)//1024} KB')

    content = open(HTML_FILE, encoding='utf-8').read()

    # Replace each <script> block by matching its opening constant declaration
    replacements = [
        (r'(<script>\s*)const DEMONS_DATA\s*=\s*\[.*?\];\s*(</script>)',     demons_data_js),
        (r'(<script>\s*)const DEMONS_HISTORY\s*=\s*\{.*?\};\s*(</script>)',  history_js),
        (r'(<script>\s*)const STATS_DATA\s*=\s*\{.*?\};\s*(</script>)',      stats_js),
        (r'(<script>\s*)const STATS2_DATA\s*=\s*\{.*?\};\s*(</script>)',     stats2_js),
    ]

    for pattern, replacement in replacements:
        new_content = re.sub(pattern, r'\g<1>' + replacement + r'\2',
                             content, flags=re.DOTALL, count=1)
        if new_content == content:
            print(f'WARNING: pattern not matched — {replacement[:40]}')
        content = new_content

    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

    size_mb = os.path.getsize(HTML_FILE) / (1024 * 1024)
    print(f'\nDone — index.html rebuilt ({size_mb:.1f} MB)')
    print(f'Built at: {now.strftime("%Y-%m-%d %H:%M UTC")}')


if __name__ == '__main__':
    main()
