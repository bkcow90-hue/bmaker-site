"""bmaker.kr/blog (tools/build_blog.py) — 2026-10-04 WordPress.com 통합(A안, docs/wp-audit-2026-10.md).

1. 글마다 페이지가 있고, 내린 글(draft)의 페이지는 없다
2. 화면 FAQ 와 FAQPage JSON-LD 100% 일치 (규격 3절)
3. 금칙어·비용 구조 문구 0 (규격 1절·4절)
4. 블로그의 내부 링크가 전부 저장소의 실제 페이지로 간다 (404 0)
5. feed.xml 이 유효한 RSS 2.0 이고 글 수가 맞다
6. 블로그 title 이 기존 페이지 title 과 겹치지 않고, 자금 정식명으로 시작하지 않는다 (카니발 방지)
7. 첫 문단 직답·작성자 줄·면책·"본 안내는 YYYY년 M월 기준" (규격 1절·2절)
8. sitemap·llms 등록, 사이트 어디에도 blog.bmaker.kr 링크가 남지 않는다
"""
import csv, html, json, re, sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import build_blog as B  # noqa: E402

POSTS = [B.read_post(p) for p in sorted((ROOT / 'posts').glob('*.md'))]
LIVE = [p for p in POSTS if not p.get('draft')]
PAGES = sorted((ROOT / 'blog').glob('*.html'))
INDEXES = [ROOT / 'blog.html'] + sorted((ROOT / 'blog' / 'category').glob('*.html'))
ALL = PAGES + INDEXES
LD = re.compile(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', re.S)


def read(p):
    return p.read_text(encoding='utf-8')


def lds(s):
    return [json.loads(x) for x in LD.findall(s)]


def text(s):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()


def test_posts_collected():
    assert len(LIVE) >= 16, f'글 {len(LIVE)}편 — posts/ 확인'


def test_every_post_has_page_and_no_orphans():
    want = {f"{p['slug']}.html" for p in LIVE}
    have = {p.name for p in PAGES}
    assert want == have, f'빠짐 {sorted(want - have)} · 남은 파일 {sorted(have - want)}'


@pytest.mark.parametrize('path', PAGES, ids=lambda p: p.stem)
def test_faq_matches_jsonld(path):
    s = read(path)
    screen = [(text(q), text(a)) for q, a in re.findall(
        r'<details><summary>(.*?)</summary><div class="body">(.*?)</div></details>', s, re.S)]
    faq = [d for d in lds(s) if d.get('@type') == 'FAQPage']
    if not screen:
        assert not faq, f'{path.name}: 화면 FAQ 없이 FAQPage 만 있다'
        return
    assert len(faq) == 1, f'{path.name}: FAQPage {len(faq)}개'
    ld = [(q['name'], q['acceptedAnswer']['text']) for q in faq[0]['mainEntity']]
    assert screen == ld, f'{path.name}: 화면 FAQ ≠ JSON-LD\n화면 {screen}\nLD   {ld}'


@pytest.mark.parametrize('path', ALL, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_no_banned_or_fee_words(path):
    s = read(path)
    main = re.search(r'<main\b.*?</main>', s, re.S).group(0)
    # 폼(conversion 공통 마크업)은 제외하고 글·목록 본문과 메타만 본다
    main = re.sub(r'<form\b.*?</form>', '', main, flags=re.S)
    head = ' '.join(re.findall(r'<(?:title|meta[^>]+content=")([^<">]*)', s))
    body = text(main) + ' ' + head
    for find in (B.banned_hit, B.FEE.search):   # 공식 기관 고유명사(B.OFFICIAL_NAMES)는 예외
        m = find(body)
        assert not m, f'{path.name}: 금칙어 "{m.group(0)}" — …{body[max(0, m.start() - 30):m.end() + 30]}…'


def resolve(href):
    """루트 절대 경로 → 저장소 파일. 페이지가 아니면 None(검사 대상 아님)."""
    path = href.split('#')[0].split('?')[0]
    if not path.startswith('/') or path.startswith(('//', '/assets/', '/data/')):
        return None
    rel = path.strip('/')
    return ROOT / ('index.html' if rel == '' else rel + '.html')


@pytest.mark.parametrize('path', ALL, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_internal_links_resolve(path):
    bad = []
    for href in re.findall(r'href="([^"]+)"', read(path)):
        f = resolve(href)
        if f is not None and not f.exists():
            bad.append(href)
        assert 'blog.bmaker.kr' not in href, f'{path.name}: 옛 블로그 주소 {href}'
    assert not bad, f'{path.name}: 404 내부 링크 {bad}'


def test_feed_is_valid_rss():
    root = ET.parse(ROOT / 'blog' / 'feed.xml').getroot()
    assert root.tag == 'rss' and root.get('version') == '2.0'
    ch = root.find('channel')
    items = ch.findall('item')
    assert len(items) == len(LIVE)
    for it in items:
        link = it.findtext('link')
        assert link.startswith('https://bmaker.kr/blog/'), link
        assert it.findtext('guid') == link
        assert re.fullmatch(r'\w{3}, \d{2} \w{3} \d{4} 00:00:00 \+0900', it.findtext('pubDate')), it.findtext('pubDate')
        assert resolve(link.replace('https://bmaker.kr', '')).exists(), link


def test_titles_do_not_compete_with_fund_pages():
    taken = B.page_titles()
    funds = B.fund_names()
    for p in LIVE:
        assert p['title'] not in taken, f"{p['file']}: 기존 페이지 {taken.get(p['title'])} 와 title 이 같다"
        for n in funds:
            assert not p['title'].replace(' ', '').startswith(n.replace(' ', '')), \
                f"{p['file']}: 제목이 자금 정식명 '{n}' 으로 시작 — 자금 페이지 검색어를 다시 노린다"
    titles = [p['title'] for p in LIVE]
    assert len(titles) == len(set(titles)), '블로그 제목 중복'


@pytest.mark.parametrize('path', PAGES, ids=lambda p: p.stem)
def test_article_contract(path):
    s = read(path)
    main = re.search(r'<main\b.*?</main>', s, re.S).group(0)
    art = re.search(r'<article>(.*?)</article>', main, re.S).group(1).strip()
    assert art.startswith('<p class="answer">'), f'{path.name}: 첫 문단 직답이 아니다'
    assert re.search(r'<p class="byline">작성 비즈니스 메이커 · 검토 김상표\(대표\) · 최종 확인 \d{4}-\d{2}</p>', art), path.name
    assert re.search(r'본 안내는 \d{4}년 \d{1,2}월 기준', art), f'{path.name}: 기준일 문장 없음'
    # 고지 문장 통일(규격 3절, 2026-10-04): 정부·공공기관 아님 + 금융기관 아님
    assert '정부·공공기관이 아닌 정책자금 경영컨설팅 회사이며, 금융기관도 아닙니다' in art, f'{path.name}: 면책 없음'
    assert len(re.findall(r'<h1\b', s)) == 1, f'{path.name}: h1 이 1개가 아니다'
    post = [d for d in lds(s) if d.get('@type') == 'BlogPosting']
    assert len(post) == 1 and post[0]['url'] == f'https://bmaker.kr/blog/{path.stem}', path.name
    crumbs = [d for d in lds(s) if d.get('@type') == 'BreadcrumbList']
    assert crumbs and crumbs[0]['itemListElement'][1]['item'] == 'https://bmaker.kr/blog', path.name


def test_og_title_equals_title():
    for p in ALL:
        s = read(p)
        t = re.search(r'<title>(.*?)</title>', s, re.S).group(1)
        og = re.search(r'<meta property="og:title" content="([^"]*)">', s).group(1)
        assert t == og, f'{p.name}: og:title ≠ title (규격 2절)'


def test_sitemap_and_llms_list_every_post():
    sm = read(ROOT / 'sitemap.xml')
    urls = ['https://bmaker.kr/blog'] + [f"https://bmaker.kr/blog/{p['slug']}" for p in LIVE]
    for u in urls:
        assert f'<loc>{u}</loc>' in sm, f'sitemap 에 {u} 없음'
    assert not re.search(r'<loc>https://bmaker\.kr/blog/[^<]*\.html</loc>', sm)
    for name in ('llms.txt', 'llms-full.txt'):
        t = read(ROOT / name)
        block = re.search(r'<!-- blog:start -->(.*?)<!-- blog:end -->', t, re.S)
        assert block, f'{name}: blog 블록 없음'
        for p in LIVE:
            assert f"https://bmaker.kr/blog/{p['slug']}" in block.group(1), f"{name}: {p['slug']} 없음"


def test_no_old_blog_links_anywhere():
    """blog.bmaker.kr 은 폐쇄된다 — 사이트·빌더 소스 어디에도 링크를 남기지 않는다(백업·진단 문서·Worker 제외)."""
    targets = (list(ROOT.glob('*.html')) + list(ROOT.glob('industry/*.html')) + list(ROOT.glob('region/*.html'))
               + list(ROOT.glob('blog/**/*.html')) + [ROOT / 'llms.txt', ROOT / 'llms-full.txt', ROOT / 'sitemap.xml']
               + list((ROOT / 'docs').glob('*.json')) + list((ROOT / 'posts').glob('*.md')))
    hits = [p.relative_to(ROOT).as_posix() for p in targets
            if re.search(r'https?://blog\.bmaker\.kr', re.sub(r'^wp_url: .*$', '', read(p), flags=re.M))]
    assert not hits, hits


def test_redirect_map_covers_backup_and_targets_exist():
    rows = list(csv.DictReader((ROOT / 'redirects' / 'blog-map.csv').open(encoding='utf-8')))
    assert len(rows) == 40 and len({r['wp_path'] for r in rows}) == 40
    assert {r['action'] for r in rows} == {'move', 'merge', 'delete', 'index'}
    with (ROOT / 'docs' / 'wp-export-2026-10' / 'index.csv').open(encoding='utf-8-sig') as f:
        backup = {re.sub(r'^https://blog\.bmaker\.kr', '', r['url']) for r in csv.DictReader(f)}
    assert backup == {r['wp_path'] for r in rows}, backup ^ {r['wp_path'] for r in rows}
    for r in rows:
        f = resolve(r['destination'].replace('https://bmaker.kr', '') or '/')
        assert f.exists(), f"{r['wp_path']} → {r['destination']}: 페이지 없음"
        if r['action'] == 'move':
            assert r['destination'].startswith('https://bmaker.kr/blog/')
            slug = r['destination'].rsplit('/', 1)[1]
            assert any(p['slug'] == slug for p in LIVE), f'{slug}: 이전 대상인데 posts/ 에 글이 없다'


@pytest.mark.parametrize('path', ALL, ids=lambda p: p.relative_to(ROOT).as_posix())
def test_no_relative_asset_paths(path):
    """헤더·푸터를 루트 페이지에서 복사하므로 assets/ 상대 경로가 남으면 /blog/<slug> 에서 로고가 깨진다(2026-10-04 실측)."""
    bad = re.findall(r'(?:src|href)="(?!/|https?:|#|mailto:|tel:)([^"]+)"', read(path))
    assert not bad, f'{path.name}: 상대 경로 {bad[:5]}'


def test_official_name_exception_is_narrow():
    """예외는 공식 기관 고유명사 그 자체만 — 같은 금칙어를 자사 표현으로 쓰면 여전히 걸린다."""
    assert B.banned_hit('순천시 소상공인원스톱지원센터 061-752-8590') is None
    assert B.banned_hit('비즈니스 메이커 지원센터에 문의하세요')
    assert B.banned_hit('승인을 보장합니다')


@pytest.mark.parametrize('path', ALL + [ROOT / 'tools' / 'build_blog.py'], ids=lambda p: p.relative_to(ROOT).as_posix())
def test_no_control_chars_and_images_keep_src(path):
    """2026-10-04 배포 사고: 치환식의 \1 이 제어문자(0x01)로 들어가 <img src> 의 속성 이름이 사라졌다(로고 깨짐).
    '상대 경로가 없다' 검사는 통과했으므로, 제어문자와 src 없는 img 를 직접 잡는다."""
    s = read(path)
    ctrl = re.findall(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', s)
    assert not ctrl, f'{path.name}: 제어문자 {len(ctrl)}개'
    if path.suffix == '.html':
        no_src = [m for m in re.findall(r'<img\b[^>]*>', s) if not re.search(r'\ssrc="[^"]+"', m)]
        assert not no_src, f'{path.name}: src 없는 img {no_src[:2]}'
