# Per-Target Research Spec (overnight A-list workflow)

Each night's workflow takes the next batch of un-researched A-list targets (from `targets_status.csv`,
fed via `5_working/inputs/_night_batch.json`) and, **one dedicated agent per target**, produces a
research packet + a short staged outreach email. One folder per target: `6_targets/<slug>/`.

## Inputs the agent receives (per target)
A queue item from `alist_queue.jsonl` — already contains our enriched facts: company, hq, state,
fleet_buses, drivers, founded, ownership_type, owner/principals, districts, website, phone, email,
USDOT, recent_news, fit notes, composite score. **Start from these; the web research confirms,
deepens, and fills gaps — don't re-derive what we already have.**

## Deliverables (write all three into `6_targets/<slug>/`)

### 1. `overview.md` — the research packet (the thing the user skims before sending)
Concise, scannable, sourced. Sections:
- **Snapshot** — company, HQ, fleet (# buses), drivers, founded, ownership type, est. size.
- **Business** — service lines (yellow-bus / SPED / charter), districts & contracts served, geographic footprint.
- **Ownership & Succession** — owner/principal names, family vs outside ownership, age/tenure/succession signals (the seller-motivation read), independence confirmation.
- **Fit for Summit** — why a tuck-in: geographic synergy with Summit's footprint, route density, scale; and **risks/watch-outs** (recent acquisition, litigation, safety rating, declining districts).
- **Recent developments** — news, awards, expansions, leadership changes (with dates + sources).
- **Sources** — list the URLs used.
Keep it tight (≈1 page). Flag uncertainty honestly; never invent.

### 2. `facts.json` — structured sidecar (machine-readable, for later sorting/filtering)
```json
{"a_rank":int,"slug":str,"company":str,"legal_name":str,"hq_city":str,"state":str,
 "website":str,"phone":str,"email":str,
 "ownership_type":"independent|family|unknown","owner_principals":[{"name":str,"title":str}],
 "succession_read":{"level":"high|medium|low","why":str},
 "fleet_buses":int,"drivers":int,"founded_year":int,"est_revenue_usd":str,
 "service_lines":[str],"districts_contracts":[str],"geography":[str],
 "summit_fit":str,"risks_watchouts":[str],
 "recent_news":[{"date":str,"item":str,"source":str}],
 "key_contacts":[{"name":str,"title":str,"source":str}],
 "sources":[str],"data_confidence":"high|medium|low","last_researched":"YYYY-MM-DD"}
```

### 3. `outreach_draft.md` — the SHORT staged email (NOT auto-sent)
Hard constraints:
- **Subject line** + body of **4–6 sentences max.** No five-paragraph essays.
- Warm, professional, peer-to-peer. **Soft ask**: explore a conversation — not a hard pitch, no valuation/price talk.
- **One genuine, specific personalization hook** drawn from the research (longevity, family legacy, a district relationship, a region) — not generic flattery.
- Signed by the sender (leave `[Your name]` / signature placeholder).
- End the file with a one-line **`> Hook used:`** note so the user can sanity-check the personalization at a glance.
- Remember Summit = the platform (ex-Durham/National Express); never imply the target is already owned.

## After writing
The orchestrating workflow marks the target `researched=1` (with date + file paths) in `targets_status.csv`.
Batches are idempotent: only targets with `researched=0` are picked, so reruns never duplicate work.

## Templates
See `6_targets/_TEMPLATE/` for skeletons of all three files.
