#!/usr/bin/env python3
"""Bulk-pull the bus/school-relevant slice of the FMCSA Company Census
(data.transportation.gov resource az4n-8mr2, anonymous SODA API) into SQLite
table `census_bus`. ~117k rows; paginated. Zero LLM tokens.
"""
import urllib.request, urllib.parse, json, sqlite3, os, time, sys

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BASE = "https://data.transportation.gov/resource/az4n-8mr2.json"
COLS = ["dot_number","legal_name","dba_name","phy_street","phy_city","phy_state","phy_zip",
        "phy_cnty","power_units","bus_units","ownschool_1_8","ownschool_9_15","ownschool_16",
        "ownbus_16","ownvan_1_8","ownvan_9_15","total_drivers","total_cdl","status_code",
        "safety_rating","safety_rating_date","recordable_crash_rate","add_date","mcs150_date",
        "company_officer_1","company_officer_2","phone","email_address","carrier_operation",
        "business_org_desc"]
WHERE = ("bus_units!='0' OR ownschool_16!='0' OR ownschool_9_15!='0' OR ownschool_1_8!='0' "
         "OR ownvan_9_15!='0' OR ownbus_16!='0'")
PAGE = 50000

def fetch(offset):
    q = {"$select": ",".join(COLS), "$where": WHERE, "$limit": PAGE,
         "$offset": offset, "$order": "dot_number"}
    url = BASE + "?" + urllib.parse.urlencode(q)
    for attempt in range(5):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "summit-screen/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.load(r)
        except Exception as e:
            print(f"  retry {attempt+1} (offset {offset}): {e}", flush=True)
            time.sleep(3 * (attempt + 1))
    sys.exit(f"FATAL: failed at offset {offset}")

def main():
    con = sqlite3.connect("2_database/summit_targets.db"); cur = con.cursor()
    cur.execute("DROP TABLE IF EXISTS census_bus")
    cur.execute(f"CREATE TABLE census_bus ({', '.join(f'\"{c}\" TEXT' for c in COLS)})")
    ins = f"INSERT INTO census_bus VALUES ({','.join('?'*len(COLS))})"
    total, offset = 0, 0
    while True:
        rows = fetch(offset)
        if not rows: break
        cur.executemany(ins, [[r.get(c) for c in COLS] for r in rows])
        total += len(rows); con.commit()
        print(f"[{time.strftime('%H:%M:%S')}] pulled {total:,}", flush=True)
        if len(rows) < PAGE: break
        offset += PAGE
    # indexes for matching
    cur.execute('CREATE INDEX idx_cb_state ON census_bus(phy_state)')
    con.commit()
    print(f"DONE: census_bus = {total:,} rows")
    con.close()

if __name__ == "__main__":
    main()
