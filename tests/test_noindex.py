"""색인 제외 페이지(2026-11-14) — 마케팅 4장은 noindex,follow, sitemap 에 없고, 껍데기를 복사한 교육·가이드 페이지에는 번지지 않는다."""
import re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import noindex


def test_marketing_pages_are_noindex_and_out_of_sitemap():
    sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    for slug in noindex.NOINDEX:
        s = (ROOT / f'{slug}.html').read_text(encoding='utf-8')
        assert s.count(noindex.META) == 1, slug
        assert f'<loc>https://bmaker.kr/{slug}</loc>' not in sm, slug


def test_noindex_does_not_leak_into_shell_copies():
    for slug in ('education', 'education-program', 'startup-consulting-cost', 'business-guide', 'funding', 'startup'):
        s = (ROOT / f'{slug}.html').read_text(encoding='utf-8')
        assert 'name="robots"' not in s, slug


def test_guide_lists_skip_noindex_pages():
    s = (ROOT / 'business-guide.html').read_text(encoding='utf-8')
    block = re.search(r'editorial-links.*?editorial-links', s, re.S)
    assert block, 'editorial-links 블록 없음'
    for slug in set(noindex.NOINDEX) - {'marketing'}:
        assert f'href="/{slug}"' not in block.group(0), slug
