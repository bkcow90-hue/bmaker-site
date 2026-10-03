"""들어오는 링크 — sitemap 의 모든 페이지는 다른 페이지(본문·메뉴·푸터)에서 들어오는 링크가 1개 이상이다.

규격 3절(2026-10-04 중간 점검 후속 B). 고아 페이지는 크롤러가 sitemap 으로만 찾게 되고 내부 신호를 받지 못한다.
자기 자신으로 가는 링크는 세지 않는다.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = 'https://bmaker.kr'
HREF = re.compile(r'<a\b[^>]*\bhref="([^"]+)"')


def _norm(href):
    h = href.split('#')[0].split('?')[0]
    if h.startswith(SITE):
        h = h[len(SITE):]
    if not h.startswith('/') or h.startswith('//'):
        return None
    h = h[:-5] if h.endswith('.html') else h
    return h.rstrip('/') or '/'


def _pages():
    sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    out = {}
    for loc in re.findall(r'<loc>([^<]+)</loc>', sm):
        path = loc[len(SITE):].rstrip('/') or '/'
        f = ROOT / ('index.html' if path == '/' else path.lstrip('/') + '.html')
        out[path] = f
    return out


def inbound_counts(pages):
    counts = {p: 0 for p in pages}
    for src, f in pages.items():
        for h in set(filter(None, map(_norm, HREF.findall(f.read_text(encoding='utf-8'))))):
            if h != src and h in counts:
                counts[h] += 1
    return counts


def test_every_sitemap_page_has_inbound_link():
    pages = _pages()
    missing = [p for p in pages if not pages[p].exists()]
    assert not missing, f"sitemap 에 있는데 파일이 없음: {missing}"
    orphans = sorted(p for p, n in inbound_counts(pages).items() if n == 0 and p != '/')
    assert not orphans, f"들어오는 링크가 없는 페이지 {len(orphans)}개: {orphans}"


def test_norm_rules():
    assert _norm('https://bmaker.kr/region/suwon?x=1#a') == '/region/suwon'
    assert _norm('/faq.html') == '/faq'
    assert _norm('/') == '/'
    assert _norm('tel:1666-2425') is None
    assert _norm('https://example.com/faq') is None
