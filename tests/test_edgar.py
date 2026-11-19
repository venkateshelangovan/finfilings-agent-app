from finfilings.ingest.edgar import find_10k_filings

FAKE = {
    "cik": "1633917",
    "filings": {
        "recent": {
            "form": ["10-Q", "10-K", "10-K/A", "10-K"],
            "accessionNumber": [
                "0001-25-000001",
                "0001-25-000002",
                "0001-25-000003",
                "0001-24-000004",
            ],
            "filingDate": ["2025-05-01", "2025-02-05", "2025-03-01", "2024-02-06"],
            "reportDate": ["2025-03-31", "2024-12-31", "2024-12-31", "2023-12-31"],
            "primaryDocument": ["q.htm", "pypl-20241231.htm", "a.htm", "pypl-20231231.htm"],
        }
    },
}


def test_only_original_10k_kept():
    filings = find_10k_filings(FAKE)
    assert [f.accession for f in filings] == ["0001-25-000002", "0001-24-000004"]


def test_fiscal_year_and_url():
    f = find_10k_filings(FAKE)[0]
    assert f.fiscal_year == 2024
    assert f.url == (
        "https://www.sec.gov/Archives/edgar/data/1633917/000125000002/pypl-20241231.htm"
    )
