"""접수 일정(/schedule) 배지 — 방문 시점 날짜로 계산되는지 브라우저 동작으로 본다.

서버는 항상 '공고상 YYYY-MM-DD 예정' 형태로 렌더하고 시작일이 지난 뒤 쓸 문장을 data 속성에
실어 보낸다. 전환은 conversion.js 가 방문 시점 날짜로 한다 — 그래서 재빌드 없이도 상태가 맞고,
빌드 날짜가 HTML 에 들어가지 않아 산출물이 매일 흔들리지 않는다.

여기서 확인하는 상태는 두 가지(시작 전 / 시작일 경과)다. 지금 자금 데이터에는 ISO 마감일이
한 건도 없고(마감일 칸은 '접수 중·예산 소진시 마감' 같은 문장), 분기마감·접수중표시는 사람이
날짜와 함께 기록한 관측이라 날짜 계산 대상이 아니다. 마감일이 데이터에 들어오면 그때 '마감'
상태와 함께 이 파일에 케이스를 추가한다.

로컬 실행: python -m pytest tests/test_schedule_badges.py
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
PHONE = {"width": 390, "height": 844}
REQUIRE_BROWSER = bool(os.environ.get("REQUIRE_BROWSER"))

try:
    from playwright import sync_api
except ImportError:
    sync_api = None


def _unavailable(reason):
    if REQUIRE_BROWSER:
        pytest.fail(f"REQUIRE_BROWSER 가 설정된 환경인데 브라우저 테스트를 실행할 수 없습니다 — {reason}")
    pytest.skip(reason)


@pytest.fixture(scope="module")
def site():
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


def _start_date():
    """서버가 실어 보낸 시작일 — 데이터가 바뀌어도 테스트가 따라간다."""
    html = (ROOT / "schedule.html").read_text(encoding="utf-8")
    dates = sorted(set(re.findall(r'data-sched-start="(\d{4}-\d{2}-\d{2})"', html)))
    assert dates, "schedule.html 에 data-sched-start 가 없다 — 서버 렌더가 바뀌었는지 확인"
    return dates[0]


def _badges(browser, site, at):
    """방문 시점을 at(KST)으로 고정해 배지 상태를 읽는다."""
    context = browser.new_context(viewport=PHONE, timezone_id="Asia/Seoul")
    page = context.new_page()
    page.clock.install(time=f"{at}T09:00:00+09:00")
    page.goto(f"{site}/schedule.html", wait_until="load")
    page.wait_for_function("document.querySelectorAll('[data-sched-start]').length > 0")
    out = page.evaluate("""() => [...document.querySelectorAll('[data-sched-start]')].map(el => ({
        start: el.getAttribute('data-sched-start'),
        cls: el.className,
        state: el.getAttribute('data-sched-state'),
        text: el.textContent.trim(),
    }))""")
    observed = page.evaluate(
        """() => [...document.querySelectorAll('td .badge:not([data-sched-start])')].map(el => el.textContent.trim())""")
    context.close()
    return out, observed


def test_before_start_shows_the_scheduled_notice(browser, site):
    """① 시작일 전 — 서버가 쓴 '공고상 … 예정' 이 그대로 보인다."""
    start = _start_date()
    day_before = (int(start[:4]), int(start[5:7]), int(start[8:10]))
    before = f"{day_before[0]:04d}-{day_before[1]:02d}-{day_before[2] - 1:02d}"
    rows, _ = _badges(browser, site, before)
    assert rows, "data-sched-start 행이 없다"
    for r in rows:
        assert r["state"] is None, r
        assert "b-soon" in r["cls"], r
        assert "예정" in r["text"], r


def test_on_the_start_date_flips_to_passed(browser, site):
    """② 첫 시작일 당일 — 도래한 행만 경과, 다른 회차의 미래 행은 예정 유지."""
    start = _start_date()
    rows, _ = _badges(browser, site, start)
    assert any(r["start"] == start for r in rows)
    for r in rows:
        if r["start"] > start:
            assert r["state"] is None, r
            assert "b-soon" in r["cls"] and "예정" in r["text"], r
            continue
        assert r["state"] == "passed", r
        assert "b-check" in r["cls"] and "b-soon" not in r["cls"], r
        assert "시작일 경과" in r["text"], r
        assert "예정" not in r["text"], r


def test_long_after_start_stays_passed(browser, site):
    """③ 한참 뒤에도 경과 상태가 유지된다."""
    start = _start_date()
    later = f"{int(start[:4]) + 1}-{start[5:7]}-{start[8:10]}"
    rows, _ = _badges(browser, site, later)
    for r in rows:
        assert r["state"] == "passed", r
        assert "시작일 경과" in r["text"], r


def test_observed_statuses_are_never_rewritten(browser, site):
    """기관 확인 관측(분기마감·접수중표시)은 사람이 기록한 사실 — 날짜로 덮지 않는다."""
    start = _start_date()
    later = f"{int(start[:4]) + 1}-{start[5:7]}-{start[8:10]}"
    _, observed_before = _badges(browser, site, start[:8] + "01")
    _, observed_after = _badges(browser, site, later)
    assert observed_before == observed_after, "관측 기반 배지가 날짜에 따라 바뀌었다"
    assert any("확인" in t for t in observed_before), observed_before


def test_page_carries_no_build_date(browser, site):
    """빌드 날짜가 페이지에 들어가면 산출물이 매일 흔들린다 — '일정 계산일' 줄은 없어야 한다."""
    html = (ROOT / "schedule.html").read_text(encoding="utf-8")
    assert "일정 계산일" not in html
    assert re.search(r'class="asof">기준일 \d{4}년 \d{1,2}월 \d{1,2}일', html), "기준일 줄이 없다"


def _fund_page_with_start():
    """날짜로 갈리는 자금 상세 페이지 — 데이터가 바뀌어도 테스트가 따라간다."""
    for path in sorted(ROOT.glob('*.html')):
        html = path.read_text(encoding='utf-8')
        m = re.search(r'data-sched-start="(\d{4}-\d{2}-\d{2})"', html)
        if m and 'class="badge' in html:
            return path.name, m.group(1)
    pytest.skip('data-sched-start 를 가진 자금 상세 페이지가 없다')


def test_fund_detail_badge_also_flips_at_visit_time(browser, site):
    """자금 상세 15장도 같은 규칙 — 배지와 '접수' 행이 방문 시점에 함께 바뀐다."""
    name, start = _fund_page_with_start()
    context = browser.new_context(viewport=PHONE, timezone_id='Asia/Seoul')
    page = context.new_page()
    page.clock.install(time=f"{start}T09:00:00+09:00")          # 시작일 당일
    page.goto(f"{site}/{name}", wait_until='load')
    page.wait_for_function("document.querySelectorAll('[data-sched-state=\"passed\"]').length > 0")
    got = page.evaluate("""() => [...document.querySelectorAll('[data-sched-start]')].map(el => ({
        tag: el.tagName, cls: el.className, state: el.getAttribute('data-sched-state'), text: el.textContent.trim(),
    }))""")
    context.close()
    assert len(got) == 2, got                                    # 배지 + 접수 행
    for g in got:
        assert g['state'] == 'passed', g
        assert '시작일 경과' in g['text'], g
    assert any('b-check' in g['cls'] for g in got), got
