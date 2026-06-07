#!/usr/bin/env python3
"""Profile the corporate hierarchy in summit_targets.db to design consolidation."""
import sqlite3, os

DB = "2_database/summit_targets.db"

def main():
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    con = sqlite3.connect(DB)
    cur = con.cursor()
    # treat NULL and blank/whitespace as "absent"
    def present(c): return f"(\"{c}\" IS NOT NULL AND TRIM(\"{c}\")<>'')"
    total = cur.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    print(f"TOTAL establishment rows: {total:,}\n")

    print("=== Location Type distribution ===")
    for v, c in cur.execute('SELECT COALESCE(NULLIF(TRIM("Location Type"),\'\'),"(blank)"), COUNT(*) '
                            'FROM companies GROUP BY 1 ORDER BY 2 DESC').fetchall():
        print(f"  {c:>9,}  {v}")

    print("\n=== Firm or Individual ===")
    for v, c in cur.execute('SELECT COALESCE(NULLIF(TRIM("Firm or Individual"),\'\'),"(blank)"), COUNT(*) '
                            'FROM companies GROUP BY 1 ORDER BY 2 DESC').fetchall():
        print(f"  {c:>9,}  {v}")

    print("\n=== Hierarchy field fill rates ===")
    for col in ["Parent Company Name", "Parent IUSA Number", "Subsidiary IUSA Number",
                "Foreign Parent Flag", "Affiliated Locations", "Affiliated Records",
                "Corporate Employee Size Actual", "Corporate Sales Volume Actual",
                "Location Employee Size Actual", "IUSA Number"]:
        c = cur.execute(f'SELECT COUNT(*) FROM companies WHERE {present(col)}').fetchone()[0]
        print(f"  {c:>9,}  ({100*c/total:5.1f}%)  {col}")

    print("\n=== Distinct identities ===")
    for col in ["IUSA Number", "Parent IUSA Number", "Parent Company Name", "Company Name"]:
        d = cur.execute(f'SELECT COUNT(DISTINCT TRIM("{col}")) FROM companies WHERE {present(col)}').fetchone()[0]
        print(f"  {d:>9,}  distinct {col}")

    # Family key = parent company name if present else own company name
    fam = 'COALESCE(NULLIF(TRIM("Parent Company Name"),\'\'), NULLIF(TRIM("Company Name"),\'\'))'
    print("\n=== Top 25 parents by establishment count (family = Parent Co name, else Company name) ===")
    rows = cur.execute(f'SELECT {fam} AS k, COUNT(*) c FROM companies WHERE k IS NOT NULL '
                       'GROUP BY k ORDER BY c DESC LIMIT 25').fetchall()
    for k, c in rows:
        print(f"  {c:>7,}  {k}")

    print("\n=== Family-size histogram (locations per family) ===")
    cur.execute(f'CREATE TEMP TABLE fam AS SELECT {fam} AS k, COUNT(*) c FROM companies '
                'WHERE ' + fam.replace("AS k","") + ' IS NOT NULL GROUP BY k')
    buckets = [("1 (singletons)","c=1"),("2-5","c BETWEEN 2 AND 5"),
               ("6-20","c BETWEEN 6 AND 20"),("21-100","c BETWEEN 21 AND 100"),
               ("101-500","c BETWEEN 101 AND 500"),("500+","c>500")]
    nfam = cur.execute("SELECT COUNT(*) FROM fam").fetchone()[0]
    locs_total = cur.execute("SELECT SUM(c) FROM fam").fetchone()[0]
    print(f"  Distinct families: {nfam:,} (covering {locs_total:,} rows that have a family key)")
    for label, cond in buckets:
        nf, nl = cur.execute(f"SELECT COUNT(*), COALESCE(SUM(c),0) FROM fam WHERE {cond}").fetchone()
        print(f"    {label:>14}: {nf:>8,} families  |  {nl:>9,} establishments")

    print("\n=== Top 15 Primary NAICS (teaser for segmentation) ===")
    for code, desc, c in cur.execute(
        'SELECT TRIM("Primary NAICS"), TRIM("Primary NAICS Description"), COUNT(*) c '
        'FROM companies GROUP BY 1,2 ORDER BY c DESC LIMIT 15').fetchall():
        print(f"  {c:>8,}  {code}  {desc}")

    con.close()

if __name__ == "__main__":
    main()
