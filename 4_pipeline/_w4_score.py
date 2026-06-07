#!/usr/bin/env python3
"""W4 — confidence-aware final score & ranking of Summit tuck-in targets.

Unifies all layers per target (rank-keyed):
  Data Axle (entities) + web recon (enrichment) + FMCSA (census high/med -> agent -> none).
Two parallel tracks: A-list (web confirmed_private=yes) and Bench (unsure). 'no' excluded.
Modular weights (W) + per-dimension functions so a later market-data overlay is a clean re-run.
Outputs: master_targets_ranked.csv, master_targets_A_top50.md, master_targets_profiles.jsonl.
"""
import sqlite3, json, re, os, csv
NOW = 2026
W = {"size_fit":25, "succession":20, "geo":15, "independence":15, "operating_health":15, "relevance":10}
EXP = {"FL","NY","PA","MO","GA","IN"}
SUMMIT = {"AK","AL","AZ","CA","CO","CT","FL","GA","IA","ID","IL","IN","KS","LA","MA","MD","MI","MN",
          "MO","MS","NC","NE","NH","NJ","NM","NY","OH","OR","PA","RI","SC","TN","TX","VA","WA"}

def to_int(v):
    if v is None: return 0
    m = re.findall(r"\d+", str(v).replace(",",""))
    return int(m[0]) if m else 0

def year_from(*vals):
    yrs = []
    for v in vals:
        for y in re.findall(r"(18|19|20)\d{2}", str(v or "")):
            yy = int(y + re.search(r"(18|19|20)(\d{2})", str(v)).group(2)) if False else None
    # simpler: scan each val for a 4-digit year
    out = []
    for v in vals:
        for mm in re.findall(r"(?:18|19|20)\d{2}", str(v or "")):
            iy = int(mm)
            if 1850 <= iy <= NOW: out.append(iy)
    return min(out) if out else None

