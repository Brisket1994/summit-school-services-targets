#!/usr/bin/env python3
"""W5 — additive overlay re-score + per-target implied valuation.

Reads the W4 output (`master_targets`) and the synthesized `market_overlay.csv`, derives per-target
join keys, scores a set of ADDITIVE overlay factors (points on top of the W4 composite — W4 baseline
left fully intact for comparison), computes an implied-valuation band per target (revenue / EBITDA /
entry-EV / build-to-8x / value-creation spread), re-ranks on the overlay composite, and writes the
overlay deliverables + diagnostics. Does NOT edit or re-run _w4_score.py.

overlay_composite = w4_composite + Σ(overlay factor points)   [no renormalize; directly comparable]

Determinism: NOW=2026 (matches _w4_score.py); tables drop/recreate each run; fully-specified sort
keys; csv newline=''. Two runs => byte-identical outputs.

Case B: runs on the `master_targets` table (rebuilt from master_targets_FULL.csv by
_build_master_view.py). Does NOT touch the gitignored enrichment/fmcsa/fmcsa_census tables.

stdlib only (sqlite3, csv, json, re, os, math).

Run:  python3 4_pipeline/_build_master_view.py && python3 4_pipeline/_w5_overlay.py
"""
import sqlite3, csv, json, re, os, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB   = os.path.join(ROOT, "2_database", "summit_targets.db")
OVERLAY_CSV = os.path.join(ROOT, "5_working", "inputs", "market_overlay.csv")
OUT_RANKED  = os.path.join(ROOT, "3_deliverables", "master_targets_ranked_overlay.csv")
OUT_TOP50   = os.path.join(ROOT, "3_deliverables", "master_targets_overlay_A_top50.md")
DIAG_DIR    = os.path.join(ROOT, "5_working", "diagnostics")
OUT_RECON   = os.path.join(DIAG_DIR, "w5_overlay_reconciliation.txt")
OUT_SKIP    = os.path.join(DIAG_DIR, "w5_overlay_skipped.csv")

NOW = 2026
PRIORITY = {"FL", "NY", "PA", "MO", "GA", "IN", "UT"}
RECON_TOLERANCE = 0.50   # bus-anchor sanity-check half-width

# per-factor point caps (sum-of-caps = 100; total swing bounded, directly comparable to W4's 0-100)
CAPS = {
    "valuation_attractiveness": 20,
    "size_margin_signal":       20,
    "succession":               15,
    "driver_market_risk":       15,
    "outsourcing_ev_mandate":   10,
    "contract_renewal_timing":  10,   # reserved 0 (no per-target contract dates)
    "ut_expansion_bonus":       10,
}

# ── helpers ──────────────────────────────────────────────────────────────────
def i(v):
    if v is None or v == "": return 0
    m = re.findall(r"-?\d+", str(v).replace(",", ""))
    return int(m[0]) if m else 0

def f(v):
    if v is None or v == "": return None
    try: return float(str(v).replace(",", ""))
    except Exception: return None

def clamp(x, cap): return max(-cap, min(cap, round(x, 1)))

def parse_types(s):
    if not s: return []
    try:
        v = json.loads(s)
        return [str(x).lower() for x in v] if isinstance(v, list) else []
    except Exception:
        return [t.strip().strip('"[]').lower() for t in str(s).split(",")]

# ── load market_overlay.csv → table ──────────────────────────────────────────
def load_overlay(con):
    cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS market_overlay")
    cur.execute("""CREATE TABLE market_overlay(
        metric TEXT, sub_sector TEXT, scale_tier TEXT, geo TEXT, period TEXT,
        low REAL, point REAL, high REAL, unit TEXT,
        n_observations INT, small_n_flag TEXT, source_basis TEXT, verification_status TEXT,
        source_count INT, citations TEXT, internal_anchor_count INT, dataroom_anchor_count INT,
        disagreement_flag TEXT, disagreement_note TEXT, overlay_factor_hook TEXT,
        overlay_neutral_value REAL, notes TEXT)""")
    with open(OVERLAY_CSV, newline="") as fh:
        for r in csv.DictReader(fh):
            cur.execute("INSERT INTO market_overlay VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                r["metric"], r["sub_sector"], r["scale_tier"], r["geo"], r["period"],
                f(r["low"]), f(r["point"]), f(r["high"]), r["unit"],
                i(r["n_observations"]), r["small_n_flag"], r["source_basis"], r["verification_status"],
                i(r["source_count"]), r["citations"], i(r["internal_anchor_count"]),
                i(r["dataroom_anchor_count"]), r["disagreement_flag"], r["disagreement_note"],
                r["overlay_factor_hook"], f(r["overlay_neutral_value"]), r["notes"]))
    cur.execute("CREATE INDEX idx_mo ON market_overlay(metric, sub_sector, scale_tier, geo, verification_status)")
    con.commit()

