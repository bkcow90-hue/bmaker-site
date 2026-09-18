#!/usr/bin/env python3
"""푸터 '최종 업데이트' 한 줄·JSON-LD dateModified·sitemap lastmod 를 같은 값으로 스탬프한다.

날짜 규칙
  - 사례 페이지(cases.html): 원장 빌드일 — cases.html Dataset 의 dateModified 를 그대로 쓴다.
  - 그 외(홈·상세·블로그): 그 페이지 내용이 마지막으로 바뀐 날.
    스탬프(푸터 한 줄·WebPage 블록·dateModified 값)는 해시에서 빼고 비교하므로
    스탬프를 넣는 커밋이 다음 날짜를 또 올리는 자기참조가 생기지 않는다.
    레지스트리(data/page-updated.json)에 없는 페이지는 git 최종 커밋일(KST)로 seed 한다.

sitemap.xml 의 lastmod 도 같은 값으로 맞춘다. 다른 빌더들은 lastmod 에 '오늘'을 쓰지만
이 스크립트가 마지막에 레지스트리 값으로 되돌리므로, 내용이 안 바뀐 페이지의 lastmod 는 움직이지 않는다.

실행: python tools/build_lastmod.py   — 다른 build_*.py 를 모두 돌린 뒤 마지막에 실행한다.
      (자금·재단·교육 빌더가 다른 페이지의 <footer>·<head> 를 복사해 가므로 순서가 중요하다)
실패 시: 아무 파일도 쓰지 않고 한국어로 원인을 출력한다.
"""
import datetime, hashlib, json, os, re, subprocess, sys
from pathlib import Path
from builddate import build_date

ROOT = Path(__file__).resolve().parent.parent
REG = ROOT / 'data' / 'page-updated.json'
SITEMAP = ROOT / 'sitemap.xml'
PREFIX = 'https://bmaker.kr/'
TODAY = build_date().isoformat()  # BUILD_DATE 있으면 그 날짜, 없으면 Asia/Seoul 오늘 (tools/builddate.py)
SKIP = {'404.html'}       # noindex 오류 페이지 — 어떤 경로에서도 서빙되므로 날짜 의미가 없다
LEDGER = {'cases.html'}   # 원장 빌드일을 쓰는 페이지
LABEL = '최종 업데이트'
LD_TYPES = {'WebPage', 'Article', 'BlogPosting', 'NewsArticle'}

STAMP = re.compile(r'<p class="lastmod"[^>]*>.*?</p>', re.S)
WEBPAGE_LD = re.compile(r'<script type="application/ld\+json" data-webpage>.*?</script>', re.S)
ANY_LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)
DATEMOD = re.compile(r'"dateModified"\s*:\s*"\d{4}-\d{2}-\d{2}"')
URL_BLOCK = re.compile(r'<url>\s*<loc>([^<]+)</loc>.*?</url>', re.S)
LASTMOD = re.compile(r'<lastmod>[^<]*</lastmod>')
MAIN = re.compile(r'<main\b[^>]*>(.*?)</main>', re.S)
TITLE = re.compile(r'<title>(.*?)</title>', re.S)
DESC = re.compile(r'<meta name="description" content="([^"]*)"')


def die(msg):
    print(f"[갱신일 스탬프 실패] {msg}")
    sys.exit(1)


def content_hash(s):
    """갱신일 판정 범위 = 페이지 본문(<main>) + <title> + meta description. 스탬프는 제외.

    공통 부품(헤더·내비·푸터)이나 페이지마다 복사돼 있는 <style> 블록을 한 번 손대면
    61개 페이지의 '최종 업데이트' 가 같은 날짜로 한꺼번에 올라간다. 실제로 바뀐 것은 공통
    부품인데 모든 페이지가 갱신된 것처럼 보이면 날짜가 거짓말이 되므로 범위에서 뺀다.
    title·description 은 검색 결과에 그대로 나가는 값이라 포함한다 — 고치면 재크롤을
    유도해야 한다. JSON-LD 는 스탬퍼 자신이 날짜를 써 넣는 곳이라 제외한다.
    <main> 이 없는 페이지는 전체를 쓴다(현재 대상 62개는 전부 <main> 이 하나씩 있다).
    """
    m = MAIN.search(s)
    head = ' '.join(TITLE.findall(s) + DESC.findall(s))
    s = (m.group(1) if m else s) + '\n<!--head-->' + head
    s = STAMP.sub('', s)
    s = WEBPAGE_LD.sub('', s)
    s = DATEMOD.sub('"dateModified":"-"', s)
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


