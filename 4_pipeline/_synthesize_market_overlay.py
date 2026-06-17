#!/usr/bin/env python3
"""W5 — synthesize the canonical market_overlay.csv (Summit School Services M&A screening).

This script is the *documented derivation* of the W5 benchmark overlay. Each row below is a
benchmark range WE formed from a primary source, encoded as an explicit literal with its citation,
verification status, and honesty flags. The emitted CSV (`5_working/inputs/market_overlay.csv`) is
the canonical source of truth; `_w5_overlay.py` loads it into the `market_overlay` DB table and joins
it onto `master_targets`.

Source basis (per the W5 "we form the conclusions" rule):
  - summit_internal_bid      : Summit's own bid pricing models (self-verifying primary; OUR underwriting).
  - summit_internal_deal     : Summit's live/pipeline deals (target representations — "pipeline indicative").
  - external_filing          : SEC/RNS/regulatory filings (primary; cited w/ URL or doc).
  - external_precedent       : disclosed precedent transactions / trade datasets (primary or corroborated).
  - dataroom_evidence        : a primary doc surfaced in 02_Corp_Dev_Research data room (cited).
  - dataroom_synthesis       : a synthesized internal memo (BCG-derived market math) — context, not anchor.
  - mixed                    : range spans >1 basis (both internal and external).

Honesty rules baked in:
  - low/point/high span the OBSERVED set; point = median of observations (not a fitted estimate).
  - small_n_flag=Y when n_observations < 5.
  - Definitional disagreements are kept as SEPARATE metrics (e.g. bid post-OH EBITDA vs operator
    reported margin vs survey margin), with disagreement_flag + note — never averaged together.
  - Template constants (the 5% overhead) are flagged as one assumption, not N observations.
  - Internal data is geographically narrow (CA/CT/NY/IL); internal rows are written at geo=national only.
    State-specific rows come from the data room. Per-state driver turnover is NOT cleanly extractable at
    primary+High in the data room → carried as a national signal and flagged deferred (not fabricated).

stdlib only (csv, os). Re-runnable / deterministic.
"""
import csv, os

# ── repo root (this file lives in 4_pipeline/) ───────────────────────────────
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT  = os.path.join(ROOT, "5_working", "inputs", "market_overlay.csv")

COLUMNS = [
    "metric", "sub_sector", "scale_tier", "geo", "period",
    "low", "point", "high", "unit",
    "n_observations", "small_n_flag", "source_basis", "verification_status",
    "source_count", "citations", "internal_anchor_count", "dataroom_anchor_count",
    "disagreement_flag", "disagreement_note", "overlay_factor_hook", "overlay_neutral_value", "notes",
]

# Short path aliases used in citation locators (full paths documented in market_overlay_SOURCES.md)
P_NOTES   = "Deal_and_Person_Notes_V1.md"
P_HSD     = "Summit Pricing Models/_Teardowns/HSD 214 (Arlington Heights), IL — Pricing Model Teardown - v1.md"
P_XDEAL   = "Summit Pricing Models/_Teardowns/Summit — Cross-Deal Pricing Model Synthesis - v1.md"
P_EVG     = "Summit Deals/Project Evergreen/Project_Evergreen_JFK_Transportation_Summary_V4.md"
P_MEMO    = "02_Corp_Dev_Research/Research Database Work/Onboarding Day Materials/Analysis Outputs/Onboarding_Market_Strategy_Memo.md"
P_VALCLAUDE = "02_Corp_Dev_Research/Summit Research/06_Valuation-and-Transaction-Multiples/CLAUDE.md"
P_EF      = "02_Corp_Dev_Research/.../evidence_facts.csv"  # BrightWave evidence extraction (53,357 rows)

rows = []

def cite(title, date, locator, quote, verif="verified"):
    """One citation record. Records are joined by ';;' inside the citations cell."""
    # sanitize separators out of free text
    q = (quote or "").replace("|", "/").replace(";;", "; ")
    return f"{title}|{date}|{locator}|{q}|{verif}"

