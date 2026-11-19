"""정책자금 자가진단(/jagajindan, 2026-11-19) — 정적 검사와 실제 브라우저 동작 검사.

결과 문장이 '될 것처럼' 말하지 않는지, 답이 신청 폼의 문의 칸으로 실려 가는지는
문자열 검사로 알 수 없어 브라우저에서 본다(규격 10절).
"""
import functools
import http.server
import json
import os
import re
import threading
from pathlib import Path

import pytest
try:
    from playwright.sync_api import sync_playwright, expect, Error
except ImportError:
    sync_playwright = None

ROOT = Path(__file__).resolve().parents[1]
SLUG = "jagajindan"
PAGE = (ROOT / f"{SLUG}.html").read_text(encoding="utf-8")
JS = (ROOT / "assets/selfcheck.js").read_text(encoding="utf-8")


def browser_unavailable(reason):
    if os.environ.get("REQUIRE_BROWSER"):
        pytest.fail(f"REQUIRE_BROWSER is set: {reason}")
    pytest.skip(reason)


# ── 정적 검사 ──────────────────────────────────────────────────────────────

def test_single_h1_canonical_and_keyword():
    assert len(re.findall(r"<h1\b", PAGE)) == 1
    assert f'<link rel="canonical" href="https://bmaker.kr/{SLUG}">' in PAGE
    title = re.search(r"<title>(.*?)</title>", PAGE).group(1)
    assert title.startswith("정책자금 자가진단") and title.endswith("| 비즈니스 메이커")
    assert re.search(r'<meta property="og:title" content="(.*?)">', PAGE).group(1) == title
    assert "정책자금 자가진단" in re.search(r"<h1[^>]*>(.*?)</h1>", PAGE, re.S).group(1)


def test_seven_questions_are_in_the_html_without_script():
    """질문은 HTML 에 그대로 있어야 한다 — 스크립트가 없어도, 검색·AI 가 읽어도 같은 내용."""
    keys = re.findall(r'<fieldset class="sc-q" data-key="([a-z]+)">', PAGE)
    assert keys == ["form", "years", "industry", "revenue", "tax", "overdue", "purpose"]
    for key in keys:
        assert len(re.findall(rf'<input type="radio" name="{key}" ', PAGE)) >= 3, key


