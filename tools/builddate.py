#!/usr/bin/env python3
"""빌드 기준일 한 곳 — 모든 build_*.py 가 이 함수로 날짜를 얻는다.

- env BUILD_DATE(YYYY-MM-DD) 가 있으면 그 날짜를 쓴다.
  CI 의 churn 검사가 '대상 커밋이 만들어진 날' 로 산출물을 재현하는 용도다.
  ledger 워크플로는 이 값을 넣지 않으므로 실제 오늘을 쓴다.
- 없으면 Asia/Seoul 기준 오늘. 러너·개발기의 TZ 환경변수에는 기대지 않는다.
  zoneinfo 에 tzdata 가 없는 환경(윈도우 기본 등)에서는 고정 +09:00 으로 떨어진다 —
  한국은 서머타임이 없어 두 계산 결과가 항상 같다.
"""
import datetime
import os
import re

try:
    from zoneinfo import ZoneInfo
    KST = ZoneInfo('Asia/Seoul')
except Exception:                                  # tzdata 없는 환경
    KST = datetime.timezone(datetime.timedelta(hours=9), 'KST')

ENV = 'BUILD_DATE'


def build_date():
    """빌드 기준일(datetime.date)."""
    raw = (os.environ.get(ENV) or '').strip()
    if not raw:
        return datetime.datetime.now(KST).date()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', raw):
        raise SystemExit(f"[빌드 기준일 실패] {ENV}='{raw}' — YYYY-MM-DD 형식이어야 합니다.")
    try:
        return datetime.date.fromisoformat(raw)
    except ValueError:
        raise SystemExit(f"[빌드 기준일 실패] {ENV}='{raw}' — 실제 날짜가 아닙니다.")
