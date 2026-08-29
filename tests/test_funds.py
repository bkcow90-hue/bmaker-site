"""자금 페이지·일정 무결성 — 시트 공개 건수와 생성물이 일치하고 금지 표현이 없는지."""
import csv, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
def _funds():
    with open(ROOT/"data"/"funds.source.csv", encoding="utf-8-sig") as f:
        return [d for d in csv.DictReader(f) if (d.get("사이트 공개") or "").strip().upper()=="Y"]
def test_fund_pages_and_schedule_align():
    F=_funds(); sch=(ROOT/"schedule.html").read_text(encoding="utf-8")
    assert sch.count("<tr><td><a href=") == len(F) >= 1
    for d in F:
        p=ROOT/(d["자금ID"]+".html")
        assert p.exists(), d["자금ID"]
        h=p.read_text(encoding="utf-8")
        assert f'canonical" href="https://bmaker.kr/{d["자금ID"]}"' in h
        assert "갚" not in h and not re.search(r"보장(?!하지)", h.replace("결과를 보장하지",""))
    assert "갚" not in sch and not re.search(r"보장(?!하지)", sch.replace("결과를 보장하지",""))
