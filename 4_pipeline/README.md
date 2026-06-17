# 4_pipeline/ — script index

All scripts **self-anchor to the project root** (`os.chdir` to the parent of `4_pipeline/`), so run them from
the project folder as `python3 4_pipeline/<script>.py` (any CWD works). Paths inside reference the typed
subfolders (`2_database/`, `5_working/inputs/`, `5_working/batch_outputs/`, `3_deliverables/`, `1_source_data/`).

## Historical build steps — re-run only intentionally (some are destructive)
| # | Script | Does | Note |
|--:|---|---|---|
| 1 | `_build_db.py` | master xlsx → `companies` table | **DROPs/rebuilds the DB** |
| 2 | `_consolidate.py` | `companies` → `targets` + `entities` | **DROPs `entities` incl. `verdict`** — re-merge W2 after |
| 3 | `_profile_hierarchy.py` | read-only hierarchy diagnostic on `companies` | safe anytime |
| 4 | `_score.py` | `entities` → `_intermediate/*` (pre-W3 rule score) | **superseded by `_w4_score.py`** |
| 5 | `_pull_census.py` | FMCSA SODA API → `census_bus` (117k rows) | network + minutes; refresh only |
| 6 | `_census_match.py` | `census_bus` + enrich input → `fmcsa_census` | DROPs/recreates; deterministic local |

## Current operational steps — idempotent, re-runnable on demand
| # | Script | Does |
|--:|---|---|
| 7 | `_merge_enrich.py` | `5_working/batch_outputs/_enrich_out_*.jsonl` → `enrichment`; refresh `_enrich_remaining.json` |
| 8 | `_merge_fmcsa.py` | `_fmcsa_out_*.jsonl` (incl. `_fb_`) → `fmcsa`; refresh `_fmcsa_remaining.json` |
| 9 | `_build_fallback.py` | `enrichment`+`fmcsa_census`+`fmcsa` → `5_working/inputs/_fmcsa_fallback.json` |
| 10 | `_diagnostic.py` | read-only profile of `enrichment` → `_intermediate/targets_independent_enriched.csv` |
| 11 | `_w4_score.py` | join sources → `master_targets_ranked.csv`, `_profiles.jsonl`, `_A_top50.md` **(the scorer)** |
| 12 | `_export_full.py` | join + raw census → `master_targets_FULL.csv` (91 cols) |
| 13 | `_build_master_view.py` | `master_targets_FULL.csv` → `master_targets` DB table (+indexes) |
| 14 | `_build_status.py` | `master_targets` → `master_targets.jsonl` + `alist_queue.jsonl` + `targets_status.csv` (idempotent; preserves progress) |
| 15 | `_next_batch.py [N]` | next N un-researched A-list → `5_working/inputs/_night_batch.json` |
| 16 | `_status.py` | read-only DB snapshot + counts |
| 17 | `_synthesize_market_overlay.py` | (W5) emit `5_working/inputs/market_overlay.csv` — the cited benchmark ranges, synthesized from internal bid/deal data + the data room. Documented derivation; deterministic. Edit its row literals to refresh benchmarks. |
| 18 | `_w5_overlay.py` | (W5) `master_targets` + `market_overlay.csv` → `master_targets_ranked_overlay.csv` + `master_targets_overlay_A_top50.md` + `5_working/diagnostics/` (reconciliation + skipped-factor log). **Additive overlay on top of the untouched W4 baseline + per-target implied valuation.** |

## Re-score chains

**W4 re-score (Case A — needs the gitignored `enrichment`/`fmcsa`/`fmcsa_census` tables):**
```
python3 4_pipeline/_w4_score.py          # re-score from DB
python3 4_pipeline/_export_full.py       # → master_targets_FULL.csv
python3 4_pipeline/_build_master_view.py # → master_targets table
python3 4_pipeline/_build_status.py      # → jsonl/queue/status
```

**W5 overlay (the implemented design — a SEPARATE additive script; `_w4_score.py` is NOT edited):**
```
# Case B (fresh clone: DB absent, master_targets_FULL.csv present) — the common case:
python3 4_pipeline/_build_master_view.py           # rebuild master_targets from the committed CSV
python3 4_pipeline/_synthesize_market_overlay.py   # (only if market_overlay.csv changed)
python3 4_pipeline/_w5_overlay.py                  # → overlay deliverables + diagnostics
```
The W5 overlay reads `master_targets` only (no enrichment/fmcsa tables), so it runs in Case B. It loads
`market_overlay.csv` into a `market_overlay` DB table itself. The W4 baseline (`composite`, `a_rank`) is
preserved in the overlay output for side-by-side comparison.

## Smoke test (verify intact; fast, non-destructive)
`python3 4_pipeline/_status.py` then the re-score chain above → expect no errors and `git diff` clean
(deliverables reproduce). Do **not** run the historical steps (1–6) in a smoke test.

_Reproducibility constants (intentional): `_w4_score.py`/`_score.py` hardcode `NOW=2026`; `_diagnostic.py` hardcodes `UNIVERSE=3703`._
