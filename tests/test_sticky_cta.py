"""Actual mobile behavior: duplicate actions, CTA intent, focus and delivery events."""
import functools
import http.server
import os
import threading
from pathlib import Path

import pytest
try:
    from playwright.sync_api import sync_playwright, expect, Error
except ImportError:
    sync_playwright = None


def browser_unavailable(reason):
    if os.environ.get("REQUIRE_BROWSER"):
        pytest.fail(f"REQUIRE_BROWSER is set: {reason}")
    pytest.skip(reason)

ROOT = Path(__file__).resolve().parents[1]


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
        page.route("**/*", lambda route: route.continue_() if route.request.url.startswith("http://127.0.0.1:") else route.abort())
        yield page
        browser.close()


@pytest.mark.parametrize("without_observer", [False, True])
def test_sticky_tracks_hero_form_focus_and_history(browser_page, site, without_observer):
    page = browser_page
    if without_observer:
        page.add_init_script("delete window.IntersectionObserver")
    page.goto(site, wait_until="networkidle")
    sticky = page.locator(".sticky-cta")
    hero = page.locator(".hero-cta-row").first.locator("a")
    expect(hero).to_have_count(1)
    expect(hero).to_be_in_viewport()
    expect(sticky).to_be_hidden()
    expect(sticky.locator("a")).to_have_count(1)
    page.locator("#cases").scroll_into_view_if_needed()
    expect(sticky).to_be_visible()
    page.locator("#leadForm").scroll_into_view_if_needed()
    expect(sticky).to_be_hidden()
    page.locator("#lf-name").focus()
    page.evaluate("scrollTo(0, 1300)")
    expect(sticky).to_be_hidden()
    page.locator("#lf-name").evaluate("e=>e.blur()")
    page.locator("#cases").scroll_into_view_if_needed()
    expect(sticky).to_be_visible()
    page.evaluate("scrollTo(0,0);dispatchEvent(new Event('pageshow'))")
    expect(sticky).to_be_hidden()
    page.set_viewport_size({"width": 360, "height": 800})
    expect(sticky).to_be_hidden()
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_policy_cta_preserves_intent_through_form_and_delivery(browser_page, site):
    page = browser_page
    page.goto(site + "/?service=marketing", wait_until="networkidle")
    page.locator(".hero-cta-row a").first.click()
    expect(page.locator("#lf-service")).to_have_value("policy")
    click = page.evaluate("window.dataLayer.filter(e=>e.event==='consultation_click').at(-1)")
    assert click["service_category"] == "policy"
    assert click["cta_location"] == "hero"
    page.locator("#lf-name").fill("테스트")
    page.locator("#lf-phone").fill("010-0000-0000")
    page.locator("#lf-consent").check()
    page.route("**/api/lead", lambda r: r.fulfill(status=200, content_type="application/json", body='{"ok":true,"delivery":"accepted"}'))
    page.locator("#leadForm button[type=submit]").click()
    expect(page.locator("#applyMsg")).to_contain_text("상담 신청이 접수됐습니다")
    leads = page.evaluate("window.dataLayer.filter(e=>e.event==='generate_lead')")
    assert len(leads) == 1
    assert leads[0]["service_category"] == "policy"
    assert leads[0]["cta_location"] == "hero"
    assert "010" not in str(leads)


def test_general_cta_does_not_reset_service_choice(browser_page, site):
    page = browser_page
    page.goto(site + "/?service=marketing", wait_until="networkidle")
    page.locator('a[data-cta-location="guidebook"]').click()
    expect(page.locator("#lf-service")).to_have_value("marketing")


@pytest.mark.parametrize("width", [320, 390, 860, 1440])
def test_hero_photo_preserves_original_proportions(browser_page, site, width):
    page = browser_page
    page.set_viewport_size({"width": width, "height": 844})
    page.goto(site, wait_until="networkidle")
    geometry = page.locator(".hero-visual img").evaluate("""img => ({
        width: img.clientWidth, height: img.clientHeight,
        naturalWidth: img.naturalWidth, naturalHeight: img.naturalHeight
    })""")
    assert geometry["naturalWidth"] > 0
    assert abs(geometry["width"] / geometry["height"] -
               geometry["naturalWidth"] / geometry["naturalHeight"]) < 0.01


def test_business_routes_and_balanced_cases_are_visible(browser_page, site):
    import csv
    with (ROOT / "data/cases.source.csv").open(encoding="utf-8-sig") as f:
        rows = {r["사례ID"]: r for r in csv.DictReader(f)}
    page = browser_page
    page.goto(site, wait_until="networkidle")
    expect(page.locator('.audience-routes a[href="/gaein"]')).to_be_visible()
    expect(page.locator('.audience-routes a[href="/jungjingong"]')).to_be_visible()
    ids = page.locator("#cases article[data-case-id]").evaluate_all("els=>els.map(e=>e.dataset.caseId)")
    assert {rows[key]["사업 형태"] for key in ids} == {"개인", "법인"}


