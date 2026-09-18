#!/usr/bin/env python3
"""업종별 정책자금 — 홈 6타일(<!-- home-industry -->)과 /industry/<slug> 의도 랜딩을 받은 사례 원장에서 생성한다.

build_cases.py 가 원장 빌드 끝에서 build(rows) 를 호출한다(8빌더 체인 순서 유지, 별도 실행 불필요).
업종 열은 자유 기재라 아래 규칙(위에서부터 첫 매칭)으로 6개 업종에 묶고, 어디에도 안 맞는 건은 타일에 넣지 않는다.
랜딩은 landing=True 인 업종만 생성한다(2026-09 시안: 음식점·카페). 나머지 타일은 받은 사례 원장으로 연결.
"""
import json, re, statistics, datetime
from builddate import build_date, data_date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TODAY = build_date()   # BUILD_DATE 있으면 그 날짜, 없으면 Asia/Seoul 오늘 (tools/builddate.py)
ASOF = data_date('data/cases.source.csv')  # 페이지에 적는 기준일 = 원장이 바뀐 날

INDUSTRIES = [
    # slug, 타일 이름, 검색 질문(h1·title), 랜딩 생성 여부, 업종 열 키워드
    dict(slug='online-shoppingmall', name='온라인쇼핑몰', question='온라인쇼핑몰 정책자금, 받을 수 있나요?', landing=False, keys=('이커머스', '온라인 도소매', '쇼핑몰', '스마트스토어')),
    dict(slug='eumsikjeom', name='음식점·카페', question='음식점·카페 정책자금, 받을 수 있나요?', landing=True, place='가게', keys=('음식', '카페', '베이커리', '요식', '식당', '주점')),
    dict(slug='geonseol', name='건설·인테리어', question='건설·인테리어 정책자금, 받을 수 있나요?', landing=False, keys=('건설', '인테리어')),
    dict(slug='miyong', name='미용·서비스', question='미용·서비스업 정책자금, 받을 수 있나요?', landing=False, keys=('뷰티', '미용', '헤어', '네일', '피부'), exact=('서비스업',)),
    dict(slug='dosomae', name='도소매·유통', question='도소매·유통 정책자금, 받을 수 있나요?', landing=False, keys=('도소매', '소매', '유통')),
    dict(slug='jejo', name='제조업', question='제조업 정책자금, 받을 수 있나요?', landing=False, keys=('제조', '가공', '설비', '장비')),
]
TILE_ORDER = ['eumsikjeom', 'jejo', 'dosomae', 'online-shoppingmall', 'miyong', 'geonseol']
BY_SLUG = {i['slug']: i for i in INDUSTRIES}
ANSWER_MAX = 40  # 첫 문단 직답 글자 수 상한

FEE = '착수금·진행비 등 실행 전 비용은 일절 받지 않고, 자금이 실제 실행된 경우에만 성공보수를 받습니다.'
TBL = ('<style>.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}table{border-collapse:collapse;width:100%;min-width:560px;font-size:.88rem}'
       'th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}'
       'tr:nth-child(even) td{background:#FAFBFD}td a{color:var(--blue-deep);text-decoration:underline}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}'
       '.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px 18px}.card b{display:block;font-size:1.4rem;color:var(--navy);margin-bottom:4px}.card span{font-size:.82rem;color:var(--ink-soft)}'
       '.hero .answer{font-size:1.15rem;font-weight:700;color:#fff;margin-top:14px}.cta-one{margin-top:28px}.cta-one .btn{background:#FEE500;color:#191600;font-weight:800}</style>')


def classify(label):
    """업종 열 값 → 업종 slug (없으면 None)."""
    s = (label or '').strip()
    if not s:
        return None
    for ind in INDUSTRIES:
        if s in ind.get('exact', ()) or any(k in s for k in ind['keys']):
            return ind['slug']
    return None


def won2(m):
    e, man = divmod(int(m), 10000)
    return ((f"{e}억" + ((" " if man else "") + f"{man:,}만" if man else "")) + "원") if e else f"{man:,}만원"


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def answer_of(ind, rows):
    total = sum(r['amt'] for r in rows)
    money = f"{total // 10000}억" if total >= 10000 else won2(total)
    return f"네. {ind['name']} 사장님 {len(rows)}분이 정책자금 {money}을 받았습니다."


