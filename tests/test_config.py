import pytest
from pydantic import ValidationError

from finfilings.config import CompaniesConfig, load_companies


def test_default_companies_config_loads():
    cfg = load_companies()
    assert {c.ticker for c in cfg.companies} >= {"PYPL", "AFRM", "COIN"}
    assert all(len(c.fiscal_years) >= 1 for c in cfg.companies)


def test_duplicate_tickers_rejected():
    c = {"ticker": "X", "name": "X Inc", "cik": 1, "fiscal_years": [2024]}
    with pytest.raises(ValidationError):
        CompaniesConfig.model_validate({"companies": [c, c]})


def test_ticker_is_uppercased():
    c = {"ticker": "pypl", "name": "P", "cik": 1, "fiscal_years": [2024]}
    assert CompaniesConfig.model_validate({"companies": [c]}).companies[0].ticker == "PYPL"
