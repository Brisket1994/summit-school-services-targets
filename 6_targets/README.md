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

See `RESEARCH_SPEC.md` for the exact agent instructions and `_TEMPLATE/` for file skeletons.
Progress is tracked in `../targets_status.csv`.
