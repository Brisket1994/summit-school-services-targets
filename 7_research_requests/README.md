# 7_research_requests/ — external-data briefs for BrightWave

Three **self-contained** research briefs (shared source-quality standard inlined in each, so each is
ready to paste as its own BrightWave run). They cover only the **external gaps** in our valuation
build-up — the operator unit economics, cost/margin, contract economics, synergies, and precedents we
can't derive from owned/free data. (Owned anchors: FMCSA fleet, web recon; free/derivable: NCES/Census
spend, BLS wages, EIA diesel — not requested here.)

**Layout — one subfolder per brief:**
```
7_research_requests/
├── README.md
├── 01_operator_unit_economics/
│   ├── 01_operator_unit_economics.md   ← the brief (paste into BrightWave)
│   ├── results/                         ← BrightWave's returned report (committed)
│   └── sources/                         ← raw primary-source downloads (LOCAL/gitignored)
├── 02_contract_reimbursement_by_state/  (same layout)
└── 03_synergies_precedent_valuation/    (same layout)
```
`sources/` contents are gitignored (raw, possibly large/paywalled downloads stay local, like the DB &
Data Axle source); the empty folder persists via `.gitkeep`. Briefs and `results/` are committed.

| Subfolder / brief | Mandate | Key outputs |
|---|---|---|
| `01_operator_unit_economics/` | Buses → revenue → EBITDA | rev/bus three ways (total PU / active / capacity class), spare-ratio conversion, **filings-derived calibration set** (STI, Mobico NA, First Student) with **<50-bus tier pressed hardest** + recency weighting, cost ratios, margins by scale, driver-workforce risk |
| `02_contract_reimbursement_by_state/` | Independent revenue cross-check via contracts | per-state reimbursement structure, contract pricing/terms/escalators, **contracted-vs-total** district spend/pupil, driver→contract-penalty risk (FL,NY,PA,MO,GA,IN,UT) |
| `03_synergies_precedent_valuation/` | Tuck-in value | **EV/bus (priority)**, EV/EBITDA & EV/Revenue precedents (incl. Mobico→I Squared sale), procurement curves, consolidation & overlap savings |

**Division of labor:** BrightWave does **source discovery + faithful, verbatim extraction** (with locatable
citations) — **we** synthesize the final view. So each brief ends with an **Evidence ledger** —
**one row per (data point × source)**, each figure reported *as stated* (`metric \| sub_sector \| scale_tier \| geo
\| value_as_stated \| period \| source_title \| source_date \| locator \| quoted_passage \| source_confidence`) — not a
pre-synthesized range. We aggregate the ledger into ranges ourselves at ingest.

**Design choice:** segmented by **theme** (not sub-sector) — each maps to one coherent source-set;
sub-sector deltas (yellow / SPED / charter) are captured *within* each. Requester identity kept generic
("a strategic consolidator").

## Status — W5 completed from internal + data-room sources (these briefs were NOT run in BrightWave)

The BrightWave research drop never landed (all `results/` and `sources/` are still empty `.gitkeep`).
W5 was instead completed (2026-06-17) by synthesizing the SAME underlying evidence **already on disk**
in the broader MASTER tree, plus Summit's own proprietary data — which is better-calibrated than
external research for the core unit-economics and valuation benchmarks. The briefs remain valid and
un-run; they can still be executed later to deepen/replace specific rows.

**Where the W5 inputs actually came from** (synthesized by us, every figure cited — see
`../5_working/inputs/market_overlay_SOURCES.md`):
- **Brief 01 (unit economics)** ← Summit bid teardowns (`Summit Pricing Models/_Teardowns/`) + live-deal
  margins (`Deal_and_Person_Notes_V1.md`). Calibration 10-Ks (STI/Mobico, in the data room Lane 15)
  carried but the rev/bus computation is **deferred** (needs PDF parsing, outside stdlib).
- **Brief 02 (contract/reimbursement)** ← data-room state docs + `Onboarding_Market_Strategy_Memo.md`
  (carried as cited categorical ordinals — outsourcing acceptance, EV-mandate stringency; per-state
  numeric rates **deferred**, not cleanly extractable at primary+High).
- **Brief 03 (synergies/precedent valuation)** ← live-deal precedents + the verified precedent-multiple
  table in `02_Corp_Dev_Research/Summit Research/06_Valuation-and-Transaction-Multiples/CLAUDE.md`.

**The mechanism that consumed them** (as designed): synthesized ranges →
`5_working/inputs/market_overlay.csv` (keyed `sub_sector × scale_tier × geo`) → loaded into a
`market_overlay` DB table by **`4_pipeline/_w5_overlay.py`** (NEW; `_w4_score.py` untouched) → additive
overlay + per-target implied valuation → `3_deliverables/master_targets_ranked_overlay.csv`.

**To run a brief later** (to replace the deferred/ordinal rows with primary extraction): drop the
returned report into that brief's `results/` and primary files into `sources/`, verify each figure, then
add/adjust the corresponding rows in `4_pipeline/_synthesize_market_overlay.py` and re-run
`_synthesize_market_overlay.py && _w5_overlay.py`. See `../NEXT_SESSION_PROMPT.md`.
