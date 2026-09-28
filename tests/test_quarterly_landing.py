"""분기별 접수 안내(/2026-4q-sosangin) — 정적 검사와 실제 브라우저 동작 검사.

문자열 검사만으로는 폼이 실제로 동작하는지 알 수 없다(규격 10절). 폼 기본값·앵커 이동·
콘솔 오류는 브라우저에서 본다. 자금 조건 숫자는 data/funds.source.csv 확정값과 대조한다.
"""
import csv
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
SLUG = "2026-4q-sosangin"
PAGE = (ROOT / f"{SLUG}.html").read_text(encoding="utf-8")

# 표에 적힌 4분기 자금 → funds.source.csv 의 자금ID
Q4_FUNDS = {
    "2026-10-06": ["ilban-gyeongyeong", "cheongnyeon", "jangaein", "gingeup"],
    "2026-10-12": ["sinyongchwiyak", "hyeoksin"],
    "2026-10-26": ["ilsijeok", "jaedojeon"],
}


def browser_unavailable(reason):
    if os.environ.get("REQUIRE_BROWSER"):
        pytest.fail(f"REQUIRE_BROWSER is set: {reason}")
    pytest.skip(reason)


def _funds():
    with (ROOT / "data/funds.source.csv").open(encoding="utf-8-sig", newline="") as f:
        return {r["자금ID"]: r for r in csv.DictReader(f)}


# ── 정적 검사 ──────────────────────────────────────────────────────────────

def test_single_h1_and_canonical():
    assert len(re.findall(r"<h1\b", PAGE)) == 1
    assert f'<link rel="canonical" href="https://bmaker.kr/{SLUG}">' in PAGE
    assert f'<meta property="og:url" content="https://bmaker.kr/{SLUG}">' in PAGE


def test_faq_screen_matches_faqpage_schema():
    """화면 FAQ 와 FAQPage JSON-LD 가 100% 일치해야 한다(규격 3절)."""
    ld = next(json.loads(m) for m in re.findall(
        r'<script type="application/ld\+json">(.*?)</script>', PAGE, re.S)
        if '"FAQPage"' in m)
    screen = re.findall(r"<details><summary>(.*?)</summary><div class=\"body\">(.*?)</div></details>", PAGE, re.S)
    assert len(screen) == 5, len(screen)
    pairs = [(q["name"], q["acceptedAnswer"]["text"]) for q in ld["mainEntity"]]
    assert pairs == [(q.replace("&amp;", "&"), a.replace("&amp;", "&")) for q, a in screen]


def test_all_jsonld_blocks_parse():
    blocks = re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', PAGE, re.S)
    assert len(blocks) == 3  # BreadcrumbList · FAQPage · WebPage
    for b in blocks:
        json.loads(b)


def test_q4_dates_and_conditions_match_funds_source():
    """공고상 접수 시작일과 한도·금리·확인일은 data/funds.source.csv 확정값만 쓴다."""
    funds = _funds()
    for start, ids in Q4_FUNDS.items():
        for fid in ids:
            row = funds[fid]
            assert row["자금명"] in PAGE, f"{fid}: 자금명이 표에 없다"
            assert f'href="/{fid}"' in PAGE, f"{fid}: 자금 상세 링크가 없다"
            assert row["최종 확인일"] in PAGE, f"{fid}: 조건 확인일 누락"
            if row["한도"]:
                num = int(re.sub(r"[^0-9]", "", row["한도"]))
                shown = f"{num:,}만원" if "만원" in row["한도"] else row["한도"]
                assert shown in PAGE, f"{fid}: 한도 {shown} 누락"
            if row["금리 방식"]:
                assert row["금리 방식"].replace("연", "연 ") in PAGE, f"{fid}: 금리 누락"
        # 10-06 그룹만 CSV 에 접수 시작일이 들어 있다 — 나머지는 공고 확인분
        assert start in PAGE, f"{start}: 접수 시작일이 표에 없다"


def test_disclaimer_and_byline_present():
    assert "작성 비즈니스 메이커 · 검토 김상표(대표)" in PAGE
    assert "본 안내는 2026년 9월 기준" in PAGE
    assert "정책자금은 대출이며 상환 의무가 있습니다" in PAGE
    assert "공식 기관에 직접 신청할 수 있고 컨설팅은 필수가 아닙니다" in PAGE


def test_no_banned_wording():
    assert "갚" not in PAGE
    assert not re.search(r"보장(?!하지)", PAGE)
    for bad in ["100% 승인", "무조건", "저신용 OK", "신용점수 부족해도", "전국 비대면 상담"]:
        assert bad not in PAGE, bad


def test_registered_in_sitemap_and_llms():
    assert f"<loc>https://bmaker.kr/{SLUG}</loc>" in (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for name in ("llms.txt", "llms-full.txt"):
        assert f"https://bmaker.kr/{SLUG}" in (ROOT / name).read_text(encoding="utf-8"), name


def test_inbound_internal_links():
    """유입 경로가 실제로 걸려 있어야 한다 — 손으로 고치는 두 페이지."""
    for name in ("sojingong.html", "funding.html"):
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
        # Local files only. Never send test contacts to the real lead API.
        page.route("**/*", lambda route: route.continue_()
                   if route.request.url.startswith("http://127.0.0.1:") else route.abort())
        yield page
        browser.close()


def test_form_opens_as_policy_and_anchor_stays_on_page(browser_page, site):
    page = browser_page
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    # 외부 CDN(폰트·스타일)은 이 픽스처가 일부러 차단한다 — 그 로드 실패는 페이지 오류가 아니다.
    page.on("console", lambda m: errors.append(m.text)
            if m.type == "error" and "Failed to load resource" not in m.text else None)
    page.goto(f"{site}/{SLUG}.html", wait_until="networkidle")

    # 폼은 한 개, 문의 분야는 정책자금으로 열린다(규격 4절)
    expect(page.locator("form#leadForm")).to_have_count(1)
    expect(page.locator("#lf-service")).to_have_value("policy")
    expect(page.locator("#lf-consent")).not_to_be_checked()
    expect(page.locator("#lf-website")).to_have_count(1)

    # 히어로 CTA 는 같은 페이지의 폼으로 내려간다 — /?service=... 로 치환되면 안 된다
    hero = page.locator(".hero .hero-cta")
    expect(hero).to_have_count(1)
    assert hero.get_attribute("href") == "#apply"
    hero.click()
    page.wait_for_timeout(300)
    assert page.url.endswith(f"/{SLUG}.html#apply"), page.url
    expect(page.locator("#lf-name")).to_be_in_viewport()

    # 필수값 검증이 살아 있다 — 빈 제출은 막힌다
    page.locator("#leadForm button[type=submit]").click()
    page.wait_for_timeout(200)
    assert page.evaluate("document.getElementById('lf-name').validity.valid") is False

    assert errors == [], errors
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "가로 스크롤 발생"


def test_generate_lead_carries_page_path(browser_page, site):
    """페이지별 전환율을 보려면 generate_lead 에 page_path 가 실려야 한다."""
    page = browser_page
    page.goto(f"{site}/{SLUG}.html", wait_until="networkidle")
    page.add_init_script("window.__events=[]")
    events = page.evaluate("""() => {
        window.__seen = [];
        window.gtag = (kind, name, params) => window.__seen.push([kind, name, params]);
        document.querySelector('a[href^="tel:"]').click();
        return window.__seen;
    }""")
    assert events, "이벤트가 잡히지 않았다"
    kind, name, params = events[0]
    assert kind == "event"
    assert params["page_path"] == f"/{SLUG}.html", params
    assert params["service_category"] == "policy", params
