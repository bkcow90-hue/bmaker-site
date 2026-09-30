"""도시 페이지(/region/<city>) 생성 규칙 — 규격 8-1 (도어웨이 방지).

1. 공식 출처 사실 3개 이상, 그중 시·군 자금(공고 단위) 1건 이상. 도 전체 사업(province-fund)은 세지 않음.
   재단 지점 근거는 재단·지자체 공식 도메인
2. 도시 페이지끼리 사실 조합(data-fact-id 집합) 중복 금지
3. 도시명을 지운 본문의 5어절 조각 자카드 유사도 0.6 초과 실패
4. 도시 → /jaedan-<시도>, 그 재단 페이지 → 도시 페이지 양방향 링크
5. 사실 확인일이 빌드일 기준 90일 초과면 실패

region/*.html 이 아직 없으면 실제 페이지 검사는 대상 0건으로 통과한다. 규칙 함수 자체는 아래 합성 예시로 고정한다.
페이지 계약: <main data-city="수원시" data-jaedan="jaedan-gyeonggi">, 사실 요소마다
data-fact · data-fact-id · data-source · data-checked(YYYY-MM-DD).
"""
import datetime, itertools, re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from builddate import build_date  # noqa: E402

MIN_FACTS = 3
MAX_SIMILARITY = 0.6
MAX_AGE_DAYS = 90
SHINGLE = 5
CITY_FUND = 'city-fund'
COUNTED_KINDS = {'jaedan-branch', 'semas-center', CITY_FUND}   # 그 외(province-fund 등 "참고")는 세지 않는다
# 정부(*.go.kr, 서울 자치구 *.seoul.kr) · 소진공 · 17개 광역 신용보증재단 공식 도메인 (docs/region/ 조사 2026-09-30)
GOV_DOMAINS = ('go.kr', 'seoul.kr')
JAEDAN_DOMAINS = (
    'seoulshinbo.co.kr', 'busansinbo.or.kr', 'dgsinbo.or.kr', 'icsinbo.or.kr', 'gjsinbo.or.kr',
    'sinbo.or.kr', 'ulsanshinbo.co.kr', 'sjsinbo.or.kr', 'gcgf.or.kr', 'gwsinbo.or.kr',
    'cbsinbo.or.kr', 'cnsinbo.co.kr', 'jbcredit.or.kr', 'jnsinbo.or.kr', 'gbsinbo.co.kr',
    'gnsinbo.or.kr', 'jcgf.or.kr',
)
OFFICIAL_DOMAINS = GOV_DOMAINS + ('semas.or.kr',) + JAEDAN_DOMAINS


# ── 페이지 파싱 ─────────────────────────────────────────────
class _Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.city = self.jaedan = None
        self.facts, self.links, self._text = [], set(), []
        self._main = self._skip = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'main':
            self._main += 1
            self.city = self.city or a.get('data-city')
            self.jaedan = self.jaedan or a.get('data-jaedan')
        elif self._main and tag in ('script', 'style'):
            self._skip += 1
        if tag == 'a' and a.get('href'):
            self.links.add(a['href'].split('#')[0].split('?')[0].rstrip('/'))
        if 'data-fact' in a:
            self.facts.append({'kind': a.get('data-fact') or '', 'id': a.get('data-fact-id') or '',
                               'source': a.get('data-source') or '', 'checked': a.get('data-checked') or ''})

    def handle_endtag(self, tag):
        if tag == 'main' and self._main:
            self._main -= 1
        elif tag in ('script', 'style') and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if self._main and not self._skip:
            self._text.append(data)


def parse(html, slug='?'):
    p = _Page()
    p.feed(html)
    return {'slug': slug, 'city': p.city or '', 'jaedan': p.jaedan or '', 'facts': p.facts,
            'links': p.links, 'text': ' '.join(p._text)}


# ── 규칙 (오류 문자열 목록을 돌려준다) ─────────────────────────
def is_official(url, domains=OFFICIAL_DOMAINS):
    m = re.match(r'^https://([^/:?#]+)', url or '')
    return bool(m) and any(m.group(1) == d or m.group(1).endswith('.' + d) for d in domains)


