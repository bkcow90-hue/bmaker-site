"""중소기업 기준 판정기(/jungsogieop-gijun) — 기준 표가 법령 별표와 어긋나지 않게 지킨다.

중소기업기본법 시행령 [별표 1] <개정 2025. 9. 1.>: 44개 업종, 7구간(400억~1,800억 원).
2025-09 개정으로 기준이 오른 업종은 16개(중기부 발표). 소기업 값은 /sosangin-gijun 표와 같아야 한다.
"""
import collections
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'assets' / 'tool-jungsogieop-gijun.js').read_text(encoding='utf-8')
ROWS = re.findall(r"\['([A-Z0-9]+)', '([^']+)', (\d+), (\d+)\]", JS)
SMALL = {c: int(v) for c, _, v, _ in re.findall(
    r"\['([A-Z0-9]+)', '([^']+)', (\d+), ([01])\]",
    (ROOT / 'assets' / 'tool-sosangin-gijun.js').read_text(encoding='utf-8'))}


def test_table_has_44_industries_in_7_tiers():
    assert len(ROWS) == 44
    assert len({r[0] for r in ROWS}) == 44
    tiers = collections.Counter(int(r[2]) for r in ROWS)
    assert dict(tiers) == {1800: 3, 1500: 3, 1200: 9, 1000: 12, 800: 7, 600: 5, 400: 5}


def test_raised_industries_are_sixteen():
    cap = {r[0]: int(r[2]) for r in ROWS}
    # 개정 전 기준에서 오른 16개: 1,500→1,800 3 · 1,000→1,200 9 · 800→1,000 3 · 600→800 1
    assert [cap[c] for c in ('C17', 'C24', 'C28')] == [1800] * 3
    assert [cap[c] for c in ('C10', 'C20', 'C22', 'C25', 'C29', 'C30', 'C31', 'F', 'G')] == [1200] * 9
    assert [cap[c] for c in ('C33', 'H', 'J')] == [1000] * 3
    assert cap['N'] == 800
    assert 3 + 9 + 3 + 1 == 16


def test_small_caps_match_sosangin_tool():
    for code, name, _, small in ROWS:
        assert SMALL['N' if code == 'N76' else code] == int(small), (code, name)


def test_page_has_tool_form_and_apply_route():
    page = (ROOT / 'jungsogieop-gijun.html').read_text(encoding='utf-8')
    assert 'id="toolForm"' in page and '/assets/tool-jungsogieop-gijun.js' in page
    assert 'class="inline-diag"' in page
    assert '참고' in page and '확인서' in page
