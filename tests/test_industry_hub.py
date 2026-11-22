"""업종 허브 /industry 와 '안 읽힌 쪽'으로 가는 길(2026-11-22).

서치콘솔에서 업종 랜딩 10장·기업인증 3장이 '발견됨 - 색인 생성되지 않음'(한 번도 안 읽힘)이었다.
원인: 홈 개편 때 업종 타일이 빠져 업종 랜딩으로 가는 링크가 서로뿐이었다. 다시 고아가 되지 않게 지킨다.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HUB = (ROOT / "industry.html").read_text(encoding="utf-8")
LANDINGS = sorted(p.stem for p in (ROOT / "industry").glob("*.html"))
UNREAD = ["/industry", "/venture-certification", "/innobiz-mainbiz", "/research-institute"]


def test_hub_lists_every_industry_landing():
    assert len(LANDINGS) >= 12
    for slug in LANDINGS:
        assert f'href="/industry/{slug}"' in HUB, slug
    assert '<link rel="canonical" href="https://bmaker.kr/industry">' in HUB
    assert len(re.findall(r"<h1\b", HUB)) == 1
    assert "<h2>정책자금 지원제외 업종</h2>" in HUB      # 구글 자동완성 '정책자금 지원제외 업종'
    ld = [json.loads(m) for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', HUB, re.S)]
    items = next(d for d in ld if d.get("@type") == "ItemList")
    assert len(items["itemListElement"]) == len(LANDINGS)


def test_landings_point_back_to_the_hub_not_a_missing_home_anchor():
    for slug in LANDINGS:
        text = (ROOT / "industry" / f"{slug}.html").read_text(encoding="utf-8")
        assert 'href="/industry"' in text, slug
        assert "/#industry" not in text, f"{slug}: 홈에 없는 앵커(/#industry)를 가리킨다"


def test_every_page_links_to_the_unread_pages():
    """메뉴(업종 허브)와 푸터 둘째 줄이 전 페이지에 있다 — build_lastmod 가 넣는다."""
    pages = [p for p in list(ROOT.glob("*.html")) + list(ROOT.glob("industry/*.html")) + list(ROOT.glob("region/*.html"))
             + list(ROOT.glob("blog/**/*.html")) if p.name not in ("404.html", "privacy.html")]
    assert len(pages) > 150
    for p in pages:
        text = p.read_text(encoding="utf-8")
        assert text.count('<p class="foot-more">') == 1, p.name
        for href in UNREAD:
            assert f'href="{href}"' in text, (p.name, href)


def test_sitemap_and_llms_have_the_hub():
    assert "<loc>https://bmaker.kr/industry</loc>" in (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    assert "(https://bmaker.kr/industry)" in (ROOT / "llms.txt").read_text(encoding="utf-8")