def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    con = sqlite3.connect("2_database/summit_targets.db"); con.row_factory = sqlite3.Row; cur = con.cursor()
    base = {e["rank"]: e for e in json.load(open("5_working/inputs/_enrich_input_all.json"))}
    web = {int(r["rank"]): dict(r) for r in cur.execute("SELECT * FROM enrichment")}
    agent = {int(r["rank"]): dict(r) for r in cur.execute("SELECT * FROM fmcsa")}
    cens = {int(r["rank"]): dict(r) for r in cur.execute("SELECT * FROM fmcsa_census")}

    def cp(rk):
        v = (web.get(rk, {}).get("confirmed_private") if rk in web else "") or ""
        v = v.strip().lower()
        return "yes" if v.startswith("yes") else "no" if v.startswith("no") else "unsure" if v.startswith("unsure") else "unknown"

    rows = []
    for rk, b in base.items():
        track_cp = cp(rk)
        if track_cp == "no":
            continue  # excluded (PE/strategic/defunct)
        w = web.get(rk, {})
        # ---- unified FMCSA (census high/med preferred, else agent valid, else none) ----
        c = cens.get(rk); a = agent.get(rk)
        fm_src = "none"; fleet = drivers = 0; status = ""; safety = ""; crash = ""; officers = ""; usdot = ""
        if c and (c["match_conf"] in ("high","medium")):
            fm_src = "census(%s)" % c["match_conf"]
            fleet = max(to_int(c["bus_units"]), to_int(c["ownschool_total"]), to_int(c["power_units"]))
            drivers = max(to_int(c["total_drivers"]), to_int(c["total_cdl"]))
            status = (c["status_code"] or ""); safety = (c["safety_rating"] or ""); crash = (c["recordable_crash_rate"] or "")
            officers = c["officers"] or ""; usdot = c["dot_number"] or ""
        elif a and re.sub(r"\D","",(a["usdot"] or "")):
            fm_src = "agent"
            fleet = to_int(a["power_units"]); drivers = to_int(a["drivers"])
            status = (a["fmcsa_status"] or ""); safety = (a["safety_rating"] or ""); officers = a["officers"] or ""
            usdot = a["usdot"] or ""
        # ---- founding year (earliest plausible across sources) ----
        founded = year_from(c["add_date"] if c else None, a["inc_date"] if a else None,
                            w.get("founded_year"), b.get("year"))
        # ---- dimension scores ----
        # size_fit: prefer verified fleet, else drivers, else Data Axle employees
        if fleet > 0:
            sf = 40 if fleet<5 else 65 if fleet<10 else 100 if fleet<=150 else 70 if fleet<=400 else 45
        elif drivers > 0:
            sf = 40 if drivers<5 else 65 if drivers<12 else 100 if drivers<=200 else 70 if drivers<=500 else 45
        else:
            emp = to_int(b.get("employees"))
            sf = (50 if emp<10 else 80 if emp<=300 else 60) if emp>0 else 40
        # succession
        if founded:
            age = NOW - founded
            su = 100 if age>=40 else 85 if age>=25 else 60 if age>=15 else 40 if age>=8 else 25
        else:
            su = 50
        # independence (web ownership_type)
        ot = (w.get("ownership_type") or "").lower()
        ind = 100 if ("independent" in ot or "family" in ot) else 60 if (ot=="" or "unknown" in ot) else 40
        # operating health (FMCSA)
        if fm_src == "none":
            oh = 50
        else:
            oh = 0
            st = status.upper()
            oh += 50 if st.startswith("A") or "ACTIVE" in st else 20 if st in ("","UNKNOWN") else 0
            sr = safety.upper()
            oh += 30 if (sr in ("","NONE","NOT RATED") or sr.startswith("S")) else 12 if sr.startswith("C") else 0
            cr = to_int(crash)
            oh += 20 if cr==0 else 10
            oh = min(oh, 100)
        # relevance
        rel = 100 if (b.get("school") and b.get("special_needs")) else 90 if b.get("school") else 75
        # geo
        stt = (b.get("state") or "").upper()
        geo = 100 if stt in EXP else 70 if stt in SUMMIT else 30
        comp = round(sum(W[k]*v/100 for k,v in
                     {"size_fit":sf,"succession":su,"geo":geo,"independence":ind,
                      "operating_health":oh,"relevance":rel}.items()), 1)
        dataconf = round(sum([fm_src!="none", bool(founded), track_cp=="yes",
                              fleet>0, bool((w.get("website") or "").strip())])/5, 2)
        rows.append({
            "rank_old": rk, "track": "A" if track_cp=="yes" else "BENCH",
            "company": b["name"], "state": stt, "hq": b.get("hq"),
            "composite": comp, "data_confidence": dataconf,
            "fleet_buses": fleet or "", "drivers": drivers or "", "founded": founded or "",
            "fmcsa_source": fm_src, "usdot": usdot, "fmcsa_status": status,
            "safety_rating": safety, "ownership_type": w.get("ownership_type",""),
            "owner_or_parent": w.get("owner_or_parent",""), "principals": w.get("principals","") or officers,
            "succession_signal": w.get("succession_signal",""), "service_types": w.get("service_types",""),
            "districts": w.get("districts_or_customers",""), "recent_news": w.get("recent_news",""),
            "website": w.get("website") or b.get("website"), "size_tier": b.get("size_tier"),
            "da_employees": b.get("employees"), "da_revenue_est": b.get("revenue_est"),
            "fit_notes": w.get("fit_notes",""),
            "_sf":round(sf),"_su":round(su),"_geo":geo,"_ind":ind,"_oh":round(oh),"_rel":rel,
        })

    A = sorted([r for r in rows if r["track"]=="A"], key=lambda x:(-x["composite"],-x["data_confidence"]))
    B = sorted([r for r in rows if r["track"]=="BENCH"], key=lambda x:(-x["composite"],-x["data_confidence"]))
    for i,r in enumerate(A,1): r["a_rank"]=i
    for i,r in enumerate(B,1): r["bench_rank"]=i

    cols = ["a_rank","bench_rank","track","company","state","hq","composite","data_confidence",
            "fleet_buses","drivers","founded","fmcsa_source","usdot","fmcsa_status","safety_rating",
            "ownership_type","owner_or_parent","principals","succession_signal","service_types",
            "districts","recent_news","website","size_tier","da_employees","da_revenue_est","fit_notes",
            "_sf","_su","_geo","_ind","_oh","_rel","rank_old"]
    allrows = A + B
    with open("3_deliverables/master_targets_ranked.csv","w",newline="") as f:
        wri = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore"); wri.writeheader()
        for r in allrows: wri.writerow(r)
    with open("3_deliverables/master_targets_profiles.jsonl","w") as f:
        for r in allrows: f.write(json.dumps(r)+"\n")
    with open("3_deliverables/master_targets_A_top50.md","w") as f:
        f.write("# Summit tuck-in targets — A-list top 50 (web-confirmed private)\n\n")
        f.write("| # | Score | Conf | Company | ST | Buses | Founded | Ownership | Succession |\n|--:|--:|--:|---|---|--:|--:|---|---|\n")
        for r in A[:50]:
            f.write(f"| {r['a_rank']} | {r['composite']} | {r['data_confidence']} | {r['company'][:30]} | {r['state']} "
                    f"| {r['fleet_buses'] or '—'} | {r['founded'] or '—'} | {(r['ownership_type'] or '—')[:14]} | {(r['succession_signal'] or '—')[:8]} |\n")

    print(f"A-list (confirmed private): {len(A):,} | Bench (unsure): {len(B):,} | excluded 'no' dropped")
    fm = sum(1 for r in allrows if r['fmcsa_source']!='none')
    print(f"With FMCSA data: {fm:,}/{len(allrows):,} ({100*fm/len(allrows):.0f}%) | with founded year: {sum(1 for r in allrows if r['founded']):,} | with fleet#: {sum(1 for r in allrows if r['fleet_buses']):,}")
    print("\n=== A-LIST TOP 25 ===")
    print(f"{'#':>3} {'Scr':>5} {'Cf':>4} {'ST':>3} {'Bus':>4} {'Fnd':>5}  Company")
    for r in A[:25]:
        print(f"{r['a_rank']:>3} {r['composite']:>5} {r['data_confidence']:>4} {r['state']:>3} {str(r['fleet_buses']):>4} {str(r['founded']):>5}  {r['company'][:34]}")
    print("\nExports: master_targets_ranked.csv | master_targets_A_top50.md | master_targets_profiles.jsonl")
    con.close()

if __name__ == "__main__":
    main()
