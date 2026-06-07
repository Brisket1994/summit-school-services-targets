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

Each brief ends with a **machine-readable summary table** (`metric \| sub_sector \| scale_tier \| geo \| low \| point \| high \| period \| primary_source_cite`) so returned results ingest into the DB as the overlay re-score without re-keying.

**Design choice:** segmented by **theme** (not sub-sector) — each maps to one coherent source-set;
sub-sector deltas (yellow / SPED / charter) are captured *within* each. Requester identity kept generic
("a strategic consolidator").

**Next:** run each brief in BrightWave; drop the returned report into that brief's `results/` folder and any
downloaded primary-source files into its `sources/` folder, then ingest the machine-readable summary tables
into the DB as the market-data overlay re-score.
