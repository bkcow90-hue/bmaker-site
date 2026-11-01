"""지역 재단 페이지 무결성 — 소스 공개 건수와 생성물 일치, 허브 그리드, 금지 표현."""
import csv, re, shutil, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT/"tools"))
import build_jaedan
def _rows():
    """페이지가 있어야 하는 재단 — 공개 Y 이고 공개 사례 3건 이상(build_jaedan 과 같은 규칙)."""
    return build_jaedan.load()
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
    """퇴역 재단(공개 N 또는 사례 3건 미만): 파일 없음(실존 파일이 _redirects 보다 우선) · sitemap 없음 · 내부 링크 없음.
    301 → /jaedan#<slug> 예비 규칙은 17개 재단 전부에 있어야 한다 — 사례가 줄어 자동 퇴역해도 404 가 나지 않게."""
    live = build_jaedan.live_ids()
    retired = [d["재단ID"] for d in _all_rows() if d["재단ID"] not in live]
    redirects = (ROOT/"_redirects").read_text(encoding="utf-8")
    for d in _all_rows():
        jid = d["재단ID"]
        assert re.search(rf"^/{jid}\s+/jaedan#{jid.removeprefix('jaedan-')}\s+301\r?$", redirects, re.M), f"{jid}: 예비 301 없음"
    sitemap = (ROOT/"sitemap.xml").read_text(encoding="utf-8")
    pages = [p for p in ROOT.rglob("*.html") if ".git" not in p.parts and "docs" not in p.parts]
    for jid in retired:
        assert not (ROOT/f"{jid}.html").exists(), jid
        assert f"https://bmaker.kr/{jid}<" not in sitemap, jid
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


def test_under_three_case_foundations_have_no_html():
    """공개 사례 3건 미만 재단의 html 파일은 존재하지 않는다(규격 2절, 2026-11-01) — 공개 Y 여도 빌더가 퇴역시킨다."""
    rows = {d["재단ID"]: d for d in _all_rows()}
    for d in rows.values():
        n = len(build_jaedan.cases_for(d["지역(시도)"]))
        if n < 3:
            assert not (ROOT/f'{d["재단ID"]}.html').exists(), f'{d["재단ID"]}: 공개 사례 {n}건인데 페이지가 있다'
    for p in ROOT.glob("jaedan-*.html"):
        assert len(build_jaedan.cases_for(rows[p.stem]["지역(시도)"])) >= 3, p.name


def test_builder_retires_foundation_below_three_cases(tmp_path):
    """빌더 동작: 공개 Y 재단의 사례가 2건으로 줄면 멈추지 않고(exit 0) 경고 후 퇴역 —
    파일 삭제 · sitemap·llms 제외 · 허브 섹션은 링크 없이 사례 건수만."""
    for name in ("tools", "data"):
        shutil.copytree(ROOT/name, tmp_path/name, ignore=shutil.ignore_patterns("__pycache__"))
    for name in ["jaedan.html", "sojingong.html", "sitemap.xml", "llms.txt", *[p.name for p in ROOT.glob("jaedan-*.html")]]:
        shutil.copy(ROOT/name, tmp_path/name)
    src = tmp_path/"data"/"cases.source.csv"
    with open(src, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f); fields = reader.fieldnames; rows = list(reader)
    ulsan = [r for r in rows if "울산신용보증재단" in r["기관"] and r["사이트 공개"].upper() == "Y"]
    assert len(ulsan) >= 3
    for r in ulsan[:len(ulsan) - 2]:
        r["사이트 공개"] = "N"
    with open(src, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)
    assert (tmp_path/"jaedan-ulsan.html").exists()

    out = subprocess.run([sys.executable, "-X", "utf8", "tools/build_jaedan.py"], cwd=tmp_path,
                         capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 0, out.stdout + out.stderr
    assert "[재단 빌드 경고] jaedan-ulsan: 공개 사례 2건" in out.stdout
    assert not (tmp_path/"jaedan-ulsan.html").exists()
    assert "https://bmaker.kr/jaedan-ulsan<" not in (tmp_path/"sitemap.xml").read_text(encoding="utf-8")
    line = re.search(r"- \[지역 신용보증재단 페이지 (\d+)종\][^\n]*", (tmp_path/"llms.txt").read_text(encoding="utf-8"))
    assert int(line.group(1)) == len(build_jaedan.live_ids()) - 1 and "울산" not in line.group(0)
    hub = (tmp_path/"jaedan.html").read_text(encoding="utf-8")
    sec = re.search(r'<section class="jd-region" id="ulsan"[^>]*>(.*?)</section>', hub, re.S).group(1)
    assert "공개 원장 사례 2건" in sec and "/jaedan-ulsan" not in sec and "/cases#" not in sec
    assert 'href="/jaedan-ulsan"' not in hub
