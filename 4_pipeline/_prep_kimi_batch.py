#!/usr/bin/env python3
"""Prepare a paste-ready Kimi K2.6 Agent Swarm brief from the current night batch (Allegro app loop).

Reads 5_working/inputs/_night_batch.json (produced by _next_batch.py), strips all internal/prohibited
fields so only public identifiers leave the machine, embeds the cleaned batch inside the PACK-01
collect-only orchestrator brief, and writes one paste-ready markdown file to
5_working/kimi_returns/_paste_<YYYY-MM-DD>_<n>.md.

Paste that file into the Kimi Allegro app Agent Swarm (one swarm run), save the returned JSON to
5_working/kimi_returns/<date>_batch<n>.json, then run _ingest_kimi_returns.py on it.

Hard data-hygiene rule: composite, data_confidence, notes, reviewed, sent (and anything not in ALLOWED)
are NEVER exported. The script asserts the cleaned records carry no prohibited key before writing.

Usage: python3 4_pipeline/_prep_kimi_batch.py
stdlib only.
"""
import json, os, datetime

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BATCH = "5_working/inputs/_night_batch.json"
OUTDIR = "5_working/kimi_returns"

# Public-only fields that MAY be exported into an outbound prompt (PACK-01 §2 / protocol §6).
ALLOWED = [
    "a_rank", "slug", "company", "legal_name", "state", "hq", "da_address",
    "fleet_buses", "drivers", "founded", "website", "da_phone", "census_phone",
    "census_email_address", "census_dot_number", "web_ownership_type", "web_owner_or_parent",
    "web_principals", "web_succession_signal", "web_districts_or_customers", "web_service_types",
    "web_recent_news", "web_fit_notes",
]
PROHIBITED = {"composite", "data_confidence", "notes", "reviewed", "sent"}

