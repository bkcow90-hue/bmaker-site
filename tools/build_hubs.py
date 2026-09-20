#!/usr/bin/env python3
"""정책자금 컨설팅 허브 2장 빌드 — /sosangin(소상공인) · /jungsogieop(중소기업).

기관 기준 분류는 build_cases.hub_of()·inst_bucket() 하나만 쓴다(소진공·지역신보·지자체=소상공인 /
중진공·신보·기보·무역보증=중소기업). 건수·건당 평균·금리 범위는 전부 원장에서 집계하고,
집계에 포함된 건이 없는 경로는 숫자를 '—' 로 둔다(취급 사실과 집계 없음을 둘 다 표시).

화면 FAQ 와 FAQPage JSON-LD 는 같은 목록에서 생성해 항상 100% 일치한다(규격 3절).
날짜는 tools/builddate 의 build_date()·data_date() 만 쓴다 — 자체 계산 금지.
폼은 홈(index.html)의 신청 섹션을 그대로 가져와 한 곳에서 관리한다.

실행: python tools/build_hubs.py   (빌더 체인에서 build_lastmod.py 앞)
"""
import csv, json, re, sys
from pathlib import Path

from builddate import build_date, data_date          # noqa: F401  (build_date 는 규칙상 노출)
from build_cases import hub_of, inst_bucket, won2

ROOT = Path(__file__).resolve().parent.parent
SRC = 'data/cases.source.csv'
ASOF = data_date(SRC)


def die(m):
    print(f"[허브 빌드 실패] {m}")
    sys.exit(1)


def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


