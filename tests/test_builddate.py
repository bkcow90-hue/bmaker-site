"""빌드 기준일 — BUILD_DATE 가 있으면 그 날짜, 없으면 Asia/Seoul 오늘.

CI 의 churn 검사가 '산출물이 만들어진 날' 을 넣어 커밋본을 그대로 재현하는 데 쓰인다.
ledger 워크플로는 이 값을 넣지 않으므로 실제 오늘로 빌드한다.
"""
import datetime
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import builddate  # noqa: E402

KST = datetime.timezone(datetime.timedelta(hours=9))


def test_env_build_date_wins(monkeypatch):
    monkeypatch.setenv('BUILD_DATE', '2026-09-18')
    assert builddate.build_date() == datetime.date(2026, 9, 18)


def test_defaults_to_seoul_today_regardless_of_runner_tz(monkeypatch):
    """러너·개발기의 TZ 에 기대지 않는다 — 한국은 서머타임이 없어 +09:00 과 항상 같다."""
    monkeypatch.delenv('BUILD_DATE', raising=False)
    for tz in ('UTC', 'America/Los_Angeles', 'Asia/Seoul'):
        monkeypatch.setenv('TZ', tz)
        assert builddate.build_date() == datetime.datetime.now(KST).date(), tz


def test_blank_env_falls_back_to_today(monkeypatch):
    monkeypatch.setenv('BUILD_DATE', '   ')
    assert builddate.build_date() == datetime.datetime.now(KST).date()


@pytest.mark.parametrize('bad', ['2026/09/18', '20260918', '2026-9-18', '2026-13-01', 'yesterday'])
def test_malformed_env_stops_the_build(monkeypatch, bad):
    """조용히 오늘로 떨어지면 잘못된 날짜로 산출물이 덮인다 — 멈추는 쪽이 맞다."""
    monkeypatch.setenv('BUILD_DATE', bad)
    with pytest.raises(SystemExit):
        builddate.build_date()


def test_every_dated_builder_uses_the_shared_helper():
    """날짜를 쓰는 빌더가 제 나름의 계산으로 되돌아가지 않게 고정한다."""
    dated = []
    for path in sorted((ROOT / 'tools').glob('build_*.py')):
        src = path.read_text(encoding='utf-8')
        if 'build_date()' in src:
            dated.append(path.name)
            assert 'from builddate import build_date' in src, path.name
        assert 'timedelta(hours=9)' not in src, f'{path.name}: 자체 KST 계산이 남아 있다'
        assert 'date.today()' not in src, f'{path.name}: date.today() 는 러너 TZ 에 흔들린다'
    assert len(dated) == 8, f'날짜를 쓰는 빌더 수가 바뀌었다: {dated}'
