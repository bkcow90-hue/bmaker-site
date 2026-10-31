"""검색 의도 대표 페이지 7장 (규격 2절, 2026-10-31).

- title = og:title = '{메인 키워드}, {A}부터 {B}까지 | 비즈니스 메이커'
- h1 아래 첫 문단(p.intent-answer)은 메인 키워드를 포함한 40자 이내 즉답
- FAQ 에 '{메인 키워드} 조건은 무엇인가요?' 1개 — 화면과 FAQPage JSON-LD 가 같고, 답은 조건 종류만(수치 없음)
- /sme-business-loans 는 /jungsogieop 로 301, 파일·sitemap·llms·내부 링크에 남지 않는다
"""
import re
from pathlib import Path

import pytest

from test_faq_consistency import BANNED, ld_faq, screen_faq, text

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    'gaein': '개인사업자 정책자금 대출',
    'sosangin': '소상공인 사업자대출',
    'jungsogieop': '중소기업 정책자금',
    'gibo': '기술보증기금 대출',
    'sinbo': '신용보증기금 대출',
    'sojingong': '소진공 정책자금 대출',
    'jungjingong': '중진공 정책자금 대출',
}
TITLE = re.compile(r'^(?P<kw>[^,|]+), \S.*부터 \S.*까지 \| 비즈니스 메이커$')


def page(slug):
    return (ROOT / f'{slug}.html').read_text(encoding='utf-8')


@pytest.mark.parametrize('slug', PAGES)
def test_title_format_and_og_sync(slug):
    s = page(slug)
    title = text(re.search(r'<title>(.*?)</title>', s).group(1))
    og = text(re.search(r'<meta property="og:title" content="([^"]*)"', s).group(1))
    m = TITLE.match(title)
    assert m and m['kw'] == PAGES[slug], f'/{slug}: title 형식 — {title}'
    assert og == title, f'/{slug}: og:title ≠ title'


def test_titles_unique():
    titles = [text(re.search(r'<title>(.*?)</title>', page(s)).group(1)) for s in PAGES]
    assert len(set(titles)) == len(titles)


@pytest.mark.parametrize('slug', PAGES)
def test_first_paragraph_is_short_answer(slug):
    s = page(slug)
    after = s[re.search(r'</h1>', s).end():]
    first = re.search(r'<p[^>]*>(.*?)</p>', after, re.S)
    assert 'class="intent-answer"' in first.group(0), f'/{slug}: h1 다음 첫 문단이 즉답이 아니다'
    ans = text(first.group(1))
    assert PAGES[slug] in ans and len(ans) <= 40, f'/{slug}: {len(ans)}자 — {ans}'


@pytest.mark.parametrize('slug', PAGES)
def test_condition_faq_synced(slug):
    s = page(slug)
    q = f'{PAGES[slug]} 조건은 무엇인가요?'
    screen, ld = dict(screen_faq(s)), dict(ld_faq(s))
    assert q in screen and q in ld, f'/{slug}: 조건 FAQ 없음'
    assert screen[q] == ld[q], f'/{slug}: 조건 FAQ 화면·JSON-LD 불일치'
    assert not re.search(r'\d', screen[q]), f'/{slug}: 조건 FAQ 답에 수치(판정 기준)가 있다'
    assert not [w for w in BANNED if w in q + screen[q]]
    assert sum(1 for k in ld if k == q) == 1


def test_sme_business_loans_retired():
    assert not (ROOT / 'sme-business-loans.html').exists()
    assert re.search(r'^/sme-business-loans\s+/jungsogieop\s+301$',
                     (ROOT / '_redirects').read_text(encoding='utf-8'), re.M)
    for name in ('sitemap.xml', 'llms.txt', 'llms-full.txt'):
        assert 'sme-business-loans' not in (ROOT / name).read_text(encoding='utf-8'), name
    linked = [p.name for p in ROOT.glob('*.html') if 'href="/sme-business-loans' in p.read_text(encoding='utf-8')
              or 'bmaker.kr/sme-business-loans"' in p.read_text(encoding='utf-8')]
    assert not linked, f'퇴역 페이지로 가는 내부 링크: {linked}'
