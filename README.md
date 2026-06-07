# Summit School Services — M&A Target Screening

Identifies and ranks private, independent school-bus / special-needs operators as tuck-in
acquisition targets for **Summit School Services** (ex-Durham/National Express, owned by
I Squared Capital). Built from Data Axle bulk exports → verified → web + FMCSA enriched → scored.

## 📂 Folder map

| Folder | What's in it |
|---|---|
| **`3_deliverables/`** | 👉 **START HERE.** The ranked target lists + memo |
| `1_source_data/` | Raw inputs: `Bulk Exports/` (292 Data Axle files) + the combined master `.xlsx` |
| `2_database/` | `summit_targets.db` — the single source of truth (all data, all tables) |
| `4_pipeline/` | The 12 reproducible Python scripts (the "engine") |
| `5_working/` | Re-run state: `inputs/` (JSON the scripts read) + `batch_outputs/` (archived per-batch recon, already merged into the DB) |
| `RESUME.md` | Full technical state + how-to-resume (for picking the project back up) |
| `.remember/` | Session handoff notes |

## 🎯 The deliverables (`3_deliverables/`)
- **`master_targets_ranked.csv`** — all 2,646 ranked targets (1,126 A-list + 1,520 "unsure" bench): curated, decision-ready columns
- **`master_targets_FULL.csv`** — same 2,646 targets with **every enriched field** (85 cols): Data Axle (`da_`) + web recon (`web_`) + agent FMCSA (`agent_`) + FMCSA census (`census_`, incl. school-buses-by-capacity, crash rate, registration date, phone/email/address). Built by `4_pipeline/_export_full.py`
- **`master_targets_A_top50.md`** — readable top-50 A-list
- **`master_targets_profiles.jsonl`** — full per-company profiles
- **`Summit_Footprint_Memo.md`** — sourced research on the acquirer
- `_intermediate/` — earlier-stage outputs (superseded by the master files)

## 🔁 How to re-run
All scripts are run **from this folder** (they self-anchor to the project root):
```
python3 4_pipeline/_status.py        # snapshot of current state
python3 4_pipeline/_w4_score.py      # re-score + regenerate the ranked deliverables
```
The database in `2_database/` holds everything; scoring (`_w4_score.py`) is free, deterministic,
and re-runnable. To apply the planned **market-data overlay** (deal multiples, contract/RFP timing,
driver-labor, outsourcing trend, EV mandates, owner-age), drop the data in and re-run W4 with the
overlay weights — a clean re-run, not a rebuild.

## 🗃️ Database tables (`summit_targets.db`)
`companies` (291,561 establishments) · `entities` (13,129 consolidated operators, with `verdict`)
· `enrichment` (web recon) · `fmcsa` (agent FMCSA) · `census_bus` (FMCSA bulk census) · `fmcsa_census` (matched).

_Note: new enrichment workflows should write batch files to `5_working/batch_outputs/`._