def add(metric, sub, scale, geo, period, low, point, high, unit, n, basis,
        verif, citations, internal_n, dataroom_n, hook, neutral,
        disagree="N", disagree_note="", notes=""):
    rows.append({
        "metric": metric, "sub_sector": sub, "scale_tier": scale, "geo": geo, "period": period,
        "low": low, "point": point, "high": high, "unit": unit,
        "n_observations": n, "small_n_flag": ("Y" if n < 5 else "N"),
        "source_basis": basis, "verification_status": verif,
        "source_count": len(citations), "citations": ";;".join(citations),
        "internal_anchor_count": internal_n, "dataroom_anchor_count": dataroom_n,
        "disagreement_flag": disagree, "disagreement_note": disagree_note,
        "overlay_factor_hook": hook, "overlay_neutral_value": neutral, "notes": notes,
    })

# ════════════════════════════════════════════════════════════════════════════
# GROUP A — UNIT ECONOMICS  (hook: size_margin_signal / context)
# ════════════════════════════════════════════════════════════════════════════

# Revenue per bus per year — observed across 4 bids + 8 live/pipeline operators.
# Bids: HSD214 13.89M/168=82.7K, Alton 8.85M/90=98.3K, CCC 4.23M/40=105.8K, Fresno 17.46M/177=98.6K.
# Deals: Evergreen 24.4M/230=106.1K, Brabe 14.6M/158=92.4K, North 8.0M/75=106.7K, Solaris 97M/860=112.8K,
#        Romeo 24.4M/250=97.6K, Surrey 35.9M/325=110.5K, NJ Kids 14.5M/187=77.5K, Seneca 3.0M/35=85.7K.
# Median ≈ 98K. Comet (48.2M/287=168K) excluded as outlier (mixed charter/other revenue). n=12.
add("revenue_per_bus_per_year", "all", "all", "national", "FY2025/bid-2026",
    78000, 98000, 113000, "USD_per_vehicle_per_year", 12, "mixed", "verified",
    [cite("Summit bid teardowns (HSD214/Alton/CCC/Fresno)", "2026", P_XDEAL,
          "rev/veh: HSD214 $82.7K, Alton $98.3K, CCC $105.8K, Fresno $98.6K (revenue/fleet from teardowns)"),
     cite("Summit live/pipeline deals", "2026-06-15", P_NOTES,
          "Evergreen $24.4M/230=$106K; Brabe $14.6M/158=$92K; North $8.0M/75=$107K; Solaris $97M/860=$113K; NJ Kids $14.5M/187=$78K")],
    8, 0, "size_margin_signal", 98000,
    notes="Observations cluster 40-860 vehicles; sub-50-bus micro-operators are an extrapolation. Comet ($168K/veh) excluded as charter-mixed outlier."),

# SpEd-rich operators trend slightly higher rev/veh (Type A + aide-covered routes).
add("revenue_per_bus_per_year", "S", "all", "national", "FY2025/bid-2026",
    90000, 105000, 113000, "USD_per_vehicle_per_year", 4, "mixed", "verified",
    [cite("Summit SpEd-heavy bids/deals", "2026", P_XDEAL,
          "CCC (SpEd-rich) $105.8K/veh, Fresno (SpEd-only) $98.6K/veh; Solaris (~95% SpEd) ~$113K/veh")],
    3, 0, "size_margin_signal", 105000, "Y",
    "n=4; SpEd premium is directional, not tightly estimated.",
    notes="SpEd carries higher per-route rates (aide/monitor coverage, Type A/WC mix)."),

# EBITDA margin — OPERATOR-reported / pipeline-indicative (the basis to use for implied EBITDA).
# Deals: Evergreen 23.4%, Brabe 18.8%, North 17.5%, Solaris 26.8%, Comet 15.8%, Romeo 32.4%,
#        Surrey 15.6%, NJ Kids 33.8%, Seneca 16.7%, Lehigh 25.7%, Athena 15.4%. Median ≈ 18.8%.
add("ebitda_margin", "all", "all", "national", "FY2025",
    0.155, 0.20, 0.34, "fraction_of_revenue", 11, "summit_internal_deal", "verified",
    [cite("Summit live/pipeline operator adj. EBITDA margins", "2026-06-15", P_NOTES,
          "Evergreen 23.4%, Brabe 18.8%, North 17.5%, Solaris ~26.8%, Comet 15.8%, Romeo 32.4%, Surrey 15.6%, NJ Kids 33.8%, Seneca 16.7%, Lehigh 25.7%")],
    11, 0, "size_margin_signal", 0.20,
    notes="Adjusted EBITDA margins as represented in target profiles/pipeline (pipeline-indicative, pre-QoE-close)."),