# scale-tier adapter: target tier -> brief-03 valuation axis candidates
SCALE_TO_VAL = {"<50": ["tuck-in"], "50-250": ["tuck-in"], "250+": ["platform"]}

def lookup(cur, metric, sub, scale, geo, use_scale_adapter=False):
    """Fallback ladder, verified-only. Returns (band_dict, matched_keys) or (None, None)."""
    geos  = [g for g in (geo, "national") if g] or ["national"]
    if use_scale_adapter:
        scales = []
        for s in SCALE_TO_VAL.get(scale, []): scales.append(s)
        if scale: scales.append(scale)
        scales.append("all")
    else:
        scales = [s for s in (scale, "all") if s] or ["all"]
    subs = [s for s in (sub, "all") if s] or ["all"]
    seen = set()
    for g in geos:
        for s in scales:
            for ss in subs:
                k = (g, s, ss)
                if k in seen: continue
                seen.add(k)
                row = cur.execute(
                    "SELECT low,point,high,unit,citations,source_basis FROM market_overlay "
                    "WHERE metric=? AND geo=? AND scale_tier=? AND sub_sector=? "
                    "AND verification_status='verified' LIMIT 1", (metric, g, s, ss)).fetchone()
                if row:
                    return ({"low": row[0], "point": row[1], "high": row[2], "unit": row[3],
                             "cite": row[4], "basis": row[5]}, k)
    return None, None

def cite_str(band, keys):
    if not band: return ""
    g, s, ss = keys or ("", "", "")
    head = (band["cite"] or "").split(";;")[0].split("|")
    src = head[0] if head else ""
    return f"{src} [{band['basis']}; geo={g}/scale={s}/sub={ss}]"

# ── derived join keys ─────────────────────────────────────────────────────────
def derive_sub(t):
    if i(t.get("da_special_needs")) == 1: return "S"
    if i(t.get("da_school")) == 1: return "Y"
    types = parse_types(t.get("web_service_types"))
    if any("charter" in x or "motorcoach" in x for x in types): return "C"
    return None

def derive_scale(t):
    fleet = i(t.get("fleet_buses"))
    if fleet > 0:
        return "<50" if fleet < 50 else "50-250" if fleet <= 250 else "250+"
    st = (t.get("da_size_tier") or "").lower()
    if st.startswith(("single", "small", "mid")) or "large(15-49)" in st:
        return "<50"
    if "very-large" in st:
        return "250+" if i(t.get("drivers")) > 500 else "50-250"
    return None

def derive_geo(t):
    return (t.get("state") or "").upper().strip() or None

def census_fleet(t):
    return i(t.get("fleet_buses")) > 0 and (t.get("fmcsa_source") or "").lower().startswith("census")

# ── overlay factor scorers: each returns (points, citation, flag) ─────────────
def fac_valuation(t, cur, sub, scale, geo):
    cap = CAPS["valuation_attractiveness"]
    band, keys = lookup(cur, "ev_ebitda_multiple", sub, scale, geo, use_scale_adapter=True)
    if band is None:
        return 0, "", "no_verified_multiple"
    # multiple-arbitrage thesis: tuck-in-scale enters cheap (~3-5x) and builds to ~8x — most attractive.
    if scale in ("<50", "50-250"): pts = 12.0
    elif scale == "250+":          pts = -6.0
    else:                          pts = 0.0
    if sub == "S":  pts += 4.0     # SpEd margin premium (leadership 'gold')
    elif sub == "C": pts -= 2.0    # charter-only: weaker strategic fit
    # cheap EV/bus reinforces
    evb, _ = lookup(cur, "ev_per_bus", sub, scale, geo, use_scale_adapter=True)
    if evb and (evb["low"] or 0) <= 100000 and scale in ("<50", "50-250"):
        pts += 2.0
    return clamp(pts, cap), cite_str(band, keys), "ok"

