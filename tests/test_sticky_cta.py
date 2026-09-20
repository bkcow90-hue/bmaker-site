"""고정바(.sticky-cta) 노출 규칙 — 소스 문자열이 아니라 실제 브라우저 동작으로 검증한다.

규격: 첫 화면 CTA 는 1개. 히어로의 '무료 진단 예약하기'(#heroCta)가 화면에 있는 동안에는
고정바를 숨기고, 화면에서 벗어나면 노출한다. 상태는 hidden 속성 하나로만 표현한다
(CSS: .sticky-cta[hidden]{display:none!important}).

로컬 실행: pip install playwright && playwright install chromium && python -m pytest tests/test_sticky_cta.py
playwright·Chromium 이 없는 환경(ledger 워크플로의 pytest 게이트)에서는 skip 된다.
단, REQUIRE_BROWSER 가 설정돼 있으면(pr-check 워크플로) skip 대신 실패한다 —
브라우저 검사가 조용히 빠진 채 초록으로 보이는 일을 막는다.
"""
import functools
import http.server
import os
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHONE = {"width": 390, "height": 844}
TIMEOUT = 5000
REQUIRE_BROWSER = bool(os.environ.get("REQUIRE_BROWSER"))

try:
    from playwright import sync_api
except ImportError:                                    # playwright 미설치
    sync_api = None


def _unavailable(reason):
    """브라우저를 못 쓰는 상황. CI(REQUIRE_BROWSER)에서는 skip 으로 넘기지 않는다."""
    if REQUIRE_BROWSER:
        pytest.fail(f"REQUIRE_BROWSER 가 설정된 환경인데 브라우저 테스트를 실행할 수 없습니다 — {reason}")
    pytest.skip(reason)


