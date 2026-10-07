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
    new_id = 'CRM-' + 'a' * 32
    sync.sync_sources(tmp_path, crm_url='https://crm.example.org/public-ledger', crm_token='test-only', fetcher=lambda _, **kw: cases(new_id))
    saved = list(csv.DictReader(io.StringIO((tmp_path / 'data/cases.source.csv').read_text(encoding='utf-8-sig'))))
    assert [r['사례ID'] for r in saved] == ['T1', new_id]
    assert saved[0]['한 줄 메모'] == '기존 공개 설명'
    with pytest.raises(sync.SyncError):
        sync.sync_sources(tmp_path, crm_url='https://crm.example.org/public-ledger', crm_token='test-only', fetcher=lambda _, **kw: cases('T3', **{'신용점수 구간': '700~800'}))
    with pytest.raises(sync.SyncError, match='EXISTING_CASE_CHANGED'):
        sync.sync_sources(tmp_path, crm_url='https://crm.example.org/public-ledger', crm_token='test-only', fetcher=lambda _, **kw: cases(amount='4000'))
    assert sync.sync_sources(tmp_path, crm_url='https://crm.example.org/public-ledger', crm_token='test-only', fetcher=lambda _, **kw: cases(new_id)) is False


def test_crm_legacy_id_must_already_exist_and_fees_are_never_public(tmp_path):
    setup_sources(tmp_path)
    sync = module()
    for payload, code in [(cases('01012345678'), 'UNKNOWN_LEGACY_CASE'),
                          (cases('CRM-' + 'b' * 32, received_amount='990000', paid_at='2026-09-12'), 'UNAPPROVED_COLUMN')]:
        with pytest.raises(sync.SyncError, match=code):
            sync.sync_sources(tmp_path, crm_url='https://example.org/crm', crm_token='test-only', fetcher=lambda _, **kw: payload)
    assert (tmp_path / 'data/cases.source.csv').read_bytes() == cases()


def test_crm_header_only_keeps_historical_cases_and_secret_is_scoped(tmp_path):
    setup_sources(tmp_path)
    (tmp_path / 'data/funds-source.url').write_text('https://example.org/funds', encoding='utf-8')
    original = (tmp_path / 'data/cases.source.csv').read_bytes()
    calls = []
    def fetch(url, **kwargs):
        calls.append((url, kwargs))
        return cases().splitlines()[0] + b'\n' if '/crm' in url else '자금ID,사이트 공개\nF1,Y\n'.encode('utf-8')
    module().sync_sources(tmp_path, crm_url='https://example.org/crm', crm_token='test-only', fetcher=fetch)
    assert calls == [('https://example.org/crm', {'token': 'test-only'}), ('https://example.org/funds', {})]
    assert (tmp_path / 'data/cases.source.csv').read_bytes() == original


def test_crm_missing_secret_fails_before_network(tmp_path):
    setup_sources(tmp_path)
    def unexpected(*args, **kwargs):
        pytest.fail('network must not be contacted without dedicated token')
    with pytest.raises(module().SyncError, match='CRM_TOKEN_NOT_CONFIGURED'):
        module().sync_sources(tmp_path, crm_url='https://example.org/crm', fetcher=unexpected)


def test_credentials_are_never_redirected_or_embedded_in_url():
    sync = module()
    with pytest.raises(sync.SyncError, match='AUTH_REDIRECT_BLOCKED'):
        sync.NoCredentialRedirect().redirect_request(None, None, 302, '', {}, 'https://other.example')
    with pytest.raises(sync.SyncError, match='INVALID_AUTH_SOURCE'):
        sync.fetch('https://example.org/crm?token=unsafe', token='test-only')


def test_fetch_sends_bearer_only_to_authenticated_crm_request(monkeypatch):
    from types import SimpleNamespace
    sync = module()
    captured = []
    class Response(io.BytesIO):
        def geturl(self):
            return 'https://example.org/source'
    def capture(request, timeout):
        captured.append(request)
        assert timeout == 30
        return Response(b'fixture')
    def opener(handler):
        assert isinstance(handler, sync.NoCredentialRedirect)
        return SimpleNamespace(open=capture)
    monkeypatch.setattr(sync, 'build_opener', opener)
    monkeypatch.setattr(sync, 'urlopen', capture)
    assert sync.fetch('https://crm.example.org/api/public-ledger', token='test-only') == b'fixture'
    assert sync.fetch('https://docs.example.org/sheet') == b'fixture'
    assert captured[0].get_header('Authorization') == 'Bearer test-only'
    assert captured[1].get_header('Authorization') is None


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