def _abs_assets(html):
    return re.sub(r'(href|src)="assets/', r'\1="/assets/', html)


def landing_html(ind, rows, all_n, period):
    url = f"https://bmaker.kr/industry/{ind['slug']}"
    rows = sorted(rows, key=lambda r: (r['실행 연월'], r['사례ID']), reverse=True)
    amts = [r['amt'] for r in rows]
    days = [int(float(r['소요일'])) for r in rows if r['소요일']]
    n, total = len(rows), sum(amts)
    med = won2(int(statistics.median(amts)))
    dmed = f"보통 {int(statistics.median(days))}일" if days else '—'
    answer = answer_of(ind, rows)
    if len(answer) > ANSWER_MAX:
        raise SystemExit(f"[업종 랜딩 빌드 실패] {ind['slug']} 첫 문단 직답이 {len(answer)}자 — {ANSWER_MAX}자 이하여야 합니다: {answer}")
    style = re.search(r'<style>.*?</style>', (ROOT / 'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    src = (ROOT / 'jaedan.html').read_text(encoding='utf-8')
    hdr = _abs_assets(re.search(r'<header>.*?</header>', src, re.S).group(0))
    foot = _abs_assets(re.search(r'<footer>.*?</footer>', src, re.S).group(0))
    trs = ''.join(
        f'<tr><td>{r["실행 연월"]}</td><td>{esc(r["지역(시도)"])}</td><td>{esc(r["업종"])}</td><td>{esc(r["기관"])}</td>'
        f'<td>{esc(r["자금명"])}</td><td style="white-space:nowrap">{won2(r["amt"])}</td><td>{esc(r["금리"]) or "—"}</td>'
        f'<td><a href="/cases#row-{esc(r["사례ID"])}">기록</a></td></tr>' for r in rows)
    title = ind['question']
    crumb = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "홈", "item": "https://bmaker.kr/"},
        {"@type": "ListItem", "position": 2, "name": "업종별 정책자금", "item": "https://bmaker.kr/#industry"},
        {"@type": "ListItem", "position": 3, "name": ind['name'], "item": url}]}, ensure_ascii=False)
    art = json.dumps({"@context": "https://schema.org", "@type": "Article", "headline": title, "description": answer,
                      "dateModified": str(ASOF), "inLanguage": "ko",
                      "author": {"@type": "Organization", "@id": "https://bmaker.kr/#org", "name": "비즈니스 메이커"},
                      "publisher": {"@type": "Organization", "@id": "https://bmaker.kr/#org", "name": "비즈니스 메이커"},
                      "mainEntityOfPage": url, "isBasedOn": "https://bmaker.kr/data/cases.csv"}, ensure_ascii=False)
    desc = f"{answer} 받은 사례 원장({period})에서 업종이 {ind['name']}인 {n}건을 기관·자금·금액·금리까지 표로 공개합니다."
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — 받은 사례 {n}건 | 비즈니스 메이커</title>
<meta name="description" content="{desc}">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{answer}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://bmaker.kr/assets/og.png">
<meta property="og:locale" content="ko_KR">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/png" href="/assets/icon-192.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap">
<script type="application/ld+json">{art}</script>
<script type="application/ld+json">{crumb}</script>
{style}
{TBL}
</head>
<body>
{hdr}
<section class="hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> › <a href="/#industry">업종별 정책자금</a> › {ind['name']}</p>
    <h1 class="serif">{title}</h1>
    <p class="answer">{answer}</p>
  </div>