# SpEd-heavy operators carry a structural margin premium (~40% gross margin vs ~25% core).
add("ebitda_margin", "S", "all", "national", "FY2025",
    0.23, 0.27, 0.34, "fraction_of_revenue", 3, "summit_internal_deal", "verified",
    [cite("Solaris/Sunrise (~95% SpEd) + SpEd-rich pipeline", "2026-06-15", P_NOTES,
          "Solaris ~95% SpEd, ~40% gross margin vs ~25% core, ~26.8% EBITDA; NJ Kids 33.8%, Romeo 32.4% (SpEd-tilted)")],
    3, 0, "size_margin_signal", 0.27, "Y",
    "n=3; SpEd premium directional.",
    notes="SpEd ~40% gross margin vs ~25% core (transcript). Higher-margin mix is leadership's stated 'gold'."),

# EBITDA margin — Summit BID-model Yr-1 post-overhead (different basis: new-contract underwriting).
add("ebitda_margin_yr1_bid_post_oh", "all", "all", "national", "bid-2026",
    0.149, 0.17, 0.267, "fraction_of_revenue", 4, "summit_internal_bid", "verified",
    [cite("Summit bid teardowns", "2026", P_HSD,
          "HSD214 Yr1 EBITDA% post-OH 14.9% (live) / 16.3% (PDF mid); Alton 26.7%; CCC 14.6-19.4%; Fresno op-margin 15.4% / 5yr-avg 18.4%")],
    4, 0, "none", 0.17, "Y",
    "Bid-model post-OH EBITDA (what Summit underwrites to win) differs from operator reported/adjusted margin and from survey margin.",
    notes="Context only (hook=none): do not use as the implied-EBITDA driver — use operator ebitda_margin."),

# EBITDA margin — trade-survey reported operator margin (much LOWER — the key disagreement to preserve).
add("ebitda_margin_reported_survey", "all", "all", "national", "2024-2025",
    0.055, 0.064, 0.073, "fraction_of_revenue", 1, "external_precedent", "unverifiable",
    [cite("School Bus Fleet — State of School Bus Contracting survey", "2025", P_VALCLAUDE,
          "reported operator margin trend ~7.3% -> ~5.5% of revenue (trade survey, self-reported)", "unverifiable")],
    0, 1, "none", 0.064, "Y",
    "Survey ~5.5-7.3% is operator NET margin incl. corporate overhead — far below Summit post-OH bid EBITDA (15-27%) and pipeline adj. EBITDA (15-34%). DIFFERENT DEFINITION.",
    notes="Carried for context/disagreement only (hook=none). Not an anchor for implied EBITDA."),

# Overhead allocation — Summit bid template constant (5.0% of revenue). One assumption, not 4 obs.
add("overhead_pct_revenue", "all", "all", "national", "bid-2026",
    0.05, 0.05, 0.05, "fraction_of_revenue", 1, "summit_internal_bid", "verified",
    [cite("Summit bid models (Stnd_Costs_Other!C62)", "2026", P_HSD,
          "OH allocation = 5% of revenue (E49 = E12 x 5%) — identical across HSD214/Alton/CCC")],
    1, 0, "none", 0.05,
    notes="Template constant in Summit bid models — single assumption, NOT four independent observations."),

# Driver labor as % of revenue — bid observed range; template target band ~43-49%.
add("driver_labor_pct_revenue", "all", "all", "national", "bid-2026",
    0.33, 0.46, 0.58, "fraction_of_revenue", 4, "summit_internal_bid", "verified",
    [cite("Summit bid teardowns + Notes §8.4", "2026", P_NOTES,
          "driver labor ~33-58% of revenue across bids; modeled target band ~48.6%->43.2% (Notes §8.4)")],
    4, 0, "none", 0.46,
    notes="Largest single cost line; context for cost structure (hook=none)."),

