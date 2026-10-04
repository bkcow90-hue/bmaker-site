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


# ── Task 3·4·5: 브라우저 동작 (390×844, 실제 신청 API 로는 아무것도 보내지 않는다) ──────────────────
import functools  # noqa: E402
import http.server  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import threading  # noqa: E402

import pytest  # noqa: E402
try:
    from playwright.sync_api import sync_playwright, Error  # noqa: E402
except ImportError:
    sync_playwright = None

# 설계서 2절 — 폼 없던 33장(페이지 끝 폼이 붙는 곳). 판정은 실행 시 '#leadForm 없음' 이고 이 목록은 기대값이다.
PAGE_END = set('''/sojingong /jungjingong /bojeung /certification /industry/eumsikjeom /cases /stats /jeosinyong
/chaksugeum /sanghwan /gyehoekseo /geojeol /gibo /sinbo /faq /schedule /gaein /consulting
/funding /marketing /startup /work /business-guide /online-ad-guide /blog-marketing-cost
/viral-marketing-guide /startup-consulting-cost /education /education-program
/corporate-loan-documents /working-capital-facility /sme-business-loans /microfinance-business'''.split())


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


@pytest.fixture(scope='module')
def site():
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(_Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown()
    server.server_close()


@pytest.fixture(scope='module')
def browser():
    if sync_playwright is None:
        if os.environ.get('REQUIRE_BROWSER'):
            pytest.fail('REQUIRE_BROWSER is set: Playwright is not installed')
        pytest.skip('Playwright is not installed')
    with sync_playwright() as p:
        try:
            b = p.chromium.launch()
        except Error as exc:
            if os.environ.get('REQUIRE_BROWSER'):
                pytest.fail(f'REQUIRE_BROWSER is set: {exc}')
            pytest.skip(f'Chromium is unavailable: {exc}')
        yield b
        b.close()


def phone(browser, sent=None):
    page = browser.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, reduced_motion='reduce')

    def route(r):
        if r.request.url.startswith('http://127.0.0.1:'):
            return r.continue_()
        if '/api/lead' in r.request.url and sent is not None:
            sent.append(json.loads(r.request.post_data or '{}'))
            return r.fulfill(status=200, content_type='application/json', body='{"ok":true,"delivery":"accepted"}')
        return r.abort()
    page.route('**/*', route)
    return page


def file_url(site, path):
    return site + ('/index.html' if path == '/' else path + ('' if path.endswith('.html') else '.html'))


BAR = """() => {
  const s = document.querySelector('.sticky-cta'); if (!s) return null;
  const box = e => e.getBoundingClientRect();
  const go = s.querySelector('.sc-apply'), k = s.querySelector('.sc-kakao'), t = s.querySelector('.sc-tel');
  return { hidden: s.hidden, top: box(s).top, bottom: box(s).bottom, vh: innerHeight, w: Math.round(box(s).right), vw: innerWidth,
    go: go && box(go).width, icon: Math.max(k ? box(k).width : 0, t ? box(t).width : 0),
    goBg: go && getComputedStyle(go).backgroundColor, kBg: k && getComputedStyle(k).backgroundColor, tBg: t && getComputedStyle(t).backgroundColor,
    labels: [k && k.getAttribute('aria-label'), t && t.getAttribute('aria-label')], forms: document.querySelectorAll('#leadForm').length,
    pageEnd: !!document.querySelector('#apply[data-page-end]'),
    formInView: (f => !!f && f.getBoundingClientRect().top < innerHeight && f.getBoundingClientRect().bottom > 0)(document.getElementById('leadForm')),
    heroInView: (h => !!h && h.getBoundingClientRect().top < innerHeight && h.getBoundingClientRect().bottom > 0)(document.getElementById('heroCta')) }
}"""
IN_VIEW = "(sel) => { const r = document.querySelector(sel).getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0 }"
SHEET_HAS_FORM = "!!document.querySelector('.apply-sheet:not([hidden]) #leadForm')"


