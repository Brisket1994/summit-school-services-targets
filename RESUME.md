# RESUME — Summit School Services M&A Target Screening
*Single authoritative current-state doc. `README.md` = navigation/index; this = full state. Keep it current — overwrite, don't append dated logs. Updated 2026-06-07.*

## ONE-LINE STATUS
W1–W4 complete: **2,646 ranked targets shipped** (1,126 A-list + 1,520 bench). **Next = W5 overlay** — layer BrightWave primary-source industry research into a re-weighted score (3 briefs staged in `7_research_requests/`, awaiting returned sources). Night-one A-list research **scaffolded, 0/1,126 run**.

## WHAT'S NEXT (active phases)
- **W5 — BrightWave overlay re-score (staged, not yet run).** Full instructions in `NEXT_SESSION_PROMPT.md`. Returned sources land in `7_research_requests/<brief>/sources/`; **we synthesize the conclusions ourselves — BrightWave's own conclusions are NOT authoritative.** Path: sources → evidence ledgers → DB overlay table → extend `4_pipeline/_w4_score.py` weights `W` → re-run. Modular, cited, re-runnable.
- **Night-one A-list research (scaffolded).** Runbook: `6_targets/README.md`; agent spec: `6_targets/RESEARCH_SPEC.md`; tracker: `targets_status.csv` (1,126 A-list, all `researched=0`); queue: `5_working/inputs/alist_queue.jsonl`; batch helper: `4_pipeline/_next_batch.py`.

## GOAL & ACQUIRER
Identify/rank private, independent **school-bus / special-needs** operators as tuck-in targets for **Summit School Services** — the ex-**Durham / National Express NA** platform, owned by **I Squared Capital** since July 2025 (~14k buses, ~32 states, "house of local brands" roll-up). Durham/National Express/Summit = the PLATFORM, excluded as targets. Acquirer memo: `3_deliverables/Summit_Footprint_Memo.md`.

## USER-LOCKED DECISIONS
- Substrate: SQLite (`2_database/summit_targets.db`). Sequence: filter-relevance → consolidate → verify → enrich → score.
- Segment: core + charter (NAICS 485410 school bus + 48599101 special-needs + SIC 4151 + school/student-named + 485510 charter). Screen priority: **school + special-needs** (charter de-prioritized).
- Acquirability: **private only** (exclude public/in-house/government and PE/strategic platforms).
- Size box: prioritize single/small/mid (1–14 locations); 15+ flagged "large independent."
- Geography: weight Summit footprint; extra for expansion states **FL, NY, PA, MO, GA, IN, UT**.
- **Count note:** `3,703` = the **W3 input universe** (W2 `private_contractor` verdicts). `2,646` = the **ranked output** after W3 web verification reclassified 1,057 as PE/strategic/defunct ('no'). 1,126 'yes' → A-list; 1,520 'unsure' → bench.
- Overlay (W5): we form the conclusions from primary sources; BrightWave = discovery + verbatim extraction only.

