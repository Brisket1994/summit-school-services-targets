#!/usr/bin/env python3
"""Build master_targets_FULL.csv — every field we pulled, per ranked target.
Unions ranking/scores + Data Axle entity fields + web recon (enrichment) +
agent FMCSA + census (fmcsa_census + extra census_bus fields via USDOT)."""
import sqlite3, csv, json, os
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
con = sqlite3.connect("2_database/summit_targets.db"); con.row_factory = sqlite3.Row; cur = con.cursor()

ranked = {int(r["rank_old"]): r for r in csv.DictReader(open("3_deliverables/master_targets_ranked.csv"))}
web   = {int(r["rank"]): dict(r) for r in cur.execute("SELECT * FROM enrichment")}
agent = {int(r["rank"]): dict(r) for r in cur.execute("SELECT * FROM fmcsa")}
fc    = {int(r["rank"]): dict(r) for r in cur.execute("SELECT * FROM fmcsa_census")}
cbus  = {(r["dot_number"] or "").strip(): dict(r) for r in cur.execute("SELECT * FROM census_bus")}
base  = {e["rank"]: e for e in json.load(open("5_working/inputs/_enrich_input_all.json"))}

RANK_COLS = ["a_rank","bench_rank","track","company","state","hq","composite","data_confidence",
             "founded","fleet_buses","drivers","fmcsa_source","usdot","fmcsa_status","safety_rating",
             "_sf","_su","_geo","_ind","_oh","_rel"]
DA_COLS   = ["address","employees","revenue_est","year","size_tier","school","special_needs","phone","lead_exec"]
WEB_SKIP  = {"rank","name","state"}
AGENT_SKIP= {"rank","name","state"}
FC_SKIP   = {"rank","name"}
CB_EXTRA  = ["dba_name","phy_street","phy_zip","phy_cnty","ownschool_1_8","ownschool_9_15",
             "ownschool_16","ownbus_16","ownvan_1_8","ownvan_9_15","safety_rating_date",
             "phone","email_address","carrier_operation","business_org_desc"]

out = []
for rk, rr in ranked.items():
    rec = {k: rr.get(k, "") for k in RANK_COLS}
    b = base.get(rk, {})
    for k in DA_COLS: rec["da_"+k] = b.get(k, "")
    w = web.get(rk, {})
    for k, v in w.items():
        if k not in WEB_SKIP: rec["web_"+k] = v
    a = agent.get(rk, {})
    for k, v in a.items():
        if k not in AGENT_SKIP: rec["agent_"+k] = v
    c = fc.get(rk, {})
    for k, v in c.items():
        if k not in FC_SKIP: rec["census_"+k] = v
    dot = (c.get("dot_number") or "").strip()
    cb = cbus.get(dot, {}) if dot else {}
    for k in CB_EXTRA: rec["census_"+k] = cb.get(k, "")
    out.append(rec)

out.sort(key=lambda r: (0 if r["track"]=="A" else 1, int(r["a_rank"] or r["bench_rank"] or 0)))
cols = list(dict.fromkeys(k for r in out for k in r))
with open("3_deliverables/master_targets_FULL.csv","w",newline="") as f:
    wri = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); wri.writeheader()
    for r in out: wri.writerow(r)
print(f"Wrote 3_deliverables/master_targets_FULL.csv — {len(out):,} rows x {len(cols)} columns")
print("Column groups:")
for pre in ["(rank/score)","da_","web_","agent_","census_"]:
    if pre=="(rank/score)": cs=[c for c in cols if not c.startswith(("da_","web_","agent_","census_"))]
    else: cs=[c for c in cols if c.startswith(pre)]
    print(f"  {pre:14} {len(cs)}: {cs}")
con.close()