def fact_key(f):
    """사실의 동일성. 시·군 자금은 공고 단위(출처 URL)로 센다 — 한 공고의 세부 항목을 따로 세지 않음."""
    return (f['kind'], f['source'] if f['kind'] == CITY_FUND else f['id'])


def fact_errors(page, today):
    """규칙 1·5 — 공식 출처 사실 수, 시·군 자금 1건 이상, 지점 근거 도메인, 확인일."""
    errs, ok = [], []
    for f in page['facts']:
        tag = f"{page['slug']} 사실 {f['kind']}:{f['id'] or '?'}"
        if not f['kind'] or not f['id']:
            errs.append(f'{tag} — data-fact·data-fact-id 누락'); continue
        if not is_official(f['source']):
            errs.append(f"{tag} — 공식 출처 아님: {f['source'] or '(없음)'}"); continue
        if f['kind'] == 'jaedan-branch' and not is_official(f['source'], GOV_DOMAINS + JAEDAN_DOMAINS):
            errs.append(f"{tag} — 지점 관할 근거는 재단 공식 사이트 또는 지자체 공고여야 함: {f['source']}"); continue
        try:
            checked = datetime.date.fromisoformat(f['checked'])
        except ValueError:
            errs.append(f"{tag} — 확인일 형식 오류: {f['checked'] or '(없음)'}"); continue
        if (today - checked).days > MAX_AGE_DAYS:
            errs.append(f'{tag} — 확인일 {checked} 이 {MAX_AGE_DAYS}일 초과, 재확인 필요')
        ok.append(f)
    keys = {fact_key(f) for f in ok if f['kind'] in COUNTED_KINDS}
    if len(keys) < MIN_FACTS:
        errs.append(f"{page['slug']} — 공식 출처 사실 {len(keys)}개 (최소 {MIN_FACTS}, 도 전체 사업 제외)")
    if not any(k == CITY_FUND for k, _ in keys):
        errs.append(f"{page['slug']} — 시·군 자금 공고가 없음 (1건 이상 필수)")
    return errs


def fact_set(page):
    return frozenset(fact_key(f) for f in page['facts'] if f['kind'] in COUNTED_KINDS)


def duplicate_errors(pages):
    """규칙 2 — 사실 조합이 같은 도시 페이지."""
    return [f"{a['slug']} ↔ {b['slug']} — 사실 조합이 같음"
            for a, b in itertools.combinations(pages, 2) if fact_set(a) == fact_set(b)]


def _city_names(city):
    names = {city}
    base = re.sub(r'(특별자치시|특별자치도|광역시|특별시|시|군|구)$', '', city.split()[-1] if city else '')
    if len(base) >= 2:
        names.add(base)
    return {n for n in names if n}


def shingles(text, names):
    for n in sorted(names, key=len, reverse=True):
        text = text.replace(n, ' ')
    words = text.split()
    return {tuple(words[i:i + SHINGLE]) for i in range(max(len(words) - SHINGLE + 1, 0))}


def similarity(a, b):
    names = _city_names(a['city']) | _city_names(b['city'])
    sa, sb = shingles(a['text'], names), shingles(b['text'], names)
    return len(sa & sb) / len(sa | sb) if sa | sb else 1.0


def similarity_errors(pages):
    """규칙 3 — 도시명 제외 본문 유사도."""
    out = []
    for a, b in itertools.combinations(pages, 2):
        s = similarity(a, b)
        if s > MAX_SIMILARITY:
            out.append(f"{a['slug']} ↔ {b['slug']} — 본문 유사도 {s:.2f} > {MAX_SIMILARITY}")
    return out


