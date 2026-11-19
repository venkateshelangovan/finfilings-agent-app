from finfilings.ingest.sections import find_headings, split_sections

TEXT = """Item 1. | Business | 4
Item 1A. | Risk Factors | 14
Item 7. | MD&A | 32
ITEM 1. BUSINESS
We do payments.
Item 1A. Risk Factors
Fraud is a risk.
See Item 7 of this report for details, which is a long sentence that is not a heading at all.
ITEM 1B. UNRESOLVED STAFF COMMENTS
None.
ITEM 7. MANAGEMENT'S DISCUSSION
Revenue grew.
ITEM 15. EXHIBITS
Financials here.
"""


def test_toc_lines_skipped():
    items = [item for _, item in find_headings(TEXT.splitlines())]
    assert items == ["1", "1A", "1B", "7", "15"]


def test_sections_split_at_next_heading():
    s = split_sections(TEXT)
    assert s["1"]["text"] == "ITEM 1. BUSINESS\nWe do payments."
    assert "Fraud is a risk." in s["1A"]["text"]
    assert "UNRESOLVED" not in s["1A"]["text"]  # 1B is the boundary, not kept
    assert "Revenue grew." in s["7"]["text"]
    assert "7A" not in s
