"""홈 다이어트(2026-09 hero-diet) 회귀 테스트 — 섹션 텍스트 규칙, FAQ 화면·LD 동기화, 업종별 정책자금 타일·랜딩."""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import industry  # noqa: E402


def _read(name):
    return (ROOT / name).read_text(encoding="utf-8")


def _section(html, cls):
    m = re.search(r'<section class="' + cls + r'"[^>]*>.*?</section>', html, re.S)
    assert m, cls
    return m.group(0)


def _faq_screen(html):
    return [(q, re.sub(r"<[^>]+>", "", a)) for q, a in
            re.findall(r"<details><summary>(.*?)</summary><(?:p|div class=\"body\")>(.*?)</(?:p|div)></details>", html, re.S)]


def _faq_ld(html):
    for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.S):
        data = json.loads(raw)
        if data.get("@type") == "FAQPage":
            return [(x["name"], x["acceptedAnswer"]["text"]) for x in data["mainEntity"]]
    return None


def _public_cases():
    with open(ROOT / "data" / "cases.csv", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


# ── 섹션 텍스트 다이어트 ──

def test_about_is_three_labeled_lines_without_prose():
    about = _section(_read("index.html"), "about")
    assert re.findall(r"<li><b>(.*?)</b>", about) == ["원칙", "규모", "방식"]
    assert "<p>" not in about, "회사소개에 산문 문단이 남아 있음"


def test_why_items_are_title_plus_one_line():
    why = _section(_read("index.html"), "why")
    cards = re.findall(r'<article class="why-card">(.*?)</article>', why, re.S)
    assert len(cards) == 4
    for card in cards:
        desc = re.findall(r"<p>(.*?)</p>", card, re.S)
        assert len(desc) == 1, card
        text = re.sub(r"<[^>]+>", "", desc[0])
        assert text.count(".") <= 1 and len(text) <= 45, text
    assert 'class="why-table"' in why, "비교표는 유지"
    assert "pf.kakao.com" not in why, "섹션당 버튼 1개 — 카톡은 문의 섹션·플로팅바로"


# ── FAQ: 홈 5개 + /faq 전체, 화면 = LD ──

def test_home_faq_shows_five_and_ld_matches_screen():
    home = _read("index.html")
    screen = _faq_screen(_section(home, "faq"))
    assert len(screen) == 5
    assert _faq_ld(home) == screen
    assert 'href="/faq"' in _section(home, "faq")


def test_faq_page_holds_everything_and_ld_matches_screen():
    page = _read("faq.html")
    screen = _faq_screen(page)
    assert _faq_ld(page) == screen
    assert page.count("<h1") == 1
    assert page.count('src="/assets/conversion.js"') == 1
    home = _faq_screen(_section(_read("index.html"), "faq"))
    assert home == screen[:len(home)] and len(screen) > len(home), "홈 FAQ 는 /faq 의 앞부분이어야 함"
    assert not re.search(r'(href|src)="assets/', page)


# ── 업종별 정책자금 ──

def test_industry_classifier_on_known_ledger_labels():
    expect = {
        "카페·베이커리": "eumsikjeom", "전문 음식점업": "eumsikjeom", "요식업": "eumsikjeom",
        "식품 제조·가공업": "jejo", "로봇 자동화 설비": "jejo", "반도체 장비 제조": "jejo",
        "건축자재 도소매": "dosomae", "가공식품 유통": "dosomae", "소매업": "dosomae",
        "온라인 이커머스": "online-shoppingmall", "유통업(온라인 도소매·이커머스)": "online-shoppingmall",
        "뷰티 서비스업": "miyong", "서비스업": "miyong", "건설·인테리어": "geonseol", "건설업": "geonseol",
        "교육 서비스업": None, "AI 솔루션": None, "온라인 B2B 플랫폼": None, "": None,
    }
    for label, slug in expect.items():
        assert industry.classify(label) == slug, label


def test_home_industry_tiles_match_ledger_counts():
    home = _read("index.html")
    sec = _section(home, "industry")
    tiles = re.findall(r'<a class="ind-tile" href="([^"]+)"><b>(.*?)</b><span>받은 사례 (\d+)건</span>', sec)
    assert [t[1] for t in tiles] == ["음식점·카페", "제조업", "도소매·유통", "온라인쇼핑몰", "미용·서비스", "건설·인테리어"]
    rows = _public_cases()
    for href, name, n in tiles:
        ind = next(i for i in industry.INDUSTRIES if i["name"] == name)
        assert int(n) == sum(1 for r in rows if industry.classify(r["업종"]) == ind["slug"]), name
        assert href == (f"/industry/{ind['slug']}" if ind["landing"] else "/cases"), name
        target = ROOT / (href.strip("/") + ".html")
        assert target.exists(), href


def test_industry_landing_follows_intent_page_rules():
    rows = _public_cases()
    landings = [i for i in industry.INDUSTRIES if i["landing"]]
    assert [i["slug"] for i in landings] == ["eumsikjeom"]
    for ind in landings:
        page = _read(f"industry/{ind['slug']}.html")
        # URL·h1 이 검색 질문 그대로
        assert re.findall(r"<h1[^>]*>(.*?)</h1>", page) == [ind["question"]]
        assert f'<link rel="canonical" href="https://bmaker.kr/industry/{ind["slug"]}">' in page
        # h1 바로 다음 문단 = 40자 이내 직답
        answer = re.search(r"</h1>\s*<p[^>]*>(.*?)</p>", page, re.S).group(1)
        assert answer.startswith("네.") and len(answer) <= industry.ANSWER_MAX, answer
        # 받은 사례 표 = 원장 업종 필터 결과 전체
        mine = [r for r in rows if industry.classify(r["업종"]) == ind["slug"]]
        body = re.search(r"<!-- industry-cases:start -->(.*?)<!-- industry-cases:end -->", page, re.S).group(1)
        trs = re.findall(r"<tr>(.*?)</tr>", body)
        assert len(trs) == len(mine) > 0
        ids = re.findall(r'href="/cases#row-([^"]+)"', body)
        assert sorted(ids) == sorted(r["사례ID"] for r in mine)
        # 공통 규격
        assert page.count('src="/assets/conversion.js"') == 1
        assert 'class="nav-menu"' in page
        assert not re.search(r'(href|src)="(?!https?://|/|#|tel:|mailto:)', page), "중첩 경로라 상대경로 금지"
        assert "갚" not in page


# ── 조건 밴드: 원장에서 자동 (히어로 아님, 최근 사례 섹션 제목 아래) ──

def test_recent_section_shows_ledger_condition_band():
    home = _read("index.html")
    recent = _section(home, "recent")
    band = re.search(r"<!-- home-band:start -->(.*?)<!-- home-band:end -->", recent, re.S)
    assert band, "조건 밴드 마커가 최근 사례 섹션에 없다"
    text = band.group(1)

    rows = _public_cases()
    amts = sorted(int(r["실행 금액(만원)"]) for r in rows)
    rates = sorted(float(m.group(1)) for r in rows
                   for m in [re.search(r"(\d+(?:\.\d+)?)", r["금리(실행 시점)"] or "")] if m)
    hi = f"{amts[-1] / 10000:g}억원" if amts[-1] >= 10000 else f"{amts[-1]:,}만원"
    assert text.startswith(f"실행 사례 기준 금액 {amts[0]:,}만원~{hi}"), text
    assert f"금리 연 {rates[0]:g}%~{rates[-1]:g}%" in text, text
    assert text.endswith(f", {len(rows)}건)"), text

    # 히어로에는 넣지 않는다 · 기관 최대치·자격 관련 표현 금지
    hero = re.search(r'<section class="hero">.*?</section>', home, re.S).group(0)
    assert "home-band" not in hero
    assert "최대" not in text and "신용" not in text


def test_condition_band_sub_lines_stay_within_two():
    """규격: 섹션당 서브는 최대 2줄."""
    recent = _section(_read("index.html"), "recent")
    assert len(re.findall(r'<p class="sub[^"]*">', recent)) <= 2
