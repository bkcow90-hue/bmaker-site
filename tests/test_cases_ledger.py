"""실행 사례 원장 무결성 — 페이지·CSV·증빙 링크가 같은 건수를 말하는지, 금지 표현이 없는지 고정한다."""
import csv, json, re
import sys
from html.parser import HTMLParser
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent

def test_home_case_renderer_keeps_each_fixture_and_escapes_markup():
    sys.path.insert(0, str(ROOT / "tools"))
    from build_cases import render_home_case_cards, won2
    fixtures = [{
        "사례ID": f"T{i}", "실행 연월": f"2026-0{i}",
        "지역(시도)": f"지역{i}", "업종": '제조 <script>alert(1)</script> & 유통',
        "기관": f'기관{i} "검토"', "사업 형태": "개인사업자",
        "업력(년)": str(i + 2), "자금명": f"자금{i}",
        "실행 금액(만원)": str(i * 3100),
    } for i in range(1, 4)]
    rendered = render_home_case_cards(fixtures)
    cards = re.findall(r'<article\b.*?</article>', rendered, re.S)
    assert len(cards) == 3
    assert '<script>' not in rendered and '&lt;script&gt;' in rendered
    class TextParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.text = ""
        def handle_data(self, data):
            self.text += data
    for card, row in zip(cards, fixtures):
        parser = TextParser()
        parser.feed(card)
        assert f'href="/cases#case-{row["사례ID"]}"' in card
        for field in ("기관", "업종", "지역(시도)", "사업 형태", "자금명"):
            assert row[field] in parser.text
        assert f'업력 {row["업력(년)"]}년' in parser.text
        assert row["실행 연월"].replace("-", ".") in parser.text
        assert won2(row["실행 금액(만원)"]) in parser.text
def test_home_case_selection_includes_both_forms_without_duplicates():
    sys.path.insert(0, str(ROOT / "tools"))
    from build_cases import select_home_cases
    fixtures = [
        {"사례ID": "I1", "실행 연월": "2026-08", "사업 형태": "개인"},
        {"사례ID": "I2", "실행 연월": "2026-09", "사업 형태": "개인"},
        {"사례ID": "C1", "실행 연월": "2026-01", "사업 형태": "법인"},
        {"사례ID": "C2", "실행 연월": "2026-02", "사업 형태": "법인"},
    ]
    assert [r["사례ID"] for r in select_home_cases(fixtures)] == ["I2", "C2", "C1"]
    assert [r["사례ID"] for r in select_home_cases(fixtures[:2])] == ["I2", "I1"]
    assert select_home_cases([]) == []
    assert len({r["사례ID"] for r in select_home_cases(fixtures[:3])}) == 3

def test_ledger_counts_align():
    html = (ROOT/"cases.html").read_text(encoding="utf-8")
    rows = html.count('<tr id="row-')
    cases = html.count('class="case"')
    figs = html.count("<figure")
    ev_links = html.count('>증빙 보기</a>')
    with open(ROOT/"data"/"cases.csv", encoding="utf-8-sig") as f:
        n = sum(1 for _ in csv.DictReader(f))
    assert rows == cases == n >= 1, (rows, cases, n)
    assert figs == ev_links, (figs, ev_links)
    for m in re.findall(r'src="(assets/cases/[^"]+)"', html):
        assert (ROOT/m).exists(), m
def test_home_evidence_and_card_anchors_match_source():
    home = (ROOT / "index.html").read_text(encoding="utf-8")
    cases = (ROOT / "cases.html").read_text(encoding="utf-8")
    with (ROOT / "data/cases.source.csv").open(encoding="utf-8-sig") as f:
        rows = {r["사례ID"]: r for r in csv.DictReader(f)}
    for key in re.findall(r'href="/cases#case-([^\"]+)"', home):
        assert key in rows
        assert f'id="case-{key}"' in cases
    matches = re.findall(r'<a href="/cases#case-([^\"]+)"><img src="assets/cases/thumb/([^\"]+)"', home)
    # 홈 증빙 4장 이상 — 2026-09-21 개편에서 6→2장으로 근거 없이 줄었던 것을 복원(대표 2026-10-02). 축소는 대표 승인 필요(규격 4-1)
    assert len(matches) >= HOME_EVIDENCE_MIN, f"홈 증빙 {len(matches)}장 — {HOME_EVIDENCE_MIN}장 이상이어야 합니다"
    for key, thumbnail in matches:
        assert Path(thumbnail).stem == Path(rows[key]["증빙 파일"]).stem, f"{key}: 썸네일과 원장 증빙 파일 불일치"
        kind = EVIDENCE_KIND.get(Path(thumbnail).stem)
        assert kind == "기관 안내문", f"{key} {thumbnail}: 홈에는 기관 안내문·약정 캡처만 — 유형 {kind or '미분류'}"


HOME_EVIDENCE_MIN = 4
# 증빙 캡처 유형(눈으로 확인한 것만 등록, 2026-10-02). 홈에 새 캡처를 올리려면 먼저 여기 "기관 안내문"으로 등록한다.
# "계산서·송금" = 수수료 계산서 발급·송금 대화 — /cases 공개는 유지하되 홈에는 싣지 않는다(대표 2026-10-02).
EVIDENCE_KIND = {
    "ev-2026-07-sojingong-sinyongchwiyak-2000": "기관 안내문",   # E13 소진공 대출실행 안내
    "ev-2026-09-jaedan-3000": "기관 안내문",                     # E1 경남신용보증재단 보증 승인 안내
    "ev-E1-sojingong-jaedojeon-5300": "기관 안내문",             # E9 소진공 대출약정내역 안내
    "ev-E2-sojingong-sinyongchwiyak-2000": "기관 안내문",        # E18 소진공 약정 안내 화면
    "ev-2026-03-jaedan-2000": "계산서·송금",                     # E17
    "ev-2026-10-jaedan-4000": "계산서·송금",                     # E2
}


def test_home_evidence_rule_rejects_billing_capture():
    """유형 검사가 실제로 계산서·송금 캡처를 걸러내는지 고정."""
    assert EVIDENCE_KIND["ev-2026-03-jaedan-2000"] != "기관 안내문"
    assert EVIDENCE_KIND["ev-2026-10-jaedan-4000"] != "기관 안내문"
    assert EVIDENCE_KIND.get("ev-E3-sojingong-4000") is None   # 미분류는 홈 금지

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
