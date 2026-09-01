"""정본 URL 규약(B안) 회귀 테스트.

Cloudflare Pages는 foo.html 을 /foo 로 서빙하고 /foo.html 은 /foo 로 308 리다이렉트한다.
따라서 canonical·sitemap·og:url·내부 링크·llms.txt 는 전부 확장자 없는 주소여야 한다.
(.html 정본은 2026-08 GSC '리디렉션 오류' → 하위 페이지 색인 0 을 만들었다.)
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = ["index.html", "sojingong.html", "jungjingong.html", "bojeung.html", "certification.html", "privacy.html", "cases.html", "stats.html", "jeosinyong.html", "chaksugeum.html", "sanghwan.html", "gyehoekseo.html", "geojeol.html", "jaedan.html", "gibo.html", "sinbo.html", "schedule.html", "sinyongchwiyak.html", "jaedojeon.html", "hyeoksin.html", "cheongnyeon.html", "gaein.html"]
SLUGS = ["sojingong", "jungjingong", "bojeung", "certification", "privacy", "cases", "stats", "jeosinyong", "chaksugeum", "sanghwan", "gyehoekseo", "geojeol", "jaedan", "gibo", "sinbo", "schedule", "sinyongchwiyak", "jaedojeon", "hyeoksin", "cheongnyeon", "gaein"]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_no_html_extension_in_absolute_urls():
    """canonical / og:url / JSON-LD / sitemap / llms.txt 에 .html 주소가 없어야 한다."""
    bad = re.compile(r"https://bmaker\.kr/[A-Za-z0-9_-]+\.html")
    for name in PAGES + ["sitemap.xml", "llms.txt"]:
        assert not bad.search(_read(name)), f"{name}: .html 절대주소 잔존"


def test_internal_links_are_root_absolute():
    """페이지 간 링크는 /slug 형태(루트 절대경로)여야 한다 — 상대경로·.html 금지."""
    rel_or_html = re.compile(r'href="(?:' + "|".join(SLUGS) + r')(?:\.html)?"|href="index\.html"')
    for name in PAGES:
        assert not rel_or_html.search(_read(name)), f"{name}: 상대경로 또는 .html 내부링크 잔존"


def test_every_page_has_single_consistent_canonical():
    expected = {
        "index.html": "https://bmaker.kr/",
        "privacy.html": "https://bmaker.kr/privacy",
        **{f"{s}.html": f"https://bmaker.kr/{s}" for s in SLUGS if s != "privacy"},
    }
    for name, url in expected.items():
        html = _read(name)
        canon = re.findall(r'<link rel="canonical" href="([^"]+)">', html)
        assert canon == [url], f"{name}: canonical={canon}, expected [{url}]"
        og = re.findall(r'<meta property="og:url" content="([^"]+)">', html)
        if og:  # privacy 는 og:url 없음
            assert og == [url], f"{name}: og:url={og} ≠ canonical"


def _fund_slugs():
    """시트가 원본인 자금 페이지 — 목록은 funds.source.csv 에서 동적으로 읽는다."""
    import csv
    with open(ROOT/"data"/"funds.source.csv", encoding="utf-8-sig") as f:
        return [d["자금ID"] for d in csv.DictReader(f) if (d.get("사이트 공개") or "").strip().upper() == "Y"]


def _jaedan_slugs():
    import csv
    with open(ROOT/"data"/"jaedan.source.csv", encoding="utf-8-sig") as f:
        return [d["재단ID"] for d in csv.DictReader(f) if (d.get("사이트 공개") or "").strip().upper() == "Y"]


def test_sitemap_matches_canonicals():
    locs = re.findall(r"<loc>([^<]+)</loc>", _read("sitemap.xml"))
    expected = (["https://bmaker.kr/"]
                + [f"https://bmaker.kr/{s}" for s in SLUGS if s != "privacy"]
                + [f"https://bmaker.kr/{s}" for s in _fund_slugs() if s not in SLUGS]
                + [f"https://bmaker.kr/{s}" for s in _jaedan_slugs() if s not in SLUGS])
    assert sorted(locs) == sorted(expected)


def test_fund_pages_canonical():
    for s in _fund_slugs():
        html = _read(f"{s}.html")
        assert f'<link rel="canonical" href="https://bmaker.kr/{s}">' in html, s


def test_redirects_has_no_catch_all():
    """'/*' 캐치올은 홈(/)과 assets 까지 물어 사이트를 깨뜨린다(2026-08-20 사고). 경로별 규칙만 허용."""
    rules = [l.split() for l in _read("_redirects").splitlines() if l.strip() and not l.startswith("#")]
    for src, dst, code in rules:
        assert src != "/*", "_redirects 에 캐치올(/*) 금지"
        assert src.lstrip("/").split("/")[0] not in SLUGS, f"_redirects 가 실존 페이지 {src} 를 가로챔"
        # 302/307 임시 리다이렉트는 SEO 평가가 안 넘어가므로 금지
        if src == dst:                      # 자기참조(예: /404.html 폴백 제외)는 200 허용
            assert code == "200", f"자기참조 규칙은 200 이어야: {src}"
        else:                               # 실제 리다이렉트는 영구만(임시 302/307 금지)
            assert code in ("301", "308"), f"영구 리다이렉트(301/308)만 허용: {src} → {code}"


def test_404_page_is_noindex_and_uses_absolute_paths():
    html = _read("404.html")
    assert 'name="robots" content="noindex' in html
    # 404.html 은 어떤 깊이의 경로에서도 서빙되므로 링크·에셋은 반드시 절대경로
    assert not re.search(r'(href|src)="(?!https?://|/|#|tel:|mailto:)', html), "404.html 에 상대경로 존재"
