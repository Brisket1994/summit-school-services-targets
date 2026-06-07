# BrightWave Request 3 — Synergies, scale economics & precedent valuation

> Self-contained brief. Paste as its own BrightWave run.

## Context
A **strategic consolidator in the sector** is acquiring contracted U.S. K-12 student-transportation operators
as tuck-ins into an existing multi-yard platform. We compute route/depot **overlap** with our footprint
in-house; we need the **benchmarks that convert scale & overlap into dollars**, plus **precedent valuation
multiples**. We hold verified per-target **FMCSA bus counts**, so an **EV-per-bus** range is our most direct,
highest-priority valuation cross-check.

## Source-quality & output rules (apply to every metric)

> **We form the final conclusions ourselves** by synthesizing the sources you surface. Your job is (a) **maximal
> discovery** of credible primary sources and (b) **faithful, verbatim extraction** of every relevant figure with a
> precise, locatable citation — **NOT** resolving the evidence into your own final number. Where sources are thin,
> vary, or conflict, **surface all of them and flag the conflict**; never collapse them into one synthesized value.

- Prioritize **PRIMARY / proprietary / paywalled** evidence: SEC EDGAR & LSE/RNS filings and deal circulars,
  earnings-call and **expert-network** transcripts (Tegus/AlphaSense, GLG, Guidepoint, Third Bridge),
  **sell-side** research, law-firm transaction announcements, and **S&P Global Ratings** credit reports.
- Do **NOT** use commodity aggregators (S&P Capital IQ, PitchBook, IBISWorld, Mergermarket) as primary evidence
  — only as an explicitly-labeled cross-check, if at all.
- For **every figure**, extract it **as the source states it** (verbatim value + unit) and give a **precise,
  locatable citation**: document **title**, **date**, **page / section / table**, and the **exact quoted passage** —
  so we can pull and re-read the source ourselves. Do **not** convert, normalize, round, or synthesize values.
- **NATIONAL FALLBACK:** if a metric will not resolve to a specific state/region, return the **national** figure
  labeled `national` and note the gap — **never drop a metric** for lack of granularity.
- Distinguish audited/filed vs survey/sentiment vs estimate; flag confidence.
- Sub-sectors: **(Y)** yellow-bus, **(S)** special-needs/SPED, **(C)** charter/motorcoach.
- Keep the requester generic ("a strategic consolidator"); do not infer or name the requester.

## Anchor sources to mine first
- **Deal disclosures (named public precedents):**
  - **Mobico Group's sale of its North American School Bus business to I Squared Capital** — RNS/circular:
    extract enterprise value, EV/EBITDA, EV/Revenue, **implied EV per bus**, and stated rationale. (Treat as a
    named public precedent; do not infer or name the requester's identity from this precedent.)
  - **Student Transportation Inc. take-private (2018)** — circular/proxy/Form 6-K.
  - **FirstGroup "Proposed Sale of First Student & First Transit"** documentation.
  - **Beacon Mobility / Audax** and other contractor tuck-ins (law-firm announcements e.g. Foley & Lardner; trade press STN / School Bus Fleet).
- Expert-network transcripts & sell-side on **integration economics, procurement leverage, insurance/benefits pooling** in multi-yard school-bus platforms.
- **S&P Global Ratings** reports on Student Transportation Inc. for capital-structure/leverage context.

## Deliverables (report each figure **as stated per source/deal**, with full locator citations — we form the ranges)

### A. EV per bus — PRIORITY OUTPUT
Implied **EV per bus** for student-transportation transactions (and per the named precedents above). State the
bus denominator used (total fleet vs revenue-earning), the deal date/size, sub-sector mix, and **distinguish
platform vs tuck-in** EV/bus and any **scale / sub-sector** pattern. This is our primary valuation cross-check
against our FMCSA counts — make it as granular and well-cited as the evidence allows.

### B. Precedent multiples
**EV/EBITDA** and **EV/Revenue** for student-transportation deals (name deal, date, size, multiple, source);
distinguish platform vs tuck-in and note any scale/sub-sector pattern.

### C. Procurement scale curves
Typical price advantage on **bus OEM purchases, fuel, insurance, and parts** as a function of fleet size
(small independent vs large platform) — expressed as % savings or $/bus.

### D. Consolidation savings
**Back-office / management G&A reduction %**, **insurance & benefits pooling** savings, and maintenance/facility
consolidation — expressed as % of acquired revenue or per-bus.

### E. Overlap-to-savings
Benchmarks for what route/depot **density overlap** converts to in cost savings, so we can apply our
in-house-computed overlap per target.

## Output format
A **precedents table** with **one row per deal** (`deal | date | size | EV/bus | EV/EBITDA | EV/Revenue | sub-sector
| primary source`), **EV/bus first**, each figure **as disclosed** (no synthesized cross-deal average), plus a
**synergy-bridge table** reporting each lever **as stated per source**. Then the **Evidence ledger** below.

## Evidence ledger (required output format — machine-readable)
Return a flat table with **one row per (data point × source)** — *not* per synthesized range — reporting each
figure **exactly as that source states it**. Columns:
`metric | sub_sector | scale_tier | geo | value_as_stated | period | source_title | source_date | locator | quoted_passage | source_confidence`
- **One row per source/deal**: each precedent and each synergy-lever benchmark is its own row — *we* aggregate.
- For precedents, `metric` = `EV/bus` / `EV/EBITDA` / `EV/Revenue`; name the deal in `source_title` and the
  filing/circular in `locator` + `quoted_passage`.
- `value_as_stated` = verbatim (do not convert or round); `geo` = `national` unless deal-specific.
- `scale_tier` ∈ {platform, tuck-in, all}; `source_confidence` = reliability read (filing/circular > press > estimate) + basis.
- If you want to offer your **own** synthesized view, put it in a **separate, clearly-labeled** section
  ("BrightWave synthesized view — not authoritative"); never merge it into the ledger.