def test_every_page_one_form_and_a_visible_bar(browser, site):
    page = phone(browser)
    bad, page_end = [], set()
    for path, _ in served_html():
        page.goto(file_url(site, path), wait_until='load')
        # 히어로 CTA·폼이 안 보이는 곳까지 내려서 잰다(그 둘이 보이면 바는 숨는 게 맞다)
        page.evaluate("""() => { const f = document.getElementById('apply'); const top = f ? f.getBoundingClientRect().top + scrollY : 1e9;
          scrollTo(0, Math.max(0, Math.min(innerHeight * 1.6, top - innerHeight * 1.2))) }""")
        page.wait_for_timeout(60)
        m = page.evaluate(BAR)
        if not m:
            bad.append(f'{path}: 바 없음')
            continue
        if m['forms'] != 1:
            bad.append(f'{path}: #leadForm {m["forms"]}개')
        if m['pageEnd']:
            page_end.add(path)
        # 바 자체가 화면 밖으로 나가지 않는다. (페이지 전체의 기존 3px 넘침은 표 때문이고 이 변경과 무관 — 2026-10-04 확인)
        if not m['hidden'] and m['w'] > m['vw'] + 1:
            bad.append(f'{path}: 바가 화면 오른쪽 밖 {m["w"]}px')
        if m['go'] < 3 * m['icon']:
            bad.append(f'{path}: 신청 버튼 {m["go"]:.0f}px < 아이콘×3')
        if m['goBg'] != 'rgb(35, 71, 128)':
            bad.append(f'{path}: 신청 버튼 색 {m["goBg"]}')
        if m['kBg'] != 'rgb(254, 229, 0)' or m['tBg'] == 'rgb(254, 229, 0)':
            bad.append(f'{path}: 노랑은 카톡에만 ({m["kBg"]}, {m["tBg"]})')
        if m['labels'] != ['카카오톡 상담', '전화 상담 1666-2425']:
            bad.append(f'{path}: 아이콘 이름 {m["labels"]}')
        if m['hidden'] and not (m['formInView'] or m['heroInView']):
            bad.append(f'{path}: 폼·히어로가 안 보이는데 바가 숨어 있다')
        if not m['hidden'] and m['formInView']:
            bad.append(f'{path}: 폼이 보이는데 바가 떠 있다')
        elif m['bottom'] > m['vh'] + 1:
            bad.append(f'{path}: 바가 화면 밖')
    page.close()
    assert not bad, '\n'.join(bad)
    norm = {p.replace('.html', '') for p in page_end}
    assert norm == PAGE_END, f'빠짐 {sorted(PAGE_END - norm)} · 넘침 {sorted(norm - PAGE_END)}'


def test_page_end_form_is_the_inline_form_exactly(browser, site):
    page = phone(browser)
    page.goto(file_url(site, '/sojingong'), wait_until='load')
    h1 = page.evaluate("(document.querySelector('h1').textContent || '').replace(/\\s+/g, ' ').trim().slice(0, 40)")
    expected = inline_form.form_html('/sojingong', h1, inline_form.TITLE_GENERAL)
    got, want = page.evaluate("""(html) => {
      const s = document.getElementById('apply').cloneNode(true); s.removeAttribute('data-page-end');
      const t = document.createElement('template'); t.innerHTML = html.trim();
      const norm = n => n.outerHTML.replace(/>\\s+</g, '><').trim();
      return [norm(s), norm(t.content.firstElementChild)] }""", expected)
    assert got == want
    assert page.evaluate("getComputedStyle(document.querySelector('#leadForm [type=submit]')).backgroundColor") == 'rgb(35, 71, 128)'
    assert page.evaluate("document.getElementById('lf-service').value") == 'policy', '정책자금 페이지의 문의 분야가 유지돼야 한다'
    page.close()


