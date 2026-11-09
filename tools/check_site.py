#!/usr/bin/env python3
"""check_site.py — 공개 HTML 전수 검사표 (규격 0절 AI 티 탈출 카피 기준 · 2절 SEO · 1절 금칙어).

사용: python tools/check_site.py            # 전체 표
      python tools/check_site.py index.html  # 특정 파일
      python tools/check_site.py --home      # 홈 기준(가운뎃점 ≤95, 3연 나열 ≤5, 줄표 0, ~니다 ≤40%, 금칙어 0) 통과/실패로 종료코드

빌드일 없이 읽기만 한다. 산출물은 docs/site-check.md (--write).
"""
import re, sys, json, html as _html
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {'tests', 'tools', 'docs', 'posts', 'workers', 'redirects', 'data', 'assets', '.git', '.github', '.claude', '.agents'}
BANNED = [r'갚[아는을다지]', r'100\s*%\s*승인', r'무조건', r'누구나\s*(가능|승인)', r'보장(합니다|해 드립니다|해드립니다)', r'실행 기록', r'중앙값', r'전부 공개', r'전건 공개', '민간 ' + '경영컨설팅', '민간 ' + '컨설팅 회사']  # 회사 호칭 금지(검사 자체가 걸리지 않게 분리)
TRIAD = re.compile(r'[가-힣A-Za-z]+·[가-힣A-Za-z]+·[가-힣A-Za-z]+')
NIDA = re.compile(r'(합니다|습니다|입니다)[.!]?$')


def pages(arg=None):
    if arg:
        return [ROOT / a for a in arg]
    out = []
    for p in ROOT.rglob('*.html'):
        rel = p.relative_to(ROOT).parts
        if rel[0] in SKIP_DIRS or p.name == '404.html':
            continue
        out.append(p)
    return sorted(out)


def visible_text(s):
    s = re.sub(r'<(script|style|noscript)[^>]*>.*?</\1>', ' ', s, flags=re.S | re.I)
    body = re.search(r'<main[^>]*>(.*?)</main>', s, re.S)
    s = body.group(1) if body else s
    s = re.sub(r'<[^>]+>', ' ', s)
    return _html.unescape(re.sub(r'\s+', ' ', s)).strip()


def metrics(p):
    s = p.read_text(encoding='utf-8', errors='ignore')
    t = visible_text(s)
    title = re.search(r'<title>(.*?)</title>', s, re.S)
    desc = re.search(r'<meta name="description" content="([^"]*)"', s)
    canon = re.search(r'<link rel="canonical" href="([^"]*)"', s)
    og = re.search(r'<meta property="og:title" content="([^"]*)"', s)
    h1 = re.findall(r'<h1[\s>]', s)
    ld_ok = True
    for m in re.finditer(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', s, re.S):
        try:
            json.loads(m.group(1))
        except Exception:
            ld_ok = False
    sents = [x.strip() for x in re.split(r'(?<=[.다요!?])\s+', t) if len(x.strip()) > 8]
    nida = sum(1 for x in sents if NIDA.search(x))
    banned = [b for b in BANNED if re.search(b, t)]
    rel = p.relative_to(ROOT).as_posix()
    slug = '' if rel == 'index.html' else rel[:-5]
    canon_ok = bool(canon) and canon.group(1).rstrip('/') == ('https://bmaker.kr/' + slug).rstrip('/')
    return {
        'page': rel,
        'title_len': len(_html.unescape(title.group(1).strip())) if title else 0,
        'desc_len': len(_html.unescape(desc.group(1))) if desc else 0,
        'h1': len(h1),
        'canon': canon_ok,
        'og=title': bool(title and og and _html.unescape(og.group(1)) == _html.unescape(title.group(1).strip())),
        'jsonld': ld_ok,
        'middot': t.count('·'),
        'triad': len(TRIAD.findall(t)),
        'emdash': t.count('—'),
        'nida%': round(nida / len(sents) * 100) if sents else 0,
        'banned': ','.join(banned),
    }


def main(argv):
    write = '--write' in argv
    home = '--home' in argv
    files = [a for a in argv if a.endswith('.html')]
    rows = [metrics(p) for p in (pages(files) if files else ([ROOT / 'index.html'] if home else pages()))]
    cols = list(rows[0].keys())
    lines = ['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)]
    for r in rows:
        lines.append('| ' + ' | '.join(str(r[c]) for c in cols) + ' |')
    table = '\n'.join(lines)
    print(table)
    if write:
        (ROOT / 'docs' / 'site-check.md').write_text('# site-check (tools/check_site.py)\n\n' + table + '\n', encoding='utf-8')
    if home:
        r = rows[0]
        fails = []
        # 기준선 2026-11-09: 가운뎃점 127→89, 3연 나열 23→5(남은 5개는 brand.json 고정 문장·규격 고정 문장·업종 데이터값)
        if r['middot'] > 95: fails.append(f"가운뎃점 {r['middot']} > 95")
        if r['triad'] > 5: fails.append(f"3연 나열 {r['triad']} > 5")
        if r['emdash'] > 0: fails.append(f"줄표 {r['emdash']}")
        if r['nida%'] > 40: fails.append(f"~니다 종결 {r['nida%']}% > 40%")
        if r['banned']: fails.append('금칙어 ' + r['banned'])
        if r['h1'] != 1: fails.append(f"h1 {r['h1']}개")
        if not r['jsonld']: fails.append('JSON-LD 파싱 실패')
        print('\nHOME:', 'PASS' if not fails else 'FAIL — ' + '; '.join(fails))
        return 1 if fails else 0
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
