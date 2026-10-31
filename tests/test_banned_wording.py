"""규격 1절 금칙어 "실행 기록" → "받은 사례" — 공개 표면(HTML·llms) 전 페이지 0건 (2026-11-01 일괄 치환)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = {'.git', '.wrangler', 'docs', 'node_modules', 'tools', 'tests'}


def test_no_execution_record_wording():
    files = [p for p in ROOT.rglob('*.html') if not SKIP & set(p.relative_to(ROOT).parts[:-1])]
    files += [ROOT / 'llms.txt', ROOT / 'llms-full.txt']
    hit = [p.relative_to(ROOT).as_posix() for p in files if '실행 기록' in p.read_text(encoding='utf-8')]
    assert not hit, f'"실행 기록" 잔존: {hit}'