## PHASE TRACKER
- ✅ **Data combine / DB build** — 292 files → master xlsx (291,561 rows) → DB (`companies` 291,561, `targets` 17,970, `entities` 13,129).
- ✅ **W1 acquirer footprint** → `3_deliverables/Summit_Footprint_Memo.md`.
- ✅ **W2 verification** — 7,137 school+special entities → `entities.verdict` (3,703 private_contractor / 1,748 public_or_inhouse / 894 not_transport / 792 unsure).
- ✅ **W3 web enrichment** — 100% of 3,703 → `enrichment`. Web funnel: 1,126 confirmed-private / 1,057 reclassified-out / 1,520 unsure.
- ✅ **W3.5 FMCSA structured** — bulk census (`census_bus`, 117,400 carriers, free SODA pull) matched → `fmcsa_census` (2,965/3,703; precision 90/77/38% high/med/low vs agents); Sonnet fallback for census-gap targets → `fmcsa`. ~98% of rankable attempted; 57% carry verified fleet/USDOT. Unified per-target source priority: `fmcsa_census`(high/med) → `fmcsa`(agent) → `enrichment`(web).
- ✅ **W4 confidence-aware score** → `master_targets` table + deliverables. 2,646 ranked (A-list 1,126 / bench 1,520).
- 🔄 **W5 overlay** — staged (see WHAT'S NEXT).
- 🔄 **Night-one research** — scaffolded (see WHAT'S NEXT).

## DELIVERABLES & ARTIFACTS
- `3_deliverables/master_targets_ranked.csv` — 2,646 ranked, curated decision columns.
- `3_deliverables/master_targets_FULL.csv` — same targets, **85 cols** (`da_`/`web_`/`agent_`/`census_`).
- `3_deliverables/master_targets.jsonl` — full master view, one JSON object/target.
- `3_deliverables/master_targets_profiles.jsonl`, `master_targets_A_top50.md`, `Summit_Footprint_Memo.md`; `_intermediate/` = superseded provenance.
- `targets_status.csv` (project root) — per-target night-research tracker (1,126 A-list).
- `7_research_requests/{01,02,03}/<brief>.md` — the 3 BrightWave briefs (+ `results/` committed, `sources/` local).

## DATA MODEL (`2_database/summit_targets.db`)
- `companies` (291,561) — all 396 Data Axle cols, `Source Batch` first.
- `targets` (17,970) — core+charter segment subset.
- `entities` (13,129) — consolidated operators; `verdict` ∈ {private_contractor|public_or_inhouse|not_transport|unsure}; `is_target=0` = excluded platforms. Confirmed universe = `WHERE verdict='private_contractor'` (3,703).
- `enrichment` (web recon) · `fmcsa` (agent FMCSA) · `census_bus` (117,400 FMCSA census) · `fmcsa_census` (matched per target).
- `master_targets` (2,646 × 91) — the joined, scored single-table view (slice this for analysis).

## SCRIPTS
Full index + classification (historical build vs current operational) + run order: **`4_pipeline/README.md`**. All scripts self-anchor to the project root; run as `python3 4_pipeline/<script>.py` from this folder.

## SCORING MODEL (W4 — `4_pipeline/_w4_score.py`)
Confidence-aware composite, weights dict `W`: **size_fit 25, succession 20, geo 15, independence 15, operating_health 15, relevance 10** (sum 100). FMCSA fields unified census→agent→none per target. A-list = `confirmed_private` 'yes'; bench = 'unsure'; 'no' dropped. **Overlay hook (W5):** add market-data columns (deal multiples / EV-per-bus, contract timing, driver-labor, outsourcing trend, EV mandates, owner-age) as a DB table joined per target, extend `W`, re-run — a modular re-score, not a rebuild.

## NIGHT-RESEARCH DATA CHAIN
`alist_queue.jsonl` (1,126, persistent) → `_next_batch.py N` slices next N un-researched (per `targets_status.csv`) → `_night_batch.json` → research workflow (per `6_targets/RESEARCH_SPEC.md`) writes `6_targets/<slug>/{overview.md,facts.json,outreach_draft.md}` + marks `researched=1`. Idempotent/resumable.

## SMOKE TEST (verify pipeline intact — fast, non-destructive; run from project root)
```
python3 4_pipeline/_status.py            # DB snapshot + counts
python3 4_pipeline/_w4_score.py          # re-score (read DB → deliverables); deterministic
python3 4_pipeline/_export_full.py       # → master_targets_FULL.csv
python3 4_pipeline/_build_master_view.py # → master_targets table
python3 4_pipeline/_build_status.py      # → master_targets.jsonl, alist_queue.jsonl, targets_status.csv
```
Success = no errors and `git diff` shows no change to committed deliverables (reproducible). Do **NOT** run the historical/destructive steps (`_build_db`, `_consolidate`, `_pull_census`, `_census_match`) in a smoke test — they rebuild tables.

## CAUTIONS
- `_consolidate.py` rebuilds `entities` and DROPS `verdict`; only re-run intentionally, then re-merge W2 verdicts.
- Big binaries kept LOCAL / gitignored: `2_database/*.db`, `1_source_data/` (Bulk Exports + master xlsx), `7_research_requests/*/sources/`. **Back up `1_source_data/Bulk Exports/` separately** — the one irreplaceable original.
- Empty cells: openpyxl reads blank as None; treat ''/None as equal.

## REPO
Private GitHub `Brisket1994/summit-school-services-targets` (branch `main`). Commit/push after milestones.
