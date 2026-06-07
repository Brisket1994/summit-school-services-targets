#!/usr/bin/env python3
"""Merge FMCSA/registry recon (_fmcsa_out_*.jsonl) into DB table `fmcsa`.
Idempotent (keyed by rank). Regenerates `_fmcsa_remaining.json` (not-yet-done, ranked).
On first run with no outputs, just initializes the table + remaining=full universe.
"""
import sqlite3, glob, json, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KEYS = ["rank","name","state","usdot","mc","power_units","drivers","carrier_operation",
        "safety_rating","fmcsa_address","fmcsa_status","inc_date","officers","entity_status",
        "registry_source","fmcsa_confidence","notes","sources"]
con = sqlite3.connect("2_database/summit_targets.db"); cur = con.cursor()
cols = ", ".join(f'"{k}" {"INTEGER PRIMARY KEY" if k=="rank" else "TEXT"}' for k in KEYS)
cur.execute(f"CREATE TABLE IF NOT EXISTS fmcsa ({cols})")
con.commit()

rows, bad = [], 0
for f in sorted(glob.glob("5_working/batch_outputs/_fmcsa_out_*.jsonl")):
    for line in open(f):
        line = line.strip()
        if not line: continue
        try:
            o = json.loads(line)
            rows.append([o.get(k) if not isinstance(o.get(k), (list, dict)) else json.dumps(o.get(k)) for k in KEYS])
        except Exception:
            bad += 1
if rows:
    ins = f"INSERT OR REPLACE INTO fmcsa ({','.join(chr(34)+k+chr(34) for k in KEYS)}) VALUES ({','.join('?'*len(KEYS))})"
    cur.executemany(ins, rows); con.commit()

done = {r[0] for r in cur.execute("SELECT rank FROM fmcsa")}
n = cur.execute("SELECT COUNT(*) FROM fmcsa").fetchone()[0]
allr = json.load(open("5_working/inputs/_fmcsa_input_all.json")) if os.path.exists("5_working/inputs/_fmcsa_input_all.json") else []
remaining = [e for e in allr if e["rank"] not in done]
json.dump(remaining, open("5_working/inputs/_fmcsa_remaining.json", "w"))
print(f"Merged {len(rows)} lines ({bad} malformed). fmcsa ledger: {n:,}.")
print(f"Universe {len(allr):,} | done {len(done):,} | REMAINING {len(remaining):,} -> _fmcsa_remaining.json"
      + (f" ({100*len(done)/len(allr):.1f}%)" if allr else ""))
con.close()
