import subprocess
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

def test_conversion_delivery_contract():
    subprocess.run(['node', 'tests/test_conversion.mjs'], cwd=ROOT, check=True, capture_output=True, text=True)

def test_only_one_form_precedes_company_introduction():
    source = (ROOT / 'index.html').read_text()
    assert source.count('id="leadForm"') == 1
    assert source.count('id="apply"') == 1
    assert source.index('id="leadForm"') < source.index('id="about"')
    assert 'class="case" aria-hidden="true"' not in source

def test_ledger_heading_matches_public_rows():
    source = (ROOT / 'cases.html').read_text()
    count = source.count('<tr id="row-')
    assert f'실행 기록 (전체 {count}건)' in source

def test_budget_exhaustion_cannot_be_inferred_from_calendar():
    import sys
    sys.path.insert(0, str(ROOT / 'tools'))
    from build_funds import status_of
    assert status_of({'접수 시작일':'2020-01-01','접수 마감일':'예산 소진 시','접수 상태':'회차'})[0] == 'check'
    assert status_of({'접수 시작일':'','접수 마감일':'','접수 상태':'상시'})[0] == 'check'
    assert status_of({'접수 시작일':'2020-01-01','접수 마감일':'2099-12-31','접수 상태':'마감'})[0] == 'closed'
