import csv
from functools import lru_cache
import importlib.util
import io
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def module():
    path = ROOT / 'tools/sync_ledger.py'
    assert path.exists(), 'transactional ledger sync is missing'
    spec = importlib.util.spec_from_file_location('sync_ledger', path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def cases(case_id='T1', amount='3000', **extra):
    row = {'사례ID': case_id, '실행 연월': '2026-10', '기관': '소상공인시장진흥공단',
           '자금명': '테스트 자금', '실행 금액(만원)': amount, '지역(시도)': '서울', '사이트 공개': 'Y', **extra}
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=list(row))
    writer.writeheader()
    writer.writerow(row)
    return out.getvalue().encode('utf-8')


def setup_sources(root):
    (root / 'data').mkdir()
    (root / 'data/ledger-source.url').write_text('https://example.org/cases', encoding='utf-8')
    (root / 'data/cases.source.csv').write_bytes(cases())


def test_failure_retries_even_when_source_is_unchanged(tmp_path):
    setup_sources(tmp_path)
    (tmp_path / 'data/ledger-status.txt').write_text('FAIL\nold gate failure', encoding='utf-8')
    sync = module()
    assert sync.needs_rebuild(tmp_path, changed=False) is True
    (tmp_path / 'data/ledger-status.txt').write_text('OK\nlast success', encoding='utf-8')
    assert sync.needs_rebuild(tmp_path, changed=False) is False


def test_second_source_failure_does_not_promote_first(tmp_path):
    setup_sources(tmp_path)
    (tmp_path / 'data/funds-source.url').write_text('https://example.org/funds', encoding='utf-8')
    (tmp_path / 'data/funds.source.csv').write_text('자금ID,사이트 공개\nF1,Y\n', encoding='utf-8')
    original = (tmp_path / 'data/cases.source.csv').read_bytes()
    def fetch(url):
        if url.endswith('/funds'):
            raise OSError('private upstream error')
        return cases(amount='4000')
    with pytest.raises(module().SyncError, match='FETCH_FAILED'):
        module().sync_sources(tmp_path, fetcher=fetch)
    assert (tmp_path / 'data/cases.source.csv').read_bytes() == original


@pytest.mark.parametrize('payload', [b'<html>login required</html>', b'', cases(amount='NaN'), cases(amount='-1'), cases(phone='01012345678')])
def test_invalid_upstream_keeps_last_good_source(tmp_path, payload):
    setup_sources(tmp_path)
    original = (tmp_path / 'data/cases.source.csv').read_bytes()
    with pytest.raises(module().SyncError):
        module().sync_sources(tmp_path, fetcher=lambda _: payload)
    assert (tmp_path / 'data/cases.source.csv').read_bytes() == original


def test_crm_appends_approved_rows_and_preserves_existing_details(tmp_path):
    setup_sources(tmp_path)
    sync = module()
    (tmp_path / 'data/cases.source.csv').write_bytes(cases(**{'한 줄 메모': '기존 공개 설명'}))
    sync.sync_sources(tmp_path, crm_url='https://crm.example.org/public-ledger', fetcher=lambda _: cases('T2'))
    saved = list(csv.DictReader(io.StringIO((tmp_path / 'data/cases.source.csv').read_text(encoding='utf-8-sig'))))
    assert [r['사례ID'] for r in saved] == ['T1', 'T2']
    assert saved[0]['한 줄 메모'] == '기존 공개 설명'
    with pytest.raises(sync.SyncError):
        sync.sync_sources(tmp_path, crm_url='https://crm.example.org/public-ledger', fetcher=lambda _: cases('T3', **{'신용점수 구간': '700~800'}))
    with pytest.raises(sync.SyncError, match='EXISTING_CASE_CHANGED'):
        sync.sync_sources(tmp_path, crm_url='https://crm.example.org/public-ledger', fetcher=lambda _: cases(amount='4000'))
    assert sync.sync_sources(tmp_path, crm_url='https://crm.example.org/public-ledger', fetcher=lambda _: cases('T2')) is False


def test_failure_rolls_back_sources_and_generated_pages_but_preserves_last_success(tmp_path):
    setup_sources(tmp_path)
    (tmp_path / 'cases.html').write_text('last good page', encoding='utf-8')
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    subprocess.run(['git', '-C', str(tmp_path), 'add', '.'], check=True)
    subprocess.run(['git', '-C', str(tmp_path), '-c', 'user.name=test', '-c', 'user.email=test@example.org', 'commit', '-qm', 'fixture'], check=True)
    sync = module()
    sync.record_status(tmp_path, True, 'complete')
    (tmp_path / 'data/cases.source.csv').write_bytes(cases(amount='4000'))
    (tmp_path / 'cases.html').write_text('partial bad page', encoding='utf-8')
    (tmp_path / 'new-generated.html').write_text('partial new page', encoding='utf-8')
    last_success = sync.read_status(tmp_path)['last_success_at']
    sync.rollback(tmp_path)
    sync.record_status(tmp_path, False, 'tests')
    assert (tmp_path / 'cases.html').read_text(encoding='utf-8') == 'last good page'
    assert (tmp_path / 'data/cases.source.csv').read_bytes() == cases()
    assert not (tmp_path / 'new-generated.html').exists()
    status = sync.read_status(tmp_path)
    assert status['last_success_at'] == last_success
    assert status['failed_at'] and status['stage'] == 'tests'


def test_bom_and_newline_changes_do_not_trigger_a_build(tmp_path):
    setup_sources(tmp_path)
    assert module().sync_sources(tmp_path, fetcher=lambda _: b'\xef\xbb\xbf' + cases().replace(b'\r\n', b'\n')) is False
