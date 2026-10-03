"""푸터 '최종 업데이트' 한 줄과 JSON-LD dateModified 가 전 페이지에 같은 값으로 붙어 있는지 고정한다.

여기서 실패하면 대개 `python tools/build_lastmod.py` 를 안 돌린 것이다(빌드 체인 마지막 단계).
"""
import datetime, glob, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_lastmod as B  # noqa: E402

STAMP = re.compile(r'<p class="lastmod" data-lastmod="(\d{4}-\d{2}-\d{2})"[^>]*>'
                   + re.escape(B.LABEL) + r': (\d{4}-\d{2}-\d{2})</p>')


def pages():
    # 업종 의도 랜딩(/industry/<slug>)도 스탬프 대상이다 — 빌더와 같은 목록을 본다
    return (sorted(p for p in ROOT.glob('*.html') if p.name not in B.SKIP)
            + sorted(ROOT.glob('industry/*.html')) + sorted(ROOT.glob('region/*.html')) + sorted(ROOT.glob('blog/**/*.html')))


def key(p):
    """레지스트리 키 = 저장소 기준 상대경로(루트 페이지는 예전과 같은 파일명)."""
    return p.relative_to(ROOT).as_posix()


def test_every_page_shows_one_last_updated_line():
    for p in pages():
        found = STAMP.findall(p.read_text(encoding='utf-8'))
        assert len(found) == 1, f"{p.name}: 푸터 '{B.LABEL}' 줄이 {len(found)}개 — build_lastmod.py 실행 필요"
        attr, text = found[0]
        assert attr == text, f"{p.name}: data-lastmod({attr}) ≠ 표시 날짜({text})"
        datetime.date.fromisoformat(text)


def test_registry_matches_pages():
    """레지스트리(날짜의 근거)가 현재 본문과 맞물려 있어야 한다 — 어긋나면 날짜가 거짓말이 된다."""
    reg = json.loads((ROOT / 'data' / 'page-updated.json').read_text(encoding='utf-8'))
    assert sorted(reg) == sorted(key(p) for p in pages()), 'data/page-updated.json 의 페이지 목록이 다름'
    for p in pages():
        k = key(p)
        s = p.read_text(encoding='utf-8')
        assert reg[k]['hash'] == B.content_hash(s), \
            f"{k}: 본문이 바뀌었는데 갱신일이 그대로 — python tools/build_lastmod.py 를 실행하세요"
        assert STAMP.findall(s)[0][0] == reg[k]['date'], f"{k}: 표시 날짜와 레지스트리 불일치"


def _page_nodes(s):
    for m in re.finditer(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', s, re.S):
        d = json.loads(m.group(1))
        nodes = d.get('@graph') if isinstance(d, dict) and '@graph' in d else (d if isinstance(d, list) else [d])
        for n in nodes:
            if isinstance(n, dict) and n.get('@type') in B.LD_TYPES:
                yield n


def test_jsonld_datemodified_matches_footer():
    for p in pages():
        s = p.read_text(encoding='utf-8')
        if 'name="robots" content="noindex' in s:
            continue
        nodes = list(_page_nodes(s))
        assert len(nodes) == 1, f"{p.name}: WebPage/Article 노드가 {len(nodes)}개"
        assert nodes[0].get('dateModified') == STAMP.findall(s)[0][0], f"{p.name}: JSON-LD dateModified ≠ 푸터 날짜"
        canon = re.search(r'<link rel="canonical" href="([^"]+)">', s)
        if nodes[0]['@type'] == 'WebPage':
            assert nodes[0]['url'] == canon.group(1), f"{p.name}: WebPage url 이 canonical 과 다름(복사 누락)"


def test_cases_page_uses_ledger_build_date():
    """사례 페이지의 날짜는 원장 빌드일(Dataset dateModified)이다."""
    s = (ROOT / 'cases.html').read_text(encoding='utf-8')
    assert STAMP.findall(s)[0][0] == B.ledger_date()


def test_sitemap_lastmod_matches_registry():
    """sitemap lastmod = 푸터·JSON-LD 와 같은 갱신일. 크롤러가 보는 세 값이 어긋나면 안 된다."""
    reg = json.loads((ROOT / 'data' / 'page-updated.json').read_text(encoding='utf-8'))
    blocks = list(B.URL_BLOCK.finditer((ROOT / 'sitemap.xml').read_text(encoding='utf-8')))
    assert blocks, 'sitemap.xml 에 <url> 항목이 없음'
    for m in blocks:
        loc, block = m.group(1), m.group(0)
        name = B.page_of(loc)
        assert name in reg, f'sitemap {loc}: 대응 페이지({name})가 레지스트리에 없음'
        lm = re.search(r'<lastmod>([^<]*)</lastmod>', block)
        assert lm, f'sitemap {loc}: lastmod 없음 — build_lastmod.py 실행 필요'
        assert lm.group(1) == reg[name]['date'], \
            f"sitemap {loc}: lastmod {lm.group(1)} ≠ 갱신일 {reg[name]['date']}"


def test_llms_files_declare_utf8_charset():
    """llms.txt 는 한글 본문 — charset 없이 text/plain 으로 나가면 크롤러가 깨뜨린다."""
    headers = (ROOT / '_headers').read_text(encoding='utf-8')
    for name in ('/llms.txt', '/llms-full.txt'):
        block = re.search(re.escape(name) + r'\n((?:  .*\n)+)', headers)
        assert block, f'_headers 에 {name} 규칙 없음'
        assert 'Content-Type: text/plain; charset=utf-8' in block.group(1), name


def test_assets_are_versioned_by_content():
    """페이지가 부르는 /assets/*.js·*.css 는 ?v=<현재 파일 해시> 여야 한다.

    _headers 가 /assets/*.js·*.css 를 1년 immutable 로 캐시한다(해시가 있어야 안전한 설정).
    주소가 그대로면 배포 뒤에도 방문자 브라우저가 옛 conversion.js 를 새 HTML 과 섞어 쓴다
    — 하루 캐시였던 2026-09-28 인라인 폼 배포 당일에도 이
    조합에서 사업자 형태 버튼이 무반응이었고 제출도 조용히 실패했다. 로컬 브라우저 테스트는
    항상 최신 JS 를 받으므로 이 사고를 재현하지 못한다. 그래서 주소 자체를 검사한다.
    """
    import hashlib, re
    root = Path(__file__).resolve().parents[1]
    ref = re.compile(r'(?:src|href)="(/assets/(?!fonts/)[\w./-]+\.(?:js|css))(\?v=[0-9a-f]+)?"')
    bad = []
    for p in sorted(root.glob('*.html')) + sorted(root.glob('industry/*.html')) + sorted(root.glob('region/*.html')) + sorted(root.glob('blog/**/*.html')):
        for path, ver in ref.findall(p.read_text(encoding='utf-8')):
            want = '?v=' + hashlib.sha256((root / path.lstrip('/')).read_bytes().replace(b'\r', b'')).hexdigest()[:10]
            if ver != want:
                bad.append(f'{p.name}: {path}{ver} (기대 {want})')
    assert not bad, '자산 버전이 파일 내용과 다르다 — python tools/build_lastmod.py 를 돌릴 것:\n' + '\n'.join(bad[:10])
