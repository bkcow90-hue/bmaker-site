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
