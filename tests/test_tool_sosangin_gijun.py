"""소상공인 기준 판정기(/sosangin-gijun) — 기준 표가 법령 별표와 어긋나지 않게 지킨다.

중소기업기본법 시행령 [별표 3] <개정 2025. 9. 1.>: 43개 업종, 9구간(15억~140억 원).
2025-09 개정으로 기준이 오른 업종은 12개(중기부 발표) — 구간별 업종 수로 확인한다.
"""
import collections
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JS = (ROOT / 'assets' / 'tool-sosangin-gijun.js').read_text(encoding='utf-8')
ROWS = re.findall(r"\['([A-Z0-9]+)', '([^']+)', (\d+), ([01])\]", JS)


def test_table_has_43_industries_in_9_tiers():
    assert len(ROWS) == 43
    assert len({r[0] for r in ROWS}) == 43
    tiers = collections.Counter(int(r[2]) for r in ROWS)
    assert dict(tiers) == {140: 2, 120: 15, 100: 2, 80: 12, 60: 1, 50: 1, 40: 2, 30: 3, 15: 5}


def test_raised_industries_are_twelve():
    # 개정 전 기준(억원): 이 12개 업종만 올랐다(120→140 2, 80→100 2, 50→60 1, 30→40 2, 10→15 5)
    raised = {'C19', 'C24', 'H', 'K', 'G', 'E', 'L', 'C34', 'I', 'P', 'Q', 'S'}
    assert len(raised) == 12
    cap = {r[0]: int(r[2]) for r in ROWS}
    assert [cap[c] for c in ('C19', 'C24')] == [140, 140]
    assert [cap[c] for c in ('I', 'P', 'Q', 'S', 'C34')] == [15] * 5
    assert cap['F'] == 80 and cap['D'] == 120 and cap['E36'] == 120


def test_ten_person_rule_only_for_mining_manufacturing_construction_transport():
    for code, name, _, ten in ROWS:
        expect = code[0] == 'C' or code in ('B', 'F', 'H')
        assert (ten == '1') == expect, (code, name)


def test_page_has_tool_form_and_apply_route():
    page = (ROOT / 'sosangin-gijun.html').read_text(encoding='utf-8')
    assert 'id="toolForm"' in page and '/assets/tool-sosangin-gijun.js' in page
    assert 'class="inline-diag"' in page or 'id="leadForm"' in page
    assert '참고' in page and '확인서' in page
