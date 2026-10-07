#!/usr/bin/env python3
"""Fetch approved CSVs as one unit; keep the last successful source on failure."""
import csv
import datetime
from decimal import Decimal, InvalidOperation
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
from urllib.parse import urlsplit
from urllib.request import urlopen, Request, build_opener, HTTPRedirectHandler

ROOT = Path(__file__).resolve().parents[1]
CASE_COLUMNS = {'사례ID', '실행 연월', '기관', '자금명', '실행 금액(만원)', '금리', '상환 조건',
                '지역(시도)', '업종', '사업 형태', '업력(년)', '신용점수 구간', '연매출 구간',
                '폐업 이력', '체납 이력', '기존 정책자금', '동시 진행 자금', '소요일', '한 줄 메모', '증빙 파일', '사이트 공개'}
# CRM transport may not add the historical sheet's sensitive buckets or free text.
CRM_COLUMNS = {'사례ID', '실행 연월', '기관', '자금명', '실행 금액(만원)', '지역(시도)', '사이트 공개', '업종', '사업 형태'}
CASE_REQUIRED = {'사례ID', '실행 연월', '기관', '자금명', '실행 금액(만원)', '지역(시도)', '사이트 공개'}
STATUS_FILES = {'data/ledger-status.txt', 'data/ledger-sync-status.json'}


class SyncError(Exception):
    """Only safe error codes belong in the public status, never response bodies."""


def normalize(payload):
    try:
        return payload.decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
    except UnicodeError:
        raise SyncError('INVALID_ENCODING') from None


def validate(payload, kind, crm=False):
    text = normalize(payload)
    reader = csv.DictReader(io.StringIO(text))
    header = reader.fieldnames or []
    required = CASE_REQUIRED if kind == 'cases' else {('자금ID' if kind == 'funds' else '재단ID'), '사이트 공개'}
    if len(header) != len(set(header)) or not required.issubset(header):
        raise SyncError('INVALID_HEADER')
    if kind == 'cases' and not set(header).issubset(CRM_COLUMNS if crm else CASE_COLUMNS):
        raise SyncError('UNAPPROVED_COLUMN')
    rows = list(reader)
    if not rows and not crm:
        raise SyncError('EMPTY_SOURCE')
    ids = set()
    id_column = '사례ID' if kind == 'cases' else ('자금ID' if kind == 'funds' else '재단ID')
    for row in rows:
        if None in row or any(row.get(key) in (None, '') for key in required):
            raise SyncError('INVALID_ROW')
        if row[id_column] in ids:
            raise SyncError('DUPLICATE_ID')
        ids.add(row[id_column])
        if row['사이트 공개'].upper() not in ('Y', 'N') or (crm and row['사이트 공개'] != 'Y'):
            raise SyncError('PUBLIC_APPROVAL_REQUIRED')
        if kind == 'cases':
            if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', row['실행 연월']):
                raise SyncError('INVALID_EXECUTION_MONTH')
            try:
                amount = Decimal(row['실행 금액(만원)'].replace(',', ''))
            except InvalidOperation:
                raise SyncError('INVALID_EXECUTION_AMOUNT') from None
            if not amount.is_finite() or amount <= 0 or amount != amount.to_integral_value():
                raise SyncError('INVALID_EXECUTION_AMOUNT')
    return text


class NoCredentialRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward the CRM bearer token, including to the same host.
        raise SyncError('AUTH_REDIRECT_BLOCKED')


def fetch(url, token=''):
    parts = urlsplit(url)
    if parts.scheme != 'https' or not parts.hostname or parts.username or parts.password:
        raise SyncError('HTTPS_SOURCE_REQUIRED')
    if token and (parts.query or parts.fragment or '\r' in token or '\n' in token):
        raise SyncError('INVALID_AUTH_SOURCE')
    request = Request(url, headers={'Authorization': 'Bearer ' + token} if token else {})
    open_request = build_opener(NoCredentialRedirect()).open if token else urlopen
    for attempt in range(3):
        try:
            with open_request(request, timeout=30) as response:
                if urlsplit(response.geturl()).scheme != 'https':
                    raise SyncError('HTTPS_SOURCE_REQUIRED')
                payload = response.read(10 * 1024 * 1024 + 1)
                if len(payload) > 10 * 1024 * 1024:
                    raise SyncError('SOURCE_TOO_LARGE')
                return payload
        except SyncError:
            raise
        except (OSError, ValueError):
            if attempt == 2:
                raise SyncError('FETCH_FAILED') from None
            time.sleep(attempt + 1)