def test_bar_hides_for_form_keyboard_and_never_covers_the_footer(browser, site):
    page = phone(browser)
    page.goto(file_url(site, '/jungjingong'), wait_until='load')
    page.evaluate('scrollTo(0, innerHeight * 2)')
    page.wait_for_timeout(80)
    assert page.evaluate(BAR)['hidden'] is False
    # iOS 처럼 초점 없이 키보드가 남아 화면이 줄어든 경우
    page.evaluate("""() => { Object.defineProperty(window.visualViewport, 'height', { configurable: true, get: () => innerHeight * 0.55 });
      window.visualViewport.dispatchEvent(new Event('resize')) }""")
    page.wait_for_timeout(50)
    assert page.evaluate(BAR)['hidden'] is True, '키보드(화면 축소) 때 바가 숨어야 한다'
    page.evaluate("""() => { Object.defineProperty(window.visualViewport, 'height', { configurable: true, get: () => innerHeight });
      window.visualViewport.dispatchEvent(new Event('resize')) }""")
    page.wait_for_timeout(50)
    assert page.evaluate(BAR)['hidden'] is False
    # 폼 입력칸 초점 = 키보드
    page.focus('#lf-name')
    page.evaluate('scrollTo(0, innerHeight * 2)')
    page.wait_for_timeout(80)
    assert page.evaluate(BAR)['hidden'] is True
    page.evaluate('document.activeElement.blur()')
    page.wait_for_timeout(50)
    # 폼이 보이면 숨김
    page.evaluate("document.getElementById('apply').scrollIntoView()")
    page.wait_for_timeout(80)
    assert page.evaluate(BAR)['hidden'] is True
    # 맨 아래에서도 푸터 마지막 링크가 바 아래로 안 들어간다
    page.evaluate("scrollTo({top: document.documentElement.scrollHeight, behavior: 'instant'})")
    page.wait_for_timeout(80)
    covered = page.evaluate("""() => { const b = document.querySelector('.sticky-cta'); if (b.hidden) return false;
      const links = [...document.querySelectorAll('footer a')].filter(a => a.offsetParent); const last = links[links.length - 1];
      return !!last && last.getBoundingClientRect().bottom > b.getBoundingClientRect().top + 1 }""")
    assert not covered
    assert page.evaluate("parseFloat(getComputedStyle(document.body).paddingBottom)") >= 70
    page.close()


def test_mid_button_only_on_long_formless_pages(browser, site):
    page = phone(browser)
    page.goto(file_url(site, '/jungjingong'), wait_until='load')
    assert page.locator('.mid-apply').count() == 1
    assert page.evaluate("!document.querySelector('.mid-apply').closest('details, table, #apply')")
    assert '진단은 무료입니다.' in page.locator('.mid-apply').inner_text()
    for short_or_inline in ('/faq', '/jaedan-seoul', '/'):
        page.goto(file_url(site, short_or_inline), wait_until='load')
        assert page.locator('.mid-apply').count() == 0, short_or_inline
    page.close()


def test_apply_sheet_opens_in_place_and_closes_every_way(browser, site):
    page = phone(browser)
    page.goto(file_url(site, '/sojingong'), wait_until='load')
    url = page.url
    page.evaluate('scrollTo(0, 1500)')
    page.wait_for_timeout(80)
    y = page.evaluate('scrollY')
    form_home = "document.getElementById('apply').parentElement.classList.contains('page-end-apply')"

    page.click('.sticky-cta .sc-apply')
    page.wait_for_timeout(80)
    assert page.evaluate(SHEET_HAS_FORM)
    assert page.url == url, '다른 페이지로 가면 안 된다'
    assert page.evaluate(BAR)['hidden'] is True
    assert page.evaluate("!!document.activeElement.closest('.apply-sheet')"), '초점이 창 안으로'
    for _ in range(30):
        page.keyboard.press('Tab')
    assert page.evaluate("!!document.activeElement.closest('.apply-sheet')"), 'Tab 이 창 밖으로 나가면 안 된다'
    page.keyboard.press('Escape')
    page.wait_for_timeout(50)
    assert not page.evaluate(SHEET_HAS_FORM) and page.evaluate(form_home)
    assert abs(page.evaluate('scrollY') - y) <= 2, '스크롤 위치 보존'
    assert page.evaluate("document.activeElement.classList.contains('sc-apply')"), '연 버튼으로 초점 복귀'

    page.click('.sticky-cta .sc-apply')
    page.click('.apply-sheet-backdrop', position={'x': 10, 'y': 10})
    page.wait_for_timeout(50)
    assert not page.evaluate(SHEET_HAS_FORM)

    page.click('.sticky-cta .sc-apply')
    page.go_back()
    page.wait_for_timeout(150)
    assert not page.evaluate(SHEET_HAS_FORM), '뒤로가기는 창만 닫는다'
    assert page.url == url

    page.click('.sticky-cta .sc-apply')
    page.click('.apply-sheet-close')
    page.wait_for_timeout(50)
    assert not page.evaluate(SHEET_HAS_FORM) and page.evaluate(form_home)
    page.close()


def test_links_that_used_to_leave_the_page_open_the_sheet_with_their_service(browser, site):
    page = phone(browser)
    page.goto(file_url(site, '/marketing'), wait_until='load')
    link = page.locator('a[href="/?service=marketing#apply"]').first
    assert link.get_attribute('href') == '/?service=marketing#apply', 'href 는 그대로(자바스크립트가 없으면 예전처럼)'
    url = page.url
    link.click()
    page.wait_for_timeout(80)
    assert page.url == url
    assert page.evaluate(SHEET_HAS_FORM)
    assert page.evaluate("document.getElementById('lf-service').value") == 'marketing'
    page.close()


