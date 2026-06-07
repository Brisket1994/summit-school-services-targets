#!/usr/bin/env python3
"""Materialize a single `master_targets` table in the DB from the full join,
so every slice is `SELECT ... FROM master_targets WHERE ...` (one table, no joins).
Rebuilds from master_targets_FULL.csv (which _export_full.py produces)."""
import sqlite3, csv, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SRC = "3_deliverables/master_targets_FULL.csv"
INTCOLS = {"a_rank","bench_rank","fleet_buses","drivers","founded","da_employees"}
REALCOLS = {"composite","data_confidence"}

rows = list(csv.DictReader(open(SRC)))
cols = list(rows[0].keys())
def decl(c):
    return f'"{c}" INTEGER' if c in INTCOLS else f'"{c}" REAL' if c in REALCOLS else f'"{c}" TEXT'

con = sqlite3.connect("2_database/summit_targets.db"); cur = con.cursor()
cur.execute("DROP TABLE IF EXISTS master_targets")
cur.execute(f"CREATE TABLE master_targets ({', '.join(decl(c) for c in cols)})")

def coerce(c, v):
    if v is None or v == "": return None
    if c in INTCOLS:
        try: return int(float(v))
        except: return None
    if c in REALCOLS:
        try: return float(v)
        except: return None
    return v

ins = f"INSERT INTO master_targets ({','.join(chr(34)+c+chr(34) for c in cols)}) VALUES ({','.join('?'*len(cols))})"
cur.executemany(ins, [[coerce(c, r.get(c)) for c in cols] for r in rows])
for ix in ["track","state","a_rank","composite","census_dot_number"]:
    cur.execute(f'CREATE INDEX "idx_mt_{ix}" ON master_targets("{ix}")')
con.commit()
n = cur.execute("SELECT COUNT(*) FROM master_targets").fetchone()[0]
na = cur.execute("SELECT COUNT(*) FROM master_targets WHERE track='A'").fetchone()[0]
print(f"master_targets table: {n} rows x {len(cols)} cols | A-list {na}")
print("Example slices now possible:")
print("  SELECT company,state,fleet_buses,founded FROM master_targets WHERE track='A' AND state='PA' ORDER BY composite DESC;")
print("  SELECT state,COUNT(*) FROM master_targets WHERE track='A' GROUP BY state ORDER BY 2 DESC;")
con.close()
