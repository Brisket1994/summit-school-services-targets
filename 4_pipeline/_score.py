#!/usr/bin/env python3
"""Score the school + special-needs private operator pool for tuck-in fit.

Candidate set: is_target, school or special-needs, NOT government/in-house,
NOT generic-facility name, size tier single/small/mid (large flagged separately).

Transparent weighted score (0-100):
  size_fit 30 | succession 20 | quality 20 | independence 15 | relevance 15
Geography is reported but unweighted (pending Summit's footprint).
"""
import sqlite3, os, re, json, csv

DB = "2_database/summit_targets.db"
NOW = 2026
W = {"size_fit":0.30, "succession":0.20, "quality":0.20, "independence":0.15, "relevance":0.15}

# --- public / in-house (NOT acquirable) signals, abbreviation-aware ---
PUBLIC_SUB = ["SCHOOL DIST","SCH DIST","SCHOOL DISTRICT","UNIFIED SCH","UNIFIED SCHOOL",
  "CENTRAL SCH","CENTRAL SCHOOL","COUNTY SCH","CO SCH","COUNTY SCHOOL","PUBLIC SCH",
  "PUBLIC SCHOOL","CITY SCH","CITY SCHOOL","AREA SCH","AREA SCHOOL","COMMUNITY UNIT",
  "COMMUNITY SCH","CONSOLIDATED SCH","SCHOOL SYS","SCH SYS","SCHOOL SYSTEM","SCH SYST",
  "BOARD OF ED","BD OF ED","DEPT OF PUPIL","OF PUPIL","PUPIL TRANS","INDEPENDENT SCH",
  "INDEP SCH","SCH DEPT","SCHOOL DEPT","COUNTY OF","CITY OF","TOWN OF","VILLAGE OF",
  "TOWNSHIP","BOROUGH","PARISH","UNIVERSITY","COLLEGE","HEAD START","CHARTER SCHOOL",
  "PUBLIC SCHOOLS","REGIONAL SCH","REGIONAL SCHOOL","SCHOOL CORP","SCH CORP","DIST 2",
  "MUNICIPAL","GOVERNMENT","DEPARTMENT OF ED","DEPT OF ED","FOR PUPIL","ASSOCIATION","ASSN",
  "HIGH SCH","HIGH SCHOOL","REGIONAL HIGH","JR SR","JUNIOR HIGH","MIDDLE SCH","ELEMENTARY",
  "CENTRAL TRNS","CENTRAL TRANSP","CENTRAL SCH","REGIONAL TRANS","HIGHWAY DEPT","ROAD DEPT",
  "PUBLIC WORKS","SCHOOL CORPORATION","COMMUNITY COLL"]
PUBLIC_TOKEN = re.compile(r"\b([A-Z]{0,4}ISD|[A-Z]{0,4}USD|CUSD\d*|ESD\d*|SD\d+)\b")
GENERIC = ["BUS GARAGE","BUS BARN","BUS DEPOT","TRANSPORTATION DEPARTMENT","TRANSPORTATION DEPT",
           "MAINTENANCE SHOP","BUS MAINTENANCE","TRANSPORTATION CENTER","BUS LOT",
           "TRANSPORTATION OFFICE","BUS SHOP","PARKING LOT","TRANSPORTATION CTR",
           "TRNSP DEPT","TRNSPRTN DEPT","TRANSP DEPT","TRANS DEPT","TRNSPRTN DEPT",
           "TRNSPRT DEPT","TRANSPORTATN DEPT"]
# --- private-business signals ---
PRIVATE_SUB = ["BUS LINE","BUS LINES","BUS SERVICE","BUS SVC","BUS SERVICES","BUS CO","BUS COMPANY",
  "BUSING","BUSSING","COACH","COACHES","CHARTER","TRANSIT","LIMO","CARTAGE","TRAILWAYS",
  "STAGE LINE","MOTORCOACH","ENTERPRISES","TRANSPORTATION INC","TRANSPORTATION LLC",
  "TRANSPORT INC","SHUTTLE","CAB ","TAXI"]
PRIVATE_SUFFIX = re.compile(r"\b(INC|LLC|L L C|CORP|LTD|LP|ENTERPRISES|GROUP|CO)\b")