def test_faq_screen_matches_faqpage_schema():
    ld = next(json.loads(m) for m in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', PAGE, re.S) if '"FAQPage"' in m)
    screen = re.findall(r'<details><summary>(.*?)</summary><div class="body">(.*?)</div></details>', PAGE, re.S)
    assert len(screen) == 6
    assert [(q["name"], q["acceptedAnswer"]["text"]) for q in ld["mainEntity"]] == screen


def test_no_banned_or_promising_wording_in_page_and_script():
    for name, text in (("page", PAGE), ("script", JS)):
        assert "갚" not in text, name
        assert not re.search(r"보장(?!하지)", text), name
        for bad in ["100% 승인", "무조건", "저신용 OK", "신용점수 부족해도", "승인됩니다", "받을 수 있습니다", "성공보수", "수수료"]:
            assert bad not in text, (name, bad)
    assert "승인 여부와 조건은 각 심사 기관" in PAGE
    assert "승인 여부와 조건은 각 심사 기관이 결정합니다" in JS


def test_ledger_numbers_are_builder_stamped():
    """체납·재창업·형태별 건수는 손으로 쓰지 않는다 — build_cases 가 data-stat 으로 넣는다."""
    for key in ("tax-n", "restart-n", "ind-n", "corp-n"):
        assert re.search(rf'data-stat="{key}">\d+</span>', PAGE), key
    assert "'jagajindan.html'" in (ROOT / "tools/build_cases.py").read_text(encoding="utf-8")


def test_registered_and_linked():
    assert f"<loc>https://bmaker.kr/{SLUG}</loc>" in (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    assert f"https://bmaker.kr/{SLUG}" in (ROOT / "llms.txt").read_text(encoding="utf-8")
    for name in ("index.html", "geojeol.html", "jeosinyong.html", "sosangin.html"):
        assert f'href="/{SLUG}"' in (ROOT / name).read_text(encoding="utf-8"), name


# ── 브라우저 동작 검사 (390×844) ───────────────────────────────────────────

class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="module")
def site():
    handler = functools.partial(QuietHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    server.server_close()
    thread.join()


@pytest.fixture
def browser_page():
    if sync_playwright is None:
        browser_unavailable("Playwright is not installed")
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Error as exc:
            browser_unavailable(f"Chromium is unavailable: {exc}")
        page = browser.new_page(viewport={"width": 390, "height": 844}, is_mobile=True,
                                has_touch=True, reduced_motion="reduce")
        yield page
        browser.close()


def _open(page, site, sent=None):
    def handle(route):
        url = route.request.url
        # /api/lead 는 같은 도메인 — 로컬 서버로 넘기기 전에 가로챈다. 실제 신청 API 로는 아무것도 보내지 않는다.
        if "/api/lead" in url:
            if sent is not None:
                sent.append(json.loads(route.request.post_data or "{}"))
            return route.fulfill(status=200, content_type="application/json", body='{"ok":true,"delivery":"accepted"}')
        return route.continue_() if url.startswith("http://127.0.0.1:") else route.abort()
    page.route("**/*", handle)
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"{site}/{SLUG}.html", wait_until="networkidle")
    return errors


def _answer(page, *values):
    for name, value in values:
        page.locator(f'#scForm fieldset[data-key="{name}"]:not([hidden]) input[value="{value}"] + span').click()
        page.wait_for_timeout(260)


def test_one_question_at_a_time_and_clear_result(browser_page, site):
    page = browser_page
    errors = _open(page, site)
    expect(page.locator("#scForm fieldset.sc-q:not([hidden])")).to_have_count(1)
    expect(page.locator("#scCount")).to_have_text("1 / 7")
    expect(page.locator("#scResult")).to_be_hidden()

    _answer(page, ("form", "ind"), ("years", "y3"), ("industry", "food"), ("revenue", "m1"),
            ("tax", "none"), ("overdue", "none"), ("purpose", "run"))
    result = page.locator("#scResult")
    expect(result).to_be_visible()
    assert result.get_attribute("data-level") == "clear"
    expect(result.locator("h2")).to_have_text("지금 조건이면 바로 살펴볼 수 있어요")
    expect(result.locator(".sc-r-list")).to_have_count(0)
    # 같은 형태로 받은 사례 건수는 페이지의 data-stat 값 그대로
    n = re.search(r'data-stat="ind-n">(\d+)', PAGE).group(1)
    expect(result.locator(".sc-r-cases")).to_contain_text(f"개인사업자가 받은 사례는 {n}건")
    expect(result).to_contain_text("승인 여부와 조건은 각 심사 기관이 결정합니다")
    assert not errors, errors


def test_tax_and_overdue_say_fixable_not_refused(browser_page, site):
    """체납·연체가 있어도 '안 된다'로 끝내지 않고, 정리하면 다시 볼 수 있는 경우를 말한다(대표 지시)."""
    page = browser_page
    _open(page, site)
    _answer(page, ("form", "corp"), ("years", "y7"), ("industry", "mfg"), ("revenue", "m5"),
            ("tax", "payable"), ("overdue", "past"), ("purpose", "facility"))
    result = page.locator("#scResult")
    assert result.get_attribute("data-level") == "fix"
    expect(result.locator("h2")).to_have_text("먼저 정리할 것이 2가지 있어요")
    expect(result.locator(".sc-r-list li")).to_have_count(2)
    expect(result).to_contain_text("납세증명서가 나오는 상태가 되면 다시 볼 수 있는 자금이 있어요")
    expect(result).to_contain_text("연체가 있었다고 결과가 모두 같지는 않아요")
    # 전화에서 들을 것 — 여기서 묻지 않은 항목
    expect(result.locator(".sc-r-ask")).to_contain_text("체납 세목과 금액")
    expect(result.locator(".sc-r-ask")).to_contain_text("연체 일수와 정리한 시점")


def test_current_overdue_is_told_to_settle_first(browser_page, site):
    """지금 연체 중인데 바로 된다고 말하지 않는다(브랜드 톤: 다 되는 것처럼 말하지 않는다)."""
    page = browser_page
    _open(page, site)
    _answer(page, ("form", "ind"), ("years", "y1"), ("industry", "retail"), ("revenue", "u1"),
            ("tax", "none"), ("overdue", "now"), ("purpose", "run"))
    result = page.locator("#scResult")
    assert result.get_attribute("data-level") == "stop"
    expect(result.locator("h2")).to_have_text("지금은 신청보다 정리가 먼저예요")
    expect(result).to_contain_text("대부분의 기관이 먼저 정리를 요구해요")


def test_pre_startup_skips_years_and_revenue_and_back_works(browser_page, site):
    page = browser_page
    _open(page, site)
    _answer(page, ("form", "pre"))
    expect(page.locator("#scCount")).to_have_text("2 / 5")
    expect(page.locator('#scForm fieldset[data-key="industry"]')).to_be_visible()
    page.locator("#scBack").click()
    expect(page.locator('#scForm fieldset[data-key="form"]')).to_be_visible()
    _answer(page, ("form", "pre"), ("industry", "it"), ("tax", "none"), ("overdue", "none"), ("purpose", "startup"))
    assert page.locator("#scResult").get_attribute("data-level") == "note"


def test_answers_travel_with_the_lead(browser_page, site):
    page = browser_page
    sent = []
    _open(page, site, sent)
    _answer(page, ("form", "corp"), ("years", "y3"), ("industry", "mfg"), ("revenue", "m5"),
            ("tax", "hard"), ("overdue", "none"), ("purpose", "run"))
    expect(page.locator("#lf-memo")).to_have_value(re.compile(r"^\[자가진단\] 결과: 정리 먼저 / 형태 법인사업자, 업력 3년 이상 7년 미만, 업종 제조"))
    expect(page.locator('#lf-biztype .biz-opt[aria-pressed="true"]')).to_have_text("법인사업자")
    expect(page.locator("#inline-diag-title")).to_have_text("이 결과로 무료 진단 받기")

    page.evaluate("document.getElementById('leadForm').scrollIntoView()")
    page.fill("#lf-name", "테스트")
    page.fill("#lf-phone", "010-1234-5678")
    page.check("#lf-consent")
    page.locator('#leadForm button[type="submit"]').click()
    page.wait_for_timeout(600)
    assert len(sent) == 1
    assert "[자가진단] 결과: 정리 먼저" in sent[0]["answers_text"]
    assert "체납 있고, 당장 정리하기 어려움" in sent[0]["answers_text"]
    assert "/jagajindan (정책자금 자가진단)" in sent[0]["answers_text"]
    assert sent[0]["service"] == "pfm"


def test_restart_clears_only_what_the_check_filled(browser_page, site):
    """다시 하기를 누르면 이전 진단 답이 신청 폼에 남지 않는다 — 새 진단을 끝내기 전에 신청해도 옛 체납·연체 답이 실려 가지 않게.
    고객이 직접 적은 이름·연락처는 그대로 둔다(2026-11-19 PR #132 검토 의견)."""
    page = browser_page
    sent = []
    _open(page, site, sent)
    _answer(page, ("form", "corp"), ("years", "y3"), ("industry", "mfg"), ("revenue", "m5"),
            ("tax", "hard"), ("overdue", "now"), ("purpose", "run"))
    page.fill("#lf-name", "테스트")
    page.fill("#lf-phone", "010-1234-5678")
    page.locator("#scResult .sc-r-again").click()
    expect(page.locator("#lf-memo")).to_have_value("")
    expect(page.locator("#lf-biz")).to_have_value("")
    expect(page.locator('#lf-biztype .biz-opt[aria-pressed="true"]')).to_have_count(0)
    expect(page.locator("#inline-diag-title")).to_have_text("우리 회사도 되는지 무료로 확인")
    expect(page.locator("#lf-name")).to_have_value("테스트")
    expect(page.locator("#lf-phone")).to_have_value("010-1234-5678")
    expect(page.locator("#scCount")).to_have_text("1 / 7")

    page.evaluate("document.getElementById('leadForm').scrollIntoView()")
    page.check("#lf-consent")
    page.locator('#leadForm button[type="submit"]').click()
    page.wait_for_timeout(600)
    assert len(sent) == 1
    assert "자가진단" not in sent[0]["answers_text"].replace("/jagajindan (정책자금 자가진단)", "")
    assert "체납" not in sent[0]["answers_text"] and "연체" not in sent[0]["answers_text"]


def test_fast_changes_and_back_do_not_skip_a_question(browser_page, site):
    """답을 빠르게 바꾸거나 바로 뒤로 가도 문항이 건너뛰어지지 않는다 — 넘어가는 예약은 하나만(2026-11-19 PR #132 검토 의견)."""
    page = browser_page
    _open(page, site)
    # 180ms 안에 답을 세 번 바꾼다 → 다음 질문은 2번(업력)이어야 한다
    page.evaluate("""() => {
        for (const v of ['ind', 'corp', 'ind']) {
            const r = document.querySelector('#scForm input[name="form"][value="' + v + '"]');
            r.checked = true; r.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }""")
    page.wait_for_timeout(400)
    expect(page.locator("#scCount")).to_have_text("2 / 7")
    expect(page.locator('#scForm fieldset[data-key="years"]')).to_be_visible()

    # 답을 고른 직후(예약이 걸린 상태) 바로 뒤로 간다 → 1번에 머물러야 한다
    page.evaluate("""() => {
        const r = document.querySelector('#scForm input[name="years"][value="y3"]');
        r.checked = true; r.dispatchEvent(new Event('change', { bubbles: true }));
        document.getElementById('scBack').click();
    }""")
    page.wait_for_timeout(400)
    expect(page.locator("#scCount")).to_have_text("1 / 7")
    expect(page.locator('#scForm fieldset[data-key="form"]')).to_be_visible()
