#!/usr/bin/env python3
"""Merge W3 recon profiles (_enrich_out_*.jsonl) into a durable DB ledger.

- Idempotent: keyed by `rank` (unique in _enrich_input_all.json). Re-running is safe.
- Computes coverage vs the full ranked universe and writes `_enrich_remaining.json`
  (the not-yet-enriched, ranked) so the next wave only processes what's missing.
"""
import sqlite3, glob, json, os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEYS = ["rank","name","state","confirmed_private","ownership_type","owner_or_parent",
        "principals","succession_signal","founded_year","fleet_size_est","employees_est",
        "service_types","districts_or_customers","recent_news","website","confidence",
        "sources","fit_notes"]

con = sqlite3.connect("2_database/summit_targets.db"); cur = con.cursor()
cols = ", ".join(f'"{k}" {"INTEGER PRIMARY KEY" if k=="rank" else "TEXT"}' for k in KEYS)
cur.execute(f"CREATE TABLE IF NOT EXISTS enrichment ({cols})")
con.commit()

rows, bad = [], 0
for f in sorted(glob.glob("5_working/batch_outputs/_enrich_out_*.jsonl")):
    for line in open(f):
        line = line.strip()
        if not line: continue
        try:
            o = json.loads(line)
            rows.append([o.get(k) if not isinstance(o.get(k), (list, dict)) else json.dumps(o.get(k)) for k in KEYS])
        except Exception:
            bad += 1
ins = f"INSERT OR REPLACE INTO enrichment ({','.join(chr(34)+k+chr(34) for k in KEYS)}) VALUES ({','.join('?'*len(KEYS))})"
cur.executemany(ins, rows)
con.commit()

enriched = cur.execute("SELECT COUNT(*) FROM enrichment").fetchone()[0]
done_ranks = {r[0] for r in cur.execute("SELECT rank FROM enrichment")}
print(f"Merged {len(rows)} profile lines ({bad} malformed). Enrichment ledger now: {enriched:,} rows.")

# coverage + remaining
allr = json.load(open("5_working/inputs/_enrich_input_all.json")) if os.path.exists("5_working/inputs/_enrich_input_all.json") else []
remaining = [e for e in allr if e["rank"] not in done_ranks]
json.dump(remaining, open("5_working/inputs/_enrich_remaining.json", "w"))
print(f"Universe: {len(allr):,} | enriched: {len(done_ranks):,} | REMAINING: {len(remaining):,} -> _enrich_remaining.json")
if allr:
    print(f"Coverage: {100*len(done_ranks)/len(allr):.1f}%")
# quick quality peek
for k, c in cur.execute("SELECT confirmed_private,COUNT(*) FROM enrichment GROUP BY 1 ORDER BY 2 DESC"):
    print(f"  confirmed_private={k}: {c}")
con.close()
