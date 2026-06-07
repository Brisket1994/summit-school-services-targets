# RESUME — Summit School Services M&A Target Screening

**Last updated:** 2026-06-07 (PIPELINE COMPLETE through W4 — ranked deliverables produced; next = user's market-data overlay re-score)
**DELIVERABLES:** `master_targets_ranked.csv` (2,646 = 1,126 A-list + 1,520 bench), `master_targets_A_top50.md`, `master_targets_profiles.jsonl`. W4 = `_w4_score.py` (re-run anytime; modular weights `W` for overlay).
**Purpose:** Full state + how-to-resume so this work plan can continue after any interruption (usage limits, compaction, new session). Read this first, then run `python3 4_pipeline/_status.py` for live counts.

> **FOLDER REORGANIZED 2026-06-07** — see `README.md` for the map. All paths below that name bare files now live under typed subfolders: scripts → `4_pipeline/`, DB → `2_database/summit_targets.db`, inputs/state JSON → `5_working/inputs/`, batch outputs → `5_working/batch_outputs/`, deliverables → `3_deliverables/` (interim in `3_deliverables/_intermediate/`), source xlsx + Bulk Exports → `1_source_data/`. Scripts self-anchor to the project root, so **run them from this folder as `python3 4_pipeline/<script>.py`**. They were updated to read/write the new subpaths.

---

## GOAL
From Data Axle bulk exports of "all transport companies," identify and deeply profile the top tuck-in acquisition targets for **Summit School Services** (the acquirer). Targets = **private, independent school-bus / special-needs operators** (not districts, not schools, not the big PE/strategic platforms).

## THE ACQUIRER (context)
Summit School Services = former **Durham School Services / National Express NA**, owned by **I Squared Capital** since July 2025 (~14k buses, ~32 states). Plays a "house of local brands" roll-up; tuck-in profile = regional/family-owned independents. Durham/National Express/Summit are the PLATFORM → excluded as targets. Full memo: `_summit_footprint.md`.

## USER-LOCKED DECISIONS
- Substrate: **SQLite** (`summit_targets.db`).
- Sequence: **filter-to-relevance first, then consolidate** entities.
- Segment scope: **core + charter** (school bus + special-needs + SIC 4151 + school/student named + charter 485510).
- Relevance priority for screen: **school + special-needs** (charter de-prioritized).
- Acquirability: **private only** — exclude public/in-house/government.
- Size box: prioritize **single/small/mid (1–14 locations)**; flag 15+ separately.
- Geography: weight by **Summit footprint** (modest boost), extra for **expansion states FL,NY,PA,MO,GA,IN**.
- Depth: **enrich & rank EVERY confirmed target** (all 3,703), not just top 300. Hours/scheduled runs OK.

---

## CURRENT STATUS (phase tracker)
- ✅ **Data combine:** 292 Data Axle files → `Data Axle Master - All Transport Companies.xlsx` (291,561 rows, sheet "All Companies", `Source Batch` col added).
- ✅ **DB build:** `summit_targets.db` — tables `companies` (291,561), `targets` (~18k segment rows), `entities` (13,129 consolidated).
- ✅ **W1 Summit footprint:** done → `_summit_footprint.md` + memory.
- ✅ **W2 full verification:** all 7,137 school+special entities classified; verdicts written to `entities.verdict`. Result: **3,703 private_contractor**, 1,748 public_or_inhouse, 894 not_transport, 792 unsure.
- ✅ **W3 web enrichment:** DONE 100% (3,703 in DB `enrichment`). Funnel: 1,126 confirmed-private / 1,057 reclassified-out (PE/strategic/defunct) / 1,520 unsure. Clean independent/family ~1,094 → `targets_independent_enriched.csv`. Waves `_enrich_out_w*`, merged via `_merge_enrich.py`; schema-less file-based after a wave-2 rate-limit incident. confirmed_private freeform (normalize: startswith yes/no/unsure).
- ✅ **Diagnostic (`_diagnostic.py`):** gaps — fleet 44%, founded 37%, website 36%, succession 24% known; confidence skews low (web-visibility bias vs small no-website family firms = prime targets). Motivated W3.5.
- 🔄 **W3.5 FMCSA/registry (user-approved):** structured pass over all 3,703 — FMCSA/SAFER (USDOT, power_units≈buses, drivers, safety rating, address, status) + state registry (inc_date, officers, status). Infra: `_fmcsa_input_all.json`, `_merge_fmcsa.py`, DB table `fmcsa`, `_fmcsa_remaining.json`. Schema-less waves of 900 (`_fmcsa_out_w<wave>_<b>.jsonl`); after each `python3 _merge_fmcsa.py`. Wave 1 running (`wf_583306ba-32e`). ~4 waves.
- ⏳ **W4 re-score/geo-weight/rank (decisions locked):** CONFIDENCE-AWARE. Down-weight Data Axle modeled revenue/employees; gate on web+FMCSA-confirmed ownership (drop confirmed_private='no'); reward verified fleet (FMCSA power_units) + succession (inc_date/owner tenure) + Summit-proximity; KEEP 1,520 'unsure' as a FLAGGED BENCH (parallel track, not dropped). Output ranked master table + per-company profiles (CSV + markdown + JSONL).
  - **FUTURE OVERLAY (post-W4, user-driven):** user will PROVIDE premium market data later — deal-comp/EV-per-bus multiples + competitive-acquirer map, district contract/RFP renewal timing, driver-labor index, outsourcing-trend by state, EV-mandate flags, owner-age/credit. Do NOT build placeholder hooks now. After W4 ships, layer this as a separate overlay re-score (per-target multipliers + state/metro market-attractiveness weights) — a clean re-run, not a rebuild. Keep `_score`/W4 script modular so an overlay column-merge + reweight is easy.

---

## DATA MODEL (`summit_targets.db`)
- `companies`: all 291,561 establishment rows, 396 cols (original Data Axle names, quoted). First col `Source Batch`.
- `targets`: rows in the core+charter segment (subset of columns; see `_consolidate.py` SEL list).
- `entities`: 13,129 consolidated operating companies. Key cols: `entity_key, canonical_name, locations, size_tier, n_states, states, primary_state, loc_employees_sum, loc_sales_sum, corp_employees, corp_sales, year_established, school, special_needs, charter, parents, website, phone, lead_exec, hq, sample_address, name_variants, review_flag, gov_flag, credit_score, is_target, verdict, verdict_conf, verdict_reason`.
  - `is_target=0` = excluded platform/public/PE (First Student/EQT, Durham/Summit, National Express, STA, Laidlaw, Coach USA…).
  - `verdict` (set by W2 for school+special, is_target=1): `private_contractor | public_or_inhouse | not_transport | unsure`.
  - **Confirmed target universe = `WHERE verdict='private_contractor'` (3,703).**

## SCRIPTS (reproducible pipeline; all in project root)
- `_build_db.py` — master xlsx → `summit_targets.db` (companies table + indexes).
- `_consolidate.py` — builds `targets` + `entities` (name-normalized consolidation, platform flagging). Re-run regenerates entities (would WIPE verdict cols — see CAUTION below).
- `_score.py` — rule-classify + weighted scoring of school+special private pool (older; superseded by W2 LLM verdicts + `_rank_private.py`).
- `_rank_private.py-equivalent` — inline script that scored `verdict='private_contractor'` with geo boost → `_enrich_input_all.json` (all 3,703 ranked) + `_enrich_pilot.json` (top 200). (Logic embedded in chat; re-create if needed — see SCORING MODEL.)
- `_status.py` — prints current counts / progress snapshot.

## KEY DATA FILES
- `_classify_input.json` — 7,137 entities fed to W2 (idx order == `SELECT * FROM entities WHERE is_target=1 AND (school=1 OR special_needs=1)`).
- `_cls_out_0..237.jsonl` — W2 verdicts (already merged to DB).
- `_enrich_input_all.json` — all 3,703 confirmed-private, ranked, with fields for recon.
- `_enrich_pilot.json` — top 200 for the pilot.
- `_enrich_out_<b>.jsonl` — W3 recon profiles (per batch). **Durable progress; never delete mid-run.**

## WORKFLOW SCRIPT PATHS (for resume via Workflow {scriptPath, resumeFromRunId})
- W1 summit-footprint: `.../workflows/scripts/summit-footprint-wf_d5f86c51-ff5.js`
- W2 verify-all-targets: `.../workflows/scripts/verify-all-targets-wf_4192a962-1a7.js`
- W3 pilot enrich: `.../workflows/scripts/enrich-targets-pilot-wf_57dd9c17-c5c.js`
(Full dir: `/Users/zabrisket/.claude/projects/-Users-zabrisket-Documents-Claude-Projects-Summit-School-Services-All-Transport-Companies/a51f7630-2c1c-4a41-bf62-4b6f3b7cec86/workflows/scripts/`)

---

## SCORING MODEL (W4 / `_enrich_input_all.json`)
Weighted 0–100: size_fit .30, succession .20, quality .20, independence .15, relevance .15; then geo boost (+8 expansion state, +4 other Summit state).
- size_fit: from employees (peak 10–300) and revenue (peak $1–30M).
- succession: older year_established = higher (≥40y=100, ≥25y=85…).
- quality: website +40, phone +25, emp≥10 +25, revenue>0 +10.
- independence: single=100, small=80, mid=60.
- relevance: school+special=100, school=90, special=75.
SUMMIT_STATES + EXPANSION sets are in the ranking script (see `summit-identity` memory).

## HOW TO RESUME EACH REMAINING STEP

### If W3 pilot interrupted / to merge it:
1. `python3 _merge_enrich.py` (creates/updates DB table `enrichment`, keyed by rank+name; idempotent — skips dupes).
2. Inspect quality; check coverage vs `_enrich_pilot.json`.

### To SCALE W3 to all 3,703 (the big job):
- Enrichment is RESUMABLE: `_merge_enrich.py` builds set of already-enriched ranks from `enrichment` table; the next wave only processes MISSING ranks from `_enrich_input_all.json`.
- Run in waves of ~250–400 (each a Workflow, ≤1000 agents, 5 targets/agent, agentType 'general-purpose', web research, writes `_enrich_out_w<wave>_<b>.jsonl`).
- After each wave: merge → update `enrichment` table → update this RESUME.md + `.remember/remember.md`.
- Consider scheduling (skill `schedule`/`loop`) to auto-run successive waves.

### W4 (after enrichment coverage sufficient):
- Re-score using enrichment fields (confirmed ownership independence, fleet size, succession, news) layered onto base score.
- Produce master ranked DB/table + per-company profile exports (CSV + markdown + JSONL).

## CAUTION
- Do NOT re-run `_consolidate.py` without re-running W2 merge — it rebuilds `entities` and drops `verdict`. If you must, re-merge `_cls_out_*.jsonl` after (mapping is by query order; verified stable).
- Empty cells: openpyxl reads blank as None; treat ''/None as equal.
- Master xlsx is ~203MB; DB ~468MB — both stay on disk across sessions.

## CHECKPOINT DISCIPLINE
Update this file + `.remember/remember.md` at every milestone (pilot merge, each enrichment wave, W4). The DB is the source of truth; these docs are the map.

## W3.5 UPDATE — bulk-census efficiency pivot (2026-06-04)
Agent FMCSA waves were expensive (~11M tok/wave). Pivoted: `_pull_census.py` pulls FMCSA Company Census (data.transportation.gov SODA resource `az4n-8mr2`, anonymous, no key) → DB `census_bus` (117,400 bus carriers, ZERO LLM tokens). `_census_match.py` → DB `fmcsa_census` (rank-keyed): matched 2,965/3,703; precision vs agents high 90% / med 77% / low 38%. Census fields RICHER than agent scrape (power_units, bus_units, ownschool_1_8/9_15/16, total_drivers/cdl, status_code, safety_rating, recordable_crash_rate, add_date=registration, mcs150_date, company_officer_1/2).
Gaps (census low/none + no agent data, yes+unsure only) → `_build_fallback.py` builds `_fmcsa_fallback.json` (1,196) → Sonnet fallback waves `_fmcsa_out_fb_w<wave>_<b>.jsonl` → `_merge_fmcsa.py`. Rebuild `_fmcsa_fallback.json` between waves (shrinks). Wave 1 = `wf_7a614761-fbb`.
**W4 unified FMCSA source priority per target: `fmcsa_census` (high/med) → `fmcsa` (agent) → `enrichment` (web).** New tables: `census_bus`, `fmcsa_census`. New scripts: `_pull_census.py`, `_census_match.py`, `_build_fallback.py`, `_diagnostic.py`, `_merge_fmcsa.py`.