def fac_size_margin(t, cur, sub, scale, geo):
    cap = CAPS["size_margin_signal"]
    if not census_fleet(t):
        return 0, "", "no_verified_fleet"
    rpb, rk = lookup(cur, "revenue_per_bus_per_year", sub, scale, geo)
    if rpb is None:
        return 0, "", "no_verified_rev_per_bus"
    fleet = i(t.get("fleet_buses"))
    rev = fleet * (rpb["point"] or 0)
    if   5_000_000 <= rev <= 15_000_000: pts = 16.0   # the explicit "$5-15M mom-and-pop" bullseye
    elif 1_000_000 <= rev <  5_000_000:  pts = 10.0
    elif 15_000_000 < rev <= 25_000_000: pts = 10.0
    elif 25_000_000 < rev <= 50_000_000: pts = 2.0
    elif 500_000   <= rev <  1_000_000:  pts = -2.0
    elif rev < 500_000:                  pts = -10.0
    else:                                pts = -8.0   # >$50M: platform-scale, not a tuck-in
    mgn, _ = lookup(cur, "ebitda_margin", sub, scale, geo)
    if mgn and rev * (mgn["point"] or 0) >= 1_500_000:
        pts += 4.0   # implied EBITDA clears typical PE deal-size floor
    return clamp(pts, cap), cite_str(rpb, rk), "ok"

def fac_succession(t, cur, sub, scale, geo):
    cap = CAPS["succession"]
    fy = i(t.get("founded"))
    if fy <= 0:
        return 0, "", "no_founded_year"
    age = NOW - fy
    if   age >= 50: pts = cap
    elif age >= 30: pts = cap * 0.53
    elif age >= 15: pts = 0.0
    else:           pts = -cap * 0.53
    return clamp(pts, cap), f"master_targets.founded={fy} (business age={age}y @ NOW={NOW})", "ok"

def fac_driver(t, cur, sub, scale, geo):
    cap = CAPS["driver_market_risk"]
    band, keys = lookup(cur, "driver_turnover_pct_annual", sub, scale, geo)
    if band is None:
        return 0, "", "no_driver_turnover_anchor"
    p = band["point"] or 0.26
    if   p <= 0.15: pts = cap
    elif p <= 0.25: pts = cap * 0.5
    elif p <= 0.35: pts = 0.0
    else:           pts = -cap
    flag = "ok" if (geo and keys and keys[0] == geo) else "national_only_no_state_signal"
    return clamp(pts, cap), cite_str(band, keys), flag

def fac_outsourcing(t, cur, sub, scale, geo):
    cap = CAPS["outsourcing_ev_mandate"]
    acc, ak = lookup(cur, "outsourcing_acceptance", "Y", scale, geo)
    evm, ek = lookup(cur, "ev_mandate_stringency", sub, scale, geo)
    if acc is None and evm is None:
        return 0, "", "no_state_signal"
    pts = 0.0
    if acc: pts += (acc["point"] - 0.45) * 20.0        # outsourcing-friendly: + ; district-run: -
    if evm: pts -= (evm["point"] - 0.20) * 12.5        # EV mandate = capex headwind: -
    cites = " ; ".join(c for c in (cite_str(acc, ak), cite_str(evm, ek)) if c)
    return clamp(pts, cap), cites, "ok"

def fac_contract_renewal(t, cur, sub, scale, geo):
    return 0, "", "reserved_zero"

def fac_ut(t, cur, sub, scale, geo):
    cap = CAPS["ut_expansion_bonus"]
    if (t.get("state") or "").upper() == "UT":
        return cap, "canonical priority set {FL,NY,PA,MO,GA,IN,UT}; W4 EXP omits UT", "ok"
    return 0, "", "non_ut"

FACTORS = [
    ("valuation_attractiveness", fac_valuation),
    ("size_margin_signal",       fac_size_margin),
    ("succession",               fac_succession),
    ("driver_market_risk",       fac_driver),
    ("outsourcing_ev_mandate",   fac_outsourcing),
    ("contract_renewal_timing",  fac_contract_renewal),
    ("ut_expansion_bonus",       fac_ut),
]

