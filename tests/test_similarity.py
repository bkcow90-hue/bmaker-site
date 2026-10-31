"""전 페이지 쌍별 본문 유사도 — 검색어·지역 이름만 바꾼 복제 페이지 방지 (규격 2절).

- 대상: 저장소의 공개 HTML 전부. 블로그(blog/ 와 목록 blog.html)는 제외 — 글 단위 품질은 test_blog 가 본다.
- 본문: <body> 텍스트에서 header·nav·footer·script·style·noscript·template 과
  class 에 related·sticky 가 들어간 요소를 뺀 것(공통 틀은 모든 페이지가 같아 비교 의미가 없다).
- 지표: 6어절 조각(6-gram) 자카드 유사도. 0.6 을 넘는 쌍이 하나라도 있으면 실패.

상위 쌍 확인: python tests/test_similarity.py [N]
"""
import itertools, re, sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NGRAM = 6
MAX_SIMILARITY = 0.6
SKIP_TAGS = {'header', 'nav', 'footer', 'script', 'style', 'noscript', 'template'}
SKIP_CLASSES = ('related', 'sticky')
VOID = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'source', 'track', 'wbr'}


class _Body(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.text, self._body, self._skip, self._skip_tag = [], False, 0, None

    def handle_starttag(self, tag, attrs):
        if tag == 'body':
            self._body = True; return
        if tag in VOID:
            return
        if self._skip:
            if tag == self._skip_tag:
                self._skip += 1
            return
        cls = dict(attrs).get('class') or ''
        if tag in SKIP_TAGS or any(c in cls for c in SKIP_CLASSES):
            self._skip, self._skip_tag = 1, tag

    def handle_endtag(self, tag):
        if self._skip and tag == self._skip_tag:
            self._skip -= 1

    def handle_data(self, data):
        if self._body and not self._skip:
            self.text.append(data)


def body_text(html):
    p = _Body()
    p.feed(html)
    return re.sub(r'\s+', ' ', ' '.join(p.text)).strip()


def grams(text):
    w = text.split()
    return {tuple(w[i:i + NGRAM]) for i in range(max(len(w) - NGRAM + 1, 0))}


def jaccard(a, b):
    return len(a & b) / len(a | b) if a | b else 0.0


def pages():
    files = [p for p in ROOT.rglob('*.html')
             if not {'.git', '.wrangler', 'blog', 'docs', 'node_modules'} & set(p.relative_to(ROOT).parts[:-1])
             and p.relative_to(ROOT).as_posix() != 'blog.html']
    return {p.relative_to(ROOT).as_posix()[:-5]: grams(body_text(p.read_text(encoding='utf-8'))) for p in sorted(files)}


def ranked():
    P = pages()
    return sorted(((jaccard(P[a], P[b]), a, b) for a, b in itertools.combinations(P, 2)), reverse=True)


def test_extraction_skips_shared_chrome():
    html = ('<html><body><header><nav>메뉴</nav>헤더</header><main><p>본문 하나</p>'
            '<div class="related"><div>함께 보기</div></div><div class="sticky-cta">고정</div>'
            '<p>본문 둘<br>계속</p></main><footer>푸터</footer><script>x()</script></body></html>')
    assert body_text(html) == '본문 하나 본문 둘 계속'


def test_jaccard_rule():
    a = grams('가 나 다 라 마 바 사')
    assert jaccard(a, a) == 1.0 and jaccard(a, grams('하 나 다 라 마 바 사')) == 1 / 3


def test_no_near_duplicate_pages():
    over = [f'/{a} ↔ /{b} — {s:.3f}' for s, a, b in ranked() if s > MAX_SIMILARITY]
    assert not over, f'본문 6-gram 자카드 {MAX_SIMILARITY} 초과 {len(over)}쌍:\n' + '\n'.join(over)


if __name__ == '__main__':
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    R = ranked()
    print(f'페이지 {len(pages())}장 · 쌍 {len(R)}개 · {MAX_SIMILARITY} 초과 {sum(s > MAX_SIMILARITY for s, *_ in R)}쌍')
    for s, a, b in R[:n]:
        print(f'{s:.3f}\t/{a}\t/{b}')
