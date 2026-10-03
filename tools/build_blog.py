#!/usr/bin/env python3
"""bmaker.kr/blog 정적 블로그 빌드 — posts/YYYY-MM-DD-<slug>.md → blog.html · blog/<slug>.html ·
blog/category/<cat>.html · blog/feed.xml, 그리고 sitemap·llms.txt·llms-full.txt 의 blog 블록.

2026-10-04 blog.bmaker.kr(WordPress.com) 통합(A안, docs/wp-audit-2026-10.md)으로 신설.
- 셸은 허브 2장(build_hubs)과 같다: sojingong 첫 <style> + jaedan 의 <header>·<footer> + 인라인 진단 폼.
- 날짜는 전부 글의 frontmatter(date·updated)에서 온다. 빌드한 날을 쓰지 않으므로 체인을 몇 번 돌려도
  산출물이 같다. 푸터 '최종 업데이트'·dateModified·sitemap lastmod 는 build_lastmod 가 스탬프한다.
- 규격(docs/homepage-standard.md): 첫 문단 직답 · 작성자 줄 · 면책 · "본 안내는 YYYY년 M월 기준" ·
  화면 FAQ 와 FAQPage JSON-LD 는 같은 목록에서 생성(100% 일치) · 정본 URL 은 확장자 없는 형태.
- 금칙어(1절)와 비용 구조 문구(4절)가 글에 있으면 멈춘다. 블로그 제목이 자금 정식명으로 시작하거나
  기존 페이지 title 과 같으면 멈춘다 — 자금 검색어는 자금 페이지 몫이다(카니발 방지).

posts/*.md 형식
  ---
  title: "제목"               (필수, " | 비즈니스 메이커" 는 빌더가 붙인다)
  date: 2026-09-21            (필수, 발행일)
  updated: 2026-09-21         (선택, 내용 확인일 — 없으면 date)
  category: guide|fund|case|news
  summary: "요약 한두 문장"    (필수, meta description·목록·feed)
  tags: [태그, 태그]
  image: /assets/og.png
  draft: false                (true 면 만들지 않는다)
  ---
  첫 문단 = 직답(필수). 이후 ## / ### 제목, 문단, - 목록, 1. 목록, | 표 |, > 인용, **굵게**, [링크](주소).
  "## 자주 묻는 질문" 아래의 "### 질문" + 답 문단이 FAQ 가 된다.

실행: python tools/build_blog.py   (빌더 체인에서 build_hubs 다음, build_lastmod 앞)
"""
import csv, html, json, re, sys
from email.utils import format_datetime
from datetime import datetime
from pathlib import Path

from builddate import KST   # feed 의 RFC 822 표기용 시간대 — 날짜 계산은 하지 않는다(글 날짜는 frontmatter)
from inline_form import form_html, CSS as FORM_CSS, TITLE_GENERAL

ROOT = Path(__file__).resolve().parent.parent
POSTS = ROOT / 'posts'
OUT = ROOT / 'blog'
SITE = 'https://bmaker.kr'
BRAND = '비즈니스 메이커'

CATEGORIES = {   # 순서 = 목록·내비 순서
    'guide': ('실무 가이드', '신청 전 자료 정리·서류·상담 준비처럼 자금 종류와 관계없이 쓰는 실무'),
    'fund': ('자금·지원정보', '자금과 지원사업을 고르고 준비하는 관점의 안내. 자금별 조건은 각 자금 페이지에 있습니다'),
    'case': ('사례', '받은 사례를 바탕으로 한 준비 과정'),
    'news': ('소식', '공고·협약·제도 변경 소식. 기간이 지난 글은 참고용입니다'),
}
REQUIRED = ('title', 'date', 'category', 'summary')

# 규격 1절 금칙어 + 사용자 지정 목록. 블로그 본문·제목·요약 어디에도 쓰지 않는다.
BANNED = re.compile(r'갚|지원센터|100%|보장|무조건|실행 기록|중앙값|비즈니스메이커|BUSINESS MAKER')
# 규격 4절 — 비용 구조 설명은 FAQ 비용 답·llms 에만. 블로그에는 두지 않는다.
FEE = re.compile(r'착수금|진행비|성과\s?보수|성공\s?보수|실행 전 비용|비용은 0원|비용 0원')

