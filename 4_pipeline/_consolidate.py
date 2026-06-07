#!/usr/bin/env python3
"""Filter to the student-transport segment (core + charter) and consolidate
location rows into operating-company entities.

- entity_key = normalized(Parent Company Name) if a parent exists,
  else normalized(Company Name). Branches roll up to their parent; same-named
  independents merge.
- Aggregates footprint (locations, states), size (employees, sales), signals.
- Flags non-targets (public / PE-owned / national-platform name / large footprint)
  with explicit reasons -- nothing is silently dropped.
- Writes tables back into summit_targets.db and exports reviewable files.
"""
import sqlite3, os, re, json, csv
from collections import Counter, defaultdict

DB = "2_database/summit_targets.db"

# ---- relevance predicate (core + charter) ----
CORE_PLUS = (
    "(\"Primary NAICS\" LIKE '485410%' OR \"Primary NAICS\"='48599101' "
    "OR \"Primary NAICS\" LIKE '485510%' OR \"Primary SIC Code\" LIKE '4151%' "
    "OR UPPER(\"Company Name\") LIKE '%SCHOOL%' OR UPPER(\"Company Name\") LIKE '%STUDENT%' "
    "OR UPPER(\"Company Description\") LIKE '%SCHOOL BUS%')"
)

SEL = ["IUSA Number","Parent IUSA Number","Parent Company Name","Company Name","Legal Name",
       "Location Type","Address","City","State","ZIP Code","County","Metro Area",
       "Primary NAICS","Primary NAICS Description","Primary SIC Code","Primary SIC Description",
       "Location Employee Size Actual","Location Sales Volume Actual",
       "Corporate Employee Size Actual","Corporate Sales Volume Actual",
       "Year Established","Phone Number Combined","Website",
       "Executive First Name","Executive Last Name","Executive Title",
       "Ticker Symbol","Stock Exchange","Owns Location","Own or Lease","Affiliated Locations",
       "Government Office","Credit Score Alpha"]

DROP = {"INC","LLC","CORP","CO","LTD","LP","THE","COMPANY","INCORPORATED","L","C"}
EXP = {"SVC":"SERVICE","SVCS":"SERVICE","SERVICES":"SERVICE","SCH":"SCHOOL",
       "TRANS":"TRANSPORTATION","TRANSP":"TRANSPORTATION","TRNSPRTN":"TRANSPORTATION",
       "TRANSPRT":"TRANSPORTATION","TRNS":"TRANSPORTATION","BUSES":"BUS","BUSSES":"BUS",
       "DEPT":"DEPARTMENT","DIST":"DISTRICT","SVS":"SERVICE"}

PLATFORM_KW = ["FIRST STUDENT","FIRSTGROUP","FIRST GROUP","FIRST TRANSIT","NATIONAL EXPRESS",
               "DURHAM SCHOOL","STUDENT TRANSPORTATION OF AMER","STUDENT TRANSPORTATION AMERICA",
               "LAIDLAW","BEACON MOBILITY","ZUM","COACH USA","GREYHOUND"]
PE_PARENTS = ["EQT","CARLYLE","HIG CAPITAL","H I G","BLACKSTONE","KKR","APOLLO","WARBURG",
              "AMERICAN SECURITIES","PARTNERS GROUP","BAIN CAPITAL"]
LARGE_FOOTPRINT = 15  # locations >= this -> flag for review

def norm(name):
    if not name: return ""
    s = re.sub(r"[^A-Z0-9 ]"," ", str(name).upper())
    toks = [EXP.get(t,t) for t in s.split()]
    toks = [t for t in toks if t not in DROP]
    return " ".join(toks).strip()

def num(v):
    if v is None: return 0.0
    if isinstance(v,(int,float)): return float(v)
    s = re.sub(r"[,$]","", str(v)).strip()
    try: return float(s)
    except: return 0.0

def present(v): return v is not None and str(v).strip() != "" and str(v).strip() != "0"

