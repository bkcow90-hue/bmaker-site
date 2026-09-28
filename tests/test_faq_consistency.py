"""FAQ 일관성 — 화면 텍스트와 FAQPage JSON-LD 가 100% 같아야 한다 (규격 3절).

대상: 자금 페이지 전부(data/funds.source.csv 의 자금ID) + 즉답·FAQ 를 넣은 정적 5장.
두 경로(HTML escape / JSON)로 따로 렌더되므로 한쪽만 고치면 조용히 갈라진다. 그 회귀를 막는다.
금칙어·시점 의존 표현·내부 링크도 같은 텍스트에서 함께 검사한다.

아직 범위 밖: FAQPage 를 가진 나머지 26장(재단 18 · /gaein · /jungjingong 등)은 마크업이 제각각이라
B묶음에서 마크업을 통일한 뒤 여기에 합친다(docs/plan-b-batch.md).
"""
import csv
import html
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

LD_BLOCK = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
# 자금 페이지는 <p class="body">, 정적 페이지는 <div class="body"> 를 쓴다
DETAILS = re.compile(
    r'<details[^>]*>\s*<summary[^>]*>(.*?)</summary>\s*'
    r'<(?P<t>p|div)[^>]*class="body"[^>]*>(.*?)</(?P=t)>\s*</details>', re.S)
LEAD = re.compile(r'<p class="lead">(.*?)</p>', re.S)
TAG = re.compile(r'<[^>]+>')

# 금칙어 — 규격 1절. FAQ·즉답 텍스트 전체에 적용한다.
BANNED = ['갚', '지원센터', '100%', '보장', '무조건']
# 예외: 우리 주장이 아니라 '피해야 할 신호' 로 인용한 경우만. 새로 추가하려면 이유를 적을 것.
BANNED_ALLOW = {
    ('chaksugeum.html', '100%'): "위험 신호로 인용 — '100% 승인'을 약속하는 업체를 피하라는 문장",
}
# 시점 의존 표현 — JSON-LD 는 방문 시점에 갱신되지 않는다
TENSE = ['예정입니다', '현재 접수 중', '지금 접수 중', '오늘', '이번 주']

STATIC = ['gyehoekseo.html', 'sanghwan.html', 'chaksugeum.html', 'geojeol.html', 'sinbo.html']
# 즉답·FAQ 를 넣은 자금 페이지
FUND_WITH_FAQ = ['cheongnyeon', 'hyeoksin', 'jaedojeon', 'sogongin', 'sangsaeng', 'ilsijeok',
                 'hyeoksin-jolup', 'hyeoksin-sahoe', 'matching']


def fund_ids():
    with open(ROOT / 'data' / 'funds.source.csv', encoding='utf-8-sig') as f:
        return [r['자금ID'].strip() for r in csv.DictReader(f) if r['자금ID'].strip()]


IDS = fund_ids()
ALL_FAQ_PAGES = [f'{i}.html' for i in FUND_WITH_FAQ] + STATIC


def text(s):
    """화면 마크업을 JSON-LD 와 비교 가능한 평문으로."""
    return re.sub(r'\s+', ' ', html.unescape(TAG.sub('', s))).strip()


def screen_faq(s):
    return [(text(m.group(1)), text(m.group(3))) for m in DETAILS.finditer(s)]


def ld_faq(s):
    blocks = [b for b in LD_BLOCK.findall(s) if '"FAQPage"' in b]
    if not blocks:
        return None
    assert len(blocks) == 1, f'FAQPage 스크립트가 {len(blocks)}개'
    ld = json.loads(blocks[0])
    return [(text(e['name']), text(e['acceptedAnswer']['text'])) for e in ld['mainEntity']]


def test_targets_exist():
    assert len(IDS) >= 15, f'자금 소스에서 {len(IDS)}개만 읽혔다'
    assert set(FUND_WITH_FAQ) <= set(IDS)
    for name in ALL_FAQ_PAGES:
        assert (ROOT / name).exists(), f'{name} 이 없다 — 체인을 먼저 돌릴 것'


