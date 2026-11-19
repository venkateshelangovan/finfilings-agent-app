"""Step 2.3: pull exact financial numbers from SEC's XBRL 'companyfacts' API.

These numbers feed the agent's facts tool later, so numeric questions are answered from
structured data instead of text. Output: data/processed/facts.csv
Run:  uv run python -m finfilings.ingest.xbrl
"""

from __future__ import annotations

import csv
import time
from datetime import date

import requests

from finfilings.config import REPO_ROOT, load_companies
from finfilings.ingest.download import read_manifest
from finfilings.ingest.edgar import MIN_SECONDS_BETWEEN_REQUESTS, get_user_agent

FACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
FACTS_FILE = REPO_ROOT / "data" / "processed" / "facts.csv"
COLUMNS = [
    "ticker",
    "fiscal_year",
    "metric",
    "value",
    "unit",
    "source_tag",
    "period_end",
    "accession",
]

# metric -> us-gaap tags to try, in order. Companies tag the same idea differently,
# so the first tag that has a value for the filing wins and is recorded in source_tag.
METRICS: dict[str, list[str]] = {
    "revenue": ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "operating_income": ["OperatingIncomeLoss"],
    "provision_for_credit_losses": [
        "ProvisionForCreditLosses",
        "ProvisionForLoanLeaseAndOtherLosses",
        "ProvisionForLoanAndLeaseLosses",
        "ProvisionForDoubtfulAccounts",
    ],
    "total_assets": ["Assets"],
    "total_liabilities": ["Liabilities"],
    "stockholders_equity": ["StockholdersEquity"],
}
FULL_YEAR_DAYS = (340, 380)


def fetch_companyfacts(cik: int, user_agent: str) -> dict:
    time.sleep(MIN_SECONDS_BETWEEN_REQUESTS)
    resp = requests.get(FACTS_URL.format(cik=cik), headers={"User-Agent": user_agent}, timeout=60)
    resp.raise_for_status()
    return resp.json()


def _entries(facts: dict, tag: str) -> list[dict]:
    node = facts.get("facts", {}).get("us-gaap", {}).get(tag)
    return node["units"].get("USD", []) if node else []


def period_end_for(facts: dict, accession: str) -> str | None:
    """A 10-K also reports prior years, so find this filing's own fiscal year end:
    the latest 'end' date among all facts tagged with its accession number."""
    ends = [
        e["end"]
        for node in facts.get("facts", {}).get("us-gaap", {}).values()
        for e in node["units"].get("USD", [])
        if e.get("accn") == accession
    ]
    return max(ends) if ends else None


def _is_full_year(entry: dict) -> bool:
    if "start" not in entry:  # point-in-time value (balance sheet)
        return True
    days = (date.fromisoformat(entry["end"]) - date.fromisoformat(entry["start"])).days
    return FULL_YEAR_DAYS[0] <= days <= FULL_YEAR_DAYS[1]


def extract_facts(facts: dict, ticker: str, fiscal_year: int, accession: str) -> list[list]:
    end = period_end_for(facts, accession)
    if end is None:
        return []
    rows = []
    for metric, tags in METRICS.items():
        for tag in tags:
            hit = next(
                (
                    e
                    for e in _entries(facts, tag)
                    if e.get("accn") == accession and e["end"] == end and _is_full_year(e)
                ),
                None,
            )
            if hit:
                rows.append([ticker, fiscal_year, metric, hit["val"], "USD", tag, end, accession])
                break
    return rows


def main() -> None:
    ua = get_user_agent()
    by_ticker = {c.ticker: c for c in load_companies().companies}
    rows: list[list] = []
    cache: dict[str, dict] = {}
    for m in read_manifest():
        t = m["ticker"]
        if t not in cache:
            cache[t] = fetch_companyfacts(by_ticker[t].cik, ua)
        got = extract_facts(cache[t], t, int(m["fiscal_year"]), m["accession"])
        missing = [k for k in METRICS if k not in {r[2] for r in got}]
        print(f"{t} FY{m['fiscal_year']}: {len(got)}/{len(METRICS)} metrics, missing: {missing}")
        rows.extend(got)
    with open(FACTS_FILE, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        w.writerows(rows)
    print(f"Wrote {len(rows)} facts to {FACTS_FILE}")


if __name__ == "__main__":
    main()
