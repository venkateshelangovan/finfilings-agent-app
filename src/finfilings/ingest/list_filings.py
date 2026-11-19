"""Step 1.1: ask EDGAR which 10-Ks exist for our companies and write data/manifest.csv.

Nothing is downloaded here. Run:  uv run python -m finfilings.ingest.list_filings
Check the printed company names to confirm each CIK is the right company.
"""

from __future__ import annotations

import csv

from finfilings.config import REPO_ROOT, load_companies
from finfilings.ingest.edgar import fetch_submissions, find_10k_filings, get_user_agent

MANIFEST = REPO_ROOT / "data" / "manifest.csv"
COLUMNS = ["ticker", "cik", "fiscal_year", "accession", "url", "filed_date", "sha256"]


def main() -> None:
    ua = get_user_agent()
    rows = []
    for company in load_companies().companies:
        subs = fetch_submissions(company.cik, ua)
        print(f"{company.ticker}: CIK {company.cik} -> EDGAR says '{subs['name']}'")
        available = {f.fiscal_year: f for f in find_10k_filings(subs)}
        for year in company.fiscal_years:
            f = available.get(year)
            if f is None:
                print(f"  FY{year}: NOT FOUND (have {sorted(available)})")
                continue
            print(f"  FY{year}: {f.accession} period {f.report_date} filed {f.filing_date}")
            rows.append([company.ticker, company.cik, year, f.accession, f.url, f.filing_date, ""])
    with open(MANIFEST, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(COLUMNS)
        writer.writerows(rows)
    print(f"Wrote {len(rows)} rows to {MANIFEST}")


if __name__ == "__main__":
    main()