def link_errors(pages, jaedan_links):
    """규칙 4 — jaedan_links: {재단ID: 그 재단 페이지의 href 집합}."""
    errs = []
    for p in pages:
        if not p['city'] or not p['jaedan']:
            errs.append(f"{p['slug']} — <main data-city·data-jaedan> 누락"); continue
        if '/' + p['jaedan'] not in p['links']:
            errs.append(f"{p['slug']} — /{p['jaedan']} 로 가는 링크 없음")
        if '/region/' + p['slug'] not in jaedan_links.get(p['jaedan'], set()):
            errs.append(f"{p['jaedan']} — /region/{p['slug']} 로 가는 링크 없음")
    return errs


# ── 실제 페이지 검사 ─────────────────────────────────────────
def _region_pages():
    return [parse(p.read_text(encoding='utf-8'), p.stem) for p in sorted((ROOT / 'region').glob('*.html'))]


def _jaedan_links(ids):
    out = {}
    for j in ids:
        f = ROOT / f'{j}.html'
        out[j] = parse(f.read_text(encoding='utf-8'))['links'] if f.exists() else set()
    return out


def test_region_pages_follow_rules():
    pages = _region_pages()
    today = build_date()
    errs = [e for p in pages for e in fact_errors(p, today)]
    errs += duplicate_errors(pages)
    errs += similarity_errors(pages)
    errs += link_errors(pages, _jaedan_links({p['jaedan'] for p in pages if p['jaedan']}))
    assert not errs, '규격 8-1 위반:\n' + '\n'.join(errs)


def test_sitemap_region_urls_match_pages():
    """sitemap 의 /region/ URL 과 region/*.html 이 1:1 — 생성 금지된 도시가 sitemap 에 남지 않게."""
    sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    in_sitemap = set(re.findall(r'<loc>https://bmaker\.kr/region/([^<]+)</loc>', sm))
    on_disk = {p.stem for p in (ROOT / 'region').glob('*.html')}
    assert in_sitemap == on_disk, f'sitemap 에만: {sorted(in_sitemap - on_disk)} / 파일만: {sorted(on_disk - in_sitemap)}'


# ── 규칙 함수 고정 (합성 예시) ────────────────────────────────
TODAY = datetime.date(2026, 10, 1)
GG = 'https://www.gcgf.or.kr/gcgf/bg/gd/brnchGd.do?mi=1344'
SEMAS = 'https://www.semas.or.kr/web/ORG01/ORG0111/ORG011102.kmdc'


def _fact(kind, fid, source, checked='2026-10-01'):
    return (f'<li data-fact="{kind}" data-fact-id="{fid}" data-source="{source}" '
            f'data-checked="{checked}">{fid}</li>')


def _page(slug, city, facts, body, jaedan='jaedan-gyeonggi', links=('/jaedan-gyeonggi',)):
    a = ''.join(f'<a href="{h}">재단 안내</a>' for h in links)
    return parse(f'<main data-city="{city}" data-jaedan="{jaedan}"><h1>{city} 소상공인 자금</h1>'
                 f'<ul>{"".join(facts)}</ul><p>{body}</p>{a}</main>', slug)


SUWON = [_fact('jaedan-branch', '경기신보/수원지점', GG),
         _fact('semas-center', '소진공/수원센터', SEMAS),
         _fact('city-fund', '수원시/2026 중소기업육성자금', 'https://www.suwon.go.kr/notice/1')]


def test_rule1_three_official_facts_pass():
    assert fact_errors(_page('suwon', '수원시', SUWON, '본문'), TODAY) == []


def test_rule1_contacts_only_fails():
    p = _page('suwon', '수원시', SUWON[:2] + [_fact('semas-center', '소진공/수원남부센터', SEMAS)], '본문')
    assert any('시·군 자금 공고가 없음' in e for e in fact_errors(p, TODAY))


def test_rule1_city_funds_count_per_notice():
    notice = 'https://www.suwon.go.kr/notice/2'
    p = _page('suwon', '수원시', [SUWON[0], _fact('city-fund', '수원시/소상공인 특례보증', notice),
                                  _fact('city-fund', '수원시/특례보증 수수료 지원', notice)], '본문')
    assert any('사실 2개' in e for e in fact_errors(p, TODAY))   # 한 공고의 세부 항목 2개 = 1건


