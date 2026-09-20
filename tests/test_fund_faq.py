"""자금 페이지 FAQ — 화면 텍스트와 FAQPage JSON-LD 가 100% 같아야 한다 (규격 3절).

build_funds.py 의 FAQ dict 한 곳에서 둘 다 생성하지만, 렌더링 경로가 둘(HTML escape / JSON)이라
어느 한쪽만 고쳐도 조용히 갈라진다. 그 회귀를 여기서 막는다.
검사 대상은 data/funds.source.csv 의 자금ID 전부 — 파일 목록을 손으로 적지 않는다.
"""
import csv
import html
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
LD_BLOCK = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
DETAILS = re.compile(r'<details><summary>(.*?)</summary><p class="body">(.*?)</p></details>', re.S)
TAG = re.compile(r'<[^>]+>')


def fund_ids():
    with open(ROOT / 'data' / 'funds.source.csv', encoding='utf-8-sig') as f:
        return [r['자금ID'].strip() for r in csv.DictReader(f) if r['자금ID'].strip()]


def text(s):
    """화면 마크업을 JSON-LD 와 비교 가능한 평문으로."""
    return html.unescape(TAG.sub('', s)).strip()


IDS = fund_ids()
# 이번 묶음에서 즉답·FAQ 를 넣은 자금 (나머지는 아직 FAQ 가 없어도 통과시킨다)
WITH_FAQ = {'cheongnyeon', 'hyeoksin', 'jaedojeon', 'sogongin', 'sangsaeng', 'ilsijeok'}


def test_fund_ids_loaded():
    assert len(IDS) >= 15, f'자금 소스에서 {len(IDS)}개만 읽혔다 — CSV 확인'
    assert WITH_FAQ <= set(IDS)


@pytest.mark.parametrize('fid', IDS)
def test_faq_screen_matches_jsonld(fid):
    p = ROOT / f'{fid}.html'
    assert p.exists(), f'{fid}.html 이 없다 — 체인을 먼저 돌릴 것'
    s = p.read_text(encoding='utf-8')
    screen = [(text(q), text(a)) for q, a in DETAILS.findall(s)]
    blocks = [b for b in LD_BLOCK.findall(s) if '"FAQPage"' in b]

    if fid not in WITH_FAQ:
        return  # 아직 FAQ 를 넣지 않은 자금 — 있으면 아래 규칙을 그대로 따른다
    assert len(blocks) == 1, f'{fid}: FAQPage JSON-LD 가 {len(blocks)}개'
    assert screen, f'{fid}: 화면 FAQ(details) 가 없다'

    ld = json.loads(blocks[0])
    pairs = [(e['name'], e['acceptedAnswer']['text']) for e in ld['mainEntity']]
    assert len(pairs) == len(screen), (
        f'{fid}: JSON-LD {len(pairs)}개 vs 화면 {len(screen)}개')
    for i, ((lq, la), (sq, sa)) in enumerate(zip(pairs, screen), 1):
        assert lq == sq, f'{fid} {i}번 질문 불일치\n  LD: {lq}\n  화면: {sq}'
        assert la == sa, f'{fid} {i}번 답변 불일치\n  LD: {la}\n  화면: {sa}'


@pytest.mark.parametrize('fid', sorted(WITH_FAQ))
def test_faq_has_lead_and_byline(fid):
    s = (ROOT / f'{fid}.html').read_text(encoding='utf-8')
    assert '<p class="lead">' in s, f'{fid}: 즉답 문단이 없다'
    assert '본 안내는 ' in s, f'{fid}: 기준일 문장이 없다'
    assert 'class="byline"' in s, f'{fid}: 작성자·검토자 줄이 없다'
    assert len(DETAILS.findall(s)) >= 4, f'{fid}: FAQ 가 4개 미만'


@pytest.mark.parametrize('fid', IDS)
def test_internal_links_resolve(fid):
    """FAQ·본문의 내부 링크가 실제 파일을 가리켜야 한다 (404 0)."""
    s = (ROOT / f'{fid}.html').read_text(encoding='utf-8')
    missing = []
    for href in set(re.findall(r'href="(/[a-z0-9\-/]*(?:#[a-z0-9\-]+)?)"', s)):
        path = href.split('#')[0].strip('/')
        if not path or path == '#':
            continue
        if (ROOT / f'{path}.html').exists() or (ROOT / path).exists():
            continue
        missing.append(href)
    assert not missing, f'{fid}: 존재하지 않는 내부 링크 {missing}'


def test_no_tense_dependent_wording_in_faq():
    """JSON-LD 는 방문 시점에 갱신되지 않는다 — 시점 의존 표현을 FAQ 에 두지 않는다."""
    bad = {'예정입니다', '현재 접수 중', '지금 접수 중', '오늘', '이번 주'}
    hits = []
    for fid in sorted(WITH_FAQ):
        s = (ROOT / f'{fid}.html').read_text(encoding='utf-8')
        for q, a in DETAILS.findall(s):
            body = text(q) + ' ' + text(a)
            for w in bad:
                if w in body:
                    hits.append(f'{fid}: "{w}"')
    assert not hits, f'FAQ 에 시점 의존 표현: {hits}'
