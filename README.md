# Summit School Services — M&A Target Screening

**Cloud:** private GitHub repo `Brisket1994/summit-school-services-targets` — the machine-readable backbone
(scripts, composite exports, per-target packets, status tracker, research briefs). The SQLite DB and raw
Data Axle source (hundreds of MB) stay **local** (gitignored): the analytical engine + raw source.

Identifies and ranks private, independent school-bus / special-needs operators as tuck-in acquisition targets
for **Summit School Services** (ex-Durham/National Express, owned by I Squared Capital).
Data Axle bulk exports → verified → web + FMCSA enriched → scored.

> **This file is navigation only.** Full project state, phase tracker, scoring model, and how-to-resume live in **`RESUME.md`**.

## 📂 Folder map
| Path | What's in it |
|---|---|
| **`3_deliverables/`** | 👉 START HERE — ranked target lists, full enriched table, acquirer memo (`_intermediate/` = superseded) |
| `2_database/` | `summit_targets.db` — the analytical source of truth *(local, gitignored)* |
| `1_source_data/` | Raw Data Axle `Bulk Exports/` + combined master xlsx *(local, gitignored)* |
| `4_pipeline/` | The reproducible Python pipeline + its index (`4_pipeline/README.md`) |
| `5_working/` | `inputs/` (JSON the scripts read) + `batch_outputs/` (archived per-batch recon, merged into the DB) |
| `6_targets/` | Overnight A-list research packets + outreach drafts (`README.md` = runbook, `RESEARCH_SPEC.md` = agent spec) |
| `7_research_requests/` | BrightWave external-data briefs — one subfolder per request (`<brief>.md` + `results/` committed + `sources/` local) |
| `targets_status.csv` | Per-target night-research progress tracker (1,126 A-list) |
| `RESUME.md` | **Full project state + how-to-resume** |
| `NEXT_SESSION_PROMPT.md` | Self-contained prompt to continue the W5 overlay re-score in a fresh session |
| `.remember/` | Session handoff notes *(local, gitignored)* |

## 🎯 Deliverables (`3_deliverables/`)
- `master_targets_ranked.csv` — 2,646 ranked targets (1,126 A-list + 1,520 bench), curated columns
- `master_targets_FULL.csv` — same targets, every enriched field (85 cols: `da_`/`web_`/`agent_`/`census_`)
- `master_targets.jsonl` — full master view, one JSON object per target
- `master_targets_profiles.jsonl` — per-company profiles · `master_targets_A_top50.md` — readable top 50
- `Summit_Footprint_Memo.md` — sourced research on the acquirer

## 🔁 How to re-run (from this folder; scripts self-anchor to the project root)
```
python3 4_pipeline/_status.py     # snapshot of current state
python3 4_pipeline/_w4_score.py   # re-score → regenerate ranked deliverables (free, deterministic)
```
Full script index + run order: `4_pipeline/README.md`. Pipeline state + smoke test: `RESUME.md`.

## ➡️ What's next
- **W5 overlay re-score** — layer BrightWave primary-source industry research into the score → see `NEXT_SESSION_PROMPT.md`
- **Overnight A-list research → outreach** → see `6_targets/README.md`

## 🗃️ Database tables (`summit_targets.db`)
`companies` · `targets` · `entities` (with `verdict`) · `enrichment` · `fmcsa` · `census_bus` · `fmcsa_census` · `master_targets`. Schema + counts in `RESUME.md`.