def test_rule1_province_fund_not_counted():
    gg = _fact('province-fund', '경기도/소상공인 경영자금', 'https://www.gg.go.kr/notice/9')
    p = _page('suwon', '수원시', SUWON[:1] + SUWON[2:] + [gg], '본문')
    assert any('사실 2개' in e for e in fact_errors(p, TODAY))
    assert fact_errors(_page('suwon', '수원시', SUWON + [gg], '본문'), TODAY) == []   # 참고 표시는 허용


def test_rule1_branch_evidence_must_be_jaedan_or_gov():
    p = _page('suwon', '수원시', [_fact('jaedan-branch', '경기신보/수원지점', SEMAS)] + SUWON[1:], '본문')
    assert any('지점 관할 근거' in e for e in fact_errors(p, TODAY))
    gov = _page('suwon', '수원시', [_fact('jaedan-branch', '경기신보/수원지점', 'https://www.suwon.go.kr/notice/1')] + SUWON[1:], '본문')
    assert fact_errors(gov, TODAY) == []


def test_rule1_too_few_or_unofficial_fails():
    two = _page('suwon', '수원시', SUWON[:1] + SUWON[2:], '본문')
    assert any('최소 3' in e for e in fact_errors(two, TODAY))
    blog = _page('suwon', '수원시', SUWON[:2] + [_fact('city-fund', '수원시/블로그', 'https://blog.naver.com/x')], '본문')
    errs = fact_errors(blog, TODAY)
    assert any('공식 출처 아님' in e for e in errs) and any('최소 3' in e for e in errs)
    assert not is_official('https://go.kr.evil.com/x') and not is_official('http://www.suwon.go.kr/')


def test_rule2_same_fact_set_fails():
    a = _page('a', '가시', SUWON, '가 본문')
    b = _page('b', '나시', SUWON, '전혀 다른 나 본문')
    assert duplicate_errors([a, b]) and not duplicate_errors([a, _page('c', '다시', SUWON[1:] + [
        _fact('city-fund', '다시/특례보증', 'https://www.da.go.kr/1')], '다 본문')])


def test_rule3_similarity_ignores_city_names():
    tpl = '{c} 소상공인은 {c} 관할 재단 지점과 소진공 센터에서 상담을 받을 수 있고 {c} 자체 육성자금은 매년 초 공고됩니다 ' * 3
    a = _page('suwon', '수원시', SUWON, tpl.format(c='수원'))
    b = _page('yongin', '용인시', [], tpl.format(c='용인'))
    assert similarity(a, b) > MAX_SIMILARITY and similarity_errors([a, b])
    c = _page('yongin', '용인시', [], '처인구 기흥구 수지구 세 구에 따라 신청 창구가 나뉘고 올해 특례보증은 상반기 조기 마감되었습니다')
    assert not similarity_errors([a, c])


def test_rule4_links_both_ways():
    p = _page('suwon', '수원시', SUWON, '본문')
    assert link_errors([p], {'jaedan-gyeonggi': {'/region/suwon'}}) == []
    assert any('jaedan-gyeonggi — /region/suwon' in e for e in link_errors([p], {'jaedan-gyeonggi': set()}))
    no_up = _page('suwon', '수원시', SUWON, '본문', links=())
    assert any('/jaedan-gyeonggi 로 가는 링크 없음' in e for e in link_errors([no_up], {'jaedan-gyeonggi': {'/region/suwon'}}))


def test_rule5_stale_fact_fails():
    old = [SUWON[0], SUWON[1], _fact('city-fund', '수원시/2026 중소기업육성자금', 'https://www.suwon.go.kr/notice/1', '2026-07-03')]
    assert fact_errors(_page('suwon', '수원시', old, '본문'), TODAY) == []          # 7/3 → 10/1 = 90일, 통과
    older = old[:2] + [_fact('city-fund', '수원시/2026 중소기업육성자금', 'https://www.suwon.go.kr/notice/1', '2026-07-02')]  # 91일
    assert any('90일 초과' in e for e in fact_errors(_page('suwon', '수원시', older, '본문'), TODAY))
