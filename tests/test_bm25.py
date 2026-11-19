from finfilings.index.bm25 import BM25Index, tokenize


def chunk(cid, ticker, year, section, text):
    return {
        "chunk_id": cid,
        "ticker": ticker,
        "year": year,
        "section": section,
        "text": text,
        "embed_text": f"[{ticker} 10-K {year} | Item {section}] {text}",
    }


CHUNKS = [
    chunk("P-1", "PYPL", 2025, "7", "Transaction expense rate was 0.93 percent of volume."),
    chunk("P-2", "PYPL", 2025, "1A", "Fraud and chargebacks could harm our business."),
    chunk("C-1", "COIN", 2025, "1A", "Custody of crypto assets exposes us to theft and fraud."),
    chunk(
        "A-1",
        "AFRM",
        2025,
        "1",
        "Our loans are funded by warehouse facilities and capital markets.",
    ),
    chunk("A-2", "AFRM", 2025, "7", "Funding capacity grew during the year."),
    chunk("A-3", "AFRM", 2025, "7", "Revenue rose; gross merchandise volume increased."),
]


def test_tokenizer_keeps_numbers_whole():
    assert tokenize("Rate: 0.93%, loans of $1,234.5 million") == [
        "rate",
        "0.93",
        "loans",
        "of",
        "1,234.5",
        "million",
    ]


def test_exact_number_finds_the_right_chunk():
    hits = BM25Index(CHUNKS).search("0.93", k=3)
    assert [c["chunk_id"] for _, c in hits] == ["P-1"]


def test_filters_and_no_match():
    idx = BM25Index(CHUNKS)
    hits = idx.search("fraud", k=5, ticker="COIN")
    assert [c["chunk_id"] for _, c in hits] == ["C-1"]
    assert idx.search("zzzunseen", k=5) == []


def test_ticker_in_header_is_searchable():
    hits = BM25Index(CHUNKS).search("AFRM funding", k=1)
    assert hits[0][1]["ticker"] == "AFRM"
