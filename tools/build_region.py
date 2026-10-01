#!/usr/bin/env python3
"""도시 페이지 /region/<slug> 빌드 — data/region.source.csv 의 사실(재단 지점·소진공 센터·시 자금 공고)만으로 만든다.

규격 8-1(도어웨이 방지)을 생성 전에 검사해 어기면 멈춘다. 검사 본체는 tests/test_region.py 와 같은 규칙이다.
  - 공식 출처 사실 3개 이상, 그중 시·군 자금 1건 이상. 시·군 자금은 공고(출처 URL) 단위로 센다.
  - province-fund(도 전체 사업)는 "참고"로만 표시하고 세지 않는다.
  - 사실 확인일이 빌드일 기준 90일을 넘으면 멈춘다.
  - 두 도시의 사실 조합이 같으면 멈춘다.
사례는 원장이 시도 단위라(규격 1절 익명화) "{시도} 사례"로만 요약한다.
재단 페이지의 "이 지역 도시" 링크는 build_jaedan 이 같은 CSV 를 읽어 만든다(체인: jaedan → region).
실행: python tools/build_region.py
"""
import csv, datetime, json, re, sys
from html import escape
from pathlib import Path
from builddate import build_date
from inline_form import form_html, CSS as FORM_CSS, TITLE_GENERAL

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / 'data' / 'region.source.csv'
TODAY = build_date()
FEE = '진단은 무료입니다.'
BYLINE = '작성 비즈니스 메이커 · 검토 김상표(대표) · 최종 확인 {}'
MIN_FACTS, MAX_AGE_DAYS = 3, 90
MAX_DESC = 150   # description 글자 수 상한(대표 2026-10-01)
COUNTED = {'jaedan-branch', 'semas-center', 'city-fund'}
KINDS = COUNTED | {'province-fund'}
OFFICE = '비즈니스 메이커 사무실(마곡): 서울 강서구 공항대로 213'   # 규격 3절 표기


def die(m):
    print(f"[도시 빌드 실패] {m}")
    sys.exit(1)


def esc(s):
    return escape(str(s or ''), quote=True)


def won2(m):
    e, man = divmod(int(m), 10000)
    return ((f"{e}억" + ((" " if man else "") + f"{man:,}만" if man else "")) + "원") if e else f"{man:,}만원"


def load():
    if not SRC.exists():
        return {}
    cities = {}
    with open(SRC, encoding='utf-8-sig', newline='') as f:
        for i, d in enumerate(csv.DictReader(f), start=2):
            d = {k: (v or '').strip() for k, v in d.items() if k}
            if not any(d.values()) or d.get('사이트 공개', '').upper() != 'Y':
                continue
            for c in ('도시ID', '도시명', '짧은이름', '시도', '재단ID', '종류', '이름', '출처 URL', '확인일'):
                if not d.get(c):
                    die(f"{i}행: '{c}' 이 비어 있습니다.")
            if not re.fullmatch(r'[a-z0-9-]+', d['도시ID']):
                die(f"{i}행 도시ID '{d['도시ID']}' — 영소문자·숫자·하이픈만.")
            if d['종류'] not in KINDS:
                die(f"{i}행 종류 '{d['종류']}' — {sorted(KINDS)} 중 하나.")
            if not d['출처 URL'].startswith('https://'):
                die(f"{i}행 출처 URL 은 https 여야 합니다: {d['출처 URL']}")
            try:
                d['_checked'] = datetime.date.fromisoformat(d['확인일'])
            except ValueError:
                die(f"{i}행 확인일 형식 오류: {d['확인일']}")
            j = ' '.join(v for k, v in d.items() if isinstance(v, str))
            if '갚' in j or re.search(r'보장', j):
                die(f"{i}행: '갚다'·'보장' 계열 금지.")
            CITY_KEYS = ('도시명', '짧은이름', '시도', '재단ID', '지점 축약', '담당 문장', '담당 질문')
            c = cities.setdefault(d['도시ID'], {'도시ID': d['도시ID']} | {k: d.get(k, '') for k in CITY_KEYS} | {'facts': []})
            for k in CITY_KEYS:
                if c[k] != d.get(k, ''):
                    die(f"{i}행: {d['도시ID']} 의 '{k}' 가 앞 행과 다릅니다.")
            c['facts'].append(d)
    return cities


