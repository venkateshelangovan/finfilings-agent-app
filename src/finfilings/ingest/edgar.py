"""Minimal SEC EDGAR client: fetch a company's submissions and pick out its 10-K filings.

EDGAR fair-access rules: send a descriptive User-Agent (name + email) and stay under
~10 requests/second. We sleep between calls to stay far below that.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass

import requests
from dotenv import load_dotenv

SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik:010d}.json"
ARCHIVE_URL = "https://www.sec.gov/Archives/edgar/data/{cik}/{acc_nodash}/{doc}"
MIN_SECONDS_BETWEEN_REQUESTS = 0.2  # ~5 req/s, half the SEC limit


@dataclass(frozen=True)
class Filing:
    cik: int
    form: str
    accession: str
    filing_date: str
    report_date: str  # fiscal period end, e.g. 2024-12-31
    primary_document: str

    @property
    def fiscal_year(self) -> int:
        """Year in which the fiscal period ends (D-008)."""
        return int(self.report_date[:4])

    @property
    def url(self) -> str:
        return ARCHIVE_URL.format(
            cik=self.cik,
            acc_nodash=self.accession.replace("-", ""),
            doc=self.primary_document,
        )


def get_user_agent() -> str:
    load_dotenv()
    ua = os.environ.get("SEC_USER_AGENT", "").strip()
    if not ua or "example.com" in ua:
        raise RuntimeError("Set SEC_USER_AGENT in .env, e.g. 'Your Name you@domain.com'")
    return ua


def fetch_submissions(cik: int, user_agent: str | None = None) -> dict:
    time.sleep(MIN_SECONDS_BETWEEN_REQUESTS)
    resp = requests.get(
        SUBMISSIONS_URL.format(cik=cik),
        headers={"User-Agent": user_agent or get_user_agent()},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def find_10k_filings(submissions: dict) -> list[Filing]:
    """Original 10-K filings only (10-K/A amendments are skipped, see D-009).

    EDGAR stores recent filings as parallel arrays under filings.recent.
    """
    cik = int(submissions["cik"])
    recent = submissions["filings"]["recent"]
    filings = []
    for i, form in enumerate(recent["form"]):
        if form != "10-K":
            continue
        filings.append(
            Filing(
                cik=cik,
                form=form,
                accession=recent["accessionNumber"][i],
                filing_date=recent["filingDate"][i],
                report_date=recent["reportDate"][i],
                primary_document=recent["primaryDocument"][i],
            )
        )
    return filings