# ── implied-valuation layer (gated on verified census fleet) ──────────────────
IV_COLS = ["iv_fleet_used", "iv_fleet_source",
           "iv_rev_low", "iv_rev_point", "iv_rev_high",
           "iv_ebitda_low", "iv_ebitda_point", "iv_ebitda_high",
           "iv_ev_mult_entry_low", "iv_ev_mult_entry_point", "iv_ev_mult_entry_high",
           "iv_ev_perbus_low", "iv_ev_perbus_point", "iv_ev_perbus_high",
           "iv_ev_entry_consensus_low", "iv_ev_entry_consensus_high",
           "iv_ev_build_8x_point", "iv_value_creation_spread_point",
           "iv_flag", "iv_citation"]

def implied_valuation(t, cur, sub, scale, geo):
    out = {c: "" for c in IV_COLS}
    out["iv_fleet_source"] = (t.get("fmcsa_source") or "")
    if not census_fleet(t):
        out["iv_flag"] = "no_verified_fleet"; return out
    rpb, _ = lookup(cur, "revenue_per_bus_per_year", sub, scale, geo)
    if rpb is None:
        out["iv_flag"] = "no_verified_rev_per_bus"; return out
    fleet = i(t.get("fleet_buses"))
    out["iv_fleet_used"] = fleet
    flags = []
    out["iv_rev_low"]   = round(fleet * (rpb["low"]   or 0))
    out["iv_rev_point"] = round(fleet * (rpb["point"] or 0))
    out["iv_rev_high"]  = round(fleet * (rpb["high"]  or 0))
    mgn, _ = lookup(cur, "ebitda_margin", sub, scale, geo)
    if mgn:
        out["iv_ebitda_low"]   = round(out["iv_rev_low"]   * (mgn["low"]   or 0))
        out["iv_ebitda_point"] = round(out["iv_rev_point"] * (mgn["point"] or 0))
        out["iv_ebitda_high"]  = round(out["iv_rev_high"]  * (mgn["high"]  or 0))
    else:
        flags.append("ebitda_band_unavailable")
    ent, _ = lookup(cur, "entry_multiple_tuckin", sub, scale, geo)
    em = (ent["low"], ent["point"], ent["high"]) if ent else (3.0, 4.0, 5.0)
    if not ent: flags.append("entry_multiple_defaulted_3_4_5x")
    if out["iv_ebitda_point"] != "":
        out["iv_ev_mult_entry_low"]   = round(out["iv_ebitda_low"]   * em[0])
        out["iv_ev_mult_entry_point"] = round(out["iv_ebitda_point"] * em[1])
        out["iv_ev_mult_entry_high"]  = round(out["iv_ebitda_high"]  * em[2])
    evb, _ = lookup(cur, "ev_per_bus", sub, scale, geo, use_scale_adapter=True)
    if evb:
        out["iv_ev_perbus_low"]   = round(fleet * (evb["low"]   or 0))
        out["iv_ev_perbus_point"] = round(fleet * (evb["point"] or 0))
        out["iv_ev_perbus_high"]  = round(fleet * (evb["high"]  or 0))
    # consensus EV band = intersection of the two methods (fallback to whichever exists)
    m_lo, m_hi = out["iv_ev_mult_entry_low"], out["iv_ev_mult_entry_high"]
    p_lo, p_hi = out["iv_ev_perbus_low"], out["iv_ev_perbus_high"]
    have_m = m_lo != "" and m_hi != ""
    have_p = p_lo != "" and p_hi != ""
    if have_m and have_p:
        out["iv_ev_entry_consensus_low"]  = max(m_lo, p_lo)
        out["iv_ev_entry_consensus_high"] = min(m_hi, p_hi)
    elif have_m:
        out["iv_ev_entry_consensus_low"], out["iv_ev_entry_consensus_high"] = m_lo, m_hi
    elif have_p:
        out["iv_ev_entry_consensus_low"], out["iv_ev_entry_consensus_high"] = p_lo, p_hi
    bm, _ = lookup(cur, "build_multiple_target", sub, scale, geo)
    build_mult = bm["point"] if bm else 8.0
    if out["iv_ebitda_point"] != "":
        out["iv_ev_build_8x_point"] = round(out["iv_ebitda_point"] * build_mult)
        if out["iv_ev_mult_entry_point"] != "":
            out["iv_value_creation_spread_point"] = out["iv_ev_build_8x_point"] - out["iv_ev_mult_entry_point"]
    cites = []
    for nm, b in (("rev_per_bus", rpb), ("ebitda_margin", mgn), ("entry_mult", ent), ("ev_per_bus", evb), ("build_mult", bm)):
        if b: cites.append(f"{nm}:{(b['cite'] or '').split('|')[0]}")
    out["iv_citation"] = " ; ".join(cites)
    out["iv_flag"] = ";".join(flags)
    return out

