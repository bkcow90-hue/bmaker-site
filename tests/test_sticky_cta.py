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
def phone(site):
    # 브라우저를 '띄우는' 단계만 예외를 가로챈다. yield 이후(테스트 본문)에서 나는
    # playwright TimeoutError 까지 여기서 잡으면 실패가 skip 으로 둔갑한다.
    if sync_api is None:
        _unavailable("playwright 미설치 — pip install playwright")
    try:
        driver = sync_api.sync_playwright().start()
    except Exception as exc:                           # 드라이버 실행 실패
        _unavailable(f"playwright 드라이버를 시작할 수 없음: {exc}")
    try:
        browser = driver.chromium.launch()
    except sync_api.Error as exc:                      # 브라우저 바이너리 미설치 등
        driver.stop()
        _unavailable(f"Chromium 을 띄울 수 없음: {exc} (playwright install chromium)")
    try:
        page = browser.new_page(viewport=PHONE)
        page.goto(f"{site}/index.html", wait_until="load")
        yield page
    finally:
        browser.close()
        driver.stop()


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