# 첫 언급 자동 내부링크 — 자금명은 시트(funds.source.csv)에서, 기관명은 대표 페이지로.
INSTITUTIONS = {
    '소상공인시장진흥공단': '/sojingong', '중소벤처기업진흥공단': '/jungjingong',
    '신용보증기금': '/sinbo', '기술보증기금': '/gibo', '지역신용보증재단': '/jaedan',
    '미소금융': '/microfinance-business',
}


def die(m):
    print(f"[블로그 빌드 실패] {m}")
    sys.exit(1)


def esc(s):
    return html.escape(str(s), quote=True)


# ── frontmatter ──────────────────────────────────────────────
def parse_value(v):
    v = v.strip()
    if v.startswith('"') and v.endswith('"') and len(v) >= 2:
        return v[1:-1].replace('\\"', '"').replace('\\\\', '\\')
    if v.startswith('[') and v.endswith(']'):
        return [x.strip().strip('"') for x in v[1:-1].split(',') if x.strip()]
    if v in ('true', 'false'):
        return v == 'true'
    return v


def read_post(path):
    m = re.fullmatch(r'(\d{4}-\d{2}-\d{2})-([a-z0-9-]+)\.md', path.name)
    if not m:
        die(f'{path.name}: 파일명은 YYYY-MM-DD-<영문 소문자·숫자·하이픈 slug>.md 여야 합니다.')
    text = path.read_text(encoding='utf-8').replace('\r\n', '\n')
    fm = re.match(r'---\n(.*?)\n---\n', text, re.S)
    if not fm:
        die(f'{path.name}: 맨 앞에 --- 로 감싼 frontmatter 가 없습니다.')
    meta = {}
    for line in fm.group(1).splitlines():
        if not line.strip():
            continue
        k, sep, v = line.partition(':')
        if not sep:
            die(f'{path.name}: frontmatter 줄 형식 오류 — {line!r}')
        meta[k.strip()] = parse_value(v)
    for k in REQUIRED:
        if not meta.get(k):
            die(f'{path.name}: frontmatter 에 {k} 가 없습니다.')
    for k in ('date', 'updated'):
        if k in meta and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', str(meta[k])):
            die(f'{path.name}: {k} 는 YYYY-MM-DD 여야 합니다 — {meta[k]!r}')
    if meta['date'] != m.group(1):
        die(f'{path.name}: 파일명 날짜({m.group(1)})와 date({meta["date"]})가 다릅니다.')
    meta.setdefault('updated', meta['date'])
    if meta['updated'] < meta['date']:
        die(f'{path.name}: updated 가 발행일보다 이릅니다.')
    if meta['category'] not in CATEGORIES:
        die(f'{path.name}: category 는 {"/".join(CATEGORIES)} 중 하나 — {meta["category"]!r}')
    meta['tags'] = meta.get('tags') or []
    meta['image'] = meta.get('image') or '/assets/og.png'
    meta['slug'] = m.group(2)
    meta['file'] = path.name
    meta['body'] = text[fm.end():].strip() + '\n'
    return meta


# ── markdown (이 저장소에 필요한 만큼만) ─────────────────────
LINK = re.compile(r'\[([^\]]+)\]\(([^)\s]+)\)')


def inline(s):
    out, pos = [], 0
    for m in LINK.finditer(s):
        out.append(_text(s[pos:m.start()]))
        href = m.group(2)
        ext = href.startswith('http')
        attrs = ' target="_blank" rel="noopener"' if ext else ''
        out.append(f'<a href="{esc(href)}"{attrs}>{_text(m.group(1))}</a>')
        pos = m.end()
    out.append(_text(s[pos:]))
    return ''.join(out)


def _text(s):
    s = esc(s).replace('&lt;br&gt;', '<br>')
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    return s.replace('\n', '<br>')


def plain(s):
    """JSON-LD·목록용 평문 — 링크는 글자만, 굵게 표시는 뺀다."""
    s = LINK.sub(r'\1', s).replace('**', '')
    return re.sub(r'\s+', ' ', s.replace('<br>', ' ')).strip()


