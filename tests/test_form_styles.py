"""폼이 있는 모든 페이지 — 브라우저가 계산한 스타일로 '기본 모양 폼'을 잡는다.

2026-09-28 허브 2장(/sosangin·/jungsogieop)이 홈 폼 HTML 만 복사하고 CSS 는 못 가져가
19px 입력칸·네이티브 select·회색 버튼으로 PR #7 부터 배포돼 있었다. 문자열 검사는 마크업이
맞으니 통과했다 — 실제로 칠해진 모양을 봐야 잡힌다.

기준(하나라도 어기면 실패):
  - 보이는 텍스트·전화 입력칸 높이 44px 이상 (허니팟 lf-website 제외)
  - 제출 버튼 배경이 브랜드 블루 계열(파랑이 빨강·초록보다 60 이상 큼) — 기본 회색 버튼 거부
  - select 가 있으면 커스텀 스타일: 높이 44px 이상·왼쪽 안쪽 여백 8px 이상

로컬 실행: python -m pytest tests/test_form_styles.py
playwright·Chromium 이 없으면 skip (REQUIRE_BROWSER 가 설정된 CI 에서는 실패).
"""
import functools
import http.server
import os
import re
import threading
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
VIEWPORTS = [{"width": 390, "height": 844}, {"width": 1280, "height": 800}]
FORM_PAGES = sorted(p.relative_to(ROOT).as_posix() for p in list(ROOT.glob('*.html')) + list(ROOT.glob('industry/*.html')) + list(ROOT.glob('region/*.html'))
                    if 'id="leadForm"' in p.read_text(encoding='utf-8'))

try:
    from playwright import sync_api
except ImportError:
    sync_api = None


def _unavailable(reason):
    if os.environ.get("REQUIRE_BROWSER"):
        pytest.fail(f"REQUIRE_BROWSER 가 설정된 환경인데 브라우저 테스트를 실행할 수 없습니다 — {reason}")
    pytest.skip(reason)


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def site():
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture(scope="module")
def browser():
    if sync_api is None:
        _unavailable("playwright 미설치")
    try:
        driver = sync_api.sync_playwright().start()
    except Exception as exc:
        _unavailable(f"playwright 드라이버를 시작할 수 없음: {exc}")
    try:
        b = driver.chromium.launch()
    except sync_api.Error as exc:
        driver.stop()
        _unavailable(f"Chromium 을 띄울 수 없음: {exc}")
    try:
        yield b
    finally:
        b.close()
        driver.stop()


MEASURE = """() => {
  const f = document.getElementById('leadForm');
  const box = e => e.getBoundingClientRect();
  const inputs = [...f.querySelectorAll('input[type=text], input[type=tel]')]
    .filter(e => e.id !== 'lf-website' && e.getAttribute('aria-hidden') !== 'true')
    .map(e => ({id: e.id, h: box(e).height}));
  const selects = [...f.querySelectorAll('select')]
    .map(e => ({id: e.id, h: box(e).height, pad: parseFloat(getComputedStyle(e).paddingLeft)}));
  const btn = f.querySelector('[type=submit]');
  return {inputs, selects, btn: getComputedStyle(btn).backgroundColor};
}"""


def test_form_pages_found():
    # 홈·허브 2장·4분기·자금/재단 상세 — 목록이 비면 아래 검사가 아무것도 안 본다
    assert len(FORM_PAGES) >= 36, FORM_PAGES
    for must in ['index.html', 'sosangin.html', 'jungsogieop.html', '2026-4q-sosangin.html', 'cheongnyeon.html']:
        assert must in FORM_PAGES, must


@pytest.mark.parametrize("viewport", VIEWPORTS, ids=["390", "1280"])
def test_every_form_is_styled(browser, site, viewport):
    page = browser.new_page(viewport=viewport)
    page.route("**/*", lambda r: r.continue_() if r.request.url.startswith("http://127.0.0.1:") else r.abort())
    bad = []
    for path in FORM_PAGES:
        page.goto(f"{site}/{path}", wait_until="domcontentloaded")
        m = page.evaluate(MEASURE)
        for i in m["inputs"]:
            if i["h"] < 44:
                bad.append(f"{path}: 입력칸 #{i['id']} 높이 {i['h']:.0f}px")
        for s in m["selects"]:
            if s["h"] < 44 or s["pad"] < 8:
                bad.append(f"{path}: select #{s['id']} 기본 모양(높이 {s['h']:.0f}px·여백 {s['pad']:.0f}px)")
        r, g, b = (int(x) for x in re.findall(r"\d+", m["btn"])[:3])
        if not (b - r >= 60 and b - g >= 60):
            bad.append(f"{path}: 제출 버튼 배경 {m['btn']} — 브랜드 블루 아님")
        if not m["inputs"]:
            bad.append(f"{path}: 보이는 입력칸이 없다")
    page.close()
    assert not bad, "\n".join(bad)