HUBS = {
    'sosangin': {
        'hub': '소상공인',
        'name': '소상공인 정책자금 컨설팅',
        'title': '소상공인 정책자금 컨설팅 | 소진공·지역신보·지자체 | 비즈니스 메이커',
        'desc_head': ('소상공인 정책자금 컨설팅. 소상공인시장진흥공단(소진공) 직접대출과 지역신용보증재단 보증부 대출, '
                      '지자체 이자 지원 가운데 어느 경로가 맞는지부터 확인합니다.'),
        'answers': [
            ('누가 대상인가', '업종별 소상공인 기준(상시근로자 수·매출) 안에 있는 사업자입니다. 개인·법인 모두 해당하고, '
                          '업력이 짧은 경우에도 볼 경로가 있습니다.'),
            ('어떤 기관인가', '소상공인시장진흥공단(소진공)의 직접대출, 지역신용보증재단의 보증부 대출, '
                          '지자체 이자 지원을 함께 봅니다.'),
            ('우리가 하는 일', '어느 기관·어느 자금이 맞는지 가려내고, 사업계획서의 숫자와 서류를 맞춰 신청과 심사 대응까지 '
                           '동행합니다. 조건이 안 되면 안 된다고 먼저 말씀드립니다.'),
        ],
        'rows': [('소진공', '소상공인시장진흥공단(소진공)', '공단 직접대출'),
                 ('지역신보', '지역신용보증재단', '재단 보증서로 은행이 대출'),
                 ('지자체', '지자체', '대출 이자의 일부를 지자체가 부담')],
        'note_track': '지자체 이자 지원',
        'faq': [
            ('소상공인 정책자금, 저도 대상인가요?',
             '업종별 소상공인 기준(상시근로자 수·매출) 안에 있으면 대상입니다. 같은 매출이라도 업종에 따라 기준이 달라서, '
             '경계에 있는 사업자는 확인이 먼저입니다.'),
            ('소진공과 지역신용보증재단, 어디부터 봐야 하나요?',
             '자금 용도와 필요한 금액에 따라 갈립니다. 직접대출과 보증부 대출은 심사 주체가 달라 같은 조건에서도 결과가 '
             '다르게 나옵니다. 진단에서 순서를 정합니다.'),
            ('비용은 어떻게 되나요?',
             '진단은 무료입니다. 실행 전 비용은 일절 없고, 자금이 실제 실행된 경우에만 성공보수를 받습니다. '
             '요율은 계약 시 안내합니다.'),
            ('직접 신청해도 되나요?',
             '됩니다. 기관 공식 경로로 직접 신청할 수 있습니다. 조건이 명확하고 서류 준비가 익숙하면 그게 가장 빠릅니다.'),
            ('얼마를 받을 수 있나요?',
             '금액은 각 기관의 심사로 정해집니다. 받은 사례 기준으로는 {RANGE} 구간이고, 특정 금액이나 승인을 '
             '약속하지 않습니다.'),
        ],
        'related': [('/sojingong', '소상공인시장진흥공단(소진공) 정책자금'), ('/jaedan', '지역신용보증재단 보증'),
                    ('/gaein', '개인사업자 정책자금'), ('/cases', '받은 사례 전체'), ('/chaksugeum', '착수금 사기 구별법')],
    },
    'jungsogieop': {
        'hub': '중소기업',
        'name': '중소기업 정책자금 컨설팅',
        'title': '중소기업 정책자금 컨설팅 | 중진공·신보·기보 | 비즈니스 메이커',
        'desc_head': ('중소기업 정책자금 컨설팅. 중소벤처기업진흥공단(중진공) 직접대출과 신용보증기금(신보)·'
                      '기술보증기금(기보) 보증부 대출 가운데 어느 경로가 맞는지부터 확인합니다.'),
        'answers': [
            ('누가 대상인가', '소상공인 기준을 넘어선 중소기업입니다. 제조·기술 기업이 많지만 업종이 제한되는 것은 아니고, '
                          '재무와 자금 용도가 갈림길입니다.'),
            ('어떤 기관인가', '중소벤처기업진흥공단(중진공)의 직접대출, 신용보증기금(신보)·기술보증기금(기보)의 보증부 대출, '
                          '수출 기업이면 무역보증을 함께 봅니다.'),
            ('우리가 하는 일', '기관을 한 곳으로 정하지 않고 조합과 순서를 설계하고, 사업계획서의 숫자를 맞춰 심사 대응까지 '
                           '동행합니다. 조건이 안 되면 안 된다고 먼저 말씀드립니다.'),
        ],
        'rows': [('중진공', '중소벤처기업진흥공단(중진공)', '공단 직접대출'),
                 ('신보', '신용보증기금(신보)', '보증서로 은행이 대출'),
                 ('기보', '기술보증기금(기보)', '기술평가 기반 보증'),
                 ('무역보증', '무역보증', '수출 거래 기반 보증')],
        'note_track': '무역보증',
        'faq': [
            ('우리 회사는 중소기업 정책자금 대상인가요?',
             '소상공인 기준을 넘었고 중소기업 범위에 있으면 대상입니다. 매출·업종·업력에 따라 볼 기관이 달라져, '
             '경계에 있는 회사는 확인이 먼저입니다.'),
            ('중진공·신보·기보 중 어디가 맞나요?',
             '자금 용도와 회사가 가진 자산에 따라 갈립니다. 설비면 직접대출, 재무로 한도를 늘려야 하면 보증, '
             '기술이 자산이면 기술평가 쪽을 먼저 봅니다. 한 곳만 보지 않습니다.'),
            ('여러 기관을 같이 진행할 수 있나요?',
             '가능한 경우가 있습니다. 같은 시점에 쓸 수 있는 조합과 순서가 정해져 있어, 순서를 잘못 잡으면 뒤가 막힙니다. '
             '받은 사례 가운데 기관을 묶어 설계한 건이 있습니다.'),
            ('비용은 어떻게 되나요?',
             '진단은 무료입니다. 실행 전 비용은 일절 없고, 자금이 실제 실행된 경우에만 성공보수를 받습니다. '
             '요율은 계약 시 안내합니다.'),
            ('얼마를 받을 수 있나요?',
             '금액은 각 기관의 심사로 정해집니다. 받은 사례 기준으로는 {RANGE} 구간이고, 특정 금액이나 승인을 '
             '약속하지 않습니다.'),
        ],
        'related': [('/jungjingong', '중소기업 정책자금(중진공)'), ('/sinbo', '신용보증기금(신보) 보증'),
                    ('/gibo', '기술보증기금(기보) 보증'), ('/bojeung', '보증서 대출'), ('/cases', '받은 사례 전체')],
    },
}


