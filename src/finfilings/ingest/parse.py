"""Step 2.1: turn a raw 10-K HTML file into clean plain text (no section splitting yet).

Tables are kept as lines of ' | '-joined cells between [TABLE] and [/TABLE] markers so a later
step can chunk them separately instead of flattening them into garbled prose.
Run:  uv run python -m finfilings.ingest.parse
"""

from __future__ import annotations

import re
import warnings

from bs4 import BeautifulSoup, NavigableString, XMLParsedAsHTMLWarning

from finfilings.config import REPO_ROOT
from finfilings.ingest.download import raw_path, read_manifest

# 10-Ks are XHTML; the HTML parser handles them fine, so silence the noisy warning.
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

TEXT_DIR = REPO_ROOT / "data" / "processed" / "text"
BLOCK_TAGS = ["p", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6"]
PAGE_NUMBER = re.compile(r"^(page\s+)?\d{1,3}(\s+of\s+\d{1,3})?$", re.I)
TOC_HEADER = re.compile(r"^table of contents$", re.I)


def _table_to_text(table) -> str:
    # Inner tables are converted first (see html_to_text). If one is inside this table, this
    # one is only a layout wrapper: keep the inner content and do not add markers again.
    if "[TABLE]" in table.get_text():
        cells = (c.get_text().strip() for c in table.find_all(["td", "th"]))
        return "\n".join(c for c in cells if c)
    lines = []
    for tr in table.find_all("tr"):
        cells = [re.sub(r"\s+", " ", c.get_text("")).strip() for c in tr.find_all(["td", "th"])]
        cells = [c for c in cells if c and c not in {"$", ")", "%"}]
        if cells:
            lines.append(" | ".join(cells))
    return "[TABLE]\n" + "\n".join(lines) + "\n[/TABLE]" if lines else ""


def html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style", "ix:header"]):
        tag.decompose()
    for tag in soup.find_all(style=re.compile(r"display\s*:\s*none", re.I)):
        tag.decompose()
    for table in reversed(soup.find_all("table")):
        table.replace_with(NavigableString("\n" + _table_to_text(table) + "\n"))
    for br in soup.find_all("br"):
        br.replace_with(NavigableString("\n"))
    for tag in soup.find_all(BLOCK_TAGS):
        tag.append(NavigableString("\n"))
    text = soup.get_text().replace("\xa0", " ")
    lines = []
    for raw in text.splitlines():
        line = re.sub(r"[ \t]+", " ", raw).strip()
        if PAGE_NUMBER.match(line) or TOC_HEADER.match(line):
            continue
        lines.append(line)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"


def main() -> None:
    TEXT_DIR.mkdir(parents=True, exist_ok=True)
    for row in read_manifest():
        src = raw_path(row)
        text = html_to_text(src.read_text(encoding="utf-8", errors="ignore"))
        out = TEXT_DIR / f"{row['ticker']}_{row['fiscal_year']}.txt"
        out.write_text(text, encoding="utf-8")
        n_tables = text.count("[TABLE]")
        print(f"{out.name}: {len(text):,} chars, {text.count(chr(10)):,} lines, {n_tables} tables")


if __name__ == "__main__":
    main()