def git_date(name):
    """그 파일을 마지막으로 건드린 커밋의 날짜(KST). 저장소·git 이 없으면 None."""
    try:
        r = subprocess.run(['git', 'log', '-1', '--format=%cd', '--date=format-local:%Y-%m-%d', '--', name],
                           cwd=ROOT, env=dict(os.environ, TZ='Asia/Seoul'),
                           capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    d = r.stdout.strip()
    return d if re.fullmatch(r'\d{4}-\d{2}-\d{2}', d) else None


def ledger_date():
    """원장 빌드일 = build_cases.py 가 cases.html Dataset 에 남긴 dateModified."""
    s = (ROOT / 'cases.html').read_text(encoding='utf-8')
    for m in ANY_LD.finditer(s):
        try:
            d = json.loads(m.group(1))
        except ValueError:
            continue
        if isinstance(d, dict) and d.get('@type') == 'Dataset' and d.get('dateModified'):
            return d['dateModified']
    die('cases.html 에서 Dataset dateModified(원장 빌드일)를 찾지 못했습니다. build_cases.py 를 먼저 실행하세요.')


def canonical_of(s):
    m = re.search(r'<link rel="canonical" href="([^"]+)">', s)
    return m.group(1) if m else None


def stamp_footer(s, date):
    """푸터 .wrap 의 마지막에 한 줄. 푸터가 없으면 </main> 앞."""
    tag = (f'<p class="lastmod" data-lastmod="{date}" '
           f'style="margin-top:14px;font-size:.78rem;opacity:.62">{LABEL}: {date}</p>')
    s = STAMP.sub('', s)                      # 복사돼 온 것까지 전부 걷어낸다
    m = re.search(r'<footer\b[^>]*>(.*?)</footer>', s, re.S)
    if m:
        inner = m.group(1)
        i = inner.rfind('</div>')
        if i < 0:
            i = len(inner)
        return s[:m.start(1)] + inner[:i] + tag + inner[i:] + s[m.end(1):]
    for close in ('</main>', '</body>'):
        if close in s:
            return s.replace(close, tag + close, 1)
    die('푸터·main·body 를 찾지 못해 스탬프를 넣을 자리가 없습니다.')


def stamp_jsonld(s, date):
    """WebPage/Article 노드의 dateModified 를 같은 값으로. 없으면 WebPage 노드를 새로 넣는다."""
    s = WEBPAGE_LD.sub('', s)                 # 다른 페이지에서 복사돼 온 블록 제거(주소가 남의 것)
    for m in ANY_LD.finditer(s):
        body = m.group(1)
        try:
            d = json.loads(body)
        except ValueError:
            continue
        nodes = d.get('@graph') if isinstance(d, dict) and '@graph' in d else (d if isinstance(d, list) else [d])
        if not any(isinstance(n, dict) and n.get('@type') in LD_TYPES for n in nodes):
            continue
        if len(DATEMOD.findall(body)) != 1:   # 애매하면 손대지 않는다
            continue
        return s[:m.start(1)] + DATEMOD.sub(f'"dateModified": "{date}"', body) + s[m.end(1):]
    if 'name="robots" content="noindex' in s:  # 색인 안 되는 페이지엔 굳이 넣지 않는다
        return s
    url = canonical_of(s)
    if not url or '</head>' not in s:
        return s
    node = {"@context": "https://schema.org", "@type": "WebPage", "@id": url + "#webpage", "url": url,
            "inLanguage": "ko", "isPartOf": {"@id": "https://bmaker.kr/#website"}, "dateModified": date}
    block = '<script type="application/ld+json" data-webpage>' + json.dumps(node, ensure_ascii=False) + '</script>'
    return s.replace('</head>', block + '</head>', 1)


def page_of(loc):
    """sitemap 의 loc → 저장소의 페이지 파일명. 홈은 index.html."""
    if not loc.startswith(PREFIX):
        return None
    slug = loc[len(PREFIX):].strip('/')
    return 'index.html' if slug == '' else slug + '.html'


def stamp_sitemap(dates):
    """sitemap lastmod = 그 페이지의 갱신일. lastmod 가 없는 항목에는 새로 넣는다."""
    s0 = SITEMAP.read_text(encoding='utf-8')
    unknown = []

    def one(m):
        block, loc = m.group(0), m.group(1)
        date = dates.get(page_of(loc) or '')
        if not date:                       # 페이지가 아닌 항목은 근거가 없으므로 건드리지 않는다
            unknown.append(loc)
            return block
        if '<lastmod>' in block:
            return LASTMOD.sub(f'<lastmod>{date}</lastmod>', block, count=1)
        return block.replace('</loc>', f'</loc><lastmod>{date}</lastmod>', 1)

    s = URL_BLOCK.sub(one, s0)
    if s != s0:
        SITEMAP.write_text(s, encoding='utf-8')
    return s != s0, unknown


def main():
    reg = {}
    if REG.exists():
        try:
            reg = json.loads(REG.read_text(encoding='utf-8'))
        except ValueError:
            die(f'{REG.name} 을 읽을 수 없습니다. 파일을 지우고 다시 실행하면 git 기록으로 다시 채웁니다.')
    pages = sorted(p for p in ROOT.glob('*.html') if p.name not in SKIP)
    if not pages:
        die('저장소 루트에 페이지가 없습니다.')
    out, touched, seeded = {}, [], []
    led = ledger_date() if any(p.name in LEDGER for p in pages) else TODAY
    for p in pages:
        s0 = p.read_text(encoding='utf-8')
        h = content_hash(s0)
        prev = reg.get(p.name)
        if p.name in LEDGER:
            date = led
        elif prev and prev.get('hash') == h:
            date = prev['date']
        elif prev is None:
            date = git_date(p.name) or TODAY   # 최초 도입 — 스탬프가 없던 시점의 커밋일이 실제 갱신일
            seeded.append(p.name)
        else:
            date = TODAY
        out[p.name] = {'date': date, 'hash': h}
        s = stamp_jsonld(stamp_footer(s0, date), date)
        if content_hash(s) != h:
            die(f'{p.name}: 스탬프 삽입이 본문을 바꿨습니다(해시 불일치). 스크립트를 고쳐야 합니다.')
        if s != s0:
            p.write_text(s, encoding='utf-8')
            touched.append(p.name)
    REG.write_text(json.dumps(out, ensure_ascii=False, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    sm_changed, unknown = stamp_sitemap({k: v['date'] for k, v in out.items()})
    print(f"[갱신일 스탬프 OK] {len(out)}개 페이지 (수정 {len(touched)}개, 신규 seed {len(seeded)}개, "
          f"sitemap {'갱신' if sm_changed else '그대로'}, 원장 빌드일 {led}, 오늘 {TODAY})"
          + (f" — sitemap 에 대응 페이지가 없는 항목 {len(unknown)}개: {unknown[:3]}" if unknown else ""))


if __name__ == '__main__':
    main()
