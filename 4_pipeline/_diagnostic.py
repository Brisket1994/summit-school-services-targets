#!/usr/bin/env python3
"""Comprehensive diagnostic of the enriched target dataset (pre-W4).
Profiles coverage, confidence, field completeness, the reclassification funnel,
ownership/succession/fleet/geography distributions, and data-quality issues —
to inform how (and whether) to re-score, and what extra enrichment would help.
"""
import sqlite3, os, re, csv
from collections import Counter

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
con = sqlite3.connect("2_database/summit_targets.db"); con.row_factory = sqlite3.Row; cur = con.cursor()
rows = cur.execute("SELECT * FROM enrichment").fetchall()
N = len(rows)
UNIVERSE = 3703
MISSING = {"", "unknown", "n/a", "na", "none", "not found", "not available", "unclear",
           "not disclosed", "no", "not specified", "tbd", "—", "-"}

def miss(v):
    return v is None or str(v).strip().lower() in MISSING

def norm_cp(v):
    s = (v or "").strip().lower()
    if s.startswith("yes"): return "yes"
    if s.startswith("no"): return "no"
    if s.startswith("unsure") or s.startswith("maybe"): return "unsure"
    return "other/blank"

def norm_lower(v):
    return (v or "").strip().lower() or "(blank)"

def fleet_num(v):
    if not v: return None
    m = re.findall(r"\d[\d,]*", str(v).replace(",", ""))
    if not m: return None
    nums = [int(x) for x in m if x.isdigit()]
    return max(nums) if nums else None

print(f"=== COVERAGE ===\nEnriched: {N:,} / {UNIVERSE:,} confirmed-private universe ({100*N/UNIVERSE:.1f}%)\n")

cp = Counter(norm_cp(r["confirmed_private"]) for r in rows)
print("=== confirmed_private (web-verified) ===")
for k in ["yes", "no", "unsure", "other/blank"]:
    print(f"  {k:12}: {cp.get(k,0):>5,}  ({100*cp.get(k,0)/N:.1f}%)")

conf = Counter(norm_lower(r["confidence"]).split()[0] if r["confidence"] else "(blank)" for r in rows)
print("\n=== confidence ===")
for k, c in conf.most_common():
    print(f"  {k:12}: {c:>5,}")

own = Counter(norm_lower(r["ownership_type"]) for r in rows)
print("\n=== ownership_type ===")
for k, c in own.most_common(12):
    print(f"  {k:22}: {c:>5,}")

succ = Counter(norm_lower(r["succession_signal"]).split()[0] if r["succession_signal"] else "(blank)" for r in rows)
print("\n=== succession_signal ===")
for k, c in succ.most_common():
    print(f"  {k:12}: {c:>5,}")

print("\n=== FIELD COMPLETENESS (% with informative value) ===")
for f in ["owner_or_parent","principals","founded_year","fleet_size_est","employees_est",
          "districts_or_customers","recent_news","website","sources","fit_notes"]:
    good = sum(1 for r in rows if not miss(r[f]))
    print(f"  {f:22}: {good:>5,}  ({100*good/N:.0f}%)")

fl = [fleet_num(r["fleet_size_est"]) for r in rows]
fl = [x for x in fl if x]
print(f"\n=== FLEET SIZE (numeric extractable: {len(fl):,}) ===")
bands = Counter()
for x in fl:
    b = "1-10" if x<=10 else "11-25" if x<=25 else "26-50" if x<=50 else "51-100" if x<=100 else "101-250" if x<=250 else "250+"
    bands[b]+=1
for b in ["1-10","11-25","26-50","51-100","101-250","250+"]:
    print(f"  {b:>8}: {bands.get(b,0):>5,}")

print("\n=== THE TARGET FUNNEL ===")
yes = [r for r in rows if norm_cp(r["confirmed_private"])=="yes"]
indep = [r for r in yes if norm_lower(r["ownership_type"]) in ("independent","family-owned","family owned","independent (family-owned)")]
print(f"  Web-confirmed private (yes)        : {len(yes):,}")
print(f"  ...of which independent/family     : {len(indep):,}")
print(f"  Reclassified OUT (no)              : {cp.get('no',0):,}")
print(f"  Needs review (unsure)              : {cp.get('unsure',0):,}")

EXP={"FL","NY","PA","MO","GA","IN"}
st=Counter(r["state"] for r in indep if r["state"])
print("\n=== Independent/family targets by state (top 15; * = Summit expansion) ===")
for s,c in st.most_common(15):
    print(f"  {s}{'*' if s in EXP else ' '}: {c}")

print("\n=== DATA-QUALITY: distinct raw values (sample) ===")
for f in ["confirmed_private","ownership_type","succession_signal","confidence"]:
    vals=Counter((r[f] or "").strip() for r in rows)
    print(f"  {f}: {len(vals)} distinct; top -> {dict(list(vals.most_common(6)))}")

# export the clean independent set for inspection
with open("3_deliverables/_intermediate/targets_independent_enriched.csv","w",newline="") as f:
    cols=["rank","name","state","ownership_type","owner_or_parent","principals","succession_signal",
          "founded_year","fleet_size_est","employees_est","service_types","districts_or_customers",
          "recent_news","website","confidence","fit_notes"]
    w=csv.DictWriter(f,fieldnames=cols,extrasaction="ignore"); w.writeheader()
    for r in sorted(indep,key=lambda x:x["rank"]): w.writerow({k:r[k] for k in cols})
print(f"\nExported {len(indep):,} independent/family targets -> targets_independent_enriched.csv")
con.close()
