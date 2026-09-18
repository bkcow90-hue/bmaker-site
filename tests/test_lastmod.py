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
    return sorted(p for p in ROOT.glob('*.html') if p.name not in B.SKIP)


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
    assert sorted(reg) == sorted(p.name for p in pages()), 'data/page-updated.json 의 페이지 목록이 다름'
    for p in pages():
        s = p.read_text(encoding='utf-8')
        assert reg[p.name]['hash'] == B.content_hash(s), \
            f"{p.name}: 본문이 바뀌었는데 갱신일이 그대로 — python tools/build_lastmod.py 를 실행하세요"
        assert STAMP.findall(s)[0][0] == reg[p.name]['date'], f"{p.name}: 표시 날짜와 레지스트리 불일치"


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


def test_llms_files_declare_utf8_charset():
    """llms.txt 는 한글 본문 — charset 없이 text/plain 으로 나가면 크롤러가 깨뜨린다."""
    headers = (ROOT / '_headers').read_text(encoding='utf-8')
    for name in ('/llms.txt', '/llms-full.txt'):
        block = re.search(re.escape(name) + r'\n((?:  .*\n)+)', headers)
        assert block, f'_headers 에 {name} 규칙 없음'
        assert 'Content-Type: text/plain; charset=utf-8' in block.group(1), name
