import subprocess
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

def test_conversion_delivery_contract():
    subprocess.run(['node', 'tests/test_conversion.mjs'], cwd=ROOT, check=True, capture_output=True, text=True)

def test_only_one_form_precedes_company_introduction():
    source = (ROOT / 'index.html').read_text(encoding='utf-8')
    assert source.count('id="leadForm"') == 1
    assert source.count('id="apply"') == 1
    assert source.index('id="leadForm"') < source.index('id="about"')
    assert 'class="case" aria-hidden="true"' not in source

def test_ledger_heading_matches_public_rows():
    source = (ROOT / 'cases.html').read_text(encoding='utf-8')
    count = source.count('<tr id="row-')
    assert f'실행 기록 (전체 {count}건)' in source

def test_budget_exhaustion_cannot_be_inferred_from_calendar():
    import sys
    sys.path.insert(0, str(ROOT / 'tools'))
    from build_funds import status_of
    assert status_of({'접수 시작일':'2020-01-01','접수 마감일':'예산 소진 시','접수 상태':'회차'})[0] == 'check'
    assert status_of({'접수 시작일':'','접수 마감일':'','접수 상태':'상시'})[0] == 'check'
    assert status_of({'접수 시작일':'2020-01-01','접수 마감일':'2099-12-31','접수 상태':'마감'})[0] == 'closed'


# ── CTA 문구·색 통일 (규격 4절, 2026-09-28 대표 지시) ──────────────────────
# 신청 CTA 는 전 사이트 "무료 진단 신청"·브랜드 블루 하나로 맞춘다. 카카오 옐로는 실제
# 카카오 이동 버튼에만 남긴다. 54곳·49곳으로 흩어져 있던 문구가 다시 갈라지는 것을 막는다.
# '무료 상담 신청하기' — 홈 폼 제출 버튼(허브 2장이 복사, 4분기 페이지가 정적 복사)에 남아 있었다.
# 9/28 통일 때 이 목록이 옛 헤더·고정바 문구 둘만 담아 제출 버튼 문구를 검사하지 못했다.
RETIRED_CTA = ['내 조건 무료 상담 신청', '무료 진단 예약하기', '무료 상담 신청하기']


def test_no_retired_cta_wording_anywhere():
    """폐기한 CTA 문구가 산출물·빌더·템플릿 어디에도 남아 있지 않아야 한다."""
    targets = (list(ROOT.glob('*.html')) + list(ROOT.glob('industry/*.html'))
               + list(ROOT.glob('tools/build_*.py')) + [ROOT / 'tools/cases_tpl.html'])
    hits = []
    for path in targets:
        body = path.read_text(encoding='utf-8')
        for bad in RETIRED_CTA:
            if bad in body:
                hits.append(f'{path.name}: {bad}')
    assert not hits, hits


def test_header_and_sticky_cta_say_free_diagnosis():
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    assert '<a class="nav-cta nav-cta-book" href="#apply" data-cta-location="header">무료 진단 신청</a>' in home
    assert '<a class="sc-apply" href="#apply" data-cta-location="mobile_sticky">무료 진단 신청</a>' in home


def test_form_success_message_matches_standard():
    """규격 4절 확정 문구. 코드에 하드코딩돼 있으므로 문자열로 고정한다."""
    js = (ROOT / 'assets/conversion.js').read_text(encoding='utf-8')
    assert ('신청이 접수됐습니다. 평일 09:00~18:00 중 정하신 시간대에 전화드리겠습니다. '
            '급한 문의는 1666-2425로 연락해 주세요.') in js
    # 버튼 문구는 폼마다 다르므로 하드코딩하지 않는다
    assert "'무료 상담 신청하기'" not in js


# ── 비용 고지 위치 (규격 1절·4절, 2026-09-28 대표 승인) ─────────────────────
# 비용·성과 보수 고지는 신청 폼에서 빼고 진단 섹션·FAQ에만 둔다. 폼에서 뺀 뒤 사이트에서
# 고지가 통째로 사라지지 않도록, 폼 밖 두 곳에 남아 있는지도 함께 고정한다.
import re as _re


def _section(html, start_marker):
    i = html.index(start_marker)
    return html[html.rfind('<section', 0, i):html.index('</section>', i)]


def _form(html):
    i = html.index('id="leadForm"')
    return html[html.rfind('<section', 0, i):html.index('</form>', i)]


def test_forms_carry_no_fee_notice_but_home_diagnosis_and_faq_do():
    fee = _re.compile(r'착수금|성과 보수|성공보수')
    pages = [p for p in list(ROOT.glob('*.html')) + list(ROOT.glob('industry/*.html'))
             if 'id="leadForm"' in p.read_text(encoding='utf-8')]
    assert len(pages) >= 36
    for path in pages:
        form = _form(path.read_text(encoding='utf-8'))
        assert not fee.search(form), f'{path.name}: 신청 폼에 비용 고지가 남아 있다'
        assert _re.search(r'<button type="submit"[^>]*>무료 진단 신청</button>', form), path.name
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    form = _form(home)
    assert '초기 상담 신청에는 서류 첨부가 필요하지 않습니다' in home[home.index('id="leadForm"'):home.index('id="about"')]
    assert 'data-cta-location="form_alternative"' in home[home.index('id="leadForm"'):home.index('id="about"')], '홈 폼 아래 카톡 링크가 사라졌다'
    diagnosis = _section(home, 'id="diagnosis"')
    assert '착수금·진행비 0원' in diagnosis and '성과 보수' in diagnosis, '진단 섹션에서 비용 고지가 사라졌다'
    faq = _section(home, 'id="faq"')
    assert '착수금·진행비 등 실행 전 비용은 일절 받지 않고' in faq and '성공보수' in faq, 'FAQ에서 비용 고지가 사라졌다'


def test_inline_form_pages_keep_fee_notice_outside_the_form():
    """폼에서 뺀 비용 고지가 인라인 폼 페이지(자금·재단·허브·4분기)에서 통째로 사라지지 않게."""
    fee = _re.compile(r'착수금|성공보수|성과로만')
    for path in ROOT.glob('*.html'):
        html = path.read_text(encoding='utf-8')
        if 'class="inline-diag"' not in html:
            continue
        body = html[html.find('<body'):]
        form = _form(body)
        outside = body.replace(form, '')
        outside = _re.sub(r'<(header|footer).*?</>', '', outside, flags=_re.S)
        assert fee.search(outside), f'{path.name}: 폼 밖 본문에 비용 고지가 없다'