</section>
<main>
  <div class="wrap">
    <p>받은 사례 원장({period})에서 업종이 {ind['name']}인 건만 자동으로 모았습니다.</p>
    <div class="cards">
      <div class="card"><b>{n}건</b><span>{ind['name']} 받은 사례 (전체 {all_n}건 중)</span></div>
      <div class="card"><b>{won2(total)}</b><span>받은 금액 합계</span></div>
      <div class="card"><b>{med}</b><span>건당 중앙값</span></div>
      <div class="card"><b>{dmed}</b><span>첫 상담 → 정산</span></div>
    </div>

    <h2>{ind['name']} 받은 사례 {n}건</h2>
    <div class="tablewrap"><table><thead><tr><th>실행</th><th>지역</th><th>업종</th><th>기관</th><th>자금</th><th>금액</th><th>금리</th><th>근거</th></tr></thead><tbody><!-- industry-cases:start -->{trs}<!-- industry-cases:end --></tbody></table></div>
    <p class="asof">기준일 {ASOF.year}년 {ASOF.month}월 {ASOF.day}일 · 금리는 각 실행 시점 기준 · 전체 기록과 증빙은 <a href="/cases">받은 사례</a>에서 확인하세요.</p>

    <div class="callout"><p>정책자금은 대출이며 상환 의무가 있습니다. 승인 여부와 조건은 각 심사 기관이 결정하고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. {FEE}</p></div>

    <div class="cta-box">
      <h3 class="serif">우리 {ind.get('place', '회사')}도 되는지</h3>
      <p>무료로 먼저 봐드립니다.</p>
      <div class="cta-one"><a class="btn" href="/#apply" data-cta-location="industry">무료 진단 예약하기 →</a></div>
    </div>
  </div>
</main>
{foot}
<script src="/assets/conversion.js" defer></script>
</body>
</html>
'''


def tiles_html(groups):
    out = []
    for slug in TILE_ORDER:
        ind, rows = BY_SLUG[slug], groups.get(slug, [])
        href = f"/industry/{slug}" if ind['landing'] else "/cases"
        more = '받은 사례 보기 →' if ind['landing'] else '원장에서 보기 →'
        out.append(f'<a class="ind-tile" href="{href}"><b>{ind["name"]}</b><span>받은 사례 {len(rows)}건</span><em>{more}</em></a>')
    return ''.join(out)


def build(rows, period):
    groups = {}
    for r in rows:
        slug = classify(r['업종'])
        if slug:
            groups.setdefault(slug, []).append(r)
    ip = ROOT / 'index.html'
    ih = ip.read_text(encoding='utf-8')
    if '<!-- home-industry:start -->' in ih:
        ih = re.sub(r'<!-- home-industry:start -->.*?<!-- home-industry:end -->',
                    lambda m: '<!-- home-industry:start -->' + tiles_html(groups) + '<!-- home-industry:end -->', ih, flags=re.S)
        ip.write_text(ih, encoding='utf-8')
    sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    lt = (ROOT / 'llms.txt').read_text(encoding='utf-8')
    for ind in INDUSTRIES:
        if not ind['landing']:
            continue
        rows_i = groups.get(ind['slug'], [])
        if not rows_i:
            raise SystemExit(f"[업종 랜딩 빌드 실패] {ind['slug']} 에 해당하는 받은 사례가 없습니다.")
        page = landing_html(ind, rows_i, len(rows), period)
        if '갚' in page:
            raise SystemExit("[업종 랜딩 빌드 실패] 생성물에 '갚' 포함")
        out = ROOT / 'industry' / f"{ind['slug']}.html"
        out.parent.mkdir(exist_ok=True)
        out.write_text(page, encoding='utf-8')
        loc = f"https://bmaker.kr/industry/{ind['slug']}"
        if loc + '</loc>' in sm:
            sm = re.sub(r'(<loc>' + re.escape(loc) + r'</loc><lastmod>)[^<]+', r'\g<1>' + str(TODAY), sm)
        else:
            sm = sm.replace('</urlset>', f'  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>\n</urlset>')
        total = sum(r['amt'] for r in rows_i)
        line = f"- [{ind['question']}]({loc}): 받은 사례 원장에서 업종 필터 — {ind['name']} {len(rows_i)}건, 총 {won2(total)}. 기관·자금·금액·금리 표"
        if f"- [{ind['question']}]" in lt:
            lt = re.sub(r'- \[' + re.escape(ind['question']) + r'\][^\n]*', lambda m: line, lt)
        else:
            lt = lt.replace('- [정책자금 접수 일정]', line + '\n- [정책자금 접수 일정]')
    (ROOT / 'sitemap.xml').write_text(sm, encoding='utf-8')
    (ROOT / 'llms.txt').write_text(lt, encoding='utf-8')
    counts = ' · '.join(f"{BY_SLUG[s]['name']} {len(groups.get(s, []))}" for s in TILE_ORDER)
    print(f"[업종 빌드 OK] {counts} (미분류 {len(rows) - sum(len(v) for v in groups.values())}건)")