def blocks(body):
    """빈 줄로 나눈 블록 [(kind, payload)]."""
    out = []
    for raw in re.split(r'\n\s*\n', body.strip()):
        lines = raw.strip('\n').split('\n')
        first = lines[0]
        if first.startswith('### '):
            out.append(('h3', first[4:].strip()))
            rest = '\n'.join(lines[1:]).strip()
            if rest:
                out.extend(blocks(rest))
        elif first.startswith('## '):
            out.append(('h2', first[3:].strip()))
            rest = '\n'.join(lines[1:]).strip()
            if rest:
                out.extend(blocks(rest))
        elif all(l.startswith('- ') for l in lines):
            out.append(('ul', [l[2:] for l in lines]))
        elif all(re.match(r'\d+\. ', l) for l in lines):
            out.append(('ol', [re.sub(r'^\d+\. ', '', l) for l in lines]))
        elif first.startswith('|'):
            rows = [[c.strip() for c in l.strip().strip('|').split('|')] for l in lines]
            if len(rows) < 2 or not all(re.fullmatch(r':?-+:?', c) for c in rows[1]):
                die(f'표 둘째 줄은 |---| 구분선이어야 합니다 — {first[:40]}')
            out.append(('table', (rows[0], rows[2:])))
        elif all(l.startswith('>') for l in lines):
            out.append(('quote', '\n'.join(l[1:].lstrip() for l in lines)))
        else:
            out.append(('p', '\n'.join(lines)))
    return out


def render(bl):
    h = []
    for kind, v in bl:
        if kind == 'h2':
            h.append(f'<h2 class="serif">{inline(v)}</h2>')
        elif kind == 'h3':
            h.append(f'<h3>{inline(v)}</h3>')
        elif kind == 'p':
            h.append(f'<p>{inline(v)}</p>')
        elif kind in ('ul', 'ol'):
            h.append(f'<{kind}>' + ''.join(f'<li>{inline(x)}</li>' for x in v) + f'</{kind}>')
        elif kind == 'quote':
            h.append(f'<blockquote>{inline(v)}</blockquote>')
        elif kind == 'table':
            head, rows = v
            h.append('<div class="tablewrap"><table><thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head)
                     + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>'
                                                        for r in rows) + '</tbody></table></div>')
    return '\n'.join(h)


def split_post(post):
    """(직답, 본문 블록, FAQ [(q, [블록])]). FAQ 절은 본문에서 떼어 따로 그린다."""
    bl = blocks(post['body'])
    if not bl or bl[0][0] != 'p':
        die(f"{post['file']}: 첫 블록은 직답 문단이어야 합니다(규격 — 첫 문단 직답).")
    answer, rest = bl[0][1], bl[1:]
    body, faq, i = [], [], 0
    while i < len(rest):
        kind, v = rest[i]
        if kind == 'h2' and v == '자주 묻는 질문':
            i += 1
            while i < len(rest) and rest[i][0] != 'h2':
                if rest[i][0] != 'h3':
                    die(f"{post['file']}: '자주 묻는 질문' 아래에는 ### 질문과 답 문단만 둡니다.")
                q, ans = rest[i][1], []
                i += 1
                while i < len(rest) and rest[i][0] not in ('h2', 'h3'):
                    ans.append(rest[i])
                    i += 1
                if not ans:
                    die(f"{post['file']}: FAQ '{q}' 에 답이 없습니다.")
                faq.append((q, ans))
            continue
        body.append(rest[i])
        i += 1
    return answer, body, faq


def faq_text(ans):
    parts = []
    for kind, v in ans:
        if kind in ('ul', 'ol'):
            parts.extend(plain(x) for x in v)
        elif kind == 'table':
            parts.extend(' '.join(plain(c) for c in r) for r in [v[0]] + v[1])
        else:
            parts.append(plain(v))
    return ' '.join(parts)


