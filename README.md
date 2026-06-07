# Summit School Services — M&A Target Screening

**Cloud:** private GitHub repo `Brisket1994/summit-school-services-targets` (machine-readable backbone — scripts, composite exports, per-target packets, status tracker). The 507 MB DB and 433 MB source stay **local** (gitignored); they're the analytical engine + raw source.

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
| `7_research_requests/` | External-data briefs for BrightWave (3 self-contained requests) + their results when returned |
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

## 🌙 Night-one runbook (overnight A-list research → outreach)
1. `python3 4_pipeline/_next_batch.py 100` → next 100 un-researched A-list targets → `5_working/inputs/_night_batch.json`
2. Kick off the research workflow (one agent per target, per `6_targets/RESEARCH_SPEC.md`) → writes `6_targets/<slug>/{overview.md, facts.json, outreach_draft.md}` and marks `researched=1` in `targets_status.csv`
3. `git add -A && git commit && git push` → packets + status land in the cloud
4. Review packets alongside the staged short emails; (from tomorrow) send via connected Outlook drafts
Idempotent & resumable: only `researched=0` targets are picked, so a missed/half night just resumes. ~12 nights @100 to cover 1,126.

## 🗃️ Database tables (`summit_targets.db`)
`companies` (291,561 establishments) · `entities` (13,129 consolidated operators, with `verdict`)
· `enrichment` (web recon) · `fmcsa` (agent FMCSA) · `census_bus` (FMCSA bulk census) · `fmcsa_census` (matched).

_Note: new enrichment workflows should write batch files to `5_working/batch_outputs/`._
