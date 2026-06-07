# BrightWave Request 2 — Contract & reimbursement economics by state

> Self-contained brief. Paste as its own BrightWave run.

## Context
A strategic consolidator in the sector, pursuing tuck-in acquisitions of contracted U.S. K-12
student-transportation operators, needs an **independent revenue cross-check**: from the districts /
municipalities a target serves, bound its revenue via **contract-value economics**. Contract structures,
escalators, reimbursement, and driver-driven contract risk vary by **state** and **sub-sector**.
Priority states: **FL, NY, PA, MO, GA, IN, UT.**

## Source-quality & output rules (apply to every metric)

> **We form the final conclusions ourselves** by synthesizing the sources you surface. Your job is (a) **maximal
> discovery** of credible primary sources and (b) **faithful, verbatim extraction** of every relevant figure with a
> precise, locatable citation — **NOT** resolving the evidence into your own final number. Where sources are thin,
> vary, or conflict, **surface all of them and flag the conflict**; never collapse them into one synthesized value.

- Prioritize **PRIMARY / proprietary / paywalled** evidence: SEC EDGAR & LSE/RNS filings, earnings-call and
  **expert-network** transcripts (Tegus/AlphaSense, GLG, Guidepoint, Third Bridge), **sell-side** research,
  **federal/state regulatory & DOE** disclosures, and **trade-association** surveys (NSTA, NAPT, NASDPTS,
  state contractor associations).
- Do **NOT** use commodity aggregators (S&P Capital IQ, PitchBook, IBISWorld) as primary evidence — only as an
  explicitly-labeled cross-check, if at all.
- For **every figure**, extract it **as the source states it** (verbatim value + unit) and give a **precise,
  locatable citation**: document **title**, **date**, **page / section / table**, and the **exact quoted passage** —
  so we can pull and re-read the source ourselves. Do **not** convert, normalize, round, or synthesize values.
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

## Deliverables (report each figure **as stated per source**, with full locator citations — we form the ranges; PER STATE, and by sub-sector where it differs)

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
Present **per-state narrative**, reporting **each source's figure as stated** (not a synthesized number); flag
clearly where only the **structure** (not dollar values) is publicly disclosed, and apply the national fallback
otherwise. Then the **Evidence ledger** below.

## Evidence ledger (required output format — machine-readable)
Return a flat table with **one row per (data point × source)** — *not* per synthesized range — reporting each
figure **exactly as that source states it**. Columns:
`metric | sub_sector | scale_tier | geo | value_as_stated | period | source_title | source_date | locator | quoted_passage | source_confidence`
- **One row per source**: if three sources speak to a state's per-pupil spend, that's three rows — *we* aggregate.
- `value_as_stated` = verbatim in the source's own units/wording (do not convert or round).
- `locator` = page / section / table / portal query (or URL anchor) precise enough to re-find it.
- `quoted_passage` = the exact sentence(s) the figure is drawn from.
- `source_confidence` = your read of reliability (DOE filing/awarded contract > survey > estimate) + one-line basis.
- Conventions: `geo` = state code (FL/NY/PA/MO/GA/IN/UT) or `national`; `sub_sector` ∈ {Y,S,C,all}; `scale_tier` = `all` unless scale-specific.
- If you want to offer your **own** synthesized view, put it in a **separate, clearly-labeled** section
  ("BrightWave synthesized view — not authoritative"); never merge it into the ledger.
