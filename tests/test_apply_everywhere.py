"""어느 페이지에서도 바로 신청 — 하단 바 · 페이지 끝 폼 · 중간 버튼 · 그 자리 신청 창.

설계: docs/superpowers/specs/2026-10-04-apply-everywhere-design.md
계획: docs/superpowers/plans/2026-10-04-apply-everywhere.md
전환 동작은 브라우저로 확인한다(규격 10절). 실제 신청 API 로는 아무것도 보내지 않는다.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import inline_form  # noqa: E402

BRAND = '#234780'   # 신청 버튼 한 색 (대표 결정 2026-10-04)
SUBMIT_RULE = re.compile(r'\.inline-diag button\[type=submit\]\{[^}]*\}')


def served_html():
    sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    out = []
    for path in re.findall(r'<loc>https://bmaker\.kr([^<]*)</loc>', sm):
        p = path.strip('/')
        for f in ([ROOT / 'index.html'] if not p else [ROOT / f'{p}.html', ROOT / p / 'index.html']):
            if f.exists():
                out.append((path or '/', f))
                break
    return out


# ── Task 1: 신청 버튼 한 색 ─────────────────────────────────────────────────

def test_inline_form_submit_color_is_brand_blue_in_source():
    rule = SUBMIT_RULE.search(inline_form.CSS).group(0)
    assert BRAND in rule and '#2454bc' not in rule, rule


def test_every_inline_form_page_uses_the_one_apply_color():
    pages = [(p, f) for p, f in served_html() if 'class="inline-diag"' in f.read_text(encoding='utf-8')]
    assert len(pages) >= 76, len(pages)
    wrong = []
    for path, f in pages:
        rules = SUBMIT_RULE.findall(f.read_text(encoding='utf-8'))
        if not rules or any(BRAND not in r or '#2454bc' in r for r in rules):
            wrong.append(path)
    assert not wrong, wrong


# ── Task 2: 인라인 폼 템플릿은 inline_form.py 가 정본, conversion.js 는 build_lastmod 가 동기화 ─────

def test_conversion_js_carries_the_inline_form_template_from_inline_form_py():
    import sync_inline_form_js as sync
    js = (ROOT / 'assets' / 'conversion.js').read_text(encoding='utf-8')
    block = sync.BLOCK.search(js)
    assert block, 'conversion.js 에 @inline-form 구간이 없다'
    # 작업 사본은 CRLF 일 수 있다(autocrlf) — 줄바꿈을 맞춘 뒤 비교한다
    assert block.group(0).replace('\r\n', '\n') == sync.render(), 'inline_form.py 를 고친 뒤 python tools/build_lastmod.py 를 돌리지 않았다'


def test_template_follows_the_source_when_it_changes():
    import sync_inline_form_js as sync
    original = inline_form.TITLE_GENERAL
    try:
        inline_form.TITLE_GENERAL = '바뀐 제목'
        assert '바뀐 제목' in sync.render()
    finally:
        inline_form.TITLE_GENERAL = original
    js = (ROOT / 'assets' / 'conversion.js').read_text(encoding='utf-8')
    assert sync.replace(js) == js, '동기화를 두 번 해도 같아야 한다(churn 0)'