def fact_key(d):
    return (d['종류'], d['출처 URL'] if d['종류'] == 'city-fund' else d['이름'])


def gate(cities):
    seen = {}
    for c in cities.values():
        keys = {fact_key(d) for d in c['facts'] if d['종류'] in COUNTED}
        if len(keys) < MIN_FACTS:
            die(f"{c['도시ID']}: 공식 출처 사실 {len(keys)}개 — 최소 {MIN_FACTS}개(규격 8-1). 페이지를 만들지 않습니다.")
        if not any(k == 'city-fund' for k, _ in keys):
            die(f"{c['도시ID']}: 시·군 자금 공고가 없습니다(규격 8-1).")
        for d in c['facts']:
            if (TODAY - d['_checked']).days > MAX_AGE_DAYS:
                die(f"{c['도시ID']}: '{d['이름']}' 확인일 {d['확인일']} 이 {MAX_AGE_DAYS}일을 넘었습니다 — 재확인 후 갱신하세요.")
        fs = frozenset(keys)
        if fs in seen:
            die(f"{c['도시ID']} ↔ {seen[fs]}: 사실 조합이 같습니다(규격 8-1).")
        seen[fs] = c['도시ID']


def sido_cases(sido):
    rows = []
    with open(ROOT / 'data' / 'cases.source.csv', encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            if (r.get('사이트 공개') or '').upper() == 'Y' and r['지역(시도)'] == sido:
                rows.append(r)
    return rows


def jaedan_name(jid):
    with open(ROOT / 'data' / 'jaedan.source.csv', encoding='utf-8-sig', newline='') as f:
        for d in csv.DictReader(f):
            if d['재단ID'] == jid:
                return d['재단명']
    die(f"재단ID '{jid}' 가 data/jaedan.source.csv 에 없습니다.")


def attrs(d):
    return (f' data-fact="{esc(d["종류"])}" data-fact-id="{esc(d["이름"] if d["종류"] != "city-fund" else d["출처 URL"])}"'
            f' data-source="{esc(d["출처 URL"])}" data-checked="{esc(d["확인일"])}"')


def link(url, text):
    return f'<a href="{esc(url)}" target="_blank" rel="noopener">{text}</a>'


def branch_label(names):
    """['경기신용보증재단 수원팔달지점', '경기신용보증재단 수원광교지점'] → '경기신용보증재단 수원팔달지점·수원광교지점'"""
    org = names[0].split(' ')[0]
    return org + ' ' + '·'.join(n.split(' ', 1)[1] for n in names)


def is_gov(url):
    return bool(re.match(r'^https://([^/]+\.)?(go\.kr|seoul\.kr)(/|$)', url or ''))


def subj(word):
    """주격 조사 — 받침 있으면 '이', 없으면 '가'."""
    ch = word.rstrip(')')[-1:] if word else ''
    return '이' if ch and '가' <= ch <= '힣' and (ord(ch) - 0xAC00) % 28 else '가'


def notices(facts):
    """시 자금 행을 공고(출처 URL) 단위로 묶는다 — 순서 유지."""
    out = {}
    for d in facts:
        if d['종류'] == 'city-fund':
            out.setdefault(d['출처 URL'], []).append(d)
    return list(out.values())


def page_html(c, style, hdr, foot):
    F = c['facts']
    city, short, sido, jid = c['도시명'], c['짧은이름'], c['시도'], c['재단ID']
    jname = jaedan_name(jid)
    br = [d for d in F if d['종류'] == 'jaedan-branch']
    ce = [d for d in F if d['종류'] == 'semas-center']
    nts = notices(F)
    prov = [d for d in F if d['종류'] == 'province-fund']
    url = f"https://bmaker.kr/region/{c['도시ID']}"
    abbr, override = c['지점 축약'], c['담당 문장']
    # title 규칙(대표 2026-10-01): 도시는 검색어 형태(짧은이름), 지점은 축약, 자체 자금 명칭은 title 에서 뺀다
    title = f"{short} 소상공인 정책자금·대출 — {jname}{' ' + abbr if abbr else ''} 안내 | 비즈니스 메이커"
    # 지점 창구 요약: 담당 문장을 따로 둔 도시(근거가 좁은 강서구·표기가 갈리는 청주)는 표로 넘긴다
    window = f"{jname} 창구(아래 표)" if override or not abbr else f"{jname} {abbr}"
    newest = max(d['_checked'] for d in F)
    # 키워드 보강(대표 2026-10-01): 끝 문장에 지원사업·지원금·소상공인지원센터 — title 은 대출·정책자금 그대로
    # description 규칙(대표 2026-10-01): 150자 이내, 키워드 앞쪽, 자금명은 본문·표에만
    desc = (f"{short} 소상공인 정책자금·대출·지원사업 창구: {jname}{' ' + abbr if abbr else ''}, "
            f"소상공인지원센터({'·'.join(d['이름'].split(' ', 1)[1] for d in ce)}), {short} 공고 {len(nts)}건. "
            "한도·금리·접수기간을 공고 원문과 함께 정리했습니다.")
    if len(desc) > MAX_DESC:
        die(f"{c['도시ID']}: description {len(desc)}자 — {MAX_DESC}자 이내여야 합니다.")
    office = city.split()[-1] + '청'   # 수원시청 · 강서구청 · ○○군청

    # ① 이 도시 사업자가 볼 자금 — 짧은 답
    first = f"신용보증재단은 {esc(window)}" if override or not abbr else f"보증부 대출은 {esc(window)}"
    answer = (f"<b>짧은 답:</b> {esc(city)} 사업장이라면 세 곳을 확인하세요. "
              f"① {first}, ② 소상공인시장진흥공단(소진공) 소상공인지원센터는 "
              f"{esc('·'.join(d['이름'].split(' ', 1)[1] for d in ce))}, ③ {esc(short)} 자체 자금은 올해 공고 {len(nts)}건입니다.")

    # ② 재단 지점 — 담당 문장은 근거 범위를 넘지 않는다(강서구 = 특별신용보증 접수처)
    blabel = branch_label([d['이름'] for d in br]) if br else jname
    sentence_txt = override or f"{city}의 신용보증재단 업무는 {blabel}{subj(blabel)} 담당합니다."
    sentence = esc(sentence_txt)
    brows = []
    for d in br:
        area = esc(d['관할']) if d['관할'] else '재단 사이트 미공개 — 아래 공고 근거 참고'
        links = [link(d['출처 URL'], f'{esc(short)} 공고' if is_gov(d['출처 URL']) else '재단 지점 안내')]
        if d['근거 URL'] and d['근거 URL'] != d['출처 URL']:
            links.append(link(d['근거 URL'], f'{esc(short)} 공고' if is_gov(d['근거 URL']) else '재단 사이트'))
        name = d['표시 이름'] or d['이름'].split(' ', 1)[1]
        brows.append(f'<tr{attrs(d)}><td>{esc(name)}</td><td>{area}</td><td>{esc(d["주소"])}</td>'
                     f'<td>{esc(d["전화"])}</td><td>{" · ".join(links)} · {esc(d["확인일"])}</td></tr>')
    ev_html = ''
    seen_q = set()
    for d in br:
        if not d['근거 문장'] or d['근거 문장'] in seen_q:
            continue
        seen_q.add(d['근거 문장'])
        ev_url = d['출처 URL'] if is_gov(d['출처 URL']) else d['근거 URL']
        ev_html += f'<p class="basis">{esc(short)} 공고 원문: “{esc(d["근거 문장"])}” — {link(ev_url, "공고 보기")}</p>'
    ev = next((d for d in br if d['근거 문장']), None)
    sec_branch = (f'<h2>{esc(jname)} — {esc(city)} 담당 지점</h2>\n<p>{sentence}</p>\n'
                  '<div class="tablewrap"><table><thead><tr><th>지점</th><th>관할(공식)</th><th>주소</th><th>전화</th><th>출처·확인일</th></tr></thead><tbody>'
                  + ''.join(brows) + '</tbody></table></div>\n' + ev_html
                  + f'<p>보증 절차·상품: <a href="/{jid}">{esc(jname)} 안내</a></p>')

    # ③ 시 자체 자금 공고 (공고 단위)
    nrows = []
    for items in nts:
        head = items[0]
        cells = '<br>'.join(
            f'<b>{esc(d["이름"])}</b> — 한도 {esc(d["한도"]) or "공고 미기재"} · 금리·이자지원 {esc(d["금리"]) or "공고 미기재"}'
            for d in items)
        nrows.append(f'<tr{attrs(head)}><td>{cells}</td><td>{esc(head["접수기간"]) or "공고 참고"}</td>'
                     f'<td>{link(head["출처 URL"], "공고 원문")} · {esc(head["확인일"])}</td></tr>')
    sec_fund = (f'<h2>{esc(short)} 소상공인 지원사업·지원금 — 2026년 공고</h2>\n'
                f'<p>대부분 융자·보증·이자지원 방식이며, 무상 지원금은 공고별로 다릅니다. '
                f'{esc(city)}{subj(city)} 직접 낸 공고 {len(nts)}건이며, 한도·금리는 사업 기준이고 예산이 소진되면 일찍 끝날 수 있습니다.</p>\n'
                '<div class="tablewrap"><table><thead><tr><th>자금(공고 기준)</th><th>접수기간(공고 문구)</th><th>출처·확인일</th></tr></thead><tbody>'
                + ''.join(nrows) + '</tbody></table></div>')

    # ④ 소상공인지원센터 (공식)
    crows = ''.join(
        f'<li{attrs(d)}><b>{esc(d["이름"])}</b> — 담당지역 {esc(d["관할"])} · {esc(d["주소"])} · {esc(d["전화"])} '
        f'({link(d["출처 URL"], "소진공 센터 안내")}, 확인일 {esc(d["확인일"])})</li>' for d in ce)
    sec_center = (f'<h2>{esc(short)} 소상공인지원센터(소상공인센터) 위치·연락처</h2>\n'
                  f'<p>소상공인시장진흥공단(소진공)이 운영하는 공식 소상공인지원센터입니다. <b>공식 기관이며 비즈니스 메이커와 무관합니다.</b> '
                  f'소진공 안내에 따르면 담당지역과 관계없이 가까운 센터를 방문할 수 있습니다.</p>\n'
                  f'<ul class="facts">{crows}</ul>')

    # ⑤ {시도} 사례 요약 — 시도 단위 라벨
    rows = sido_cases(sido)
    if rows:
        total = sum(int(r['실행 금액(만원)']) for r in rows)
        jd = sum(1 for r in rows if '신용보증재단' in r['기관'])
        sec_cases = (f'<h2>{esc(sido)} 사례 — 시도 단위</h2>\n<p>{esc(sido)} 받은 사례 {len(rows)}건·{won2(total)}(재단 경로 {jd}건). '
                     f'원장은 시도 단위라 {esc(short)}만 나누지 않고, 과거 사례는 현재 조건이 아닙니다. <a href="/{jid}">{esc(sido)} 사례 보기</a></p>')
    else:
        sec_cases = (f'<h2>{esc(sido)} 사례 — 시도 단위</h2>\n<p>현재 공개 원장에 {esc(sido)} 사례는 없습니다. '
                     f'<a href="/cases">다른 지역 받은 사례</a>를 참고하세요. 해당 지역 실적이 아닙니다.</p>')

    # ⑧ 도 전체 사업 — 참고(개수 제외)
    if prov:
        plist = ''.join(f'<li{attrs(d)}>{esc(d["이름"])} — {link(d["출처 URL"], "공고 원문")} · {esc(d["확인일"])}</li>' for d in prov)
        sec_prov = f'<h2>참고 — {esc(sido)} 전체 사업</h2>\n<p>{esc(sido)} 전역에 적용되는 사업입니다. {esc(city)}만의 제도는 아닙니다.</p><ul class="facts">{plist}</ul>'
    else:
        sec_prov = (f'<h2>참고 — {esc(sido)} 전체 사업</h2>\n<p><a href="/schedule">정책자금 접수 일정</a></p>')

    # ⑥ FAQ — 이 도시 사실로만 답한다
    ev_q = ev['근거 문장'] if ev else ''
    faq = [
        (c['담당 질문'] or f"{city} 사업장은 신용보증재단 어느 지점에 문의하나요?",
         (sentence_txt + ' ' + (f"{short} 공고 원문은 “{ev_q}”입니다." if ev_q else '')).strip()),
        (f"{short} 소상공인 지원금은 어디서 확인하나요?",
         f"{office} 고시·공고, 기업마당(bizinfo.go.kr), 소상공인24(sbiz24.kr)에서 확인합니다. "
         f"이 페이지 '{short} 소상공인 지원사업·지원금' 표에 2026년 {short} 공고 {len(nts)}건을 공고 원문 링크와 함께 정리했습니다. "
         "대부분 융자·보증·이자지원 방식이며, 무상 지원금은 공고별로 다릅니다."),
        (f"{short} 자체 자금 한도·금리가 우리 회사 조건인가요?",
         f"아닙니다. 예를 들어 {nts[0][0]['이름']} 공고의 한도 '{nts[0][0]['한도'] or '공고 미기재'}'는 사업 전체 기준입니다. "
         "실제 금액과 대상 여부는 심사로 정해집니다. " + FEE),
        (f"{short} 자금 접수는 언제까지인가요?",
         ' '.join(f"{items[0]['이름']}: {items[0]['접수기간'] or '공고 참고'}." for items in nts)),
        (f"{short} 소상공인센터는 어디에 있나요?",   # 기존 "소상공인지원센터는 어디인가요?"를 대체(중복 방지)
         ' '.join(f"{d['이름']}(소상공인지원센터)이며 주소는 {d['주소']}, 전화는 {d['전화']}, 담당지역은 {d['관할']}입니다." for d in ce)
         + " 소진공이 운영하는 공식 기관이며 비즈니스 메이커와 무관합니다."),
    ]
    faq_html = ''.join(f'<details><summary>{esc(q)}</summary><div class="body">{esc(a)}</div></details>' for q, a in faq)
    faq_ld = json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}, ensure_ascii=False)
    crumb = json.dumps({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": 1, "name": "홈", "item": "https://bmaker.kr/"},
        {"@type": "ListItem", "position": 2, "name": jname, "item": f"https://bmaker.kr/{jid}"},
        {"@type": "ListItem", "position": 3, "name": city, "item": url}]}, ensure_ascii=False)
    svc = json.dumps({"@context": "https://schema.org", "@type": "Service", "name": f"{city} 소상공인 정책자금 진단",
                      "serviceType": "정책자금 컨설팅·진단",
                      "provider": {"@type": "Organization", "@id": "https://bmaker.kr/#org", "name": "비즈니스 메이커", "url": "https://bmaker.kr/"},
                      "areaServed": city, "url": url}, ensure_ascii=False)
    office = f'<p class="office">{esc(OFFICE)}</p>' if c['도시ID'] == 'seoul-gangseo' else ''
    h1 = f"{city} 소상공인 정책자금·대출, 창구는 세 곳입니다"
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://bmaker.kr/assets/og.png">
<meta property="og:locale" content="ko_KR">
<link rel="canonical" href="{url}">
<link rel="icon" type="image/png" href="/assets/icon-192.png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap">
<script type="application/ld+json">{svc}</script>
<script type="application/ld+json">{crumb}</script>
<script type="application/ld+json">{faq_ld}</script>
{style}
<style>{TBL}{FORM_CSS}</style>
</head>
<body data-service="policy">
{hdr}
<section class="hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> › <a href="/{jid}">{esc(jname)}</a> › {esc(city)}</p>
    <h1 class="serif">{esc(h1)}</h1>
    <p>{esc(city)} 사업장이 확인할 공식 창구와 올해 {esc(short)} 공고를 출처와 함께 정리했습니다.</p>
  </div>
