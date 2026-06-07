# BrightWave Request 1 — Operator unit economics & path to EBITDA

> Self-contained brief. Paste as its own BrightWave run.

## Context
A strategic consolidator in the sector, pursuing tuck-in acquisitions of contracted U.S. K-12
student-transportation (school bus) operators, values targets **bottom-up from a known bus count**.
Our only verified per-operator anchor is the **FMCSA Company Census fleet count** (total power units,
and school buses by capacity class: ≤8, 9–15, 16+ seats). We need defensible **ranges** to convert
buses → revenue → EBITDA, by sub-sector and operator scale, that **reconcile to that bus anchor**.

## Source-quality & output rules (apply to every metric)
- Prioritize **PRIMARY / proprietary / paywalled** evidence: SEC EDGAR & LSE/RNS filings, earnings-call
  and **expert-network** transcripts (Tegus/AlphaSense, GLG, Guidepoint, Third Bridge, AlphaSights),
  **sell-side** research (e.g., UBS/Numis/Peel Hunt on Mobico & FirstGroup), federal/state regulatory &
  DOE disclosures, and **trade-association** surveys (NSTA, NAPT, School Bus Fleet, School Transportation News).
- Do **NOT** use commodity aggregators (S&P Capital IQ, PitchBook, IBISWorld) as primary evidence — only
  as an explicitly-labeled cross-check, if at all.
- For **every** metric return: (1) clear definition, (2) value or **RANGE**, (3) time period, (4) geographic
  + sub-sector scope, (5) citation to the underlying **primary** source with **sentence-level attribution**.
- **NATIONAL FALLBACK:** if a metric will not resolve to a specific state, return the **national** figure
  labeled `national` and note the state-disclosure gap — **never drop a metric** for lack of state granularity.
- Distinguish audited/filed figures vs survey/sentiment vs estimate; flag confidence.
- Sub-sectors throughout: **(Y)** home-to-school yellow-bus, **(S)** special-needs/SPED, **(C)** charter/motorcoach.
- We already hold verified FMCSA fleet counts; we do **not** want commodity revenue estimates (e.g., Data Axle).
- Regional priority where state detail exists: **FL, NY, PA, MO, GA, IN, UT** (else `national`).
- **RECENCY:** weight and flag the most recent **3–5 years**; explicitly note where **pre-2020** unit
  economics may not reflect current driver-cost / wage structure — never present a pre-2020 figure as
  applicable to a 2026 target without that caveat.
- **SCALE FOCUS:** most of our targets are **<50 buses**. The filed calibration operators are all large
  platforms, so press hardest on the **<50-bus tier**, where filings give the least coverage (see §C).

## Anchor sources to mine first (the only audited operator disclosures that exist)
- **Student Transportation Inc. (STI/STA, ticker STB)** — SEC EDGAR 40-F/6-K, FY2008–2018 (NA pure-play).
- **Mobico Group / National Express — North American School Bus segment** — Annual Reports FY2007–FY2024
  (Durham / Petermann / Stock): segment revenue, margin, fleet, contract retention.
- **FirstGroup plc — First Student segment** — Annual Reports through FY ending March 2021.
- Historical pure-plays: **Atlantic Express** (10-K to ~2008), **Laidlaw** (SEC EDGAR).
- Expert-network transcripts & sell-side notes on the above for unit-economic color.
- Public cost-input context (triangulation only): BLS OEWS SOC 53-3051 (driver wage by state), BLS ECI/CPI,
  EIA on-highway diesel; NSTA Cost Analysis framework; School Bus Fleet Maintenance & Contractor surveys.

## Deliverables (ranges + primary citations; segment by sub-sector Y/S/C and by scale tier <50 / 50–250 / 250+ buses)

