#!/usr/bin/env python3
"""Ingest a saved Kimi Agent Swarm return into the repo (Allegro app loop, step 4).

Parses the consolidated JSON the app returned (tolerant of code fences, surrounding prose, and the
main-array + VERIFIER_RESULTS-array shape), validates each target's facts against the 26-field
6_targets/_TEMPLATE/facts.json, writes 6_targets/<slug>/{facts.json, overview.md}, applies verifier-leg
upgrades, flips targets_status.csv (researched=1 + paths + date), and writes a run summary.

Idempotent and non-destructive: a slug whose 6_targets/<slug>/overview.md already exists is written to
overview.md.candidate-<ts> (+ facts.json.candidate-<ts>) and flagged — never overwritten, and status is
not flipped for it. Outreach is NOT produced here (Claude drafts outreach_draft.md after Mac verifies).

Usage:  python3 4_pipeline/_ingest_kimi_returns.py 5_working/kimi_returns/<file>.json [--check-links]
stdlib only.
"""
import json, csv, os, sys, datetime

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE = "6_targets/_TEMPLATE/facts.json"
STATUS = "targets_status.csv"


def extract_values(text):
    """Pull every top-level JSON value (object/array) out of arbitrary text."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("```", 2)[1] if t.count("```") >= 2 else t
        if t.lstrip().lower().startswith("json"):
            t = t.lstrip()[4:]
    dec = json.JSONDecoder()
    i, vals, n = 0, [], len(t)
    while i < n:
        while i < n and t[i] not in "[{":
            i += 1
        if i >= n:
            break
        try:
            v, end = dec.raw_decode(t, i)
            vals.append(v)
            i = end
        except json.JSONDecodeError:
            i += 1
    return vals


def collect_items(vals):
    """Flatten decoded values into a flat item list (arrays expanded)."""
    items = []
    for v in vals:
        if isinstance(v, list):
            items.extend(x for x in v if isinstance(x, dict))
        elif isinstance(v, dict):
            items.append(v)
    return items


def get_facts(obj):
    for k in ("facts_json", "facts"):
        if isinstance(obj.get(k), dict):
            return obj[k]
    if "ownership_type" in obj and "company" in obj:   # obj IS the facts object
        return obj
    return None


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: _ingest_kimi_returns.py <return-file.json> [--check-links]")
    path = sys.argv[1]
    check_links = "--check-links" in sys.argv[2:]
    if not os.path.exists(path):
        raise SystemExit(f"return file not found: {path}")

    required = set(json.load(open(TEMPLATE)).keys())   # the 26 canonical keys
    items = collect_items(extract_values(open(path, encoding="utf-8", errors="replace").read()))

    targets = [o for o in items if get_facts(o) is not None or ("slug" in o and "overview_md" in o)]
    verifiers = {o.get("slug"): o for o in items if isinstance(o.get("verifier_results"), list)}
    if not targets:
        raise SystemExit("No target objects found in the return file (expected facts_json + overview_md).")

    today = datetime.date.today().isoformat()
    ts = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    written, skipped, invalid = [], [], []
    status_updates = {}   # slug -> (packet_path, facts_path)

    for obj in targets:
        facts = get_facts(obj) or {}
        slug = obj.get("slug") or facts.get("slug")
        overview = obj.get("overview_md", "")
        if not slug or not facts.get("company"):
            invalid.append({"slug": slug, "reason": "missing slug or company"})
            continue

        # validate against the canonical schema (write anyway; record drift)
        missing = sorted(required - set(facts))
        extra = sorted(set(facts) - required)

        # apply verifier-leg upgrades (best-effort: overwrite the named field with resolved_value)
        vr = verifiers.get(slug)
        if vr:
            for r in vr["verifier_results"]:
                fld, val = r.get("field"), r.get("resolved_value")
                if fld in facts and val not in (None, ""):
                    facts[fld] = val

        folder = os.path.join("6_targets", slug)
        os.makedirs(folder, exist_ok=True)
        exists = os.path.exists(os.path.join(folder, "overview.md"))
        suffix = f".candidate-{ts}" if exists else ""
        fpath = os.path.join(folder, f"facts.json{suffix}")
        opath = os.path.join(folder, f"overview.md{suffix}")
        json.dump(facts, open(fpath, "w"), indent=2, ensure_ascii=False)
        open(opath, "w").write(overview or f"# {facts.get('company','')} — packet (overview_md was empty)\n")
        if vr:
            json.dump(vr, open(os.path.join(folder, "_verifier.json"), "w"), indent=2, ensure_ascii=False)

        rec = {"slug": slug, "sources": len(facts.get("sources", [])),
               "missing_fields": missing, "extra_fields": extra,
               "data_confidence": facts.get("data_confidence", "")}
        if exists:
            skipped.append({**rec, "reason": "folder exists — wrote .candidate, status NOT flipped"})
        else:
            written.append(rec)
            status_updates[slug] = (opath, fpath)
        if missing:
            invalid.append({"slug": slug, "missing_fields": missing})

    # flip targets_status.csv for freshly-written slugs (idempotent; never touches existing folders)
    if status_updates and os.path.exists(STATUS):
        rows = list(csv.DictReader(open(STATUS)))
        fields = rows[0].keys() if rows else []
        for r in rows:
            if r.get("slug") in status_updates and str(r.get("researched", "0")) in ("0", "", "None"):
                opath, fpath = status_updates[r["slug"]]
                r["researched"], r["research_date"] = "1", today
                r["packet_path"], r["facts_path"] = opath, fpath
        with open(STATUS, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(fields))
            w.writeheader()
            w.writerows(rows)

    # optional, best-effort link liveness (off by default — network may be unavailable)
    link_report = "skipped (use --check-links)"
    if check_links:
        import urllib.request
        ok = bad = 0
        for obj in targets:
            for u in (get_facts(obj) or {}).get("sources", [])[:5]:
                if not str(u).startswith("http"):
                    continue
                try:
                    req = urllib.request.Request(u, method="HEAD")
                    urllib.request.urlopen(req, timeout=5)
                    ok += 1
                except Exception:
                    bad += 1
        link_report = f"{ok} live / {bad} dead (HEAD, first 5 sources/target)"

    rundir = os.path.join("5_working", "runs", today)
    os.makedirs(rundir, exist_ok=True)
    summary = {"ingested_file": path, "date": today, "targets_in_file": len(targets),
               "written": written, "skipped_existing": skipped, "validation_issues": invalid,
               "verifier_legs": len(verifiers), "link_check": link_report}
    json.dump(summary, open(os.path.join(rundir, "_ingest_summary.json"), "w"), indent=2)

    print(f"Ingested {path}")
    print(f"  written:          {len(written)}  -> 6_targets/<slug>/ + targets_status.csv flipped")
    print(f"  skipped existing: {len(skipped)}  (wrote .candidate-{ts}; status NOT flipped)")
    print(f"  validation issues:{len(invalid)}  (missing/extra facts.json fields — see summary)")
    print(f"  verifier legs:    {len(verifiers)}   link-check: {link_report}")
    print(f"  summary: {os.path.join(rundir, '_ingest_summary.json')}")
    if invalid:
        print("  NOTE: review validation_issues before promoting; partial facts were still written.")


if __name__ == "__main__":
    main()