@pytest.mark.parametrize('name', ALL_FAQ_PAGES)
def test_screen_matches_jsonld(name):
    s = (ROOT / name).read_text(encoding='utf-8')
    screen, pairs = screen_faq(s), ld_faq(s)
    assert pairs is not None, f'{name}: FAQPage JSON-LD 가 없다'
    assert screen, f'{name}: 화면 FAQ(details) 가 없다'
    assert len(pairs) == len(screen), f'{name}: JSON-LD {len(pairs)}개 vs 화면 {len(screen)}개'
    for i, ((lq, la), (sq, sa)) in enumerate(zip(pairs, screen), 1):
        assert lq == sq, f'{name} {i}번 질문 불일치\n  LD: {lq}\n  화면: {sq}'
        assert la == sa, f'{name} {i}번 답변 불일치\n  LD: {la}\n  화면: {sa}'


@pytest.mark.parametrize('name', ALL_FAQ_PAGES)
def test_no_banned_words(name):
    """규격 1절 금칙어 — FAQ·즉답 텍스트 전부."""
    s = (ROOT / name).read_text(encoding='utf-8')
    chunks = [text(x) for x in LEAD.findall(s)] + [f'{q} {a}' for q, a in screen_faq(s)]
    hits = []
    for w in BANNED:
        for c in chunks:
            if w in c and (name, w) not in BANNED_ALLOW:
                i = c.find(w)
                hits.append(f'"{w}" → …{c[max(0, i - 40):i + 40]}…')
    assert not hits, f'{name} 금칙어:\n  ' + '\n  '.join(hits)


@pytest.mark.parametrize('name', ALL_FAQ_PAGES)
def test_no_tense_dependent_wording(name):
    s = (ROOT / name).read_text(encoding='utf-8')
    chunks = [text(x) for x in LEAD.findall(s)] + [f'{q} {a}' for q, a in screen_faq(s)]
    hits = [w for w in TENSE for c in chunks if w in c]
    assert not hits, f'{name}: 시점 의존 표현 {sorted(set(hits))}'


@pytest.mark.parametrize('name', [f'{i}.html' for i in IDS] + STATIC)
def test_internal_links_resolve(name):
    """내부 링크가 실제 파일을 가리켜야 한다 (404 0). 앵커(#)는 떼고 본다."""
    s = (ROOT / name).read_text(encoding='utf-8')
    missing = []
    for href in set(re.findall(r'href="(/[a-z0-9\-/]*(?:#[a-z0-9\-]+)?)"', s)):
        path = href.split('#')[0].strip('/')
        if not path:
            continue
        if (ROOT / f'{path}.html').exists() or (ROOT / path).exists():
            continue
        missing.append(href)
    assert not missing, f'{name}: 존재하지 않는 내부 링크 {missing}'


@pytest.mark.parametrize('name', [f'{i}.html' for i in FUND_WITH_FAQ])
def test_fund_pages_have_lead_and_byline(name):
    s = (ROOT / name).read_text(encoding='utf-8')
    assert '<p class="lead">' in s or name.replace('.html', '') not in (
        'cheongnyeon', 'hyeoksin', 'jaedojeon', 'sogongin', 'sangsaeng', 'ilsijeok'), f'{name}: 즉답 없음'
    assert '본 안내는 ' in s, f'{name}: 기준일 문장 없음'
    assert 'class="byline"' in s, f'{name}: 작성자·검토자 줄 없음'
    assert len(screen_faq(s)) >= 4, f'{name}: FAQ 4개 미만'


@pytest.mark.parametrize('name', STATIC)
def test_static_pages_have_byline(name):
    s = (ROOT / name).read_text(encoding='utf-8')
    assert 'class="byline"' in s, f'{name}: 작성자·검토자 줄 없음'
    assert len(screen_faq(s)) >= 6, f'{name}: FAQ 6개 미만'
