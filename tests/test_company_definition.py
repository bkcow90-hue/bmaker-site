"""회사 정의·고지 문장 통일(규격 3절·4-1, 2026-10-04 대표 지시).

- 회사를 가리켜 "민간 경영컨설팅"·"민간 컨설팅 회사"·"민간 진단 회사"를 쓰지 않는다 — 공개 페이지·llms·빌더·글 원본 전체.
  (업계 일반 설명인 "민간 컨설팅 자료"·"민간 컨설팅 이용" 등은 대상이 아니다.)
- 고지 문장은 홈(회사소개 #about 포함)에 1회 이상, 삭제 금지.
- 정의 문장은 홈 히어로 설명 첫 문장·llms 파일·Organization description 에 있다.
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEF = '비즈니스 메이커는 소상공인·개인사업자와 제조·기술 중소기업 법인의 정책자금을 상담하는 정책자금 경영컨설팅 회사입니다.'
NOTICE = '비즈니스 메이커는 정부·공공기관이 아닌 정책자금 경영컨설팅 회사입니다.'
BANNED = re.compile(r'민간 경영컨설팅|민간 컨설팅 회사|민간 진단 회사|민간 회사')
# 과거 기록 문서(당시 문구를 인용)는 검사하지 않는다
SKIP_DIRS = {'.git', 'node_modules', '.wrangler', 'docs', 'tests'}


def _sources():
    for p in ROOT.rglob('*'):
        if p.suffix not in ('.html', '.txt', '.py', '.md', '.json') or not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if rel.parts[0] in SKIP_DIRS or rel.name in ('CLAUDE.md', 'AGENTS.md'):
            continue
        yield rel, p
    for name in ('docs/education-body.html', 'docs/education-program-body.html',
                 'docs/editorial-content.json', 'docs/funding-guides.json'):
        p = ROOT / name
        if p.exists():
            yield Path(name), p


def test_no_private_consulting_label():
    hits = []
    for rel, p in _sources():
        for m in BANNED.finditer(p.read_text(encoding='utf-8', errors='ignore')):
            hits.append(f"{rel.as_posix()}: …{m.group(0)}…")
    assert not hits, "회사를 '민간 …'으로 부르는 문구가 남아 있음:\n" + '\n'.join(hits[:20])


def test_notice_on_home_and_about():
    s = (ROOT / 'index.html').read_text(encoding='utf-8')
    assert s.count(NOTICE) >= 1, '홈에 고지 문장이 없습니다.'
    about = re.search(r'<section[^>]*id="about"[^>]*>(.*?)</section>', s, re.S)
    assert about, '홈 #about(회사소개) 구역을 찾지 못했습니다.'
    assert '정책자금 경영컨설팅 회사' in about.group(1), '회사소개에 정의 표현이 없습니다.'


def test_definition_sentence_in_hero_llms_and_org():
    s = (ROOT / 'index.html').read_text(encoding='utf-8')
    lead = re.search(r'<p class="lead">(.*?)</p>', s, re.S)
    assert lead and lead.group(1).strip().startswith(DEF), '홈 히어로 설명 첫 문장이 정의 문장이 아닙니다.'
    for name in ('llms.txt', 'llms-full.txt'):
        assert DEF in (ROOT / name).read_text(encoding='utf-8'), f'{name} 에 정의 문장이 없습니다.'
    orgs = []
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        d = json.loads(m)
        for n in d.get('@graph', [d]) if isinstance(d, dict) else d:
            if isinstance(n, dict) and n.get('@id') == 'https://bmaker.kr/#org':
                orgs.append(n.get('description', ''))
    assert any('정책자금 경영컨설팅 회사' in d for d in orgs), 'Organization description 에 정의 표현이 없습니다.'
