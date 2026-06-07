#!/usr/bin/env python3
"""Match our 3,703 targets to the local FMCSA census_bus table (no LLM, no API).
Conservative name+state+city matching; writes table `fmcsa_census`; cross-validates
precision against the agent-built `fmcsa` table.
"""
import sqlite3, json, re, os
from collections import defaultdict

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GENERIC = {"BUS","BUSES","BUSING","BUSSING","SCHOOL","TRANSPORTATION","TRANSPORT","TRANS","TRANSP",
           "SERVICE","SERVICES","SVC","SVCS","INC","LLC","CORP","CO","LTD","LP","COMPANY","THE",
           "LINES","LINE","CHARTER","COACH","COACHES","TRANSIT","VAN","VANS","TOURS","TOUR","OF",
           "AND","&","ENTERPRISES","GROUP","SYSTEMS","SYSTEM"}

def toks(name):
    return [t for t in re.sub(r"[^A-Z0-9 ]", " ", (name or "").upper()).split() if t]
def distinctive(name):
    return {t for t in toks(name) if t not in GENERIC and len(t) > 1}
def city_of(hq):
    return (hq or "").split(",")[0].strip().upper()

def main():
    con = sqlite3.connect("2_database/summit_targets.db"); con.row_factory = sqlite3.Row; cur = con.cursor()
    # pre-tokenize census, inverted index per state: distinctive token -> [rowids]
    cens = cur.execute("SELECT rowid,legal_name,dba_name,phy_city,phy_state,power_units,bus_units,"
        "ownschool_1_8,ownschool_9_15,ownschool_16,total_drivers,total_cdl,status_code,safety_rating,"
        "recordable_crash_rate,add_date,mcs150_date,company_officer_1,company_officer_2,phone,"
        "email_address,dot_number FROM census_bus").fetchall()
    crow = {r["rowid"]: r for r in cens}
    cdist = {}; cfull = {}
    inv = defaultdict(lambda: defaultdict(list))  # state -> token -> [rowid]
    for r in cens:
        nm = (r["legal_name"] or "") + " " + (r["dba_name"] or "")
        d = distinctive(nm); cdist[r["rowid"]] = d; cfull[r["rowid"]] = set(toks(nm))
        st = (r["phy_state"] or "").upper()
        for t in d:
            inv[st][t].append(r["rowid"])
    print(f"Indexed {len(cens):,} census carriers")

    targets = json.load(open("5_working/inputs/_enrich_input_all.json"))
    KEYS = ["rank","name","matched","match_conf","dot_number","census_legal_name","census_city",
            "power_units","bus_units","ownschool_total","total_drivers","total_cdl","status_code",
            "safety_rating","recordable_crash_rate","add_date","mcs150_date","officers"]
    cur.execute("DROP TABLE IF EXISTS fmcsa_census")
    cur.execute(f"CREATE TABLE fmcsa_census ({', '.join(f'\"{k}\" TEXT' for k in KEYS)})")

    out = []
    for t in targets:
        st = (t["state"] or "").upper(); tname = t["name"]; tcity = city_of(t.get("hq"))
        td = distinctive(tname); tf = set(toks(tname))
        cand = set()
        for tok in td:
            cand.update(inv[st].get(tok, []))
        best = None; best_score = 0
        for rid in cand:
            shared = td & cdist[rid]
            if not shared: continue
            jac = len(tf & cfull[rid]) / max(1, len(tf | cfull[rid]))
            citym = 1 if tcity and tcity == (crow[rid]["phy_city"] or "").upper() else 0
            distov = len(shared) / max(1, len(td))
            score = jac + 0.3*citym + 0.2*distov
            if score > best_score:
                best_score = score; best = (rid, shared, jac, citym)
        rec = {k: "" for k in KEYS}; rec["rank"] = t["rank"]; rec["name"] = tname
        if best:
            rid, shared, jac, citym = best
            r = crow[rid]
            # conservative confidence
            conf = "high" if (citym and jac >= 0.5) or jac >= 0.7 else \
                   "medium" if jac >= 0.4 or (citym and len(shared) >= 1) else "low"
            sch = sum(int(r[c] or 0) for c in ("ownschool_1_8","ownschool_9_15","ownschool_16"))
            rec.update(matched="Y", match_conf=conf, dot_number=r["dot_number"],
                census_legal_name=r["legal_name"], census_city=r["phy_city"],
                power_units=r["power_units"], bus_units=r["bus_units"], ownschool_total=str(sch),
                total_drivers=r["total_drivers"], total_cdl=r["total_cdl"], status_code=r["status_code"],
                safety_rating=r["safety_rating"], recordable_crash_rate=r["recordable_crash_rate"],
                add_date=r["add_date"], mcs150_date=r["mcs150_date"],
                officers=" | ".join(x for x in (r["company_officer_1"], r["company_officer_2"]) if x))
        else:
            rec.update(matched="N", match_conf="none")
        out.append(rec)
    cur.executemany(f"INSERT INTO fmcsa_census VALUES ({','.join('?'*len(KEYS))})",
                    [[r[k] for k in KEYS] for r in out]); con.commit()

    from collections import Counter
    mc = Counter(r["match_conf"] for r in out)
    matched = sum(1 for r in out if r["matched"] == "Y")
    print(f"\n=== MATCH RESULTS (3,703 targets) ===")
    print(f"  matched: {matched:,} ({100*matched/len(out):.0f}%) | confidence: {dict(mc)}")
    hi = sum(1 for r in out if r['match_conf']=='high')
    print(f"  high-confidence: {hi:,} | medium: {mc.get('medium',0):,} | low: {mc.get('low',0):,} | none: {mc.get('none',0):,}")

    # cross-validate vs agent fmcsa table (DOT number agreement where both have one)
    agent = {r[0]: (r[1] or "").strip() for r in cur.execute("SELECT rank,usdot FROM fmcsa")}
    both = agree = 0
    for r in out:
        a = agent.get(r["rank"], "")
        a_digits = re.sub(r"\D","", a)
        c_digits = re.sub(r"\D","", r["dot_number"] or "")
        if a_digits and c_digits:
            both += 1
            if a_digits == c_digits: agree += 1
    print(f"\n=== CROSS-VALIDATION vs agent FMCSA (where both found a USDOT) ===")
    print(f"  overlap: {both:,} | DOT# agreement: {agree:,} ({100*agree/both:.0f}%)" if both else "  no overlap yet")
    con.close()

if __name__ == "__main__":
    main()