def classify(nm):
    """Return 'public', 'private', 'ambiguous', or 'generic'."""
    raw = nm or ""
    u = " " + re.sub(r"[^A-Z0-9 ]", " ", raw.upper()) + " "
    if any(p in u for p in GENERIC):
        return "generic"
    is_public = any(p in u for p in PUBLIC_SUB) or bool(PUBLIC_TOKEN.search(u))
    has_private = (any(p in u for p in PRIVATE_SUB) or "'" in raw
                   or bool(PRIVATE_SUFFIX.search(u)))
    if is_public:
        return "ambiguous" if has_private else "public"
    # un-suffixed name that reads like an in-house dept: "<place> SCHOOL TRANSPORTATION"
    if not has_private and ("SCHOOL" in u or "PUPIL" in u) and \
       ("TRANSP" in u or "TRNS" in u or "TRANSIT" in u or "BUS" in u):
        return "ambiguous"
    return "private"

def size_fit(emp, rev):
    es = rs = None
    if emp > 0:
        es = 20 if emp < 3 else 50 if emp < 10 else 100 if emp <= 300 else 70 if emp <= 750 else 40
    if rev > 0:
        rs = 30 if rev < 250_000 else 60 if rev < 1_000_000 else 100 if rev <= 30_000_000 else 70 if rev <= 75_000_000 else 40
    vals = [v for v in (es, rs) if v is not None]
    return (sum(vals)/len(vals)) if vals else 40.0

def succession(year):
    if not year: return 50.0
    age = NOW - int(year)
    return 100 if age >= 40 else 85 if age >= 25 else 60 if age >= 15 else 40 if age >= 8 else 25

def quality(website, phone, emp, rev):
    s = 0
    if website: s += 40
    if phone: s += 25
    if emp >= 10: s += 25
    if rev > 0: s += 10
    return min(s, 100)

def independence(tier):
    return {"single":100, "small(2-5)":80, "mid(6-14)":60, "large(15-49)":45, "very-large(50+)":30}.get(tier, 50)

def relevance(school, special):
    return 100 if (school and special) else 90 if school else 75 if special else 0

