from finfilings.ingest.xbrl import extract_facts, find_tags, period_end_for

ACC = "0001-25-000002"
OLD = "0001-24-000001"


def _e(val, end, accn, start=None):
    d = {"val": val, "end": end, "accn": accn}
    if start:
        d["start"] = start
    return d


FACTS = {
    "facts": {
        "us-gaap": {
            # 'Revenues' absent -> falls back to second tag
            "RevenueFromContractWithCustomerExcludingAssessedTax": {
                "units": {
                    "USD": [
                        _e(900, "2023-12-31", ACC, "2023-01-01"),  # prior year, same filing
                        _e(1000, "2024-12-31", ACC, "2024-01-01"),  # what we want
                        _e(250, "2024-12-31", ACC, "2024-10-01"),  # a quarter, not full year
                    ]
                }
            },
            "Assets": {
                "units": {"USD": [_e(5000, "2024-12-31", ACC), _e(4000, "2023-12-31", OLD)]}
            },
        }
    }
}


def test_period_end_is_latest_end_for_accession():
    assert period_end_for(FACTS, ACC) == "2024-12-31"


def test_extract_picks_current_full_year_and_falls_back_on_tag():
    rows = {r[2]: r for r in extract_facts(FACTS, "PYPL", 2024, ACC)}
    assert rows["revenue"][3] == 1000
    assert rows["revenue"][5] == "RevenueFromContractWithCustomerExcludingAssessedTax"
    assert rows["total_assets"][3] == 5000
    assert "net_income" not in rows


def test_find_tags_searches_company_extensions_too():
    facts = {
        "facts": {
            "us-gaap": {"Assets": {"units": {"USD": [{}]}}},
            "afrm": {"ProvisionForCreditLosses": {"units": {"USD": [{}, {}]}}},
        }
    }
    assert find_tags(facts, "provision") == [("afrm", "ProvisionForCreditLosses", 2)]