def independent_rev_signal(t):
    rev = f(t.get("da_revenue_est"))
    if rev and rev > 0: return rev
    emp = i(t.get("web_employees_est"))
    if emp > 0: return emp * 135000   # brief-01 §G labor-productivity proxy ($/employee)
    return None

# ── main ──────────────────────────────────────────────────────────────────────
def main():
    con = sqlite3.connect(DB); con.row_factory = sqlite3.Row
    load_overlay(con)
    cur = con.cursor()
    targets = [dict(r) for r in cur.execute("SELECT * FROM master_targets")]

    skipped = []
    recon = {"n": 0, "in": 0, "below": 0, "above": 0, "nosig": 0, "by_tier": {},
             "ratios_da": [], "ratios_emp": []}
    out_rows = []

    for t in targets:
        sub, scale, geo = derive_sub(t), derive_scale(t), derive_geo(t)
        rec = dict(t)
        rec["sub_sector_derived"] = sub or ""
        rec["scale_tier_derived"] = scale or ""
        total = 0.0
        for fname, fn in FACTORS:
            pts, c, flag = fn(t, cur, sub, scale, geo)
            rec[fname + "_pts"]  = pts
            rec[fname + "_cite"] = c
            rec[fname + "_flag"] = "" if flag == "ok" else flag
            total += pts
            if flag not in ("ok", "reserved_zero", "non_ut"):
                skipped.append({"track": t.get("track"), "a_rank": t.get("a_rank"),
                                "bench_rank": t.get("bench_rank"), "company": t.get("company"),
                                "factor": fname, "reason": flag,
                                "sub_sector": sub or "", "scale_tier": scale or "", "geo": geo or ""})
        iv = implied_valuation(t, cur, sub, scale, geo)
        rec.update(iv)
        w4 = f(t.get("composite")) or 0.0
        rec["w4_composite"] = w4
        rec["overlay_pts_sum"] = round(total, 1)
        rec["overlay_composite"] = round(w4 + total, 1)
        out_rows.append(rec)

        # bus-anchor reconciliation (A-list, verified census fleet, implied rev computed)
        if t.get("track") == "A" and census_fleet(t) and isinstance(iv.get("iv_rev_low"), int):
            tier = scale or "unknown"
            d = recon["by_tier"].setdefault(tier, {"n": 0, "in": 0, "below": 0, "above": 0, "nosig": 0})
            recon["n"] += 1; d["n"] += 1
            sig = independent_rev_signal(t)
            ivp = iv["iv_rev_point"]
            da = f(t.get("da_revenue_est"))
            emp = i(t.get("web_employees_est"))
            if da and da > 0 and ivp: recon["ratios_da"].append(ivp / da)
            if emp > 0 and ivp:       recon["ratios_emp"].append(ivp / (emp * 135000))
            if sig is None:
                recon["nosig"] += 1; d["nosig"] += 1
            else:
                lo = iv["iv_rev_low"] * (1 - RECON_TOLERANCE)
                hi = iv["iv_rev_high"] * (1 + RECON_TOLERANCE)
                if   sig < lo: recon["below"] += 1; d["below"] += 1
                elif sig > hi: recon["above"] += 1; d["above"] += 1
                else:          recon["in"]    += 1; d["in"]    += 1

    # re-rank (deterministic): overlay_composite desc, data_confidence desc, W4 rank asc
    A = sorted([r for r in out_rows if r["track"] == "A"],
               key=lambda x: (-x["overlay_composite"], -(f(x.get("data_confidence")) or 0), i(x.get("a_rank"))))
    B = sorted([r for r in out_rows if r["track"] == "BENCH"],
               key=lambda x: (-x["overlay_composite"], -(f(x.get("data_confidence")) or 0), i(x.get("bench_rank"))))
    for n, r in enumerate(A, 1): r["a_rank_overlay"] = n
    for n, r in enumerate(B, 1): r["bench_rank_overlay"] = n

    write_ranked(A + B)
    write_top50(A)
    write_recon(recon)
    write_skipped(skipped)
    con.close()
    print(f"_w5_overlay: {len(out_rows)} targets scored (A={len(A)}, BENCH={len(B)})")
    print(f"  implied valuation computed: {sum(1 for r in out_rows if isinstance(r.get('iv_rev_point'), int))}")
    print(f"  reconciliation A/census: n={recon['n']} in={recon['in']} below={recon['below']} above={recon['above']} nosig={recon['nosig']}")
    print(f"  skipped-factor log rows: {len(skipped)}")