# ── 자동 내부링크 ──────────────────────────────────────────
def link_terms():
    terms = dict(INSTITUTIONS)
    with (ROOT / 'data/funds.source.csv').open(encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            if (r.get('사이트 공개') or '').strip().upper() == 'Y' and '(' not in r['자금명']:
                terms[r['자금명'].strip()] = '/' + r['자금ID'].strip()
    for t, href in terms.items():
        if not (ROOT / (href.lstrip('/') + '.html')).exists():
            die(f'자동 링크 대상 페이지가 없습니다: {t} → {href}')
    return sorted(terms.items(), key=lambda kv: -len(kv[0]))


TOKEN = re.compile(r'(<a\b.*?</a>|<h[1-6]\b.*?</h[1-6]>|<summary\b.*?</summary>|<th\b.*?</th>|<[^>]+>)', re.S)


def autolink(page_html, terms, already):
    """본문 텍스트에서 각 용어의 첫 언급 한 번만 링크한다. 링크·제목·표 머리·FAQ 질문 안은 건드리지 않는다.
    이미 같은 주소로 가는 링크가 글에 있으면 그 용어는 건너뛴다."""
    done = set(already)
    parts = TOKEN.split(page_html)
    for i in range(0, len(parts), 2):          # 짝수 = 태그 밖 텍스트
        text, out = parts[i], []
        while True:
            hits = [(text.find(t), -len(t), t, h) for t, h in terms if h not in done and t in text]
            if not hits:
                break
            pos, _, term, href = min(hits)
            out.append(text[:pos] + f'<a href="{href}">{term}</a>')
            done.add(href)
            text = text[pos + len(term):]
        parts[i] = ''.join(out) + text
    return ''.join(parts)


# ── 공통 셸 ─────────────────────────────────────────────────
def shell_parts():
    style = re.search(r'<style>.*?</style>', (ROOT / 'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    src = (ROOT / 'jaedan.html').read_text(encoding='utf-8')
    hdr = re.search(r'<header>.*?</header>', src, re.S).group(0)
    foot = re.search(r'<footer>.*?</footer>', src, re.S).group(0)
    foot = re.sub(r'<p class="lastmod"[^>]*>.*?</p>', '', foot, flags=re.S)   # build_lastmod 가 다시 넣는다
    return style, hdr, foot


EXTRA_CSS = ('<style>'
             '.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}'
             'table{border-collapse:collapse;width:100%;min-width:520px;font-size:.92rem}'
             'th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;font-weight:600}'
             'td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}'
             'tr:nth-child(even) td{background:#FAFBFD}'
             '.hero .hub-label{color:#C6D0E4;font-size:.86rem;font-weight:700;margin:0 0 10px}'
             '.hero .hub-lead{margin:16px 0 0;color:#C6D0E4;font-size:1rem;line-height:1.75;max-width:680px}'
             '.hero .post-meta{margin:12px 0 0;color:#AEB9CC;font-size:.86rem}'
             '.hero .btn-hub-cta{display:inline-flex;align-items:center;justify-content:center;margin-top:24px;'
             'background:var(--blue-deep);color:#fff;border:1px solid var(--blue-deep);border-radius:4px;'
             'padding:15px 26px;font-weight:700;font-size:1rem;min-height:52px;text-decoration:none}'
             'main .post{max-width:780px;padding-top:28px}'
             'main .post .answer{margin:0 0 22px;padding:18px 20px;background:var(--paper);'
             'border-left:3px solid var(--navy);font-size:1.02rem;line-height:1.8;color:var(--ink)}'
             'main .post h2{margin:38px 0 12px}main .post h3{margin:24px 0 8px;font-size:1.08rem;color:var(--navy)}'
             'main .post p,main .post li{line-height:1.85;color:#2E3748}main .post li{margin:0 0 8px}'
             'main .post blockquote{margin:18px 0;padding:14px 18px;border-left:3px solid var(--line);'
             'background:#FAFBFD;color:#3A4356}'
             'main .post .disclaimer{margin:26px 0 0;font-size:.88rem;color:#4a5669;line-height:1.7}'
             'main .post .byline{margin-top:14px;font-size:.8rem;opacity:.7}'
             '.post-list{list-style:none;margin:0;padding:0}'
             '.post-list li{padding:18px 0;border-top:1px solid var(--line)}'
             '.post-list a.t{font-weight:700;color:var(--navy);text-decoration:none;font-size:1.06rem}'
             '.post-list .m{display:block;margin:0 0 4px;font-size:.82rem;color:#6B7486}'
             '.post-list p{margin:6px 0 0;color:#3A4356;font-size:.94rem;line-height:1.7}'
             '.cats a,.related a{display:inline-block;margin:0 8px 8px 0;padding:8px 13px;border:1px solid var(--line);'
             'border-radius:999px;color:var(--ink);text-decoration:none;font-size:.88rem}'
             '.cats a[aria-current]{background:var(--navy);color:#fff;border-color:var(--navy)}'
             '@media(max-width:680px){.hero .btn-hub-cta{width:100%}}' + FORM_CSS + '</style>')


def head(title, desc, url, og_type, lds, style):
    full = f'{title} | {BRAND}'
    ld = ''.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>\n' for x in lds)
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="canonical" href="{url}">
<title>{esc(full)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:title" content="{esc(full)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/assets/og.png">
<link rel="icon" type="image/png" href="/assets/icon-192.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="{BRAND} 블로그" href="{SITE}/blog/feed.xml">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap">
{ld}{style}
{EXTRA_CSS}
</head>
<body data-service="policy">
'''


def crumb_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}


def hero(crumb_html, label, h1, lead, meta=''):
    return f'''<section class="hero"><div class="wrap">
  <p class="crumb">{crumb_html}</p>
  <p class="hub-label">{esc(label)}</p>
  <h1 class="serif">{esc(h1)}</h1>
  <p class="hub-lead">{esc(lead)}</p>{meta}
  <a class="btn btn-hub-cta" id="heroCta" href="#apply" data-cta-location="hero" data-consultation-service="policy">무료 진단 신청</a>
</div></section>
'''


def tail(path, label, foot):
    return f'''<section class="block"><div class="wrap">
{form_html(path, label, title=TITLE_GENERAL)}</div></section>
</main>
{foot}
<script src="/assets/conversion.js" defer></script>
</body>
</html>
'''


def ym(d):
    return f'{int(d[:4])}년 {int(d[5:7])}월'


def post_list(posts):
    return '<ul class="post-list">' + ''.join(
        f'<li><span class="m">{p["date"]} · {esc(CATEGORIES[p["category"]][0])}</span>'
        f'<a class="t" href="/blog/{p["slug"]}">{esc(p["title"])}</a><p>{esc(p["summary"])}</p></li>'
        for p in posts) + '</ul>'


def cats_nav(cats, current=None):
    return '<p class="cats">' + f'<a href="/blog"{" aria-current=\"page\"" if current is None else ""}>전체</a>' + ''.join(
        f'<a href="/blog/category/{c}"{" aria-current=\"page\"" if c == current else ""}>{esc(CATEGORIES[c][0])}</a>'
        for c in cats) + '</p>'


# ── 검사 ─────────────────────────────────────────────────────
def page_titles():
    """기존 페이지의 title 앞부분(브랜드 제외) — 블로그 제목이 같으면 카니발."""
    out = {}
    for p in list(ROOT.glob('*.html')) + list(ROOT.glob('industry/*.html')) + list(ROOT.glob('region/*.html')):
        if p.name == 'blog.html':
            continue
        m = re.search(r'<title>(.*?)</title>', p.read_text(encoding='utf-8'), re.S)
        if m:
            out[html.unescape(m.group(1)).split(' | ')[0].strip()] = p.name
    return out


def fund_names():
    with (ROOT / 'data/funds.source.csv').open(encoding='utf-8-sig', newline='') as f:
        names = {re.sub(r'\(.*?\)', '', r['자금명']).strip() for r in csv.DictReader(f)}
    return sorted(n for n in names if n)


def check(posts):
    funds, titles = fund_names(), page_titles()
    for p in posts:
        text = ' '.join([p['title'], p['summary'], p['body']])
        for pat, why in ((BANNED, '금칙어(규격 1절)'), (FEE, '비용 구조 문구(규격 4절 — FAQ·llms 에만)')):
            m = pat.search(text)
            if m:
                die(f"{p['file']}: {why} '{m.group(0)}' — 문장을 고쳐 주세요.")
        for n in funds:
            if p['title'].replace(' ', '').startswith(n.replace(' ', '')):
                die(f"{p['file']}: 제목이 자금 정식명 '{n}' 으로 시작합니다 — 자금 페이지 검색어를 다시 노리지 않도록 "
                    f"상황·절차·사례 관점으로 제목을 바꿔 주세요.")
        if p['title'] in titles:
            die(f"{p['file']}: 제목이 기존 페이지 {titles[p['title']]} 의 title 과 같습니다.")
    seen = {}
    for p in posts:
        if p['slug'] in seen:
            die(f"slug '{p['slug']}' 가 {seen[p['slug']]} 와 {p['file']} 에 중복됩니다.")
        seen[p['slug']] = p['file']
        if (ROOT / f"{p['slug']}.html").exists() and p['slug'] == 'blog':
            die('slug 로 blog 는 쓸 수 없습니다.')
        if p['slug'] == 'category' or p['slug'] == 'feed':
            die(f"slug '{p['slug']}' 는 예약어입니다.")


# ── 빌드 ─────────────────────────────────────────────────────
def build_post(p, posts, terms, style, hdr, foot):
    url = f"{SITE}/blog/{p['slug']}"
    cat_label = CATEGORIES[p['category']][0]
    answer, body, faq = split_post(p)
    article = f'<p class="answer">{inline(answer)}</p>\n' + render(body)
    faq_html = ''
    if faq:
        faq_html = '<h2 class="serif">자주 묻는 질문</h2>\n' + ''.join(
            f'<details><summary>{esc(q)}</summary><div class="body">{render(a)}</div></details>' for q, a in faq)
    already = set(re.findall(r'href="(/[a-z0-9-]+)"', article + faq_html))
    linked = autolink(article + '\n<!--faq-->\n' + faq_html, terms, already)
    article, faq_html = linked.split('\n<!--faq-->\n', 1)
    related = [x for x in posts if x is not p and x['category'] == p['category']][:4]
    related_html = ''.join(f'<a href="/blog/{x["slug"]}">{esc(x["title"])}</a>' for x in related)
    related_html += f'<a href="/blog/category/{p["category"]}">{esc(cat_label)} 전체</a><a href="/blog">블로그 전체</a>'

    lds = [{"@context": "https://schema.org", "@type": "BlogPosting", "headline": p['title'],
            "description": p['summary'], "inLanguage": "ko", "mainEntityOfPage": url, "url": url,
            "image": SITE + p['image'], "datePublished": p['date'], "dateModified": p['updated'],
            "articleSection": cat_label, "keywords": p['tags'],
            "author": {"@type": "Organization", "@id": f"{SITE}/#org", "name": BRAND, "url": SITE + "/"},
            "publisher": {"@type": "Organization", "@id": f"{SITE}/#org", "name": BRAND,
                          "logo": {"@type": "ImageObject", "url": f"{SITE}/assets/logo.png"}}},
           crumb_ld([('홈', SITE + '/'), ('블로그', SITE + '/blog'),
                     (cat_label, f"{SITE}/blog/category/{p['category']}"), (p['title'], url)])]
    if faq:
        lds.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": faq_text(a)}}
            for q, a in faq]})

    crumb = (f'<a href="/">홈</a> › <a href="/blog">블로그</a> › '
             f'<a href="/blog/category/{p["category"]}">{esc(cat_label)}</a>')
    meta = f'\n  <p class="post-meta">발행 {p["date"]} · 내용 확인 {p["updated"]}</p>'
    page = head(p['title'], p['summary'], url, 'article', lds, style) + hdr + '\n<main>\n'
    page += hero(crumb, cat_label, p['title'], p['summary'], meta)
    page += f'''<section class="block"><div class="wrap post">
<article>
{article}
{faq_html}
<p class="asof">※ 본 안내는 {ym(p["updated"])} 기준이며, 조건·일정은 각 기관의 최신 공고를 기준으로 확인해야 합니다.</p>
<p class="disclaimer">이 글은 일반 정보이며 특정 기업의 신청 자격이나 승인 여부를 판단하지 않습니다. 승인·금리·한도는 각 기관의 심사로 정해집니다. {BRAND}는 민간 컨설팅 회사이며 정부기관·금융기관이 아닙니다.</p>
<p class="byline">작성 {BRAND} · 검토 김상표(대표) · 최종 확인 {p["updated"][:7]}</p>
</article>
</div></section>
<section class="block"><div class="wrap">
  <h2 class="serif">함께 보면 좋은 글</h2>
  <p class="related">{related_html}</p>
</div></section>
'''
    page += tail(f"/blog/{p['slug']}", p['title'], foot)
    return page


def build_index(posts, cats, style, hdr, foot, category=None):
    if category:
        label, lead = CATEGORIES[category]
        url, path = f'{SITE}/blog/category/{category}', f'/blog/category/{category}'
        title = f'{label} — 정책자금 실무 블로그'
        mine = [p for p in posts if p['category'] == category]
        crumb = f'<a href="/">홈</a> › <a href="/blog">블로그</a> › {esc(label)}'
        items = [('홈', SITE + '/'), ('블로그', SITE + '/blog'), (label, url)]
        desc = f'{BRAND} 블로그의 {label} 글 {len(mine)}편. {lead}.'
    else:
        url, path = f'{SITE}/blog', '/blog'
        title, label = '정책자금 실무 블로그', '블로그'
        lead = '자금 신청 전 자료 정리, 지원정보 찾는 법, 공고·제도 소식을 정리합니다. 자금별 조건은 각 자금 페이지에서 안내합니다.'
        mine = posts
        crumb = '<a href="/">홈</a> › 블로그'
        items = [('홈', SITE + '/'), ('블로그', url)]
        desc = f'{BRAND} 블로그 — {lead}'
    asof = max(p['updated'] for p in mine)
    lds = [crumb_ld(items),
           {"@context": "https://schema.org", "@type": "Blog" if not category else "CollectionPage",
            "name": f'{BRAND} {title}', "url": url, "inLanguage": "ko",
            "publisher": {"@type": "Organization", "@id": f"{SITE}/#org", "name": BRAND},
            ("blogPost" if not category else "hasPart"): [
                {"@type": "BlogPosting", "headline": p['title'], "url": f"{SITE}/blog/{p['slug']}",
                 "datePublished": p['date']} for p in mine]}]
    page = head(title, desc, url, 'website', lds, style) + hdr + '\n<main>\n'
    page += hero(crumb, label if category else '블로그', title, lead)
    page += f'''<section class="block"><div class="wrap">
  {cats_nav(cats, category)}
  {post_list(mine)}
  <p class="asof">※ 글마다 내용 확인일이 다릅니다. 목록 기준일 {ym(asof)} · 기간이 지난 공고 글은 참고용입니다.</p>
</div></section>
'''
    page += tail(path, title, foot)
    return page


def rss(posts):
    def when(d):
        return format_datetime(datetime.fromisoformat(d).replace(tzinfo=KST))
    items = ''.join(
        f'<item><title>{esc(p["title"])}</title><link>{SITE}/blog/{p["slug"]}</link>'
        f'<guid isPermaLink="true">{SITE}/blog/{p["slug"]}</guid><pubDate>{when(p["date"])}</pubDate>'
        f'<category>{esc(CATEGORIES[p["category"]][0])}</category><description>{esc(p["summary"])}</description></item>\n'
        for p in posts)
    last = max(p['updated'] for p in posts)
    return (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
            f'<channel><title>{BRAND} 블로그</title><link>{SITE}/blog</link>'
            f'<atom:link href="{SITE}/blog/feed.xml" rel="self" type="application/rss+xml"/>'
            f'<description>정책자금 실무 가이드·지원정보·공고 소식</description><language>ko</language>'
            f'<lastBuildDate>{when(last)}</lastBuildDate>\n{items}</channel>\n</rss>\n')


def update_sitemap(urls):
    path = ROOT / 'sitemap.xml'
    sm = path.read_text(encoding='utf-8')
    keep = set(urls)
    # 내린 글(draft·삭제)의 항목은 뺀다 — 블로그 항목은 이 빌더 소유다
    sm = re.sub(r'[ \t]*<url><loc>(https://bmaker\.kr/blog(?:/[^<]*)?)</loc>.*?</url>\n?',
                lambda m: m.group(0) if m.group(1) in keep else '', sm, flags=re.S)
    for u in urls:
        if f'<loc>{u}</loc>' not in sm:
            pri = '0.7' if u.rstrip('/').endswith('/blog') else '0.6'
            sm = sm.replace('</urlset>', f'  <url><loc>{u}</loc><changefreq>monthly</changefreq>'
                                         f'<priority>{pri}</priority></url>\n</urlset>')
    path.write_text(sm, encoding='utf-8')


def update_llms(posts):
    start, end = '<!-- blog:start -->', '<!-- blog:end -->'
    lines = '\n'.join(f'- [{p["title"]}]({SITE}/blog/{p["slug"]}): {p["summary"]}' for p in posts)
    block = (f'{start}\n## 블로그 ({SITE}/blog)\n자금별 조건은 각 자금 페이지가 대표이고, 블로그는 신청 전 실무·지원정보 찾기·'
             f'공고 소식을 다룹니다. 글마다 내용 확인일이 있으며 기간이 지난 공고 글은 참고용입니다.\n{lines}\n{end}')
    for name in ('llms.txt', 'llms-full.txt'):
        path = ROOT / name
        s = path.read_text(encoding='utf-8')
        s = re.sub(re.escape(start) + r'.*?' + re.escape(end) + r'\n*', '', s, flags=re.S).rstrip() + '\n'
        # 자리 고정: build_editorial 이 preparation-guides 블록을 매번 맨 끝으로 옮기므로 그 바로 앞에 둔다.
        # (맨 끝에 붙이면 두 빌더가 번갈아 순서를 뒤집어 체인 2회 churn 이 생긴다)
        anchor = '<!-- preparation-guides:start -->'
        if anchor in s:
            s = s.replace(anchor, block + '\n\n' + anchor, 1)
        else:
            s = s + '\n' + block + '\n'
        path.write_text(s, encoding='utf-8')


def update_guide_hub(posts):
    """사업 가이드 허브에 최신 글 블록 — 블로그가 내부 링크 없는 고아 페이지가 되지 않게."""
    start, end = '<!-- blog-latest:start -->', '<!-- blog-latest:end -->'
    path = ROOT / 'business-guide.html'
    s = path.read_text(encoding='utf-8')
    s = re.sub(re.escape(start) + r'.*?' + re.escape(end), '', s, flags=re.S)
    latest = sorted(posts, key=lambda p: (p['date'], p['slug']), reverse=True)[:6]
    cells = ''.join(f'<a href="/blog/{p["slug"]}">{esc(p["title"])}<span>읽기 →</span></a>' for p in latest)
    block = (f'{start}<section class="editorial-links"><div class="wrap"><h2>블로그 최신 글</h2>'
             f'<div class="editorial-grid">{cells}<a href="/blog">블로그 전체 보기<span>목록 →</span></a></div></div></section>{end}')
    if '</main>' not in s:
        die('business-guide.html 에 </main> 이 없습니다.')
    path.write_text(s.replace('</main>', block + '</main>', 1), encoding='utf-8')


def main():
    files = sorted(POSTS.glob('*.md'))
    if not files:
        die('posts/*.md 가 없습니다.')
    posts = [read_post(f) for f in files]
    posts = [p for p in posts if not p.get('draft')]
    posts.sort(key=lambda p: (p['date'], p['slug']), reverse=True)
    check(posts)
    style, hdr, foot = shell_parts()
    terms = link_terms()
    cats = [c for c in CATEGORIES if any(p['category'] == c for p in posts)]

    made = {}
    for p in posts:
        made[f"blog/{p['slug']}.html"] = build_post(p, posts, terms, style, hdr, foot)
    made['blog.html'] = build_index(posts, cats, style, hdr, foot)
    for c in cats:
        made[f'blog/category/{c}.html'] = build_index(posts, cats, style, hdr, foot, category=c)

    (OUT / 'category').mkdir(parents=True, exist_ok=True)
    for old in list(OUT.glob('*.html')) + list((OUT / 'category').glob('*.html')):   # 내린 글 정리
        if old.relative_to(ROOT).as_posix() not in made:
            old.unlink()
    for rel, page in made.items():
        # 헤더·푸터를 루트 페이지(jaedan)에서 복사해 오므로 assets/ 상대 경로를 루트 절대 경로로(허브 빌더와 같은 처리).
        # /blog/<slug> 에서는 상대 경로가 /blog/assets/… 로 풀려 로고가 깨진다.
        page = re.sub(r'(href|src)="assets/', r'="/assets/', page)
        target = ROOT / rel
        # build_lastmod 가 넣은 스탬프는 다음 실행에서 다시 붙는다. 내용이 같으면 쓰지 않아 churn 을 막는다
        if target.exists():
            cur = re.sub(r'<p class="lastmod"[^>]*>.*?</p>', '', target.read_text(encoding='utf-8'), flags=re.S)
            cur = re.sub(r'<script type="application/ld\+json" data-webpage>.*?</script>', '', cur, flags=re.S)
            cur = re.sub(r'"dateModified": "\d{4}-\d{2}-\d{2}"', '"dateModified": "-"', cur)
            cur = re.sub(r'((?:src|href)="/assets/[\w./-]+\.(?:js|css))\?v=[0-9a-f]+"', r'\1"', cur)
            new = re.sub(r'"dateModified": "\d{4}-\d{2}-\d{2}"', '"dateModified": "-"', page)
            if cur == new:
                continue
        target.write_text(page, encoding='utf-8')
    (OUT / 'feed.xml').write_text(rss(posts), encoding='utf-8')

    urls = [f'{SITE}/blog'] + [f'{SITE}/blog/category/{c}' for c in cats] + [f"{SITE}/blog/{p['slug']}" for p in posts]
    update_sitemap(urls)
    update_llms(posts)
    update_guide_hub(posts)
    print(f"[블로그 빌드 OK] 글 {len(posts)}편 · 카테고리 {len(cats)}개({', '.join(cats)}) · feed·sitemap·llms 블록 갱신")


if __name__ == '__main__':
    main()
