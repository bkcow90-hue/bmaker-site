"""전 사이트 신뢰 문구 — 푸터 근거 한 줄 · Organization JSON-LD(규격 3절·4절, 2026-11-02).

- 푸터 근거 한 줄: build_lastmod 가 모든 페이지 푸터의 최종 업데이트 줄 앞에 넣는다(복사돼 온 것은 걷어내고 다시).
  숫자는 data/cases.csv(build_cases 생성)에서 센다 — 홈 data-stat 과 같은 값.
- "왜 여기서" 3줄(폼 위)은 넣지 않는다 — 넣으면 /ilsijeok-homeplus·/jangaein 본문 유사도가 0.580→0.618 로 0.6 을 넘어 푸터 한 줄로만 둔다(2026-11-02).
- Organization: @type 이 있는 #org 노드에 description = brand.json definition, sameAs = brand.json sameAs(빈 배열이면 키 생략).
"""
import csv
import json
import re
from pathlib import Path

import brand

ROOT = Path(__file__).resolve().parent.parent


def ledger_counts():
    """(공개 원장 건수, 증빙 건수) — data/cases.csv 기준."""
    with open(ROOT / 'data' / 'cases.csv', encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))
    return len(rows), sum(1 for r in rows if r.get('근거') == '기관 안내문·약정 캡처')


FOOT_RE = re.compile(r'<p class="foot-trust">.*?</p>', re.S)


def footer_line(n, ev):
    return (f'<p class="foot-trust"><a href="/cases">공개 원장 <span data-stat="total-n">{n:,}</span>건 · '
            f'증빙 <span data-stat="ev-n">{ev:,}</span>건</a> · <a href="/#about">대표 김상표</a> · '
            f'<a href="/geojeol">진행이 어려우면 먼저 말합니다</a></p>')


def stamp_footer_trust(s, n, ev):
    """푸터 안 최종 업데이트 줄 바로 앞에 근거 한 줄. 푸터나 최종 업데이트 줄이 없으면 그대로."""
    m = re.search(r'<footer\b[^>]*>.*?</footer>', s, re.S)
    if not m:
        return s
    foot = FOOT_RE.sub('', m.group(0))
    if '<p class="lastmod"' not in foot:
        return s
    foot = foot.replace('<p class="lastmod"', footer_line(n, ev) + '<p class="lastmod"', 1)
    return s[:m.start()] + foot + s[m.end():]


LD_RE = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)


def stamp_org(s, b=None):
    """@type 이 있는 #org 노드의 description·sameAs 를 brand.json 에 맞춘다. 바뀐 블록만 다시 쓴다."""
    b = b or brand.load()

    def fix(node):
        changed = False
        if isinstance(node, dict):
            if node.get('@id') == 'https://bmaker.kr/#org' and '@type' in node:
                want = dict(node)
                want['description'] = b['definition']
                if b['sameAs']:
                    want['sameAs'] = list(b['sameAs'])
                else:
                    want.pop('sameAs', None)
                if want != node:
                    node.clear(); node.update(want); changed = True
            for v in node.values():
                changed |= fix(v)
        elif isinstance(node, list):
            for v in node:
                changed |= fix(v)
        return changed

    def one(m):
        try:
            data = json.loads(m.group(2))
        except ValueError:
            return m.group(0)
        if not fix(data):
            return m.group(0)
        return m.group(1) + json.dumps(data, ensure_ascii=False) + m.group(3)

    return LD_RE.sub(one, s)