@pytest.fixture(scope="module")
def site():
    """저장소 루트를 그대로 서빙한다 — /assets 루트 절대경로가 실제 배포와 같게 걸리도록."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(scope="module")
def browser():
    """뷰포트를 바꿔가며 열어야 하는 검사용 — phone 픽스처는 페이지 하나를 공유한다."""
    if sync_api is None:
        _unavailable("playwright 미설치 — pip install playwright")
    try:
        driver = sync_api.sync_playwright().start()
    except Exception as exc:
        _unavailable(f"playwright 드라이버를 시작할 수 없음: {exc}")
    try:
        b = driver.chromium.launch()
    except sync_api.Error as exc:
        driver.stop()
        _unavailable(f"Chromium 을 띄울 수 없음: {exc} (playwright install chromium)")
    try:
        yield b
    finally:
        b.close()
        driver.stop()


@pytest.fixture(scope="module")
def phone(browser, site):
    """첫 화면 검사용 페이지 하나. 드라이버는 browser 픽스처가 만든 것을 공유한다
    (같은 스레드에서 sync_playwright 를 두 번 start 하면 asyncio 충돌로 실행되지 못한다)."""
    context = browser.new_context(viewport=PHONE, timezone_id='Asia/Seoul')
    page = context.new_page()
    page.goto(f"{site}/index.html", wait_until="load")
    try:
        yield page
    finally:
        context.close()


def _cta_in_viewport(page):
    return page.evaluate("""() => {
        const r = document.getElementById('heroCta').getBoundingClientRect();
        return r.bottom > 0 && r.top < window.innerHeight;
    }""")


def _scroll_to(page, selector):
    page.evaluate(
        "sel => window.scrollTo({top: document.querySelector(sel).getBoundingClientRect().top + window.scrollY,"
        " behavior: 'instant'})", selector)


def test_sticky_bar_is_hidden_on_the_first_screen(phone):
    """① 로드 직후 — 히어로 CTA 가 화면에 있으므로 고정바는 보이지 않는다."""
    assert _cta_in_viewport(phone), "전제 실패: 390x844 첫 화면에 히어로 CTA 가 없다"
    phone.wait_for_selector(".sticky-cta", state="hidden", timeout=TIMEOUT)
    assert phone.locator(".sticky-cta").evaluate("el => el.hasAttribute('hidden')"), \
        "고정바는 hidden 속성으로 숨겨야 한다(class 토글 금지)"


def test_sticky_bar_appears_once_the_hero_cta_scrolls_away(phone):
    """② 히어로 CTA 가 화면에서 벗어나면 고정바가 나온다 (폼도 화면 밖인 지점에서 확인)."""
    _scroll_to(phone, ".why")
    assert not _cta_in_viewport(phone), "전제 실패: .why 까지 스크롤했는데 히어로 CTA 가 아직 보인다"
    phone.wait_for_selector(".sticky-cta", state="visible", timeout=TIMEOUT)


def test_sticky_bar_hides_again_when_scrolled_back_to_the_hero(phone):
    """③ 다시 위로 올리면 사라진다 — 스크롤 구간은 IntersectionObserver 가 담당."""
    phone.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    assert _cta_in_viewport(phone)
    phone.wait_for_selector(".sticky-cta", state="hidden", timeout=TIMEOUT)


def test_sticky_bar_state_survives_a_resize_without_scrolling(phone):
    """뷰포트만 바뀌어도(스크롤 없이) 상태를 다시 계산한다 — load·resize·pageshow 안전장치."""
    _scroll_to(phone, ".why")
    phone.wait_for_selector(".sticky-cta", state="visible", timeout=TIMEOUT)
    phone.set_viewport_size({"width": 390, "height": 300})
    phone.wait_for_timeout(120)
    assert phone.locator(".sticky-cta").is_visible(), "CTA 가 여전히 화면 밖이면 고정바는 계속 보여야 한다"
    phone.set_viewport_size(PHONE)
    phone.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    phone.wait_for_selector(".sticky-cta", state="hidden", timeout=TIMEOUT)


def test_sticky_bar_is_hidden_after_a_pageshow_restore(phone):
    """뒤로가기 복귀(bfcache) 경로 — pageshow 에서 다시 판정한다."""
    phone.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    phone.evaluate("""() => {
        document.querySelector('.sticky-cta').hidden = false;   // 복귀 직후 어긋난 상태를 흉내
        window.dispatchEvent(new PageTransitionEvent('pageshow', {persisted: true}));
    }""")
    phone.wait_for_selector(".sticky-cta", state="hidden", timeout=TIMEOUT)


DESKTOP = {"width": 1280, "height": 800}
BOOK_TEXT = "무료 진단 예약하기"

VISIBLE_BOOK = """() => [...document.querySelectorAll('a')]
    .filter(a => a.textContent.trim().includes('무료 진단 예약'))
    .filter(a => a.getClientRects().length)
    .filter(a => { const r = a.getBoundingClientRect(); return r.top < innerHeight && r.bottom > 0; })
    .map(a => ({text: a.textContent.trim(), cls: a.className, loc: a.getAttribute('data-cta-location')}))"""


def _home(browser, site, viewport):
    context = browser.new_context(viewport=viewport, timezone_id='Asia/Seoul')
    page = context.new_page()
    page.goto(f"{site}/index.html", wait_until='load')
    page.wait_for_function("document.querySelector('.sticky-cta') !== null")
    return context, page


@pytest.mark.parametrize('viewport', [PHONE, DESKTOP], ids=['phone', 'desktop'])
def test_first_screen_shows_exactly_one_booking_button(browser, site, viewport):
    """규격 4절 — 첫 화면 CTA 는 1개. 폰·데스크톱 모두 히어로 버튼 하나만 보인다."""
    context, page = _home(browser, site, viewport)
    try:
        page.wait_for_timeout(200)
        shown = page.evaluate(VISIBLE_BOOK)
        assert len(shown) == 1, shown
        assert shown[0]['loc'] == 'hero', shown
        assert shown[0]['text'] == BOOK_TEXT, shown
    finally:
        context.close()


def test_desktop_header_button_cycle(browser, site):
    context, page = _home(browser, site, DESKTOP)
    try:
        header = page.locator('.nav-cta-book')
        page.wait_for_timeout(200)
        assert header.is_hidden(), '첫 화면에서는 헤더 버튼이 숨어 있어야 한다'

        page.evaluate("window.scrollTo({top: document.querySelector('.why').getBoundingClientRect().top"
                      " + window.scrollY, behavior: 'instant'})")
        page.wait_for_selector('.nav-cta-book', state='visible', timeout=TIMEOUT)
        shown = page.evaluate(VISIBLE_BOOK)
        assert [s['loc'] for s in shown] == ['header'], shown

        page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
        page.wait_for_selector('.nav-cta-book', state='hidden', timeout=TIMEOUT)
        assert header.evaluate("el => el.hasAttribute('hidden')"), 'hidden 속성 방식이어야 한다'
    finally:
        context.close()


def test_mobile_header_has_no_button_and_menu_carries_the_cta():
    """모바일 헤더에는 버튼을 두지 않는다 — 메뉴 항목이 그 자리를 대신한다."""
    home = (ROOT / 'index.html').read_text(encoding='utf-8')
    header = home[home.index('<header>'):home.index('</header>')]
    assert 'class="nav-book"' in header, '메뉴에 예약 항목이 있어야 한다'
    assert f'>{BOOK_TEXT}</a>' in header
    css = home[home.index('/* nav-7 '):]
    assert '@media(max-width:680px){.nav-cta-book{display:none}' in css, '모바일에서 헤더 버튼을 감춰야 한다'
    assert '.nav-book{display:none}' in css, '데스크톱에서는 메뉴 항목을 감춰야 한다'
