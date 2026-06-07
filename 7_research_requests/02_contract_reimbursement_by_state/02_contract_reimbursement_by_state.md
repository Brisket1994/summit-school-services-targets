# BrightWave Request 2 — Contract & reimbursement economics by state

> Self-contained brief. Paste as its own BrightWave run.

## Context
A strategic consolidator in the sector, pursuing tuck-in acquisitions of contracted U.S. K-12
student-transportation operators, needs an **independent revenue cross-check**: from the districts /
municipalities a target serves, bound its revenue via **contract-value economics**. Contract structures,
escalators, reimbursement, and driver-driven contract risk vary by **state** and **sub-sector**.
Priority states: **FL, NY, PA, MO, GA, IN, UT.**

## Source-quality & output rules (apply to every metric)
- Prioritize **PRIMARY / proprietary / paywalled** evidence: SEC EDGAR & LSE/RNS filings, earnings-call and
  **expert-network** transcripts (Tegus/AlphaSense, GLG, Guidepoint, Third Bridge), **sell-side** research,
  **federal/state regulatory & DOE** disclosures, and **trade-association** surveys (NSTA, NAPT, NASDPTS,
  state contractor associations).
- Do **NOT** use commodity aggregators (S&P Capital IQ, PitchBook, IBISWorld) as primary evidence — only as an
  explicitly-labeled cross-check, if at all.
- For **every** metric return: (1) clear definition, (2) value or **RANGE**, (3) time period, (4) geographic +
  sub-sector scope, (5) citation to the underlying **primary** source with **sentence-level attribution**.
- **NATIONAL FALLBACK:** if a metric will not resolve to a specific state, return the **national** figure
  labeled `national` and note the state-disclosure gap — **never drop a metric** for lack of state granularity.
- Distinguish audited/filed vs survey/sentiment vs estimate; flag confidence.
- Sub-sectors: **(Y)** yellow-bus, **(S)** special-needs/SPED, **(C)** charter/motorcoach.
- We already hold verified FMCSA fleet counts; we do **not** want commodity revenue estimates (e.g., Data Axle).

## Anchor sources to mine first (per state)
- **FL** — FEFP transportation categorical + FLDOE transportation reporting / transparency cost reports + district bid lists (DemandStar).
- **NY** — NYSED Transportation Aid + ST-3 annual financial report + **NYSED-posted RFP-awarded transportation contracts**.
- **PA** — PDE formula (Title 22 Ch. 23) + subsidy payment schedule + Annual Financial Report data + PA eMarketplace.
- **MO** — DESE transportation funding formula + Annual Secretary of the Board Report (ASBR).
- **GA** — QBE reports + GOSA per-pupil expenditure + Georgia Procurement Registry (DOAS).
- **IN** — IDOE INview / Digest of Public School Finance + Indiana Gateway.
- **UT** — USBE Pupil Transportation (Rule R277-600) + Transparent Utah + USBE purchasing/contracts.
- Cross-state: **NCES NPEFS & Census F-33** (district/state transportation expenditure & spend-per-pupil);
  **NSTA / state contractor associations** (NYSBCA, PSBA) for contracting-structure norms; posted district RFPs/awarded contracts for actual pricing.

## Deliverables (ranges + primary citations; PER STATE, and by sub-sector where it differs)

### A. Reimbursement structure
Funding-formula **type** per state (per-rider / per-mile / per-route / %-of-cost reimbursement / block grant /
hybrid) and how it shapes what a contractor can charge.

### B. Contract pricing
Prevailing **pricing structure(s)** — per-bus, per-route, per-student, per-aide — and typical **contract values /
unit rates** from awarded contracts and RFPs.

### C. Contract terms
Typical **term length**, renewal/extension rights, **retention / re-bid** norms, annual **escalator** basis
(CPI / fuel index), and **fuel pass-through** prevalence.

### D. District spend (independent revenue cross-check)
Transportation **expenditure per pupil / per enrolled rider** by state (and district range), to bound revenue
from the districts a target serves.
**Critical — isolate the contractor's slice:** many districts run a **hybrid in-house + contracted** model, so
distinguish **contracted-out** transportation spend (paid to private operators) from **total** district
transportation expenditure. Report **both**, plus the **contracted share %** where disclosed, so we bound the
*contractor's* revenue — not the district's whole transportation budget.

### E. Driver workforce → contract risk (required)
- Regional **driver wage scale** as embedded in/assumed by contracts; **turnover / retention** rates.
- **Guaranteed-hours** and **benefit** norms reflected in contract pricing.
- **Wage trajectory** (recent driver wage growth) and its effect on re-bid pricing.
- How **driver availability / scarcity** drives **route-fulfillment** rates and exposure to
  **contract penalties / liquidated damages / non-performance** clauses — by state (`national` fallback).

### F. SPED contract economics
Incremental contract economics for special-needs routes — **aide billing**, per-student premiums, specialized-
vehicle requirements — by state.

## Output format
Per-state tables: `metric | definition | range | period | sub-sector | primary source (sentence-level cite)`.
Flag clearly where only the **structure** (not dollar values) is publicly disclosed, and apply the national fallback otherwise.

## Machine-readable summary (for ingest — include in addition to the narrative)
End with a **flat table, one row per metric**, columns exactly:
`metric | sub_sector | scale_tier | geo | low | point | high | period | primary_source_cite`
so results drop straight into our database without re-keying. Conventions: `geo` = state code (FL/NY/PA/MO/GA/IN/UT)
or `national` (per the fallback rule); `sub_sector` ∈ {Y,S,C,all}; `scale_tier` = `all` unless a metric is scale-specific;
leave `point` blank if only a range exists; emit **one row per (metric × sub_sector × geo)** combination.