def merge_crm(existing, incoming):
    """Add new public IDs, never erase old details or silently revise a case."""
    old = csv.DictReader(io.StringIO(existing))
    rows = list(old)
    by_id = {row['사례ID']: row for row in rows}
    new = csv.DictReader(io.StringIO(incoming))
    headers = list(old.fieldnames)
    added = []
    for row in new:
        previous = by_id.get(row['사례ID'])
        if previous is not None:
            if any(previous.get(key, '') != value for key, value in row.items()):
                raise SyncError('EXISTING_CASE_CHANGED')
        else:
            if not re.fullmatch(r'CRM-[0-9a-f]{32}', row['사례ID']):
                raise SyncError('UNKNOWN_LEGACY_CASE')
            added.append(row)
    if not added:
        return existing
    headers.extend(key for key in new.fieldnames if key not in headers)
    out = io.StringIO(newline='')
    writer = csv.DictWriter(out, fieldnames=headers, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows + added)
    return out.getvalue()


def sync_sources(root, crm_url='', crm_token='', fetcher=fetch):
    if crm_url and not crm_token:
        raise SyncError('CRM_TOKEN_NOT_CONFIGURED')
    staged = []
    for kind, url_name in [('cases', 'ledger'), ('funds', 'funds'), ('jaedan', 'jaedan')]:
        url_file = root / f'data/{url_name}-source.url'
        url = crm_url if kind == 'cases' and crm_url else (url_file.read_text(encoding='utf-8').strip() if url_file.exists() else '')
        if not url:
            if kind == 'cases':
                raise SyncError('SOURCE_NOT_CONFIGURED')
            continue
        try:
            payload = fetcher(url, token=crm_token) if kind == 'cases' and crm_url else fetcher(url)
        except SyncError:
            raise
        except OSError:
            raise SyncError('FETCH_FAILED') from None
        text = validate(payload, kind, crm=kind == 'cases' and bool(crm_url))
        target = root / f'data/{kind}.source.csv'
        # CRM's approved subset appends to the last successful historical source.
        # Old fields survive; matching IDs are immutable until separately reviewed.
        if kind == 'cases' and crm_url:
            if not target.exists():
                raise SyncError('HISTORICAL_SOURCE_REQUIRED')
            text = merge_crm(normalize(target.read_bytes()), text)
        if not target.exists() or normalize(target.read_bytes()) != text:
            staged.append((target, text))
    # All network reads and validation succeed before touching any source.
    for target, text in staged:
        tmp = target.with_suffix('.tmp')
        tmp.write_bytes(b'\xef\xbb\xbf' + text.encode('utf-8'))
        tmp.replace(target)
    return bool(staged)


def needs_rebuild(root, changed, force=False, daily=False):
    status = root / 'data/ledger-status.txt'
    return changed or force or daily or not status.exists() or not status.read_text(encoding='utf-8').startswith('OK\n')


def read_status(root):
    try:
        return json.loads((root / 'data/ledger-sync-status.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {}


def record_status(root, ok, stage):
    previous = read_status(root)
    now = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    state = {'status': 'OK' if ok else 'FAIL', 'stage': stage,
             'last_success_at': now if ok else previous.get('last_success_at'),
             'failed_at': None if ok else now}
    (root / 'data/ledger-sync-status.json').write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    (root / 'data/ledger-status.txt').write_text(
        f"{state['status']}\nstage={stage}\nlast_success_at={state['last_success_at'] or 'unknown'}\nfailed_at={state['failed_at'] or '-'}\n", encoding='utf-8')


def rollback(root):
    def git(*args):
        return subprocess.check_output(['git', '-C', str(root), *args]).decode('utf-8').split('\0')
    paths = [p for p in git('diff', '--name-only', '-z', 'HEAD') if p and p not in STATUS_FILES]
    if paths:
        subprocess.run(['git', '-C', str(root), 'restore', '--source=HEAD', '--worktree', '--', *paths], check=True)
    # On a clean Actions checkout only newly generated HTML can be untracked.
    for path in git('ls-files', '--others', '--exclude-standard', '-z'):
        target = (root / path).resolve()
        if path.endswith('.html') and target.is_relative_to(root.resolve()):
            target.unlink()


def main():
    action = sys.argv[1]
    if action == 'fetch':
        try:
            changed = sync_sources(ROOT, crm_url=os.environ.get('BMAKER_CRM_LEDGER_URL', '').strip(),
                                   crm_token=os.environ.get('BMAKER_CRM_LEDGER_TOKEN', '').strip())
            rebuild = needs_rebuild(ROOT, changed, force=os.environ.get('LEDGER_FORCE') == 'true', daily=os.environ.get('LEDGER_DAILY') == 'true')
            with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as out:
                out.write(f"changed={'yes' if rebuild else 'no'}\n")
            print(f"ledger: source_changed={changed}, rebuild={rebuild}")
        except SyncError as error:
            rollback(ROOT)
            record_status(ROOT, False, 'fetch:' + str(error))
            print('ledger fetch failed: ' + str(error))
            return 1
    elif action == 'failure':
        previous = read_status(ROOT)
        rollback(ROOT)
        stage = os.environ.get('LEDGER_FAILURE_STAGE', 'build_or_tests')
        record_status(ROOT, False, previous.get('stage', 'fetch') if stage == 'fetch' else stage)
    elif action == 'success':
        record_status(ROOT, True, 'complete')
    return 0


if __name__ == '__main__':
    sys.exit(main())
