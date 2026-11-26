"""스크롤 등장 효과가 화면보다 긴 요소를 숨긴 채 두지 않는다.

2026-11-26 /cases 의 403행 표가 빈 상자로 보였다 — 표 전체에 등장 효과를 걸었는데
'10% 보임' 기준은 화면의 10배보다 긴 요소에서 영영 채워지지 않는다.
"""
import pathlib

JS = (pathlib.Path(__file__).resolve().parents[1] / 'assets' / 'conversion.js').read_text(encoding='utf-8')


def test_long_tables_are_not_reveal_targets():
    assert 'else add(tb)' not in JS


def test_elements_taller_than_viewport_are_not_hidden():
    assert 'r.height <= vh * 0.9' in JS
