from finfilings.ingest.qa import check_sections


def rec(item, n, ticker="AAA", year=2024, heading=None):
    head = heading or f"ITEM {item}. TITLE"
    return {
        "ticker": ticker,
        "year": year,
        "section": item,
        "n_chars": n,
        "text": head + "\n" + "x" * 10,
    }


GOOD = [rec("1", 6000), rec("1A", 20000), rec("7", 20000), rec("8", 60000)]


def test_good_filing_passes():
    assert check_sections(GOOD) == []


def test_missing_required_item_flagged():
    problems = check_sections([r for r in GOOD if r["section"] != "1A"])
    assert any("missing Item 1A" in p for p in problems)


def test_short_section_flagged():
    problems = check_sections([rec("1", 100)] + GOOD[1:])
    assert any("Item 1 too short" in p for p in problems)


def test_wrong_heading_flagged():
    bad = [rec("1", 6000, heading="ITEM 2. PROPERTIES")] + GOOD[1:]
    assert any("does not start with its heading" in p for p in check_sections(bad))


def test_financials_may_live_in_item_15():
    recs = [r for r in GOOD if r["section"] != "8"] + [rec("8", 300), rec("15", 200000)]
    assert check_sections(recs) == []


def test_oversized_section_flagged():
    others = [rec("1", 6000, year=y) for y in (2021, 2022, 2023)]
    problems = check_sections(others + [rec("1", 600000)] + GOOD[1:])
    assert any("peers' median" in p for p in problems)
