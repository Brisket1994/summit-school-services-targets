# market_overlay.csv — provenance & method (W5)

*Canonical benchmark overlay for the W5 re-score. Synthesized **by us** from primary sources, per the
W5 rule: BrightWave/vendor conclusions are NOT authoritative — we form the ranges. Generated
deterministically by `4_pipeline/_synthesize_market_overlay.py` (the documented derivation; each row's
numbers + citation are explicit literals there). The CSV is the source of truth; `_w5_overlay.py` loads
it into the `market_overlay` DB table.*

## Why this exists / what changed vs the original W5 plan
The original W5 waited on a BrightWave research drop into `7_research_requests/*/results/` that never
arrived (all empty). The underlying research was found **already on disk** in the broader MASTER tree,
plus Summit's own proprietary bid/deal data — which is better-calibrated than external research for the
core unit-economics and valuation benchmarks. This overlay is synthesized from those two corpora,
labeled by `source_basis`.

## Source basis taxonomy (`source_basis` column)
| value | meaning | verification |
|---|---|---|
| `summit_internal_bid` | Summit's own bid pricing models (HSD214/Alton/CCC/Fresno teardowns) | self-verifying primary — OUR underwriting; cite teardown + value |
| `summit_internal_deal` | Summit live/pipeline deals (Evergreen, Brabe, North, Solaris, +pipeline) | pipeline-indicative — target representations; cite Notes/summary |
| `external_filing` | SEC/RNS/regulatory filings (Mobico, FirstGroup, STI) | primary; cite filing + (where available) URL |
| `external_precedent` | disclosed precedents / trade datasets (Beacon, School Bus Fleet survey, rules-of-thumb) | corroborated secondary; many `unverifiable` pending source re-fetch |
| `dataroom_evidence` | a primary doc surfaced in the `02_Corp_Dev_Research` data room (e.g. NY ZEB mandate) | cite the underlying doc, not the extraction CSV |
| `dataroom_synthesis` | a synthesized internal memo (BCG-derived market math, state ordinals) | context, not an anchor |
| `mixed` | range spans >1 basis (the common case for valuation/margin) | needs ≥1 verified citation |

## Verification convention
- `verified` — figure appears verbatim in a named Summit teardown/note (internal), OR at a stated
  locator in a cited primary filing/doc. Internal bid/deal numbers are self-verifying primary.
- `unverifiable` — carried for context/range-widening but NOT used to anchor a score (trade survey
  margins, practitioner rules-of-thumb, BCG-vintage TAM, national EV baseline). Kept, flagged.
- Only `verified` rows are joined as anchors by `_w5_overlay.py` (the lookup filters on it).

## Honesty flags
- **`small_n_flag`** = Y when fewer than 5 distinct observations (33/37 rows — the internal corpus is
  4 bids + ~12 deals/pipeline operators). The scorer should down-weight small-n.
- **`disagreement_flag`** (8 rows) — kept, never collapsed. The load-bearing ones:
  - **EBITDA margin is THREE separate metrics**, not one averaged range, because the definitions differ:
    - `ebitda_margin` (operator/pipeline adjusted): **15.4–34%** — the basis used to drive implied EBITDA.
    - `ebitda_margin_yr1_bid_post_oh` (Summit bid underwriting, post-5%-OH): **14.9–26.7%** — context only.
    - `ebitda_margin_reported_survey` (School Bus Fleet trade survey, net of corporate OH): **5.5–7.3%** — context only.
  - **Platform EBITDA margin** ~$122M adj (Mobico FY24) vs ~$153M post-corporate (Scarlet IM) → 11% vs 14%.
  - **EV/bus** varies strongly with margin/mix (Scarlet platform ~$43K/bus at 5× on ~11% margin vs
    high-margin tuck-ins $78–130K) → EV/EBITDA is the cleaner anchor; EV/bus is a cross-check only.