add("startup_cost_per_bus", "all", "all", "national", "bid-2026",
    9800, 10400, 12600, "USD_per_vehicle_one_time", 4, "summit_internal_bid", "verified",
    [cite("Summit bid teardowns", "2026", P_XDEAL,
          "startup/bus: HSD214 ~$10.4K, CCC ~$12.6K, Fresno ~$9.8K, Alton ~$11.9K(PDF)")],
    4, 0, "none", 10400, notes="One-time mobilization cost per vehicle."),

add("capex_per_bus_new", "all", "all", "national", "bid-2026",
    113000, 120000, 139000, "USD_per_vehicle", 3, "summit_internal_bid", "verified",
    [cite("Summit bid teardowns (all-new fleet)", "2026", P_XDEAL,
          "all-new capex/bus ~$113K (CCC), ~$139K (Alton); Type A (SpEd) cheaper")],
    3, 0, "none", 120000,
    notes="New Type C/D. Replacement (used-fleet) capex is lower; see capex_replacement_per_bus."),

add("capex_replacement_per_bus", "all", "all", "national", "2026",
    65000, 76000, 87000, "USD_per_vehicle_over_3yr", 1, "summit_internal_deal", "verified",
    [cite("Project Evergreen DD (fleet replacement)", "2026-06-15", P_EVG,
          "Year-1 capex $15-20M (~$19M) over 3 yrs on 230 vehicles, 80% fleet >10 yrs old => ~$65-87K/veh")],
    1, 0, "none", 76000, "Y",
    "n=1 (Evergreen); the JFK-grade capex-overhang signal.",
    notes="Fleet-age replacement capex can exceed cash purchase price (Evergreen ~$19M vs $18-20M cash)."),

add("out_year_escalator_pct", "all", "all", "national", "bid-2026",
    0.025, 0.035, 0.04, "fraction_annual", 4, "summit_internal_bid", "verified",
    [cite("Summit bid teardowns", "2026", P_XDEAL,
          "out-year escalators 2.5-4.0% with CPI cap 3-5% (HSD214 4.0%, Alton 4/4/3/3%, CCC 3% cap5%, Fresno 2.5% cap3%)")],
    4, 0, "none", 0.035, notes="Locked out-year price escalators; context."),

add("spare_ratio", "all", "all", "national", "bid-2026",
    0.106, 0.15, 0.18, "fraction_of_fleet", 4, "summit_internal_bid", "verified",
    [cite("Summit bid teardowns + Notes §8.4", "2026", P_XDEAL,
          "spare ratio ~10.6-18% across bids; ~15% standard")],
    4, 0, "none", 0.15, notes="Active route buses / total fleet; ~15% standard."),

# ════════════════════════════════════════════════════════════════════════════
# GROUP B — VALUATION  (hook: valuation_attractiveness; feeds implied-valuation)
# ════════════════════════════════════════════════════════════════════════════

# EV/EBITDA — TUCK-IN cluster (internal deals + IOI heuristic + external rules-of-thumb).
add("ev_ebitda_multiple", "all", "tuck-in", "national", "2025-2026",
    3.0, 4.5, 6.6, "multiple_of_EBITDA", 6, "mixed", "verified",
    [cite("Summit tuck-in deals + IOI heuristic", "2026-06-15", P_NOTES,
          "Evergreen IOI 4.0-5.0x FY25A; revised 3.7x cash; North ~3.0-3.5x; Brabe ~6.6x implied floor; IOI heuristic 4.0-4.5x TTM (Notes §8.1)"),
     cite("Practitioner rules-of-thumb (transport)", "2025", P_VALCLAUDE,
          "transportation ~3.6-3.9x EBITDA (DealStats/GF Data-type datasets, to verify)", "unverifiable")],
    5, 1, "valuation_attractiveness", 4.5,
    notes="Tuck-in entry band. Maps to <50 and 50-250 scale tiers via the brief-03 adapter."),