def load_rows():
    with open(ROOT / SRC, encoding='utf-8-sig', newline='') as f:
        rows = [r for r in csv.DictReader(f) if (r.get('사이트 공개') or '').strip().upper() == 'Y']
    if not rows:
        die('공개된 실행 기록이 없습니다.')
    return rows


def money_range(amts):
    hi = f"{amts[-1] / 10000:g}억원" if amts[-1] >= 10000 else f"{amts[-1]:,}만원"
    return f"{amts[0]:,}만원~{hi}"


def rate_range(rows):
    rates = sorted(float(m.group(1)) for r in rows
                   for m in [re.search(r'(\d+(?:\.\d+)?)', r['금리'] or '')] if m)
    return f"연 {rates[0]:g}~{rates[-1]:g}%" if rates else '—'


def build():
    rows = load_rows()
    style = re.search(r'<style>.*?</style>', (ROOT / 'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    src = (ROOT / 'jaedan.html').read_text(encoding='utf-8')
    hdr = re.search(r'<header>.*?</header>', src, re.S).group(0)
    foot = re.search(r'<footer>.*?</footer>', src, re.S).group(0)
    form = re.search(r'<section id="apply-section".*?</section>', (ROOT / 'index.html').read_text(encoding='utf-8'),
                     re.S).group(0)
    extra = ('<style>.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}'
             'table{border-collapse:collapse;width:100%;min-width:560px;font-size:.9rem}'
             'th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}'
             'td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}'
             'td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}'
             'tr:nth-child(even) td{background:#FAFBFD}'
             '.answers{list-style:none;margin:0;padding:0}'
             '.answers li{padding:14px 0;border-top:1px solid var(--line)}'
             '.answers b{display:block;color:var(--navy);margin-bottom:4px}'
             '.related a{display:inline-block;margin:0 8px 8px 0;padding:8px 13px;border:1px solid var(--line);'
             'border-radius:999px;color:var(--ink);text-decoration:none;font-size:.88rem}</style>')

    made = []
    for slug, cfg in HUBS.items():
        mine = [r for r in rows if hub_of(r['기관']) == cfg['hub']]
        if not mine:
            die(f"{slug}: '{cfg['hub']}' 로 분류된 건이 없습니다. build_cases.HUB_OF 를 확인하세요.")
        amts = sorted(int(r['실행 금액(만원)']) for r in mine)
        total, n = sum(amts), len(mine)
        rng = money_range(amts)
        url = f'https://bmaker.kr/{slug}'
        desc = (f"{cfg['desc_head']} 받은 사례 {n}건({won2(total)}), 익명으로 일부 공개합니다. "
                f"진단은 무료, 착수금 없이 성과로만 보수를 받습니다.")

        trs = ''
        for key, label, track in cfg['rows']:
            part = [r for r in mine if inst_bucket(r['기관']) == key]
            if part:
                pa = sorted(int(r['실행 금액(만원)']) for r in part)
                cells = (f'<td class="num">{len(part)}건</td>'
                         f'<td class="num">{won2(round(sum(pa) / len(pa)))}</td>'
                         f'<td class="num">{rate_range(part)}</td>')
            else:
                cells = '<td class="num">—</td><td class="num">—</td><td class="num">—</td>'
            trs += f'<tr><td>{esc(label)}</td><td>{esc(track)}</td>{cells}</tr>'

        faq = [(q, a.replace('{RANGE}', rng)) for q, a in cfg['faq']]
        faq_html = ''.join(f'<details><summary>{esc(q)}</summary><div class="body">{esc(a)}</div></details>'
                           for q, a in faq)
        faq_ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]},
            ensure_ascii=False)
        svc_ld = json.dumps({"@context": "https://schema.org", "@type": "Service", "name": cfg['name'],
                             "serviceType": "정책자금 컨설팅", "areaServed": "KR", "url": url,
                             "provider": {"@type": "Organization", "@id": "https://bmaker.kr/#org",
                                          "name": "비즈니스 메이커", "url": "https://bmaker.kr/"},
                             "offers": {"@type": "Offer", "priceCurrency": "KRW",
                                        "description": "실행 전 비용 0원, 자금 실행 시에만 성공보수"}}, ensure_ascii=False)
        crumb_ld = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "홈", "item": "https://bmaker.kr/"},
            {"@type": "ListItem", "position": 2, "name": cfg['name'], "item": url}]}, ensure_ascii=False)
        answers = ''.join(f'<li><b>{esc(k)}</b>{esc(v)}</li>' for k, v in cfg['answers'])
        related = ''.join(f'<a href="{href}">{esc(label)}</a>' for href, label in cfg['related'])

        page = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="canonical" href="{url}">
