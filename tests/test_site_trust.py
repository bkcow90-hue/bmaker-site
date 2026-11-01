"""사이트 신뢰 흐름(2026-11-02, PR B) — 옛 회사 표기 0건 · 푸터 근거 한 줄 · Organization 단일 출처 · 공통 폼 4항목 · 문장 정리."""
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import brand
import inline_form

B = brand.load()
SKIP_DIRS = {'.git', 'node_modules', '.wrangler', 'tests'}


def _pages():
    for p in ROOT.rglob('*.html'):
        rel = p.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS | {'docs', 'tools'}:
            continue
        yield rel, p.read_text(encoding='utf-8')


def test_old_company_label_is_gone_everywhere():
    """옛 고지·정의의 "정책자금 경영컨설팅 회사" 표기 — 공개 페이지·llms·빌더·글 원본·자료 원본 0건(docs/*.md 기록 문서 제외)."""
    hits = []
    for p in ROOT.rglob('*'):
        if not p.is_file() or p.suffix not in ('.html', '.txt', '.py', '.md', '.json', '.js', '.mjs', '.xml'):
            continue
        rel = p.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS or (rel.parts[0] == 'docs' and p.suffix == '.md') or '__pycache__' in rel.parts:
            continue
        if '정책자금 경영컨설팅 회사' in p.read_text(encoding='utf-8', errors='ignore'):
            hits.append(rel.as_posix())
    assert not hits, hits


def _ledger():
    with open(ROOT / 'data' / 'cases.csv', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    return len(rows), sum(1 for r in rows if r['근거'] == '기관 안내문·약정 캡처')


def test_every_footer_carries_one_trust_line_with_ledger_numbers():
    n, ev = _ledger()
    line = (f'<p class="foot-trust"><a href="/cases">공개 원장 <span data-stat="total-n">{n:,}</span>건 · '
            f'증빙 <span data-stat="ev-n">{ev:,}</span>건</a> · <a href="/#about">대표 김상표</a> · '
            f'<a href="/geojeol">진행이 어려우면 먼저 말합니다</a></p>')
    checked = 0
    for rel, s in _pages():
        foot = re.search(r'<footer\b[^>]*>.*?</footer>', s, re.S)
        if not foot or 'class="lastmod"' not in foot.group(0):
            continue
        assert foot.group(0).count('class="foot-trust"') == 1, rel
        assert line in foot.group(0), rel
        assert s.count('class="foot-trust"') == 1, f'{rel}: 푸터 밖에도 근거 줄이 있다'
        checked += 1
    assert checked >= 120, checked   # 2026-11-02 블로그 26편 삭제 뒤 136장


def test_typed_org_nodes_follow_brand_json():
    seen = 0
    for rel, s in _pages():
        for m in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', s, re.S):
            data = json.loads(m)
            stack = [data]
            while stack:
                n = stack.pop()
                if isinstance(n, dict):
                    if n.get('@id') == 'https://bmaker.kr/#org' and '@type' in n:
                        seen += 1
                        assert n.get('description') == B['definition'], rel
                        if B['sameAs']:
                            assert n.get('sameAs') == B['sameAs'], rel
                        else:
                            assert 'sameAs' not in n, rel
                    stack.extend(n.values())
                elif isinstance(n, list):
                    stack.extend(n)
    assert seen >= 150, seen


def test_home_founder_person_carries_founder_same_as():
    s = (ROOT / 'index.html').read_text(encoding='utf-8')
    orgs = [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)]
    org = next(d for d in orgs if d.get('@id') == 'https://bmaker.kr/#org')
    assert org['founder']['@id'] == 'https://bmaker.kr/#founder' and org['founder']['@type'] == 'Person'
    assert org['founder']['sameAs'] == B['founder_sameAs']
    assert not set(B['founder_sameAs']) & set(org['sameAs'])


def test_stamp_org_drops_same_as_when_brand_list_is_empty():
    import trust_copy
    page = '<script type="application/ld+json">{"@id": "https://bmaker.kr/#org", "@type": "Organization", "sameAs": ["x"]}</script>'
    out = trust_copy.stamp_org(page, {**B, 'sameAs': []})
    node = json.loads(re.search(r'>(\{.*\})<', out).group(1))
    assert 'sameAs' not in node and node['description'] == B['definition']
    ref = '<script type="application/ld+json">{"provider": {"@id": "https://bmaker.kr/#org"}}</script>'
    assert trust_copy.stamp_org(ref, B) == ref   # @type 없는 참조 노드는 그대로


def test_inline_form_lists_four_returns_under_title():
    html = inline_form.form_html('/x', 'X')
    items = re.findall(r'<li>(.*?)</li>', html)
    assert items == ['신청해 볼 기관·자금 후보', '지금 부족한 요건', '준비 순서와 서류', '진행이 어렵다면 그 이유']
    assert html.index('inline-diag-title') < html.index('진단에서 돌려드리는 것') < html.index('lf-website')
    assert '<p class="sub">' not in html and not re.search(r'착수금|성공보수|진행비', html)
    assert '진단에서 돌려드리는 것' not in inline_form.form_html('/startup', 'S', service='startup')
    assert '진단에서 돌려드리는 것' not in inline_form.form_html('/jaedan', 'J', returns=False)


def test_builder_sentences_read_as_people_wrote_them():
    # 근거 문장을 따로 쓴 도시(data/region.source.csv '담당 문장', 예: 청주·서울 강서)는 템플릿 대상이 아니다
    with open(ROOT / 'data' / 'region.source.csv', encoding='utf-8-sig') as f:
        override = {r['도시ID'] for r in csv.DictReader(f) if (r.get('담당 문장') or '').strip()}
    templated = [s for rel, s in _pages() if rel.parts[0] == 'region' and rel.stem not in override]
    assert templated and not any('신용보증재단 업무는' in s for s in templated)
    assert all('사업장의 보증 창구는' in s for s in templated)
    for p in ROOT.glob('jaedan-*.html'):
        s = p.read_text(encoding='utf-8')
        assert '자동으로 모았습니다' not in s and '최근 10건을 표시합니다' not in s, p.name
        assert '보증으로 받은 사례입니다.' in s, p.name
    jj = (ROOT / 'jungjingong.html').read_text(encoding='utf-8')
    assert re.search(r'\(전체 [\d,]+건은 <a href="/cases">받은 사례 페이지</a>에서\)', jj)
    assert '<p>각 사례의 조건과' in (ROOT / 'business-guide.html').read_text(encoding='utf-8')
    for slug in ('sosangin', 'jungsogieop'):
        s = (ROOT / f'{slug}.html').read_text(encoding='utf-8')
        assert '<p class="sc-label">비즈니스 메이커 · 준비 상담</p>' in s, slug