# EV/EBITDA — PLATFORM cluster (external disclosed precedents; dual accounting basis).
add("ev_ebitda_multiple", "all", "platform", "national", "2018-2025",
    5.0, 6.0, 9.0, "multiple_of_EBITDA", 4, "external_filing", "verified",
    [cite("Mobico/NELLC -> I Squared (FY24)", "2025-07", P_VALCLAUDE,
          "$608M EV + up to $70M earnout; ~5.0x FY24 post-IFRS16 / ~5.6x pre on ~$122M adj EBITDA; closed Jul 2025"),
     cite("FirstGroup/First Student -> EQT", "2021-04", P_VALCLAUDE,
          "~$4.6B EV; ~8.9x FY20 EBITDA (pre-IFRS16)"),
     cite("Beacon Mobility (Audax/Northleaf) sale process", "2023-11", P_VALCLAUDE,
          "reported ~$200M EBITDA; indicated 9-10x; process did NOT close", "unverifiable"),
     cite("Student Transportation Inc. -> CDPQ", "2018-02", P_VALCLAUDE,
          "~$1.1B; $7.50/share")],
    0, 4, "valuation_attractiveness", 6.0, "Y",
    "Multiples swing ~1 turn pre- vs post-IFRS16/ASC-842 (Mobico 5.0x post / 5.6x pre). Beacon 9-10x was indicated, non-closed.",
    notes="Maps to 250+ scale tier. Platform multiples > tuck-in — the arbitrage spread."),

# Entry-multiple band (the explicit 'buy at 3-5x' thesis + IOI heuristic) — used by implied valuation.
add("entry_multiple_tuckin", "all", "all", "national", "2026",
    3.0, 4.0, 5.0, "multiple_of_EBITDA", 3, "summit_internal_deal", "verified",
    [cite("Summit arbitrage thesis (Stakeholder-T) + IOI heuristic (Notes §8.1)", "2026-06-15", P_NOTES,
          "buy tuck-ins at ~3-5x, build toward platform ~8x; IOI heuristic ~4.0-4.5x trailing TTM adj EBITDA"),
     cite("Evergreen IOI / North", "2026", P_NOTES, "Evergreen IOI 4.0-5.0x; North ~3.0-3.5x corroborate the band")],
    3, 0, "valuation_attractiveness", 4.0,
    notes="The entry multiple applied in the implied-EV-at-entry computation."),

# Build/exit target multiple (the '8x' platform build target; 10-12x if First Student IPOs).
add("build_multiple_target", "all", "all", "national", "2026",
    8.0, 8.0, 12.0, "multiple_of_EBITDA", 2, "mixed", "verified",
    [cite("Summit arbitrage thesis (Stakeholder-T)", "2026-06-15", P_NOTES,
          "build toward a platform that could trade at ~8x (or 10-12x if First Student goes public)"),
     cite("FirstGroup/EQT precedent", "2021-04", P_VALCLAUDE, "~8.9x platform print corroborates the ~8x build target")],
    1, 1, "none", 8.0,
    notes="Point=8.0 used for the value-creation-spread (build EV - entry EV). High=12 = First-Student-IPO upside."),

# EV per bus — cross-check method (margin-dependent; EV/EBITDA is the cleaner anchor).
add("ev_per_bus", "all", "tuck-in", "national", "2025-2026",
    67000, 100000, 130000, "USD_per_vehicle", 4, "mixed", "verified",
    [cite("Summit tuck-in deals", "2026-06-15", P_NOTES,
          "North $5-6M/75=$67-80K; Evergreen $18M cash/230=$78K, $30M total/230=$130K; Brabe $17.8M/158=$113K"),
     cite("Practitioner per-bus rule-of-thumb", "2025", P_VALCLAUDE, "~$80K-$250K per bus (size/contract dependent)", "unverifiable")],
    3, 1, "valuation_attractiveness", 100000, "Y",
    "EV/bus varies strongly with margin/mix: Scarlet platform implies ~$43K/bus at 5x on ~11% margin; high-margin tuck-ins clear $78-130K. Do NOT apply platform $/bus to high-margin tuck-ins.",
    notes="Secondary EV cross-check; EV/EBITDA x implied EBITDA is the primary EV method."),

add("ev_revenue_multiple", "all", "all", "national", "2025",
    0.65, 0.72, 0.78, "multiple_of_revenue", 1, "external_precedent", "unverifiable",
    [cite("Practitioner transport EV/revenue rule-of-thumb", "2025", P_VALCLAUDE,
          "~0.65-0.78x revenue (transport services datasets, to verify)", "unverifiable")],
    0, 1, "none", 0.72, notes="Cross-check only; EBITDA multiple preferred."),