def write_ranked(rows):
    base = ["a_rank_overlay", "bench_rank_overlay", "track", "company", "state", "hq",
            "w4_composite", "overlay_pts_sum", "overlay_composite", "data_confidence",
            "sub_sector_derived", "scale_tier_derived", "fleet_buses", "drivers", "founded",
            "fmcsa_source", "usdot", "_sf", "_su", "_geo", "_ind", "_oh", "_rel",
            "composite", "a_rank", "bench_rank"]
    factor = []
    for fn, _ in FACTORS:
        factor += [fn + "_pts", fn + "_cite", fn + "_flag"]
    context = ["da_revenue_est", "da_employees", "web_employees_est", "da_size_tier",
               "web_ownership_type", "web_owner_or_parent", "web_succession_signal",
               "web_service_types", "web_districts_or_customers", "web_website"]
    cols = base + factor + IV_COLS + context
    with open(OUT_RANKED, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow(r)

def _m(v):
    if v in (None, "", 0): return "—"
    try: return f"{float(v)/1e6:.1f}"
    except Exception: return "—"

def _band_m(r, p):
    lo, hi = r.get(p + "_low"), r.get(p + "_high")
    if lo in (None, "") or hi in (None, ""): return "—"
    return f"{float(lo)/1e6:.1f}–{float(hi)/1e6:.1f}"

def _top_factor(r):
    best = ("", 0.0)
    for fn, _ in FACTORS:
        v = r.get(fn + "_pts") or 0
        if abs(v) > abs(best[1]): best = (fn, v)
    return f"{best[0]} {best[1]:+.0f}" if best[0] else "—"

def write_top50(A):
    with open(OUT_TOP50, "w") as fh:
        fh.write("# Summit tuck-in targets — A-list TOP 50 (W5 overlay-adjusted)\n\n")
        fh.write("*Overlay composite = W4 composite + Σ(overlay factor points). The W4 baseline is "
                 "preserved (`composite`, `a_rank`) for side-by-side comparison. Implied valuation is "
                 "shown as a low–high band ($M); gated on verified census fleet — `—` = not computed. "
                 "Δrank > 0 = the overlay promoted the target vs W4.*\n\n")
        fh.write("| # | Δrank | Ovl | W4 | Conf | Company | ST | Sub | Buses | Impl Rev $M | Impl EBITDA $M | EV@entry $M | Δ→8× $M | Top factor |\n")
        fh.write("|--:|--:|--:|--:|--:|---|---|:--:|--:|---|---|---|--:|---|\n")
        for r in A[:50]:
            dr = i(r.get("a_rank")) - r["a_rank_overlay"]
            fh.write(f"| {r['a_rank_overlay']} | {dr:+d} | {r['overlay_composite']:.0f} | {r['w4_composite']:.0f} "
                     f"| {r.get('data_confidence','')} | {str(r['company'])[:26]} | {r.get('state','')} "
                     f"| {r.get('sub_sector_derived') or '—'} | {r.get('fleet_buses') or '—'} "
                     f"| {_band_m(r,'iv_rev')} | {_band_m(r,'iv_ebitda')} | {_band_m(r,'iv_ev_entry_consensus')} "
                     f"| {_m(r.get('iv_value_creation_spread_point'))} | {_top_factor(r)} |\n")
        fh.write("\n*Columns: Ovl = overlay composite; W4 = baseline composite; Sub = derived sub-sector "
                 "(Y school / S special-needs / C charter); EV@entry = consensus entry-EV band (intersection of "
                 "implied-EBITDA × 3–5× and fleet × $/bus methods); Δ→8× = value-creation spread to an 8× build "
                 "multiple (point estimate). Implied bands anchor on Summit's own ~$98K/bus, 15–34% EBITDA economics.*\n")

def write_recon(recon):
    os.makedirs(DIAG_DIR, exist_ok=True)
    with open(OUT_RECON, "w") as fh:
        n = recon["n"]
        fh.write(f"W5 bus-anchor reconciliation (±{int(RECON_TOLERANCE*100)}% tolerance)\n")
        fh.write("Tests whether each A-list target's implied-revenue band (fleet × rev/bus) brackets an "
                 "independent signal (da_revenue_est, else web_employees_est × $135K). Sanity check, not a gate.\n\n")
        if n == 0:
            fh.write("A-list with verified census fleet + computed implied revenue: 0 — no reconciliation possible.\n")
            return
        denom = max(1, n - recon["nosig"])
        fh.write(f"A-list w/ verified census fleet + implied rev: {n}\n")
        fh.write(f"  in_band:    {recon['in']:>4}  ({100.0*recon['in']/denom:.1f}% of {denom} with an independent signal)\n")
        fh.write(f"  below_band: {recon['below']:>4}  (implied range above the independent signal)\n")
        fh.write(f"  above_band: {recon['above']:>4}  (implied range below the independent signal)\n")
        fh.write(f"  no_signal:  {recon['nosig']:>4}\n\n")
        fh.write("By derived scale tier:\n")
        for tier in sorted(recon["by_tier"]):
            d = recon["by_tier"][tier]
            fh.write(f"  {tier:>8}: n={d['n']:>4}  in={d['in']:>4}  below={d['below']:>4}  above={d['above']:>4}  nosig={d['nosig']:>4}\n")
        b, a = recon["below"], recon["above"]
        if (b + a) > 0 and abs(b - a) / (b + a) > 0.4:
            skew = "implied OVERSTATES" if b > a else "implied UNDERSTATES"
            fh.write(f"\nFLAG: systemic skew — one-sided mismatch >40% ({skew} the independent signal). "
                     f"Revisit revenue_per_bus (currently national, observed on 40-860 vehicle operators).\n")
        else:
            fh.write("\nNo systemic skew (one-sided bracket mismatch <=40%).\n")

        # ratio distribution — characterizes the bias and exposes how noisy the independent signal is
        def _stats(xs):
            xs = sorted(xs)
            if not xs: return None
            n = len(xs)
            med = xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2
            return n, xs[max(0, n // 10)], xs[n // 4], med, xs[3 * n // 4], xs[min(n - 1, 9 * n // 10)]
        sda = _stats(recon["ratios_da"])
        semp = _stats(recon["ratios_emp"])
        fh.write("\nRatio of implied_rev_point to the independent signal (characterizes bias + signal noise):\n")
        if sda:
            fh.write(f"  vs da_revenue_est (n={sda[0]}):  p10={sda[1]:.2f} p25={sda[2]:.2f} median={sda[3]:.2f} p75={sda[4]:.2f} p90={sda[5]:.2f}\n")
        if semp:
            fh.write(f"  vs web_employees_est x $135K (n={semp[0]}):  p10={semp[1]:.2f} p25={semp[2]:.2f} median={semp[3]:.2f} p75={semp[4]:.2f} p90={semp[5]:.2f}\n")
        fh.write(
            "\nINTERPRETATION: the low in-band rate is driven by NOISE IN da_revenue_est, not by the implied model.\n"
            "Data Axle revenue estimates for these private operators are internally implausible (observed range\n"
            "~$4K to ~$343K of stated revenue per census bus), so they make a weak reconciliation anchor. The\n"
            "fleet x rev/bus implied revenue — anchored on Summit's own bid/deal economics (~$98K/bus) — is the\n"
            "more internally consistent estimate. Median implied/da ~1.6x reflects Data Axle UNDER-counting small\n"
            "private-operator revenue. Treat the implied bands as the better revenue read; da_revenue_est is a\n"
            "cross-check, not ground truth. (Cleaner per-target revenue requires the night-research pass.)\n")

def write_skipped(skipped):
    os.makedirs(DIAG_DIR, exist_ok=True)
    with open(OUT_SKIP, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["track", "a_rank", "bench_rank", "company",
                                           "factor", "reason", "sub_sector", "scale_tier", "geo"])
        w.writeheader()
        for r in skipped: w.writerow(r)

if __name__ == "__main__":
    main()