BRIEF = r"""# PASTE THIS WHOLE FILE INTO THE KIMI ALLEGRO APP — AGENT SWARM (one swarm run)

You are coordinating a public-records research run for Summit School Services, a K-12 student-
transportation platform. The job: turn the pre-enriched private bus-operator records in NIGHT_BATCH into
per-target research packets a corp-dev reviewer can skim in under a minute. Every fact must come from a
public source you can cite. This is a collection-and-summarization task — you make no decision about these
companies.

Treat each target as ONE sub-agent task (one company per sub-agent, no shared context). You have 4 sub-
agents at a time — run the batch in waves of 4. Use TASK_TEMPLATE for each target, substituting that
target's fields. Aim for ~10 tool calls per sub-agent; cap output ~16,000 tokens.

The enrichment fields on each record are our prior public-web pass — confirm, deepen, fill gaps; do not
re-derive them. If fresh evidence contradicts a prior field, the fresh evidence wins and you surface the
conflict (Conflicting) with both sources quoted.

GUARDRAILS (binding — collection, not valuation or decision):
Report only what a source states; for anything unsourced write "not found in the provided sources" — never
compute revenue/EBITDA/EV/multiples or triangulate revenue from a per-bus benchmark (est_revenue_usd is
filled ONLY from a directly-stated public revenue figure). "No evidence found" = NO_SIGNAL/Unverified,
never "refuted." A person not in a primary government filing (state SoS, FMCSA, court docket) is Inference
at most. Keep seller/owner-stated figures tagged separately from verified ones. Do NOT output any
proceed/pass/recommend language or an overall verdict. Label every factual field
Confirmed/Corroborated/Inference/Conflicting/Unverified and close each sub-agent with a verification block.

Verifier leg: after each sub-agent, list any HIGH-IMPACT field that finished single-source or Conflicting
in verifier_queue (high-impact = ownership_type, owner_principals, fleet_buses, succession_read, top-3
districts). After the main array, run one verifier sub-agent per target with a non-empty verifier_queue:
re-fetch the original source + one independent public source (state SoS strongest for ownership; FMCSA
SAFER strongest for fleet) and resolve to Corroborated / leave Confirmed / Conflicting / Unverified.

Re-queue any target whose JSON won't parse once; a second failure → list it under "abandoned"; never drop
silently. If >1 in 20 abandons, stop and flag.

FINAL OUTPUT: reply with ONE JSON array of the per-target objects (OUTPUT_SCHEMA), in NIGHT_BATCH order,
then a second JSON array named VERIFIER_RESULTS. No prose around the arrays.

TASK_TEMPLATE (per target):
  Research this one operator on the public web, starting from its record. Return ONE JSON object exactly
  like OUTPUT_SCHEMA. Start with the company site, then FMCSA SAFER (USDOT), then the state Secretary of
  State filing, then local news / district board minutes / trade press. est_revenue_usd only if a source
  states revenue directly. Every URL in sources must be one you actually retrieved.

OUTPUT_SCHEMA (one object per target; facts_json must match the 26-field template exactly):
{
  "slug": "<slug>",
  "facts_json": {
    "a_rank": <int>, "slug": "<slug>", "company": "<str>", "legal_name": "<str>",
    "hq_city": "<str>", "state": "<str>", "website": "<str>", "phone": "<str>", "email": "<str>",
    "ownership_type": "independent|family|unknown",
    "owner_principals": [{"name": "<str>", "title": "<str>"}],
    "succession_read": {"level": "high|medium|low", "why": "<str>"},
    "fleet_buses": <int|null>, "drivers": <int|null>, "founded_year": <int|null>,
    "est_revenue_usd": "<stated figure or 'not found in the provided sources'>",
    "service_lines": ["<str>"], "districts_contracts": ["<str>"], "geography": ["<str>"],
    "summit_fit": "<str>", "risks_watchouts": ["<str>"],
    "recent_news": [{"date": "<YYYY-MM-DD>", "item": "<str>", "source": "<url>"}],
    "key_contacts": [{"name": "<str>", "title": "<str>", "source": "<url>"}],
    "sources": ["<url>"], "data_confidence": "high|medium|low", "last_researched": "<YYYY-MM-DD>"
  },
  "overview_md": "<the ~1-page markdown packet: Snapshot / Business / Ownership & Succession / Fit for Summit (+ Watch-outs) / Recent developments / Sources>",
  "verification_block": [{"claim": "<str>", "status": "<str>", "evidence": "<str>", "confidence": "<label>"}],
  "verifier_queue": [{"field": "<str>", "reason": "<str>"}]
}

Notes: data_confidence "high" only if ownership_type, owner_principals, fleet_buses, and >=3 districts are
each Confirmed/Corroborated; else "medium"; "low" if >=2 are weak. last_researched = today (YYYY-MM-DD).
Do NOT include outreach text — outreach is drafted later by the reviewer, not by you.

NIGHT_BATCH:
"""


def clean(rec):
    out = {k: rec[k] for k in ALLOWED if k in rec}
    bad = PROHIBITED & set(out)
    if bad:
        raise SystemExit(f"PROHIBITED field leaked into export: {bad} (slug={rec.get('slug')})")
    return out


def main():
    if not os.path.exists(BATCH):
        raise SystemExit(f"{BATCH} not found — run `python3 4_pipeline/_next_batch.py N` first.")
    batch = json.load(open(BATCH))
    if not batch:
        raise SystemExit("Night batch is empty — nothing pending (A-list research complete?).")
    cleaned = [clean(r) for r in batch]
    # belt-and-suspenders: confirm no prohibited keys anywhere
    for r in cleaned:
        assert not (PROHIBITED & set(r)), "prohibited key survived cleaning"

    os.makedirs(OUTDIR, exist_ok=True)
    today = datetime.date.today().isoformat()
    n = 1
    while os.path.exists(os.path.join(OUTDIR, f"_paste_{today}_{n}.md")):
        n += 1
    path = os.path.join(OUTDIR, f"_paste_{today}_{n}.md")
    with open(path, "w") as f:
        f.write(BRIEF)
        f.write(json.dumps(cleaned, indent=2))
        f.write("\n")
    ranks = [r.get("a_rank") for r in cleaned]
    print(f"Prepared {len(cleaned)} targets (a_rank {ranks[0]}..{ranks[-1]}) -> {path}")
    print("Exported fields per target:", ", ".join(ALLOWED))
    print("Next: paste this file into the Kimi Allegro app Agent Swarm; save its returned JSON to")
    print(f"  {OUTDIR}/{today}_batch{n}.json ; then: python3 4_pipeline/_ingest_kimi_returns.py <that file>")


if __name__ == "__main__":
    main()
