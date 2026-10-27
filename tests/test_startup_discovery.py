"""Startup traffic must preserve consultation intent and honest review attribution."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_blog as B
from test_sticky_cta import browser_page, site


def post(category='guide', reviewed=False):
    return dict(title='창업을 준비할 때 비교할 것은?', summary='예산과 운영 조건을 함께 비교합니다.',
                slug='sample-startup', date='2026-10-28', updated='2026-10-28',
                category=category, tags=[], image='/assets/og.png', reviewed=reviewed,
                body='예산과 운영 조건을 함께 비교합니다.\n\n## 준비\n\n조건을 정리합니다.\n')


def test_startup_intent_reaches_form_and_hero_without_changing_policy_default():
    p = post('startup')
    startup = B.build_post(p, [p], {}, '', '', '')
    assert '<body data-service="startup">' in startup
    assert 'data-consultation-service="startup"' in startup
    assert re.search(r'id="lf-service"[^>]+value="startup"', startup)
    p = post()
    policy = B.build_post(p, [p], {}, '', '', '')
    assert '<body data-service="policy">' in policy
    assert re.search(r'id="lf-service"[^>]+value="policy"', policy)


def test_unreviewed_content_never_claims_founder_review():
    p = post()
    page = B.build_post(p, [p], {}, '', '', '')
    assert '검토 김상표' not in page
    assert '"reviewedBy"' not in page
    assert '"lastReviewed"' not in page
    assert '자료 확인 2026-10-28' in page


def test_existing_reviewed_article_keeps_review_signal():
    p = post(reviewed=True)
    page = B.build_post(p, [p], {}, '', '', '')
    assert '검토 김상표' in page and '"reviewedBy"' in page


def test_startup_page_render_is_repeatable_and_faq_matches():
    import startup_page
    original = (ROOT / 'startup.html').read_text(encoding='utf-8')
    first = startup_page.render_page(original)
    assert startup_page.render_page(first) == first
    assert first.count('<h1') == 1
    screen = re.findall(r'<details><summary>(.*?)</summary><p>(.*?)</p></details>', first, re.S)
    nodes = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', first, re.S)]
    faq = next(x for x in nodes if x.get('@type') == 'FAQPage')
    assert screen == [(q['name'], q['acceptedAnswer']['text']) for q in faq['mainEntity']]
    assert 'href="/#about"' in first
    assert 'data-service="startup"' in first


def test_startup_mobile_layout_and_consultation_intent(browser_page, site):
    page = browser_page
    for path in ['startup.html', 'blog/category/startup.html', 'blog/franchise-comparison-sales-profit.html']:
        page.goto(site + '/' + path, wait_until='networkidle')
        assert page.evaluate('document.documentElement.scrollWidth') <= page.viewport_size['width'], path
        assert page.locator('#lf-service').input_value() == 'startup', path
        assert page.locator('#leadForm button[type="submit"]').inner_text() == '창업 비교 상담 신청', path
        page.locator('#heroCta').click()
        assert page.locator('#leadForm').is_visible(), path
        assert page.locator('#lf-service').input_value() == 'startup', path
        assert not page.locator('#lf-consent').is_checked(), path