</section>
<main data-city="{esc(city)}" data-jaedan="{jid}">
  <div class="wrap">
    <p>{answer}</p>
    <p class="asof">본 안내는 {newest.year}년 {newest.month}월 기준 · 각 항목의 확인일과 공고 원문 링크를 함께 적었습니다.</p>
    {sec_branch}
    {sec_fund}
    {sec_center}
    {sec_cases}
    <h2>자주 묻는 질문</h2>
    {faq_html}
    {form_html('/region/' + c['도시ID'], city, TITLE_GENERAL)}
    {sec_prov}
    <div class="callout"><p>정책자금은 대출이며 상환 의무가 있습니다. 보증·대출 승인 여부와 조건은 재단·은행·지자체가 결정하고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. 비즈니스 메이커는 민간 컨설팅 회사이며 위 공공기관과 무관합니다. {FEE}</p></div>
    {office}
    <p class="byline">{BYLINE.format(newest)}</p>
    <div class="related">
      <p class="t">함께 보기</p>
      <a href="/{jid}">{esc(jname)} 안내</a>
      <a href="/jaedan">신용보증재단 사업자대출</a>
      <a href="/sojingong">소상공인시장진흥공단 정책자금</a>
      <a href="/schedule">정책자금 접수 일정</a>
    </div>
  </div>