def test_home_case_cards_link_to_matching_ledger_records(browser_page, site):
    import csv
    with (ROOT / "data/cases.csv").open(encoding="utf-8-sig") as f:
        rows = {r["사례ID"]: r for r in csv.DictReader(f)}
    page = browser_page
    page.goto(site, wait_until="networkidle")
    cards = page.locator("#cases article[data-case-id]")
    expect(cards).to_have_count(3)
    for card in cards.all():
        key = card.get_attribute("data-case-id")
        row = rows[key]
        expect(card.locator('a')).to_have_attribute("href", "/cases#case-" + key)
        expect(card).to_contain_text(row["업종"])
        expect(card).to_contain_text(row["지역(시도)"])
        expect(card).to_contain_text(row["실행 연월"].replace("-", "."))


@pytest.mark.parametrize("width", [320, 390, 1440])
def test_growth_pages_readable_without_horizontal_overflow(browser_page, site, width):
    page = browser_page
    page.set_viewport_size({"width": width, "height": 900})
    for slug in ['education', 'education-program', 'corporate-loan-documents',
                 'working-capital-facility', 'cheongnyeon', 'jaedan', 'sanghwan', 'gaein', 'sojingong']:
        page.goto(site + '/' + slug + '.html', wait_until='networkidle')
        expect(page.locator('h1')).to_have_count(1)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), (slug, width)
        for link in page.locator('.editorial-grid a').all():
            assert link.bounding_box()['width'] > 100


def test_education_course_intent_and_print_action(browser_page, site):
    page = browser_page
    page.goto(site + '/education.html', wait_until='networkidle')
    expect(page.locator('#course-corporate')).to_contain_text('90분')
    page.locator('[data-cta-location="education_corporate"]').click()
    expect(page.locator('#lf-service')).to_have_value('education')
    page.emulate_media(reduced_motion='no-preference')
    page.goto(site + '/education-program.html', wait_until='networkidle')
    page.evaluate('() => { window.__printed=0; window.print=()=>window.__printed++; }')
    page.locator('#print-program').click()
    assert page.evaluate('window.__printed') == 1
    page.emulate_media(media='print')
    expect(page.locator('header')).to_be_hidden()
    expect(page.locator('#corporate-plan')).to_be_visible()
    expect(page.locator('#staff-checklist')).to_be_visible()
    assert page.locator('tbody tr').evaluate_all("els=>els.every(e=>getComputedStyle(e).opacity==='1')")


@pytest.mark.parametrize('width', [390, 1440])
def test_clean_hero_keeps_evidence_and_fee_below_first_section(browser_page, site, width):
    page = browser_page
    page.set_viewport_size({'width': width, 'height': 900})
    page.goto(site, wait_until='networkidle')
    hero = page.locator('.hero')
    expect(hero.locator('a')).to_have_count(1)
    expect(hero.locator('aside')).to_have_count(0)
    expect(hero).not_to_contain_text('받은 사례')
    expect(hero).not_to_contain_text('성과 보수')
    expect(page.locator('#cases .case-proof')).to_contain_text('받은 사례')
    expect(page.locator('#diagnosis')).to_contain_text('성과 보수')
    assert page.locator('#cases .case-proof').get_attribute('href') == '/cases'
    expect(hero.locator('h1')).to_contain_text('정책자금')
    backgrounds = page.evaluate("performance.getEntriesByType('resource').filter(e=>e.name.includes('hero-architecture')).map(e=>e.name)")
    variant = 'hero-architecture-mobile-v1.webp' if width <= 860 else 'hero-architecture-v1.webp'
    assert backgrounds == [site + '/assets/' + variant], 'Fetch only the background needed by this viewport'


def test_hero_motion_is_finite_readable_and_respects_reduced_motion(browser_page, site):
    page = browser_page
    page.emulate_media(reduced_motion='no-preference')
    page.goto(site, wait_until='domcontentloaded')
    timings = page.locator('.hero').evaluate("e=>e.getAnimations({subtree:true}).map(a=>a.effect.getTiming())")
    assert len(timings) >= 3, 'Title, photo and decorative light should animate'
    assert all(t['iterations'] == 1 and t['duration'] + t['delay'] <= 5000 for t in timings)
    movement = page.locator('.hero-title-line').first.evaluate("""e=>{
      const a=e.getAnimations()[0]; a.pause(); a.currentTime=0;
      const start=getComputedStyle(e).transform;
      const opacity=getComputedStyle(e).opacity;
      a.currentTime=a.effect.getTiming().duration;
      return {start,end:getComputedStyle(e).transform,opacity};
    }""")
    assert movement['start'] != movement['end']
    assert float(movement['opacity']) >= .85
    page.emulate_media(reduced_motion='reduce')
    page.reload(wait_until='networkidle')
    assert page.locator('.hero').evaluate('e=>e.getAnimations({subtree:true}).length') == 0
    expect(page.locator('#heroCta')).to_be_visible()
    assert page.locator('.hero-title-line').first.evaluate("e=>getComputedStyle(e).opacity") == '1'
