"""지역 재단 페이지 무결성 — 소스 공개 건수와 생성물 일치, 허브 그리드, 금지 표현."""
import csv, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def _rows():
    with open(ROOT/"data"/"jaedan.source.csv", encoding="utf-8-sig") as f:
        return [d for d in csv.DictReader(f) if (d.get("사이트 공개") or "").strip().upper()=="Y"]
def test_jaedan_pages_and_hub():
    J=_rows(); hub=(ROOT/"jaedan.html").read_text(encoding="utf-8")
    for d in J:
        p=ROOT/(d["재단ID"]+".html"); assert p.exists(), d["재단ID"]
        h=p.read_text(encoding="utf-8")
        assert f'canonical" href="https://bmaker.kr/{d["재단ID"]}"' in h
        assert "갚" not in h and not re.search(r"보장(?!하지)", h.replace("결과를 보장하지",""))
    assert hub.count('href="/jaedan-') >= len(J)


def _all_rows():
    with open(ROOT/"data"/"jaedan.source.csv", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def test_hub_has_anchor_section_for_every_foundation():
    """퇴역 페이지의 301 목적지(/jaedan#<slug>)가 실제로 있어야 한다 — 17개 전부."""
    hub = (ROOT/"jaedan.html").read_text(encoding="utf-8")
    for d in _all_rows():
        slug = d["재단ID"].removeprefix("jaedan-")
        m = re.search(rf'<section class="jd-region" id="{slug}"[^>]*>(.*?)</section>', hub, re.S)
        assert m, f"/jaedan#{slug} 섹션 없음"
        assert d["재단명"] in m.group(1)


def test_retired_pages_are_gone_and_redirected():
    """공개 N 재단: 파일 없음(실존 파일이 _redirects 보다 우선) · sitemap 없음 · 301 → /jaedan#<slug> · 내부 링크 없음."""
    retired = [d["재단ID"] for d in _all_rows() if (d.get("사이트 공개") or "").strip().upper() != "Y"]
    redirects = (ROOT/"_redirects").read_text(encoding="utf-8")
    sitemap = (ROOT/"sitemap.xml").read_text(encoding="utf-8")
    pages = [p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "docs" not in p.parts]
    for jid in retired:
        assert not (ROOT/f"{jid}.html").exists(), jid
        assert f"https://bmaker.kr/{jid}<" not in sitemap, jid
        assert re.search(rf"^/{jid}\s+/jaedan#{jid.removeprefix('jaedan-')}\s+301$", redirects, re.M), jid
        linked = [p.name for p in pages if re.search(rf'href="(?:https://bmaker\.kr)?/{jid}(?:\.html)?["#?]', p.read_text(encoding="utf-8"))]
        assert not linked, f"{jid} 로 가는 내부 링크: {linked}"


def test_region_pages_have_unique_data_titles_and_synced_faq():
    """지역 재단 페이지 title 은 '{재단명} 사업자대출, {데이터 꼬리}' — 꼬리까지 서로 달라야 하고 og:title 과 같다.
    FAQPage JSON-LD 질문은 화면의 지역 FAQ 와 같고, 공통 FAQ 는 허브에만 있다."""
    import json
    tails = set()
    for d in _rows():
        h = (ROOT/(d["재단ID"]+".html")).read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", h).group(1)
        assert title.startswith(d["재단명"] + " 사업자대출, "), title
        tails.add(title.split(", ", 1)[1])
        assert f'<meta property="og:title" content="{title}">' in h
        faq = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)]
        names = [q["name"] for x in faq if x.get("@type") == "FAQPage" for q in x["mainEntity"]]
        shown = re.findall(r'<details><summary>(.*?)</summary>', re.search(r"<h2>자주 묻는 질문</h2>(.*?)</main>", h, re.S).group(1))
        assert names == shown and 2 <= len(names) <= 3, (d["재단ID"], names, shown)
        assert "어떻게 진행되나요?" not in names and "무엇을 준비해야 하나요?" not in names
    assert len(tails) == len(_rows())
    hub = (ROOT/"jaedan.html").read_text(encoding="utf-8")
    for q in ("어떻게 진행되나요?", "무엇을 준비해야 하나요?", "신용점수가 낮아도 되나요?"):
        assert hub.count(f"<summary>{q}</summary>") == 1 and f'"name": "{q}"' in hub


def test_region_pages_need_three_public_cases():
    """지역 재단 개별 페이지는 공개 사례 3건 이상일 때만(규격 2절, 2026-11-01). 미만이면 overlay 공개 N → 허브 섹션 + 301."""
    import sys
    sys.path.insert(0, str(ROOT/"tools"))
    import build_jaedan
    for d in _rows():
        n = len(build_jaedan.cases_for(d["지역(시도)"]))
        assert n >= 3, f'{d["재단ID"]}: 공개 사례 {n}건 — 3건 미만은 개별 페이지를 두지 않는다'
