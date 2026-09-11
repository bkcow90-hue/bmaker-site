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

def test_unverified_round_never_becomes_open_from_sheet_date():
    import importlib.util
    spec=importlib.util.spec_from_file_location('fund_builder', ROOT/'tools/build_funds.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    assert module.status_of({'회차 확인':'미확인','접수 시작일':'2099-10-06','접수 마감일':'','접수 상태':'회차'})[0]=='check'
    assert module.status_of({'회차 확인':'미확인','접수 시작일':'2026-01-01','접수 마감일':'2099-12-31','접수 상태':'회차'})[0]=='check'
    rows=module.load()
    assert len(rows)==15
    assert all('PBLN_000000000124909' in r['공고 링크'] for r in rows)
    sch=(ROOT/'schedule.html').read_text(encoding='utf-8')
    assert '접수 예정 · 2026-10-06 시작' not in sch
    assert len(re.findall(r'연간계획 [0-9]+쪽 확인', sch))==15
    assert '잔여 예산을 뜻하지 않습니다' in sch