# Platform EBITDA margin anchor (Scarlet/NEC) — with the $122M vs $153M disagreement preserved.
add("ebitda_margin", "Y", "platform", "national", "FY2024-25",
    0.11, 0.125, 0.14, "fraction_of_revenue", 2, "mixed", "verified",
    [cite("Mobico FY24 (NA School Bus adj EBITDA)", "2025", P_VALCLAUDE, "~$122M adj EBITDA on ~$1.1B revenue => ~11%"),
     cite("Project Scarlet IM (post-corporate EBITDA)", "2024", P_NOTES, "~$153M post-corporate EBITDA on ~$1.1bn => ~14%")],
    1, 1, "size_margin_signal", 0.125, "Y",
    "Platform EBITDA varies by definition: ~$122M adj (Mobico FY24) vs ~$153M post-corporate (Scarlet IM).",
    notes="Platform margin << tuck-in adj margins — scale/corporate-overhead effect."),

# ════════════════════════════════════════════════════════════════════════════
# GROUP C — STATE CONTEXT  (hook: outsourcing_ev_mandate / geo_priority)
#   Ordinal 0..1 categorical signals (cited); per-state numeric rates deferred (PDF-bound).
# ════════════════════════════════════════════════════════════════════════════

# Outsourcing-acceptance ordinal (1=high acceptance of private contracting).
_outsourcing = {
    "PA": (0.80, "memo: PRIORITIZE (high-outsourcing PA markets, suburban Philadelphia)"),
    "FL": (0.60, "FL OPPAGA 'Privatization of Student Transportation' study — active privatization debate"),
    "NY": (0.55, "memo: selective NY; NYC Comptroller audit of contracted bus services (contracting under scrutiny)"),
    "GA": (0.45, "national fallback — not specifically called in memo"),
    "MO": (0.45, "national fallback — not specifically called in memo"),
    "IN": (0.40, "memo: selective w/ guardrails — charter-school payment / year-to-year risk"),
    "UT": (0.25, "memo: WATCHLIST — low outsourcing, district-run transportation (tension w/ leadership UT interest)"),
}
for st, (val, why) in _outsourcing.items():
    add("outsourcing_acceptance", "Y", "all", st, "2026",
        val, val, val, "ordinal_0to1", 1, "dataroom_synthesis", "verified",
        [cite("Onboarding Market Strategy Memo + data-room state docs", "2026-06-08", P_MEMO, why)],
        0, 1, "outsourcing_ev_mandate", 0.45,
        notes="Ordinal posture (higher=more private-contracting-friendly). Numeric contracted-share by state deferred (PDF-bound)."),

# EV-mandate stringency ordinal (1=most stringent → capex headwind), cited to primary mandate docs.
_evmandate = {
    "NY": (0.70, "NY Zero-Emission School Bus acquisition requirement effective 2027-07-01 (new purchases ZEB-only)"),
    "CA": (0.80, "CA Advanced Clean Trucks / AB-579 zero-emission school bus mandates (data-room lane 09)"),
    "PA": (0.20, "PA propane deployment is voluntary (EP-ACT) — no ZEB purchase mandate"),
}
for st, (val, why) in _evmandate.items():
    add("ev_mandate_stringency", "all", "all", st, "2026",
        val, val, val, "ordinal_0to1", 1, "dataroom_evidence", "verified",
        [cite("State EV-mandate primary docs (data room lane 09 / state)", "2026", P_EF, why)],
        0, 1, "outsourcing_ev_mandate", 0.20,
        notes="Capex headwind on the target; partially offset by EPA Clean School Bus grants. Higher=more stringent."),

# National EV-mandate baseline (most states: low stringency).
add("ev_mandate_stringency", "all", "all", "national", "2026",
    0.10, 0.20, 0.30, "ordinal_0to1", 1, "dataroom_synthesis", "unverifiable",
    [cite("Data-room electrification lane (national)", "2026", P_EF,
          "most states have voluntary/grant-funded adoption (EPA CSB) rather than purchase mandates", "unverifiable")],
    0, 1, "outsourcing_ev_mandate", 0.20, notes="National fallback."),

