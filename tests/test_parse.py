from finfilings.ingest.parse import html_to_text

HTML = """
<html><body>
<ix:header><div>HIDDEN XBRL</div></ix:header>
<div style="display:none">secret</div>
<p>Table of Contents</p>
<p>Item 1. Business</p>
<p>We&nbsp;process   payments.<br/>Second line.</p>
<p>42</p>
<table>
  <tr><td>Revenue</td><td>$</td><td>1,000</td></tr>
  <tr><td></td><td></td></tr>
  <tr><td>Net income</td><td>$</td><td>(50</td><td>)</td></tr>
</table>
<script>var x=1;</script>
</body></html>
"""


def test_removes_noise():
    t = html_to_text(HTML)
    for bad in ["HIDDEN", "secret", "var x", "Table of Contents"]:
        assert bad not in t
    assert "\n42\n" not in t


def test_text_and_line_breaks():
    t = html_to_text(HTML)
    assert "We process payments.\nSecond line." in t
    assert "Item 1. Business" in t


def test_table_kept_as_rows():
    t = html_to_text(HTML)
    assert "[TABLE]\nRevenue | 1,000\nNet income | (50\n[/TABLE]" in t


def test_table_cell_does_not_split_words_across_spans():
    t = html_to_text("<table><tr><td>Disagreements w<span>ith</span> Accountants</td></tr></table>")
    assert "Disagreements with Accountants" in t
