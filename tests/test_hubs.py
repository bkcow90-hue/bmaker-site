"""허브 2장(/sosangin·/jungsogieop) — 규격 2·3·4절이 요구하는 것만 고정한다.

숫자는 전부 받은 사례에서 집계된 값이어야 하고(손으로 쓴 실적 금지), 화면 FAQ 와
FAQPage JSON-LD 는 100% 일치해야 한다. 집계에 포함된 건이 없는 경로는 숫자가 '—' 다.
"""
import csv
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_cases import hub_of, inst_bucket  # noqa: E402

HUBS = {'sosangin.html': '소상공인', 'jungsogieop.html': '중소기업'}
DETAILS = re.compile(r'<details><summary>(.*?)</summary><div class="body">(.*?)</div></details>', re.S)


def _read(name):
    return (ROOT / name).read_text(encoding='utf-8')


def _rows():
    with open(ROOT / 'data' / 'cases.source.csv', encoding='utf-8-sig', newline='') as f:
        return [r for r in csv.DictReader(f) if (r.get('사이트 공개') or '').strip().upper() == 'Y']


def _faq_ld(html):
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        data = json.loads(raw)
        if data.get('@type') == 'FAQPage':
            return [(q['name'], q['acceptedAnswer']['text']) for q in data['mainEntity']]
    return None


@pytest.mark.parametrize('page', sorted(HUBS))
def test_faq_screen_and_jsonld_are_identical(page):
    html = _read(page)
    screen = [(re.sub(r'<[^>]+>', '', q).strip(), re.sub(r'<[^>]+>', '', a).strip())
              for q, a in DETAILS.findall(html)]
    assert len(screen) == 5, f'{page}: FAQ 5개여야 한다 — {len(screen)}개'
    assert _faq_ld(html) == screen, f'{page}: FAQPage JSON-LD 가 화면 FAQ 와 다르다'
    for q, a in screen:
        first = re.split(r'(?<=다\.)|(?<=요\.)', a)[0].strip()
        assert first.endswith(('다.', '요.')), f'{page} / {q}: 첫 문장이 완결된 직답이 아니다 — {first!r}'


@pytest.mark.parametrize('page,hub', sorted(HUBS.items()))
def test_case_counts_come_from_the_ledger(page, hub):
    html = _read(page)
    mine = [r for r in _rows() if hub_of(r['기관']) == hub]
    assert mine, f'{hub} 로 분류된 건이 없다'
    assert f'받은 사례 {len(mine)}건' in html, f'{page}: 건수가 원장 집계와 다르다'
    body = html[html.index('<tbody>'):html.index('</tbody>')]
    for key in {inst_bucket(r['기관']) for r in mine}:
        n = sum(1 for r in mine if inst_bucket(r['기관']) == key)
        assert f'>{n}건</td>' in body, f'{page}: {key} {n}건이 표에 없다'


@pytest.mark.parametrize('page', sorted(HUBS))
def test_tracks_without_cases_show_a_dash_not_a_zero(page):
    """취급하는 경로는 표에 남기되, 집계에 포함된 건이 없으면 숫자는 — 로 둔다."""
    body = _read(page)
    tbody = body[body.index('<tbody>'):body.index('</tbody>')]
    assert '>0건<' not in tbody, f'{page}: 0건 표기 대신 — 를 쓴다'
    assert '<td class="num">—</td>' in tbody, f'{page}: — 행이 없다'


@pytest.mark.parametrize('page', sorted(HUBS))
def test_required_surfaces_exist(page):
    html = _read(page)
    slug = page[:-5]
    assert f'<link rel="canonical" href="https://bmaker.kr/{slug}">' in html
    assert html.count('<h1') == 1
    assert 'id="leadForm"' in html, '폼이 있어야 한다'
    for kind in ('"Service"', '"BreadcrumbList"', '"FAQPage"'):
        assert kind in html, f'{page}: {kind} JSON-LD 없음'
    assert '함께 보면 좋은 안내' in html
    assert not re.search(r'(href|src)="(?!https?://|/|#|tel:|mailto:)', html), f'{page}: 상대경로'


@pytest.mark.parametrize('page', sorted(HUBS))
def test_compliance_wording(page):
    text = re.sub(r'<script.*?</script>|<style>.*?</style>', '', _read(page), flags=re.S)
    assert '갚' not in text
    assert '지원센터' not in text
    assert '실행 기록' not in text, '신규 페이지는 "받은 사례" 표기를 쓴다'
    for m in re.finditer('보장', text):
        seg = text[max(0, m.start() - 12):m.start() + 14]
        assert '보장하지' in seg or '약속하지' in seg, f'{page}: 보장성 표현 — {seg.strip()}'
    for word in ('강서구', '마곡', '서울특별시'):
        head = text[:text.index('<footer')] if '<footer' in text else text
        assert word not in head, f'{page}: 본문에 지역어 — {word}'
