"""회사 정의·고지 문장 통일(규격 3절·4-1, 2026-10-04 대표 지시 · 2026-11-02 개정).

- 문장의 단일 출처는 data/brand.json(definition·notice·statements·sameAs). 빌더가 여기서 읽어 넣는다.
- 회사를 가리켜 "민간 경영컨설팅"·"민간 컨설팅 회사"·"민간 진단 회사"·"민간 회사"를 쓰지 않는다 — 고지 문장 포함,
  공개 페이지·llms·빌더·글 원본 전체(기관들이 불법 브로커를 "민간 컨설팅 업체"라고 부른다).
  (업계 일반 설명인 "민간 컨설팅 자료"·"민간 컨설팅 이용" 등은 대상이 아니다.)
- 고지 문장은 홈에 1회 이상, 삭제 금지. 정의 문장은 홈 히어로 설명 첫 문장·회사소개·llms 파일·Organization description 에 있다.
- 홈 회사소개 첫 문단 = 정의 + statements[1] + statements[2]. llms.txt 첫 문단 아래 "## 회사" 블록 = statements 0~2.
- statements 의 profile_only 문장(비용 구조)은 사이트 본문·JSON-LD·llms 본문에 쓰지 않는다.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import brand

B = brand.load()
DEF, NOTICE = B['definition'], B['notice']
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


def _text(html):
    return re.sub(r'<!--.*?-->', '', html, flags=re.S)


def test_brand_json_loads_with_required_keys():
    assert B['name'] == '비즈니스 메이커'
    assert DEF.startswith('비즈니스 메이커는 ') and DEF.endswith('경영컨설팅 회사입니다.')
    assert NOTICE == '비즈니스 메이커는 정부·공공기관이 아닌 경영컨설팅 회사입니다.'
    assert len(B['statements']) == 4 and isinstance(B['sameAs'], list)
    assert [s.get('profile_only', False) for s in B['statements']] == [False, False, False, True]
    assert '{N}' in B['statements'][2]['text']
    site = brand.statements(1234)
    assert len(site) == 3 and '받은 사례 1,234건' in site[2] and '{N}' not in ' '.join(site)
    assert len(brand.statements(5, site=False)) == 4
    for s in B['statements']:
        assert '갚' not in s['text'] and '보장' not in s['text'] and '실행 기록' not in s['text']


def test_no_private_consulting_label():
    hits = []
    for rel, p in _sources():
        text = p.read_text(encoding='utf-8', errors='ignore')
        for m in BANNED.finditer(text):
            hits.append(f"{rel.as_posix()}: …{m.group(0)}…")
    assert not hits, "회사를 '민간 …'으로 부르는 문구가 남아 있음:\n" + '\n'.join(hits[:20])


def test_notice_on_home_and_about():
    s = _text((ROOT / 'index.html').read_text(encoding='utf-8'))
    assert s.count(NOTICE) >= 1, '홈에 고지 문장이 없습니다.'
    about = re.search(r'<section[^>]*id="about"[^>]*>(.*?)</section>', s, re.S)
    assert about, '홈 #about(회사소개) 구역을 찾지 못했습니다.'
    assert DEF in about.group(1), '회사소개에 정의 문장이 없습니다.'


def test_definition_sentence_in_hero_llms_and_org():
    s = (ROOT / 'index.html').read_text(encoding='utf-8')
    lead = re.search(r'<p class="lead">(.*?)</p>', s, re.S)
    assert lead and _text(lead.group(1)).strip().startswith(DEF), '홈 히어로 설명 첫 문장이 정의 문장이 아닙니다.'
    for name in ('llms.txt', 'llms-full.txt'):
        first = next(l for l in (ROOT / name).read_text(encoding='utf-8').splitlines() if l.startswith('> '))
        assert first.startswith('> ' + DEF), f'{name} 첫 문단 첫 문장이 정의 문장이 아닙니다.'
    orgs = []
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
        d = json.loads(m)
        for n in d.get('@graph', [d]) if isinstance(d, dict) else d:
            if isinstance(n, dict) and n.get('@id') == 'https://bmaker.kr/#org':
                orgs.append(n.get('description', ''))
    assert orgs == [DEF], f'Organization description 이 정의 문장과 다릅니다: {orgs}'


def test_profile_only_statement_stays_off_site():
    profile = [s['text'] for s in B['statements'] if s.get('profile_only')]
    for name in ('index.html', 'llms.txt', 'llms-full.txt'):
        text = (ROOT / name).read_text(encoding='utf-8')
        for t in profile:
            assert t not in text, f'{name}: profile_only 문장이 들어가 있습니다.'


def _ledger_n():
    html = (ROOT / 'cases.html').read_text(encoding='utf-8')
    return html.count('<tr id="row-')


def test_about_first_paragraph_is_definition_plus_statements():
    s = _text((ROOT / 'index.html').read_text(encoding='utf-8'))
    about = re.search(r'<section[^>]*id="about"[^>]*>(.*?)</section>', s, re.S).group(1)
    first = re.search(r'<p>(.*?)</p>', about, re.S).group(1)
    st = brand.statements(_ledger_n())
    assert first == f'{DEF} {st[1]} {st[2]}'
    assert st[0] not in s, 'statements[0] 은 홈에 쓰지 않는다(정의와 겹침)'
    assert f'받은 사례 {_ledger_n():,}건' in first


def test_llms_company_block_has_statements_0_to_2():
    text = (ROOT / 'llms.txt').read_text(encoding='utf-8')
    lines = text.splitlines()
    i = next(k for k, l in enumerate(lines) if l.startswith('> '))
    assert lines[i + 1:i + 4] == ['', '## 회사', '']
    assert lines[i + 4:i + 7] == [f'- {t}' for t in brand.statements(_ledger_n())]
    assert lines.count('## 회사') == 1
    full = (ROOT / 'llms-full.txt').read_text(encoding='utf-8')
    assert '## 회사' not in full.splitlines() and B['statements'][1]['text'] not in full
