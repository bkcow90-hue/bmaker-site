"""비용 구조 설명(착수금·진행비·성과 보수·성공보수)은 FAQ 비용 답과 llms 파일에만 둔다.

대표 결정 2026-09-28(1B·2A·3A), 규격 1절·4절. 그 외 화면 텍스트·메타·JSON-LD 는 "진단은 무료입니다."까지.

허용(검사 제외):
  - FAQ — 화면 문장이 그 페이지 FAQPage JSON-LD 의 질문·답과 같은 것, 그리고 FAQPage JSON-LD 자체
  - llms.txt·llms-full.txt (이 파일은 HTML 만 본다)
  - /chaksugeum 으로 가는 링크 문구(3A)
  - /chaksugeum 페이지의 착수금 일반 정보·사기 구별 내용(2A) — 단 "비즈니스 메이커…"·"저희…" 우리 소개 문장은 검사
동결 6장(메타 동결 ~10/6)의 메타에는 결정 시점에 비용 구절이 없었다 — 예외 없이 검사한다.
"""
import json
import re
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# '실행 전 비용 0원' 처럼 금칙어 없이 같은 뜻을 말하는 표현도 비용 구조 설명이다
KW = re.compile(r'착수금|진행비|성과\s?보수|성공\s?보수|성과로만|실행 전 비용|비용은 0원|비용 0원|보수를 받|보수가 발생')
OURS = re.compile(r'비즈니스 ?메이커[는가은의]|저희|우리 ')
VOID = {'meta', 'link', 'br', 'img', 'input', 'hr', 'source', 'area', 'base', 'col', 'embed', 'param', 'track', 'wbr'}


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def sentences(text):
    return [x for x in re.split(r'(?<=[.다요?!])\s+', norm(text)) if x]


class _Scan(HTMLParser):
    """화면 텍스트(헤더·푸터 포함)·메타·JSON-LD 를 위치와 함께 모은다."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.text, self.meta, self.ld = [], [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('content'):
            key = a.get('name') or a.get('property') or ''
            if key in ('description', 'keywords') or key.startswith(('og:', 'twitter:')):
                self.meta.append((key, a['content']))
        if tag not in VOID:
            self.stack.append((tag, a))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data):
        if not data.strip():
            return
        tags = [t for t, _ in self.stack]
        if 'script' in tags:
            a = [a for t, a in self.stack if t == 'script'][-1]
            if 'ld+json' in (a.get('type') or ''):
                self.ld.append(data)
            return
        if 'style' in tags or 'noscript' in tags:
            return
        if 'title' in tags:
            self.meta.append(('title', data))
            return
        link = next((a.get('href', '') for t, a in reversed(self.stack) if t == 'a'), None)
        self.text.append((data, link))


def _faq_texts(lds):
    out = set()
    for raw in lds:
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        for node in data if isinstance(data, list) else [data]:
            if isinstance(node, dict) and node.get('@type') == 'FAQPage':
                for q in node.get('mainEntity', []):
                    out.add(norm(q.get('name', '')))
                    out.add(norm((q.get('acceptedAnswer') or {}).get('text', '')))
    return {x for x in out if x}


def _strings(node):
    if isinstance(node, dict):
        if node.get('@type') == 'FAQPage':
            return
        for v in node.values():
            yield from _strings(v)
    elif isinstance(node, list):
        for v in node:
            yield from _strings(v)
    elif isinstance(node, str):
        yield node


def violations(path):
    name = path.relative_to(ROOT).as_posix()
    s = _Scan()
    s.feed(path.read_text(encoding='utf-8'))
    faq = _faq_texts(s.ld)
    faq_blob = ' '.join(faq)
    topic = name == 'chaksugeum.html'
    bad = []

    def allowed_topic(sent):
        return topic and not OURS.search(sent)

    for data, link in s.text:
        if not KW.search(data):
            continue
        if link is not None and 'chaksugeum' in link:
            continue
        for sent in sentences(data):
            if KW.search(sent) and sent not in faq_blob and not allowed_topic(sent):
                bad.append(('화면', sent))
    for key, content in s.meta:
        if not KW.search(content):
            continue
        for sent in sentences(content):
            if KW.search(sent) and not allowed_topic(sent):
                bad.append((key, sent))
    for raw in s.ld:
        try:
            data = json.loads(raw)
        except ValueError:
            continue
        for text in _strings(data):
            for sent in sentences(text):
                if KW.search(sent) and sent not in faq_blob and not allowed_topic(sent):
                    bad.append(('JSON-LD', sent))
    return bad


def pages():
    return sorted(list(ROOT.glob('*.html')) + list(ROOT.glob('industry/*.html')) + list(ROOT.glob('region/*.html')) + list(ROOT.glob('blog/**/*.html')))


def test_fee_structure_only_in_faq_and_llms():
    found = {p.relative_to(ROOT).as_posix(): v for p in pages() for v in [violations(p)] if v}
    lines = [f'{f}: [{w}] {x}' for f, v in found.items() for w, x in v]
    assert not found, f'비용 구조 설명은 FAQ 비용 답·llms 파일에만 — {len(lines)}건\n' + '\n'.join(lines[:60])


def test_llms_keep_fee_structure():
    """llms 파일은 비용 구조 설명을 유지하는 곳이다(대표 결정 1B)."""
    for f in ('llms.txt', 'llms-full.txt'):
        assert KW.search((ROOT / f).read_text(encoding='utf-8')), f