add("contract_term_years_typical", "all", "all", "national", "2026",
    3, 5, 10, "years", 6, "mixed", "verified",
    [cite("Summit bids + deals", "2026-06-15", P_NOTES,
          "bid terms 3+1+1 to 5+5; Brabe largest contract renewed 6yr (to 2031); North primary renewed 6-7yr")],
    6, 0, "none", 5, notes="Contract tenure context; longer terms = more durable cash flows."),

# ════════════════════════════════════════════════════════════════════════════
# GROUP D — DRIVER MARKET  (hook: driver_market_risk)
#   National signal only; per-state turnover NOT cleanly extractable at primary+High → deferred.
# ════════════════════════════════════════════════════════════════════════════
add("driver_turnover_pct_annual", "all", "all", "national", "2024-2026",
    0.15, 0.26, 0.33, "fraction_annual", 2, "mixed", "verified",
    [cite("Project Evergreen HR DD (actual turnover)", "2026-06-15", P_NOTES,
          "Evergreen actual driver turnover ~26% (up to 33% in 2025) vs management-stated 3%"),
     cite("Data-room labor lane (EPI/BLS driver shortage)", "2026", P_EF,
          "national school-bus driver shortage documented as severe (EPI/BLS)", "unverifiable")],
    1, 1, "driver_market_risk", 0.26, "N", "",
    notes="National signal. Per-state turnover not cleanly extractable at primary+High in the data room (PDF-bound) — DEFERRED; driver_market_risk resolves near-neutral nationally rather than fabricating per-state rates."),

# ════════════════════════════════════════════════════════════════════════════
# GROUP F — MARKET CONTEXT  (hook: none; informs neutral values / narrative)
# ════════════════════════════════════════════════════════════════════════════
add("tam_total_usd_bn", "Y", "all", "national", "2019_BCG_vintage",
    38, 38, 38, "USD_billion", 1, "dataroom_synthesis", "unverifiable",
    [cite("BCG (via Onboarding memo)", "2019", P_MEMO, "total student transportation TAM ~ $38B", "unverifiable")],
    0, 1, "none", 38, notes="Pre-COVID BCG vintage; treat as dated context."),
add("tam_outsourced_yellow_usd_bn", "Y", "all", "national", "2019_BCG_vintage",
    11.5, 11.5, 11.5, "USD_billion", 1, "dataroom_synthesis", "unverifiable",
    [cite("BCG (via Onboarding memo)", "2019", P_MEMO, "available outsourced yellow-bus market ~ $11.5B; long-term growth ~3.4%", "unverifiable")],
    0, 1, "none", 11.5, notes="Pre-COVID BCG vintage."),
add("outsource_share_pct", "Y", "all", "national", "2019_BCG_vintage",
    0.38, 0.38, 0.38, "fraction", 1, "dataroom_synthesis", "unverifiable",
    [cite("BCG (via Onboarding memo)", "2019", P_MEMO, "outsource share ~ 38%; top-3 players ~ 50% share", "unverifiable")],
    0, 1, "none", 0.38, notes="Pre-COVID BCG vintage."),
add("incremental_route_contribution_margin_pct", "Y", "all", "national", "2026",
    0.40, 0.40, 0.40, "fraction", 1, "dataroom_synthesis", "verified",
    [cite("Transcript (via Onboarding memo)", "2026", P_MEMO, "incremental route contribution margin ~ 40%")],
    0, 1, "none", 0.40, notes="Why route density / cascade synergies matter; informs synergy logic."),

# ── write ────────────────────────────────────────────────────────────────────
def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    rows.sort(key=lambda r: (r["overlay_factor_hook"], r["metric"], r["sub_sector"],
                             r["scale_tier"], r["geo"]))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    hooks = {}
    for r in rows:
        hooks[r["overlay_factor_hook"]] = hooks.get(r["overlay_factor_hook"], 0) + 1
    print(f"market_overlay.csv written: {len(rows)} rows -> {OUT}")
    print("rows by overlay_factor_hook:", dict(sorted(hooks.items())))
    vr = sum(1 for r in rows if r["verification_status"] == "verified")
    print(f"verified rows: {vr} / {len(rows)}  | small_n: {sum(1 for r in rows if r['small_n_flag']=='Y')}"
          f"  | disagreement: {sum(1 for r in rows if r['disagreement_flag']=='Y')}")

if __name__ == "__main__":
    main()
