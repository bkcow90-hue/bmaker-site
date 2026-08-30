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