<title>{esc(cfg['title'])}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="비즈니스 메이커">
<meta property="og:title" content="{esc(cfg['title'])}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://bmaker.kr/assets/og.png">
<link rel="icon" type="image/png" href="/assets/icon-192.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap">
<script type="application/ld+json">{svc_ld}</script>
<script type="application/ld+json">{crumb_ld}</script>
<script type="application/ld+json">{faq_ld}</script>
{style}
{extra}
</head>
<body>
{hdr}
<main>
<section class="hero"><div class="wrap">
  <p class="crumb"><a href="/">홈</a> › {esc(cfg['name'])}</p>
  <h1 class="serif">{esc(cfg['name'])}</h1>
</div></section>

<section class="block"><div class="wrap">
  <ul class="answers">{answers}</ul>
</div></section>

<section class="block"><div class="wrap">
  <h2 class="serif">대상 기관</h2>
  <div class="tablewrap"><table aria-label="{esc(cfg['name'])} 대상 기관">
    <thead><tr><th>기관</th><th>자금</th><th>건수</th><th>건당 평균</th><th>금리 범위</th></tr></thead>
    <tbody>{trs}</tbody>
  </table></div>
  <p class="asof">{esc(cfg['note_track'])}은 취급하는 경로이지만 공개 집계에 포함된 건이 없어 숫자는 —로 둡니다.
  숫자는 받은 사례에서 자동으로 집계한 값이며 각 실행 시점 기준입니다. 기준일 {ASOF.year}년 {ASOF.month}월 {ASOF.day}일 ·
  전체는 <a href="/cases">받은 사례</a>에서 확인하실 수 있습니다.</p>
</div></section>

<section class="block"><div class="wrap">
  <h2 class="serif">자주 묻는 질문</h2>
  {faq_html}
</div></section>

{form}

<section class="block"><div class="wrap">
  <h2 class="serif">함께 보면 좋은 안내</h2>
  <p class="related">{related}</p>
</div></section>
</main>
{foot}
<script src="/assets/conversion.js" defer></script>
</body>
</html>
'''
        page = re.sub(r'(href|src)="assets/', r'\1="/assets/', page)
        (ROOT / f'{slug}.html').write_text(page, encoding='utf-8')
        made.append((slug, n, won2(total)))

    sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    for slug, _n, _t in made:
        loc = f'https://bmaker.kr/{slug}'
        if f'<loc>{loc}</loc>' not in sm:
            sm = sm.replace('</urlset>', f'  <url><loc>{loc}</loc><changefreq>monthly</changefreq>'
                                         f'<priority>0.9</priority></url>\n</urlset>')
    (ROOT / 'sitemap.xml').write_text(sm, encoding='utf-8')
    print('[허브 빌드 OK] ' + ' · '.join(f'/{s} {n}건 {t}' for s, n, t in made) + f' (기준일 {ASOF})')


if __name__ == '__main__':
    build()
