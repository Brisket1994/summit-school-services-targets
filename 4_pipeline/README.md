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
| 12 | `_export_full.py` | join + raw census → `master_targets_FULL.csv` (85 cols) |
| 13 | `_build_master_view.py` | `master_targets_FULL.csv` → `master_targets` DB table (+indexes) |
| 14 | `_build_status.py` | `master_targets` → `master_targets.jsonl` + `alist_queue.jsonl` + `targets_status.csv` (idempotent; preserves progress) |
| 15 | `_next_batch.py [N]` | next N un-researched A-list → `5_working/inputs/_night_batch.json` |
| 16 | `_status.py` | read-only DB snapshot + counts |

## Re-score / overlay chain (the W4 → W5 re-run)
```
python3 4_pipeline/_w4_score.py          # re-score from DB
python3 4_pipeline/_export_full.py       # → master_targets_FULL.csv
python3 4_pipeline/_build_master_view.py # → master_targets table
python3 4_pipeline/_build_status.py      # → jsonl/queue/status
```
For the W5 overlay, the market-data table is joined in `_w4_score.py` and its weights dict `W` extended — a
re-run of this chain, not a rebuild.

## Smoke test (verify intact; fast, non-destructive)
`python3 4_pipeline/_status.py` then the re-score chain above → expect no errors and `git diff` clean
(deliverables reproduce). Do **not** run the historical steps (1–6) in a smoke test.

_Reproducibility constants (intentional): `_w4_score.py`/`_score.py` hardcode `NOW=2026`; `_diagnostic.py` hardcodes `UNIVERSE=3703`._
