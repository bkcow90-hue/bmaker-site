"""실행 사례 원장 무결성 — 페이지·CSV·증빙 링크가 같은 건수를 말하는지, 금지 표현이 없는지 고정한다."""
import csv, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def test_ledger_counts_align():
    html = (ROOT/"cases.html").read_text(encoding="utf-8")
    rows = html.count('<tr id="row-')
    cases = html.count('class="case"')
    figs = html.count("<figure")
    ev_links = html.count('">보기</a>')
    with open(ROOT/"data"/"cases.csv", encoding="utf-8-sig") as f:
        n = sum(1 for _ in csv.DictReader(f))
    assert rows == cases == n >= 1, (rows, cases, n)
    assert figs == ev_links, (figs, ev_links)
    for m in re.findall(r'src="(assets/cases/[^"]+)"', html):
        assert (ROOT/m).exists(), m
def test_ledger_compliance_wording():
    for name in ("cases.html", "stats.html", "llms-full.txt"):
        text = (ROOT/name).read_text(encoding="utf-8")
        assert "갚" not in text, name
        assert not re.search(r"보장(?!하지)", text.replace("결과를 보장하지","").replace("보장할 수 없","")), name
        assert not re.search(r"성공보수[^.\n]{0,20}\d+\s*%", text), name
def test_new_pages_have_dataset_and_org_ref():
    for name in ("cases.html", "stats.html"):
        html = (ROOT/name).read_text(encoding="utf-8")
        blocks = [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">\s*(.*?)\s*</script>', html, re.S)]
        ds = [b for b in blocks if b.get("@type") == "Dataset"]
        assert ds and ds[0]["creator"]["@id"] == "https://bmaker.kr/#org", name