### A. Revenue per unit — reported THREE ways against our bus anchor
Because our anchor is the FMCSA count, every revenue-per-bus figure must state its denominator. Provide:
1. **Revenue per total power unit** (revenue ÷ entire registered fleet, incl. spares) — matches FMCSA total.
2. **Revenue per active/route bus** (revenue ÷ buses in daily revenue service).
3. **Revenue per bus by capacity class** — separately for **≤8**, **9–15**, and **16+ seat** buses
   (mapping to FMCSA `ownschool_1_8 / 9_15 / 16`), since small/SPED vehicles and full-size buses earn very differently.
Also provide revenue per route, per rider/student, and per bus-day with explicit definitions.

### B. Utilization / spare ratio (the conversion factor)
The typical **active route buses ÷ total fleet** ratio (i.e., spare/reserve ratio) for contracted operators,
by sub-sector and scale — so we can convert our FMCSA **total** counts into **revenue-earning** buses.

### C. Ground-truth calibration set (compute from filings — do not estimate)
For **STI, Mobico NA School Bus, and First Student**, compute **implied revenue-per-bus = filed segment
revenue ÷ disclosed fleet count**, for **each fiscal year** both are disclosed. Present the per-year series with
the exact source figures, the division shown, currency/FX basis, and citations. This is the **calibration /
back-test set** our modeled ranges must reconcile against; flag where "fleet" definition differs (buses vs power units).

**Scale caveat (critical):** this filed calibration set is **large-scale platforms only**, but most of our
targets are **<50 buses**. Filings give the least coverage there — so **press hardest on the <50-bus tier**
using expert-network transcripts, smaller-operator/owner interviews, trade & association sources, and posted
small-district contracts; report explicitly **how small-operator unit economics diverge from the large-platform
calibration**. **Recency:** within all of the above, weight the most recent **3–5 years** and flag that
**pre-2020** figures may not reflect current driver-cost / wage structure.

### D. Cost structure — as % of revenue AND per-bus
Fully-loaded driver labor; fuel (incl. typical **gallons/bus/year**); maintenance $/bus/yr; insurance
(auto-liability + workers-comp, split); facilities/depot; G&A.

### E. Margin
Operating-margin and EBITDA-margin **ranges by scale tier and sub-sector**, and how margin scales with fleet size.

### F. Capital
Bus replacement cycle / average fleet age; capex per bus (maintenance vs growth); lease-vs-own mix and
operating-lease cost per bus.

### G. Driver workforce (current #1 value-and-risk lever — required)
- **Turnover / retention rate** of school-bus drivers (annual), by region (`national` fallback).
- **Wage trajectory** — recent multi-year driver wage growth / inflation.
- **Guaranteed-hours norms** (minimum daily/weekly paid hours) and **benefit norms** (health, pension/retirement, paid training/CDL sponsorship).
- **Driver availability → route-fulfillment**: typical % of routes covered vs uncovered during shortages, and how
  driver scarcity translates into **contract-penalty / liquidated-damages risk** and re-bid exposure.

### H. Sub-sector deltas
**SPED:** revenue premium and added cost (aide/monitor coverage ratio; wheelchair-lift / Type-A vehicle mix).
**Charter/motorcoach:** utilization (miles/coach, passenger-miles) and seasonality vs contracted yellow-bus.

## Output format
A metrics table: `metric | definition | range | period | geo (national/state) | sub-sector | scale tier | primary source (sentence-level cite)`, plus the calibration set in Section C shown as an explicit per-year, per-company computation.

## Machine-readable summary (for ingest — include in addition to the narrative)
End with a **flat table, one row per metric**, columns exactly:
`metric | sub_sector | scale_tier | geo | low | point | high | period | primary_source_cite`
so results drop straight into our database without re-keying. Conventions: `geo` = state code or `national`
(per the fallback rule); `sub_sector` ∈ {Y,S,C,all}; `scale_tier` ∈ {<50,50-250,250+,all}; leave `point`
blank if only a range exists; emit **one row per (metric × sub_sector × scale_tier × geo)** combination.