def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    con = sqlite3.connect(DB); cur = con.cursor()

    # 1) relevant segment table
    cur.execute("DROP TABLE IF EXISTS targets")
    cols = ", ".join(f'"{c}"' for c in SEL)
    cur.execute(f"CREATE TABLE targets AS SELECT {cols} FROM companies WHERE {CORE_PLUS}")
    con.commit()
    nseg = cur.execute("SELECT COUNT(*) FROM targets").fetchone()[0]
    print(f"Relevant segment rows (core+charter): {nseg:,}")

    # 2) consolidate
    idx = {c:i for i,c in enumerate(SEL)}
    rows = cur.execute(f"SELECT {cols} FROM targets").fetchall()
    ent = defaultdict(lambda: {
        "locations":0,"iusa":set(),"states":Counter(),"names":Counter(),
        "parents":set(),"emp_sum":0.0,"sales_sum":0.0,"corp_emp":0.0,"corp_sales":0.0,
        "years":[],"website":"","phone":"","exec":"","ticker":"","credit":"",
        "school":False,"special":False,"charter":False,"gov":False,
        "sample_addr":"","hq_city_state":""})
    for r in rows:
        def g(c): return r[idx[c]]
        pname = g("Parent Company Name"); cname = g("Company Name")
        key = norm(pname) if present(pname) else norm(cname)
        if not key: key = norm(cname) or "(unnamed)"
        e = ent[key]
        e["locations"] += 1
        e["iusa"].add(str(g("IUSA Number")))
        if present(g("State")): e["states"][g("State")] += 1
        if present(cname): e["names"][cname] += 1
        if present(pname): e["parents"].add(pname)
        e["emp_sum"] += num(g("Location Employee Size Actual"))
        e["sales_sum"] += num(g("Location Sales Volume Actual"))
        e["corp_emp"] = max(e["corp_emp"], num(g("Corporate Employee Size Actual")))
        e["corp_sales"] = max(e["corp_sales"], num(g("Corporate Sales Volume Actual")))
        ye = num(g("Year Established"))
        if ye and ye > 1800: e["years"].append(int(ye))
        if not e["website"] and present(g("Website")): e["website"] = g("Website")
        if not e["phone"] and present(g("Phone Number Combined")): e["phone"] = g("Phone Number Combined")
        if not e["exec"] and present(g("Executive Last Name")):
            e["exec"] = f"{g('Executive First Name') or ''} {g('Executive Last Name') or ''} ({g('Executive Title') or ''})".strip()
        if not e["ticker"] and present(g("Ticker Symbol")): e["ticker"] = g("Ticker Symbol")
        naics = str(g("Primary NAICS") or ""); sic = str(g("Primary SIC Code") or "")
        nm = (str(cname or "")+" "+str(g("Primary NAICS Description") or "")).upper()
        if naics.startswith("485410") or sic.startswith("4151") or "SCHOOL" in nm: e["school"] = True
        if naics == "48599101" or "SPECIAL NEED" in nm: e["special"] = True
        if naics.startswith("485510") or "CHARTER" in nm: e["charter"] = True
        if present(g("Government Office")): e["gov"] = True
        if not e["credit"] and present(g("Credit Score Alpha")): e["credit"] = g("Credit Score Alpha")
        lt = str(g("Location Type") or "")
        if (lt in ("Headquarter","Single Loc")) and not e["sample_addr"] and present(g("Address")):
            e["sample_addr"] = f"{g('Address')}, {g('City')}, {g('State')} {g('ZIP Code')}"
            e["hq_city_state"] = f"{g('City')}, {g('State')}"

    # 3) build entity records + flags
    out = []
    for key, e in ent.items():
        canonical = e["names"].most_common(1)[0][0] if e["names"] else key
        states = [s for s,_ in e["states"].most_common()]
        n = e["locations"]
        size_tier = ("single" if n == 1 else "small(2-5)" if n <= 5 else "mid(6-14)"
                     if n <= 14 else "large(15-49)" if n <= 49 else "very-large(50+)")
        # hard-exclude reasons = genuinely un-acquirable. Size is NOT an exclusion.
        reasons = []
        up_can = canonical.upper(); up_key = key.upper()
        if present(e["ticker"]): reasons.append("public")
        for p in e["parents"]:
            if any(pe in p.upper() for pe in PE_PARENTS): reasons.append(f"PE-owned({p})"); break
        if any(kw in up_can or kw in up_key for kw in PLATFORM_KW): reasons.append("national-platform")
        review = (n >= LARGE_FOOTPRINT and not reasons)  # large independent worth a manual look
        out.append({
            "entity_key": key, "canonical_name": canonical,
            "locations": n, "size_tier": size_tier, "n_states": len(states),
            "states": ",".join(states[:8]),
            "primary_state": states[0] if states else "",
            "loc_employees_sum": int(e["emp_sum"]),
            "loc_sales_sum": int(e["sales_sum"]),
            "corp_employees": int(e["corp_emp"]), "corp_sales": int(e["corp_sales"]),
            "year_established": min(e["years"]) if e["years"] else "",
            "school": int(e["school"]), "special_needs": int(e["special"]), "charter": int(e["charter"]),
            "parents": " | ".join(sorted(e["parents"]))[:120],
            "website": e["website"], "phone": e["phone"], "lead_exec": e["exec"],
            "hq": e["hq_city_state"], "sample_address": e["sample_addr"],
            "name_variants": "; ".join(f"{n2}({c})" for n2, c in e["names"].most_common(4)),
            "nontarget_reason": "; ".join(dict.fromkeys(reasons)),
            "review_flag": "large-independent" if review else "",
            "gov_flag": int(e["gov"]), "credit_score": e["credit"],
            "is_target": int(len(reasons) == 0),
        })
    out.sort(key=lambda x: (-x["locations"], -x["loc_sales_sum"]))

    # 4) write entities table
    cur.execute("DROP TABLE IF EXISTS entities")
    ekeys = list(out[0].keys())
    cur.execute(f"CREATE TABLE entities ({', '.join(f'\"{k}\"' for k in ekeys)})")
    cur.executemany(f"INSERT INTO entities VALUES ({','.join('?'*len(ekeys))})",
                    [[e[k] for k in ekeys] for e in out])
    con.commit()

    # 5) exports
    with open("3_deliverables/_intermediate/entities_all.csv","w",newline="") as f:
        w = csv.DictWriter(f, fieldnames=ekeys); w.writeheader(); w.writerows(out)
    targets = [e for e in out if e["is_target"]]
    with open("3_deliverables/_intermediate/targets_independent.jsonl","w") as f:
        for e in targets: f.write(json.dumps(e)+"\n")

    # 6) report
    print(f"\nDistinct entities (after consolidation): {len(out):,}")
    nont = [e for e in out if not e["is_target"]]
    print(f"  Flagged NON-targets: {len(nont):,}  |  Independent targets: {len(targets):,}")
    rc = Counter()
    for e in nont:
        for part in e["nontarget_reason"].split("; "):
            rc[part.split("(")[0]] += 1
    print("  Non-target reasons:", dict(rc))

    print("\n=== Top 15 excluded platforms (by locations) ===")
    for e in nont[:15]:
        print(f"  {e['locations']:>4} locs | {e['canonical_name'][:38]:38} | {e['nontarget_reason']}")

    bands = Counter(e["size_tier"] for e in targets)
    print("\n=== Independent target pool: size tiers ===")
    for b in ["single","small(2-5)","mid(6-14)","large(15-49)","very-large(50+)"]:
        print(f"  {b:>16}: {bands.get(b,0):,} entities")
    print("\n=== Independent target pool: signal mix ===")
    print(f"  with school signal : {sum(1 for e in targets if e['school']):,}")
    print(f"  special-needs      : {sum(1 for e in targets if e['special_needs']):,}")
    print(f"  charter (any)      : {sum(1 for e in targets if e['charter']):,}")
    print(f"  charter-only (no school/special): {sum(1 for e in targets if e['charter'] and not e['school'] and not e['special_needs']):,}")
    rev = [e for e in targets if e['review_flag']]
    print(f"\n=== Large independents kept as targets (review): {len(rev)} ===")
    for e in rev[:12]:
        print(f"  {e['locations']:>4} locs | {e['canonical_name'][:34]:34} | {e['primary_state']} | school={e['school']}")
    topst = Counter(e["primary_state"] for e in targets if e["primary_state"])
    print("\n=== Independent targets by primary state (top 12) ===")
    print("  " + ", ".join(f"{s}:{c}" for s,c in topst.most_common(12)))
    sized = [e for e in targets if e["loc_employees_sum"]>0]
    print(f"\n  Targets with employee data: {len(sized):,}")
    print("  Exports: entities_all.csv (all), targets_independent.jsonl (target pool)")
    con.close()

if __name__ == "__main__":
    main()
