"""고정바(.sticky-cta) 노출 규칙 — 소스 문자열이 아니라 실제 브라우저 동작으로 검증한다.

규격: 첫 화면 CTA 는 1개. 히어로의 '무료 진단 예약하기'(#heroCta)가 화면에 있는 동안에는
고정바를 숨기고, 화면에서 벗어나면 노출한다. 상태는 hidden 속성 하나로만 표현한다
(CSS: .sticky-cta[hidden]{display:none!important}).

로컬 실행: pip install playwright && playwright install chromium && python -m pytest tests/test_sticky_cta.py
playwright 가 없는 환경(ledger 워크플로의 pytest 게이트)에서는 skip 된다.
"""
import functools
import http.server
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PHONE = {"width": 390, "height": 844}
TIMEOUT = 5000

sync_api = pytest.importorskip(
    "playwright.sync_api", reason="playwright 미설치 — 브라우저 동작 테스트를 건너뜁니다")


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
    try:
        with sync_api.sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page(viewport=PHONE)
            page.goto(f"{site}/index.html", wait_until="load")
            yield page
            browser.close()
    except sync_api.Error as exc:                      # 브라우저 바이너리 미설치 등
        pytest.skip(f"Chromium 을 띄울 수 없어 건너뜁니다: {exc}")


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
