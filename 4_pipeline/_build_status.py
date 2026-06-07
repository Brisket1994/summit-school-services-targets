#!/usr/bin/env python3
"""Generate the night-one work artifacts from master_targets:
- 3_deliverables/master_targets.jsonl     (full composite, machine-readable)
- 5_working/inputs/alist_queue.jsonl      (A-list research work items)
- targets_status.csv                       (per-target progress tracker; idempotent — preserves existing progress)
"""
import sqlite3, json, csv, os, re
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
con = sqlite3.connect("2_database/summit_targets.db"); con.row_factory = sqlite3.Row; cur = con.cursor()

def slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "").lower()).strip("-")
    return s[:40] or "unknown"

allrows = [dict(r) for r in cur.execute("SELECT * FROM master_targets ORDER BY track, a_rank, bench_rank")]
with open("3_deliverables/master_targets.jsonl", "w") as f:
    for r in allrows: f.write(json.dumps(r)+"\n")

A = [dict(r) for r in cur.execute("SELECT * FROM master_targets WHERE track='A' ORDER BY a_rank")]
QFIELDS = ["a_rank","company","state","hq","da_address","fleet_buses","drivers","founded",
           "web_ownership_type","web_owner_or_parent","web_principals","web_succession_signal",
           "web_districts_or_customers","website","da_phone","census_phone","census_email_address",
           "census_dot_number","web_service_types","web_recent_news","web_fit_notes","composite","data_confidence"]
queue = []
for r in A:
    slug = f"{int(r['a_rank']):04d}-{slugify(r['company'])}"
    item = {k: r.get(k) for k in QFIELDS}
    item["slug"] = slug
    item["folder"] = f"6_targets/{slug}"
    queue.append(item)
with open("5_working/inputs/alist_queue.jsonl", "w") as f:
    for it in queue: f.write(json.dumps(it)+"\n")

# status tracker — preserve any existing progress on re-run
STATUS = "targets_status.csv"
SCOLS = ["a_rank","slug","company","state","hq","fleet_buses","founded","composite","folder",
         "researched","research_date","packet_path","facts_path","draft_path","reviewed","sent","notes"]
existing = {}
if os.path.exists(STATUS):
    for row in csv.DictReader(open(STATUS)):
        existing[row["slug"]] = row
out = []
for it in queue:
    slug = it["slug"]
    prev = existing.get(slug, {})
    out.append({
        "a_rank": it["a_rank"], "slug": slug, "company": it["company"], "state": it["state"],
        "hq": it["hq"], "fleet_buses": it["fleet_buses"], "founded": it["founded"],
        "composite": it["composite"], "folder": it["folder"],
        "researched": prev.get("researched","0"), "research_date": prev.get("research_date",""),
        "packet_path": prev.get("packet_path",""), "facts_path": prev.get("facts_path",""),
        "draft_path": prev.get("draft_path",""), "reviewed": prev.get("reviewed","0"),
        "sent": prev.get("sent","0"), "notes": prev.get("notes",""),
    })
with open(STATUS, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=SCOLS); w.writeheader(); w.writerows(out)

done = sum(1 for r in out if r["researched"] not in ("0","",None))
print(f"master_targets.jsonl: {len(allrows)} | alist_queue.jsonl: {len(queue)} | targets_status.csv: {len(out)} (researched so far: {done})")
print(f"Nights @100/night to cover A-list: ~{-(-len(queue)//100)}")
con.close()
