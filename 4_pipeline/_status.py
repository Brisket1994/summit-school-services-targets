#!/usr/bin/env python3
"""Snapshot of pipeline state — run anytime to see where things stand."""
import sqlite3, os, glob, json

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
con = sqlite3.connect("2_database/summit_targets.db"); cur = con.cursor()

def tbl(n):
    try: return cur.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0]
    except Exception: return "—"

print("=== DB tables ===")
for t in ("companies", "targets", "entities"):
    print(f"  {t:10}: {tbl(t):>10,}" if isinstance(tbl(t), int) else f"  {t:10}: {tbl(t)}")

print("\n=== W2 verdicts (school+special universe) ===")
try:
    for v, c in cur.execute("SELECT verdict,COUNT(*) FROM entities WHERE verdict IS NOT NULL GROUP BY verdict ORDER BY 2 DESC"):
        print(f"  {c:>7,}  {v}")
    priv = cur.execute("SELECT COUNT(*) FROM entities WHERE verdict='private_contractor'").fetchone()[0]
    print(f"  -> confirmed-private universe: {priv:,}")
except Exception as e:
    print("  (no verdicts yet)", e)

print("\n=== W3 enrichment progress ===")
try:
    n = cur.execute("SELECT COUNT(*) FROM enrichment").fetchone()[0]
    print(f"  enriched (DB ledger): {n:,}")
    for k, c in cur.execute("SELECT confirmed_private,COUNT(*) FROM enrichment GROUP BY 1 ORDER BY 2 DESC"):
        print(f"    confirmed_private={k}: {c:,}")
except Exception:
    print("  (enrichment table not created yet)")
outs = glob.glob("5_working/batch_outputs/_enrich_out_*.jsonl")
lines = sum(sum(1 for _ in open(f)) for f in outs)
print(f"  _enrich_out_*.jsonl files: {len(outs)} ({lines} profile lines on disk)")
if os.path.exists("5_working/inputs/_enrich_input_all.json"):
    tot = len(json.load(open("5_working/inputs/_enrich_input_all.json")))
    print(f"  ranked confirmed-private to enrich: {tot:,}")

con.close()
print("\nSee RESUME.md for full state + how-to-resume.")
