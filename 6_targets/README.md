# 6_targets/ — per-target research packets & outreach drafts

One subfolder per A-list target (`<rank>-<slug>/`), produced by the overnight research workflow.
Each contains:
- `overview.md` — the research packet (skim this before sending)
- `facts.json` — structured facts (machine-readable, for sorting/filtering later)
- `outreach_draft.md` — the short staged email (review, then send; never auto-sent)

**How a night runs:**
1. `python3 4_pipeline/_next_batch.py 100` → writes the next 100 un-researched targets to `5_working/inputs/_night_batch.json`
2. The research workflow runs one agent per target per `RESEARCH_SPEC.md`, writing the three files here
3. The workflow marks each `researched=1` in `../targets_status.csv` (idempotent — reruns skip done targets)

**Kimi Allegro app loop (current production path — Kimi collects, Claude drafts).** Research is run on the
Kimi K2.6 Agent Swarm (Allegro app), which produces `facts.json` + `overview.md` only; **Claude drafts
`outreach_draft.md` after the user verifies the facts** (the swarm over-reaches on synthesis/outreach). Loop:
1. `python3 4_pipeline/_next_batch.py 8` → `python3 4_pipeline/_prep_kimi_batch.py` → a public-only,
   paste-ready brief in `5_working/kimi_returns/` (internal scores/notes stripped).
2. Paste into the Allegro app (one swarm run, ~8 targets); save the returned JSON to `5_working/kimi_returns/`.
3. `python3 4_pipeline/_ingest_kimi_returns.py <return.json>` → writes the two files here + flips
   `../targets_status.csv` (idempotent; never overwrites). Then verify, and Claude writes the outreach draft.

Full runbook, batching budget, pilot gate, and the recalibrated swarm briefs:
`…/AI Tool Research/kimi-swarm-execution-kit/RUNBOOK_Allegro_target-screening.md` + `PACK-01_alist-research_ALLEGRO.md`.

See `RESEARCH_SPEC.md` for the exact per-target spec and `_TEMPLATE/` for file skeletons.
Progress is tracked in `../targets_status.csv`.
