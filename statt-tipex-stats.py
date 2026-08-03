#!/usr/bin/env python3
"""statt-tipex.de Zugriffsstatistik mit Praxis-Code-Auswertung und Log-Rotation"""
import re, os, gzip, glob
from datetime import datetime, timedelta
from collections import Counter, defaultdict

LOG_PATTERN = "/var/log/nginx/statt-tipex.access.log*"
OUT = "/var/www/statt-tipex/_stats/index.html"
TAGE = 30

log_re = re.compile(r'(\S+) - - \[([^\]]+)\] "(\S+) (\S+) [^"]*" (\d+) (\d+)')
ping_re = re.compile(r'/ping\?t=([A-Za-z0-9]+)')

now = datetime.now()
cutoff = now - timedelta(days=TAGE)

hits_per_day = Counter()
tenant_hits = Counter()
total = 0
pages = Counter()

# Read all log files including rotated ones
log_files = sorted(glob.glob(LOG_PATTERN), reverse=True)
for log_file in log_files:
    try:
        if log_file.endswith(".gz"):
            f = gzip.open(log_file, "rt", errors="replace")
        else:
            f = open(log_file, errors="replace")
        for line in f:
            m = log_re.search(line)
            if not m:
                continue
            ip, date_str, method, path, status, size = m.groups()
            try:
                dt = datetime.strptime(date_str.split()[0], "%d/%b/%Y:%H:%M:%S")
            except:
                continue
            if dt < cutoff:
                continue
            day = dt.strftime("%Y-%m-%d")
            total += 1
            hits_per_day[day] += 1
            pages[path.split("?")[0]] += 1
            pm = ping_re.search(path)
            if pm:
                tenant_hits[pm.group(1)] += 1
        f.close()
    except Exception as e:
        print(f"Skipping {log_file}: {e}")

# Generate HTML
days_sorted = sorted(hits_per_day.keys())
tenants_sorted = sorted(tenant_hits.items(), key=lambda x: -x[1])
pages_sorted = sorted(pages.items(), key=lambda x: -x[1])[:15]
max_hits = max(hits_per_day.values()) if hits_per_day else 1
max_tenant = max(tenant_hits.values()) if tenant_hits else 1

html = f"""<!DOCTYPE html><html lang="de"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>statt-tipex.de Statistik</title>
<style>
body{{font-family:-apple-system,system-ui,sans-serif;max-width:900px;margin:0 auto;padding:24px;background:#faf9f7;color:#1c1917}}
h1{{font-size:24px;font-weight:800}}h1 span{{background:#1c1917;color:#fff;padding:2px 10px;border-radius:6px;font-size:14px;vertical-align:middle}}
h2{{font-size:18px;color:#44403c;margin-top:32px}}
.sub{{color:#a8a29e;font-size:13px;margin-bottom:24px}}
table{{width:100%;border-collapse:collapse;margin:8px 0 24px}}
th{{text-align:left;padding:8px 12px;background:#f5f5f4;color:#44403c;font-size:12px;font-weight:600}}
td{{padding:6px 12px;border-bottom:1px solid #e7e5e4;font-size:13px}}
.bar{{height:18px;background:#6b97b8;border-radius:4px;display:inline-block;vertical-align:middle}}
tr:nth-child(even){{background:#faf9f7}}
.today{{background:#f0fdfa!important;font-weight:600}}
</style></head><body>
<h1>statt-tipex.de <span>Statistik</span></h1>
<div class="sub">Letzte {TAGE} Tage &middot; Stand: {now.strftime("%d.%m.%Y %H:%M")} Uhr &middot; {total} Zugriffe</div>

<h2>Zugriffe pro Tag</h2>
<table><tr><th>Datum</th><th>Zugriffe</th><th></th></tr>
"""

today_str = now.strftime("%Y-%m-%d")
for day in days_sorted:
    pct = int(hits_per_day[day] / max_hits * 250)
    cls = ' class="today"' if day == today_str else ''
    html += f'<tr{cls}><td>{day}</td><td>{hits_per_day[day]}</td><td><span class="bar" style="width:{pct}px"></span></td></tr>\n'

html += "</table>"

if tenants_sorted:
    html += '<h2>Aufrufe pro Praxis-Code</h2>\n<table><tr><th>Code</th><th>Aufrufe</th><th></th></tr>\n'
    for code, count in tenants_sorted:
        pct = int(count / max_tenant * 250)
        html += f'<tr><td>{code}</td><td>{count}</td><td><span class="bar" style="width:{pct}px"></span></td></tr>\n'
    html += "</table>"

html += '<h2>Meistaufgerufene Seiten</h2>\n<table><tr><th>Pfad</th><th>Aufrufe</th></tr>\n'
for path, count in pages_sorted:
    html += f'<tr><td>{path}</td><td>{count}</td></tr>\n'

html += "</table></body></html>"

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w") as f:
    f.write(html)
print(f"Stats: {total} hits, {len(tenants_sorted)} tenants, {len(days_sorted)} days -> {OUT}")
