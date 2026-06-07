#!/usr/bin/env python3
"""Build/rebuild _fmcsa_fallback.json = rankable targets still needing FMCSA:
yes+unsure, census match low/none, and not already in agent `fmcsa` table.
Run before each fallback wave; it shrinks as waves complete."""
import sqlite3, json, os, re
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
con=sqlite3.connect("2_database/summit_targets.db"); cur=con.cursor()
cp={int(r[0]):(r[1] or "").strip().lower() for r in cur.execute("SELECT rank,confirmed_private FROM enrichment")}
def nm(v): return "yes" if v.startswith("yes") else "no" if v.startswith("no") else "unsure" if v.startswith("unsure") else "o"
mc={int(r[0]):r[1] for r in cur.execute("SELECT rank,match_conf FROM fmcsa_census")}
# 'attempted' = ANY row in fmcsa (agent wave OR prior fallback). Don't re-attempt confirmed 'none'.
attempted={int(r[0]) for r in cur.execute("SELECT rank FROM fmcsa")}
allr=json.load(open("5_working/inputs/_enrich_input_all.json"))
gaps=[e for e in allr if nm(cp.get(e["rank"],"")) in ("yes","unsure")
      and mc.get(e["rank"]) in ("low","none") and e["rank"] not in attempted]
slim=[{"rank":e["rank"],"name":e["name"],"state":e["state"],"hq":e["hq"],"address":e["address"]} for e in gaps]
json.dump(slim, open("5_working/inputs/_fmcsa_fallback.json","w"))
print(f"Fallback gap list: {len(slim)} targets -> _fmcsa_fallback.json")
con.close()
