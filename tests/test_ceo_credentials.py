"""대표 자격 표기(대표 2026-10-04 PR #27 답변).

- 자격은 홈 회사소개(#about)의 "대표 자격" 항목과 Person(#founder) JSON-LD 에만 둔다. 다른 페이지·llms 에 쓰지 않는다.
- 대표 개인 자격임을 분명히 한다("김상표 대표 개인 자격"). 회사가 ISO 인증을 받은 것처럼 읽히는 문구 금지 —
  자격 항목 안에는 "인증"이라는 말을 쓰지 않고, 사이트 전체에서 회사가 ISO 인증을 받았다는 식의 문장을 막는다.
  (/certification 의 "ISO 인증 무료 진단"처럼 고객사 인증을 돕는 서비스 설명은 대상이 아니다.)
"""
import json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CREDS = ['ISO 9001·14001·45001 내부심사원', '창업상권분석지도사 1급(민간자격)', 'AI 창업지도사(민간자격)']
MARKERS = ('내부심사원', '창업상권분석지도사', 'AI 창업지도사')
# 회사(비즈니스 메이커·당사)가 ISO 인증 주체로 읽히는 문장
COMPANY_ISO = re.compile(r'(비즈니스 메이커|당사|저희)[^.。<]{0,40}ISO[^.。<]{0,20}(인증|획득|보유)'
                         r'|ISO[^.。<]{0,15}인증\s?(기업|회사|획득|보유|업체)')


def _index():
    return (ROOT / 'index.html').read_text(encoding='utf-8')


def _block(s):
    m = re.search(r'<div class="ceo-credentials"[^>]*>(.*?)</div>', s, re.S)
    assert m, '회사소개에 대표 자격 항목(div.ceo-credentials)이 없습니다.'
    return m.group(1)


def test_credentials_in_about_block():
    s = _index()
    about = re.search(r'<section[^>]*id="about"[^>]*>(.*?)</section>', s, re.S).group(1)
    blk = _block(about)
    assert '대표 자격' in blk and '대표 개인 자격' in blk
    items = [re.sub(r'<[^>]+>', '', x).strip() for x in re.findall(r'<li>(.*?)</li>', blk, re.S)]
    assert items == CREDS
    assert '인증' not in re.sub(r'<[^>]+>', '', blk), '자격 항목에 "인증"이 들어가면 회사 인증처럼 읽힙니다.'


def test_person_has_credentials():
    founder = None
    for m in re.findall(r'<script type="application/ld\+json">(.*?)</script>', _index(), re.S):
        d = json.loads(m)
        for n in d.get('@graph', [d]) if isinstance(d, dict) else d:
            f = n.get('founder') if isinstance(n, dict) else None
            if isinstance(f, dict) and f.get('@id') == 'https://bmaker.kr/#founder':
                founder = f
    assert founder, 'Organization.founder(#founder) 를 찾지 못했습니다.'
    names = [c['name'] for c in founder.get('hasCredential', [])]
    assert names == ['ISO 9001·14001·45001 내부심사원', '창업상권분석지도사 1급', 'AI 창업지도사']
    assert all('인증' not in json.dumps(c, ensure_ascii=False) for c in founder['hasCredential'])


def test_credentials_only_in_about_and_person():
    s = _index()
    rest = re.sub(r'<div class="ceo-credentials"[^>]*>.*?</div>', '', s, flags=re.S)
    rest = re.sub(r'"hasCredential":\s*\[.*?\]', '', rest, flags=re.S)
    assert not [m for m in MARKERS if m in rest], '대표 자격이 회사소개·Person 밖(홈)에 있습니다.'
    others = []
    for p in list(ROOT.glob('*.html')) + list(ROOT.glob('*/**/*.html')) + [ROOT / 'llms.txt', ROOT / 'llms-full.txt']:
        if p.name == 'index.html' and p.parent == ROOT or 'node_modules' in p.parts or 'docs' in p.parts:
            continue
        t = p.read_text(encoding='utf-8', errors='ignore')
        others += [f'{p.relative_to(ROOT).as_posix()}: {m}' for m in MARKERS if m in t]
    assert not others, '대표 자격이 다른 페이지에 있습니다: ' + ', '.join(others[:10])


def test_no_company_iso_certification_claim():
    hits = []
    for p in list(ROOT.glob('*.html')) + list(ROOT.glob('*/**/*.html')) + [ROOT / 'llms.txt', ROOT / 'llms-full.txt']:
        if 'node_modules' in p.parts or 'docs' in p.parts:
            continue
        for m in COMPANY_ISO.finditer(p.read_text(encoding='utf-8', errors='ignore')):
            hits.append(f'{p.relative_to(ROOT).as_posix()}: …{m.group(0)}…')
    assert not hits, '회사가 ISO 인증을 받은 것처럼 읽히는 문구:\n' + '\n'.join(hits[:10])


def test_rule_catches_misuse():
    assert COMPANY_ISO.search('비즈니스 메이커는 ISO 9001 인증을 받은 회사입니다')
    assert COMPANY_ISO.search('ISO 인증 기업 비즈니스 메이커')
    assert not COMPANY_ISO.search('기업부설연구소 설립, ISO 인증 무료 진단')
