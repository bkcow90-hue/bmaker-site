"""검색 색인에서 빼는 페이지 (2026-11-14 대표 "마케팅 키워드가 SEO 에 문제가 되면 빼도 된다").

정책자금 전문 사이트에 광고·바이럴·블로그 견적 페이지가 섞이면 주제 신호가 흐려진다.
GSC 상 이 페이지들의 검색어(블로그작성비용·마케팅견적 등)는 클릭 0. 서비스 안내로는 남기고
(메뉴·푸터 링크 유지) 검색 색인·sitemap·가이드 목록에서만 뺀다. build_lastmod 가 마지막에 스탬프한다.
"""
import re

NOINDEX = ('marketing', 'viral-marketing-guide', 'online-ad-guide', 'blog-marketing-cost')
META = '<meta name="robots" content="noindex,follow">'
_META_RE = re.compile(r'<meta name="robots" content="noindex,follow">\n?')


def strip(s):
    """빌더가 marketing.html 을 껍데기로 복사할 때 noindex 가 따라가지 않게 지운다."""
    return _META_RE.sub('', s)


def stamp(s, key):
    slug = key[:-5] if key.endswith('.html') else key
    if slug not in NOINDEX or META in s or '</head>' not in s:
        return s
    return s.replace('</head>', META + '\n</head>', 1)


def strip_sitemap(sm):
    for slug in NOINDEX:
        sm = re.sub(r'<url>\s*<loc>https://bmaker\.kr/' + re.escape(slug) + r'</loc>.*?</url>\n?', '', sm, flags=re.S)
    return sm