- **Template constant**: `overhead_pct_revenue` = 5.0% is ONE bid-template assumption, not 4 observations.
- **Geographic narrowness**: internal observations are CA/CT/NY/IL; internal rows are written at
  `geo=national` only — never assigned to a specific state we have no deal in. State rows come from the data room.

## What each overlay factor consumes (`overlay_factor_hook`)
- **valuation_attractiveness** ← `ev_ebitda_multiple` (tuck-in/platform), `entry_multiple_tuckin`, `ev_per_bus`
- **size_margin_signal** ← `revenue_per_bus_per_year`, `ebitda_margin`
- **driver_market_risk** ← `driver_turnover_pct_annual` (national only)
- **outsourcing_ev_mandate** ← `outsourcing_acceptance` (7 states), `ev_mandate_stringency` (NY/CA/PA + national)
- **none** (context / implied-valuation inputs / narrative) ← overhead, driver-labor, startup, capex,
  escalator, spare ratio, build_multiple_target, survey/bid margins, EV/revenue, TAM, contribution margin
- The **implied-valuation layer** uses: `revenue_per_bus_per_year` → implied revenue; `ebitda_margin` →
  implied EBITDA; `entry_multiple_tuckin` → implied EV at entry; `ev_per_bus` → EV cross-check;
  `build_multiple_target` (8×) → build EV and value-creation spread.

## Scale-tier adapter (brief-03 `{platform, tuck-in, all}` → `{<50, 50-250, 250+}`)
Valuation multiples are observed on a platform/tuck-in axis. `_w5_overlay.py` maps a target's derived
tier in its lookup ladder: `<50`→`tuck-in`, `50-250`→`tuck-in`, `250+`→`platform`, with `all` as the
final fallback. (Handled in the consumer's lookup, so the CSV stays one-row-per-observation.)

## Deferred (carried as `unverifiable` / national, NOT fabricated)
- **Brief 01 §C calibration** — implied rev/bus from MCG/STI/First Student segment revenue ÷ fleet
  needs PDF parsing of the Lane-15 10-Ks (outside the repo's stdlib-only rule). The *multiples* from
  those filings are usable today (cited above); the rev/bus computation is deferred.
- **Per-state driver turnover & contracted-share rates** — not cleanly extractable at primary+High in
  `evidence_facts.csv` (the numbers live inside source PDFs). Driver turnover carried as a national
  signal; per-state is deferred. `outsourcing_acceptance` carried as cited ordinals, not numeric shares.
- **Per-state reimbursement formulas** — carried as categorical context where the data room supports;
  numeric rates deferred.

## Primary source files (full paths)
- Bid teardowns: `Summit Pricing Models/_Teardowns/` (HSD 214 reference; Cross-Deal Synthesis)
- Live deals: `Deal_and_Person_Notes_V1.md` (§4 dossiers, §8 methodology); `Summit Deals/Project Evergreen/Project_Evergreen_JFK_Transportation_Summary_V4.md`
- Precedent multiples: `02_Corp_Dev_Research/Summit Research/06_Valuation-and-Transaction-Multiples/CLAUDE.md` (Shared-constants table, w/ primary-source URLs)
- State posture / market math: `02_Corp_Dev_Research/Research Database Work/Onboarding Day Materials/Analysis Outputs/Onboarding_Market_Strategy_Memo.md`
- Evidence ledger (53,357 rows): `02_Corp_Dev_Research/Research Database Work/Onboarding Day Materials/Analysis Outputs/BrightWave_Document_Evidence_Extraction_20260609_101459/evidence_facts/evidence_facts.csv`
- Calibration filings (deferred): `02_Corp_Dev_Research/BrightWave Downloads/15_Summit-and-I-Squared/primary_documents/pdfs/` (MCG/STI 10-Ks)

## Refresh
`python3 4_pipeline/_synthesize_market_overlay.py` regenerates `market_overlay.csv` deterministically.
Edit the row literals in that script to add/adjust benchmarks (e.g., once the deferred calibration or
per-state rates are extracted), then re-run `_w5_overlay.py`.