def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row; cur = con.cursor()
    rows = cur.execute("SELECT * FROM entities WHERE is_target=1 AND (school=1 OR special_needs=1) "
                       "AND gov_flag=0").fetchall()
    main_pool, large_pool, ambiguous_pool = [], [], []
    cls_counts = {"public":0, "generic":0, "private":0, "ambiguous":0}
    for r in rows:
        nm = r["canonical_name"] or ""
        cls = classify(nm)
        cls_counts[cls] += 1
        if cls in ("public", "generic"):
            continue
        emp = int(r["loc_employees_sum"] or 0); rev = int(r["loc_sales_sum"] or 0)
        yr = r["year_established"] or 0
        web = bool((r["website"] or "").strip()); ph = bool((r["phone"] or "").strip())
        sf = size_fit(emp, rev); su = succession(yr); ql = quality(web, ph, emp, rev)
        ind = independence(r["size_tier"]); rel = relevance(r["school"], r["special_needs"])
        score = round(W["size_fit"]*sf + W["succession"]*su + W["quality"]*ql
                      + W["independence"]*ind + W["relevance"]*rel, 1)
        conf = sum([rev > 0, emp > 0, bool(yr), web]) / 4.0
        age = (NOW - int(yr)) if yr else None
        rationale = "; ".join(filter(None, [
            f"{emp} emp" if emp else "emp n/a",
            f"${rev/1e6:.1f}M rev" if rev else "rev n/a",
            f"est {int(yr)} ({age}y)" if yr else "year n/a",
            r["size_tier"],
            "web+phone" if web and ph else "web" if web else "phone" if ph else "no contact",
            "school+special" if (r["school"] and r["special_needs"]) else "school" if r["school"] else "special-needs",
        ]))
        rec = {"score":score, "canonical_name":nm, "primary_state":r["primary_state"],
               "hq":r["hq"], "size_tier":r["size_tier"], "locations":r["locations"],
               "employees":emp, "revenue_est":rev, "year_established":int(yr) if yr else "",
               "school":r["school"], "special_needs":r["special_needs"],
               "website":r["website"], "phone":r["phone"], "lead_exec":r["lead_exec"],
               "credit_score":r["credit_score"], "data_confidence":round(conf,2),
               "rationale":rationale, "sample_address":r["sample_address"],
               "review_flag":r["review_flag"], "classification":cls,
               "_sf":round(sf), "_su":round(su), "_ql":round(ql), "_ind":ind, "_rel":rel}
        if cls == "ambiguous":
            ambiguous_pool.append(rec)
        elif r["size_tier"] in ("large(15-49)", "very-large(50+)"):
            large_pool.append(rec)
        else:
            main_pool.append(rec)

    main_pool.sort(key=lambda x:(-x["score"], -x["data_confidence"], -x["revenue_est"]))
    large_pool.sort(key=lambda x:(-x["score"], -x["revenue_est"]))
    ambiguous_pool.sort(key=lambda x:(-x["score"], -x["revenue_est"]))
    for i,e in enumerate(main_pool,1): e["rank"]=i

    cols = ["rank","score","canonical_name","primary_state","hq","size_tier","locations",
            "employees","revenue_est","year_established","school","special_needs","website",
            "phone","lead_exec","credit_score","data_confidence","rationale","sample_address",
            "_sf","_su","_ql","_ind","_rel"]
    with open("3_deliverables/_intermediate/targets_scored.csv","w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=cols); w.writeheader()
        for e in main_pool: w.writerow({k:e.get(k,"") for k in cols})
    with open("3_deliverables/_intermediate/targets_top.jsonl","w") as f:
        for e in main_pool[:300]: f.write(json.dumps(e)+"\n")
    lc=["score","canonical_name","primary_state","locations","employees","revenue_est",
        "year_established","school","special_needs","website","rationale"]
    with open("3_deliverables/_intermediate/large_independents_review.csv","w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=lc); w.writeheader()
        for e in large_pool: w.writerow({k:e.get(k,"") for k in lc})
    with open("3_deliverables/_intermediate/ambiguous_review.csv","w",newline="") as f:
        w=csv.DictWriter(f, fieldnames=lc); w.writeheader()
        for e in ambiguous_pool: w.writerow({k:e.get(k,"") for k in lc})
    # markdown top 50
    with open("3_deliverables/_intermediate/targets_top50.md","w") as f:
        f.write("# Top 50 tuck-in candidates (school + special-needs, private)\n\n")
        f.write("| # | Score | Company | ST | Tier | Emp | Rev($M) | Est | Conf | Why |\n")
        f.write("|--:|--:|---|---|---|--:|--:|--:|--:|---|\n")
        for e in main_pool[:50]:
            rev = f"{e['revenue_est']/1e6:.1f}" if e['revenue_est'] else "—"
            f.write(f"| {e['rank']} | {e['score']} | {e['canonical_name'][:32]} | {e['primary_state']} "
                    f"| {e['size_tier']} | {e['employees'] or '—'} | {rev} | {e['year_established'] or '—'} "
                    f"| {e['data_confidence']} | {e['rationale']} |\n")

    # report
    print(f"Classification of school/special-needs private targets: {cls_counts}")
    print(f"Candidates scored (PRIVATE, single/small/mid)        : {len(main_pool):,}")
    print(f"Large private independents (15+, review)             : {len(large_pool):,}")
    print(f"Ambiguous (likely in-house/district -> review)       : {len(ambiguous_pool):,}")
    print(f"Dropped as public/generic                            : {cls_counts['public']+cls_counts['generic']:,}")
    pop = lambda k: sum(1 for e in main_pool if e[k])
    n=len(main_pool)
    print(f"\nData fill (main pool): revenue {pop('revenue_est')/n*100:.0f}% | "
          f"employees {pop('employees')/n*100:.0f}% | year {pop('year_established')/n*100:.0f}% | "
          f"website {pop('website')/n*100:.0f}%")
    import statistics as st
    sc=[e['score'] for e in main_pool]
    print(f"Score: max {max(sc)}, median {st.median(sc):.1f}, "
          f">=70: {sum(1 for s in sc if s>=70):,}, >=60: {sum(1 for s in sc if s>=60):,}")
    print("\n=== TOP 25 ===")
    print(f"{'#':>3} {'Score':>5} {'ST':>3} {'Tier':>11} {'Emp':>5} {'Rev$M':>6} {'Est':>5}  Company")
    for e in main_pool[:25]:
        rev=f"{e['revenue_est']/1e6:.1f}" if e['revenue_est'] else "-"
        print(f"{e['rank']:>3} {e['score']:>5} {e['primary_state']:>3} {e['size_tier']:>11} "
              f"{(e['employees'] or '-'):>5} {rev:>6} {(e['year_established'] or '-'):>5}  {e['canonical_name'][:34]}")
    print("\nExports: targets_scored.csv | targets_top.jsonl | targets_top50.md | large_independents_review.csv")
    con.close()

if __name__ == "__main__":
    main()