</main>
{foot}
<script src="/assets/conversion.js" defer></script>
</body>
</html>
'''


TBL = ('.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}'
       'table{border-collapse:collapse;width:100%;min-width:560px;font-size:.88rem}'
       'th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}'
       'td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}'
       'tr:nth-child(even) td{background:#FAFBFD}td a,.facts a,.basis a{color:var(--blue-deep);text-decoration:underline}'
       'main .facts{padding-left:18px;line-height:1.7}main .facts li{margin:6px 0}'
       'main p.basis{font-size:.88rem;color:var(--ink-soft);border-left:3px solid var(--line);padding-left:12px}'
       'main p.office{font-size:.9rem;color:var(--ink-soft)}main p.byline{margin-top:14px;font-size:.8rem;color:var(--ink-soft)}')


def _abs_assets(html):
    return re.sub(r'(href|src)="assets/', r'\1="/assets/', html)


def build():
    cities = load()
    if not cities:
        print("[도시 빌드 OK] 도시 0개 (data/region.source.csv 없음·비공개)")
        return
    gate(cities)
    style = re.search(r'<style>.*?</style>', (ROOT / 'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    src = (ROOT / 'jaedan.html').read_text(encoding='utf-8')
    hdr = _abs_assets(re.search(r'<header>.*?</header>', src, re.S).group(0))
    foot = _abs_assets(re.search(r'<footer>.*?</footer>', src, re.S).group(0))
    out_dir = ROOT / 'region'
    out_dir.mkdir(exist_ok=True)
    for c in cities.values():
        page = page_html(c, style, hdr, foot)
        if '갚' in page:
            die(f"{c['도시ID']}: '갚' 포함")
        if re.search(r'보장(?!하지)', page):
            die(f"{c['도시ID']}: '보장' 포함")
        if '실행 기록' in page or '중앙값' in page:
            die(f"{c['도시ID']}: 금칙어('실행 기록'·'중앙값') 포함")
        (out_dir / f"{c['도시ID']}.html").write_text(page, encoding='utf-8')
    for p in out_dir.glob('*.html'):          # 데이터에서 빠진 도시 페이지는 지운다(sitemap 과 1:1)
        if p.stem not in cities:
            p.unlink()
    sm = (ROOT / 'sitemap.xml').read_text(encoding='utf-8')
    sm = re.sub(r'  <url><loc>https://bmaker\.kr/region/(?!(?:' + '|'.join(map(re.escape, cities)) + r')</loc>)[^<]+</loc>.*?</url>\n', '', sm)
    for cid in cities:
        loc = f"https://bmaker.kr/region/{cid}"
        if loc + '</loc>' not in sm:
            sm = sm.replace('</urlset>', f'  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>\n</urlset>')
    (ROOT / 'sitemap.xml').write_text(sm, encoding='utf-8')
    lt = (ROOT / 'llms.txt').read_text(encoding='utf-8')
    line = (f"- [도시별 소상공인 정책자금 창구 {len(cities)}곳](https://bmaker.kr/region/{next(iter(cities))}): "
            f"도시마다 신용보증재단 담당 지점·소진공 센터·시 자체 자금 공고를 공식 출처와 함께 정리 — "
            + '·'.join(c['도시명'] for c in cities.values()))
    if '- [도시별 소상공인 정책자금 창구' in lt:
        lt = re.sub(r'- \[도시별 소상공인 정책자금 창구[^\n]*', lambda m: line, lt)
    else:
        lt = lt.replace('- [지역 신용보증재단 페이지 17종]', line + '\n- [지역 신용보증재단 페이지 17종]')
    (ROOT / 'llms.txt').write_text(lt, encoding='utf-8')
    print(f"[도시 빌드 OK] {len(cities)}개 도시 페이지 생성 ({', '.join(cities)}, 기준일 {TODAY})")


if __name__ == '__main__':
    build()