def test_submitting_inside_the_sheet_sends_once_and_keeps_the_result(browser, site):
    sent = []
    page = phone(browser, sent)
    page.goto(file_url(site, '/gibo'), wait_until='load')
    page.evaluate('scrollTo(0, 1200)')
    page.wait_for_timeout(60)
    page.click('.sticky-cta .sc-apply')
    page.fill('#lf-name', '테스트')
    page.fill('#lf-phone', '010-0000-0099')
    page.check('#lf-consent')
    page.click('#leadForm [type=submit]')
    page.wait_for_timeout(400)
    assert len(sent) == 1
    body = sent[0]
    assert body['name'] == '테스트' and body.get('request_id') and body.get('landing_url', '').startswith('http://127.0.0.1')
    assert body['consent_privacy'] is True
    leads = page.evaluate("(window.dataLayer || []).filter(e => e && (e.event === 'generate_lead' || e[1] === 'generate_lead')).length")
    assert leads == 1
    page.click('.apply-sheet-close')
    page.wait_for_timeout(50)
    page.evaluate("document.querySelector('.sticky-cta .sc-apply').click()")
    page.wait_for_timeout(50)
    assert page.evaluate(SHEET_HAS_FORM)
    assert '접수' in page.locator('#applyMsg').inner_text(), '다시 열어도 완료 문구가 남는다'
    page.click('#leadForm [type=submit]')
    page.wait_for_timeout(200)
    assert len(sent) == 1, '완료 뒤 다시 보내지 않는다'
    page.close()


def test_home_keeps_scrolling_to_its_form(browser, site):
    page = phone(browser)
    page.goto(file_url(site, '/'), wait_until='load')
    page.locator('#cases').scroll_into_view_if_needed()
    page.wait_for_timeout(80)
    page.click('.sticky-cta .sc-apply')
    page.wait_for_timeout(600)
    assert page.locator('.apply-sheet:not([hidden])').count() == 0
    assert page.evaluate(IN_VIEW, '#leadForm')
    page.close()


def test_hash_entry_lands_on_the_new_form_and_pc_box(browser, site):
    page = phone(browser)
    page.goto(file_url(site, '/sojingong') + '#apply', wait_until='load')
    page.wait_for_timeout(150)
    assert page.evaluate(IN_VIEW, '#apply')
    page.close()
    pc = browser.new_page(viewport={'width': 1366, 'height': 900})
    pc.route('**/*', lambda r: r.continue_() if r.request.url.startswith('http://127.0.0.1:') else r.abort())
    pc.goto(file_url(site, '/sojingong'), wait_until='load')
    pc.evaluate('scrollTo(0, 900)')
    pc.wait_for_timeout(80)
    box = pc.locator('.sticky-cta').bounding_box()
    assert box and box['x'] > 900 and box['width'] < 400, box
    pc.close()


def test_sheet_stays_above_the_keyboard(browser, site):
    page = phone(browser)
    page.goto(file_url(site, '/sojingong'), wait_until='load')
    page.evaluate('scrollTo(0, 1500)')
    page.wait_for_timeout(60)
    page.click('.sticky-cta .sc-apply')
    page.wait_for_timeout(80)
    page.click('#lf-name')
    # iOS: 키보드가 화면 아래 330px 을 덮는다 — visualViewport 만 줄어든다
    page.evaluate("""() => { Object.defineProperty(window.visualViewport, 'height', { configurable: true, get: () => innerHeight - 330 });
      window.visualViewport.dispatchEvent(new Event('resize')) }""")
    page.wait_for_timeout(400)
    m = page.evaluate("""() => { const panel = document.querySelector('.apply-sheet-panel').getBoundingClientRect();
      const input = document.getElementById('lf-name').getBoundingClientRect(); const kbTop = innerHeight - 330;
      return { panelBottom: panel.bottom, inputTop: input.top, inputBottom: input.bottom, kbTop } }""")
    assert m['panelBottom'] <= m['kbTop'] + 1, f'창이 키보드 밑으로 들어간다 {m}'
    assert m['inputTop'] >= 0 and m['inputBottom'] <= m['kbTop'], f'초점 칸이 키보드에 가린다 {m}'
    page.close()
