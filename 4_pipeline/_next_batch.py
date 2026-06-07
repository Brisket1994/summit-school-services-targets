#!/usr/bin/env python3
"""Prepare the next night's batch: pick the next N un-researched A-list targets
(from targets_status.csv) and write them with full research fields to
5_working/inputs/_night_batch.json for the research workflow to consume.

Usage: python3 4_pipeline/_next_batch.py [N]   (default N=100)
Idempotent: only researched=0 targets are selected, so reruns advance the queue.
"""
import csv, json, os, sys
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
N = int(sys.argv[1]) if len(sys.argv) > 1 else 100

status = list(csv.DictReader(open("targets_status.csv")))
queue = {json.loads(l)["slug"]: json.loads(l) for l in open("5_working/inputs/alist_queue.jsonl")}
pending = [r for r in status if str(r.get("researched","0")) in ("0","","None")]
batch_rows = pending[:N]
batch = [queue[r["slug"]] for r in batch_rows if r["slug"] in queue]

os.makedirs("5_working/inputs", exist_ok=True)
json.dump(batch, open("5_working/inputs/_night_batch.json", "w"))
done = len(status) - len(pending)
print(f"A-list total {len(status)} | researched {done} | pending {len(pending)}")
print(f"This batch: {len(batch)} targets (ranks {batch_rows[0]['a_rank'] if batch_rows else '-'}"
      f"..{batch_rows[-1]['a_rank'] if batch_rows else '-'}) -> 5_working/inputs/_night_batch.json")
if not batch:
    print("Nothing pending — A-list research complete.")
