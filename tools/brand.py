"""브랜드 문장의 단일 출처 data/brand.json 을 읽는다(규격 3절, 2026-11-02).

definition·notice 는 페이지에 손으로 쓰지 않고 빌더가 이 파일에서 넣는다.
statements 의 {N} 은 공개 원장 건수로 바꾼다. profile_only 문장은 사이트 본문·JSON-LD·llms 본문에 쓰지 않는다.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ('name', 'definition', 'notice', 'statements', 'sameAs')


def load():
    d = json.loads((ROOT / 'data' / 'brand.json').read_text(encoding='utf-8'))
    missing = [k for k in REQUIRED if k not in d]
    if missing:
        raise ValueError(f'data/brand.json 에 {missing} 키가 없습니다.')
    return d


def statements(n, site=True):
    """{N} 을 원장 건수로 바꾼 문장 목록. site=True 면 profile_only 문장은 뺀다."""
    return [s['text'].replace('{N}', f'{n:,}') for s in load()['statements']
            if not (site and s.get('profile_only'))]
