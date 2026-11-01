#!/usr/bin/env python3
"""지역 신용보증재단 페이지 빌드 — data/jaedan.source.csv 공개(Y) 한 줄 = 페이지 하나, 공개 N 은 파일 삭제·/jaedan#<slug> 301.
받은 사례에서 (기관에 '재단' 포함 & 지역 일치) 사례를 자동 연결하고, /jaedan 허브의 지역 그리드를 마커 사이에 주입한다.
실행: python tools/build_jaedan.py
"""
import csv, json, re, sys, datetime
from html import escape
from pathlib import Path
from builddate import build_date
from inline_form import form_html, CSS as FORM_CSS
from reviewer import byline_html
from service_consulting import STYLESHEET, hero_content, service_content, region_config
ROOT = Path(__file__).resolve().parent.parent
TODAY = build_date()  # BUILD_DATE 있으면 그 날짜, 없으면 Asia/Seoul 오늘 (tools/builddate.py)
FEE = '진단은 무료입니다.'   # 안내 박스용. 비용 구조 설명은 FAQ 비용 답·llms 에만(대표 결정 2026-09-28)
def die(m): print(f"[재단 빌드 실패] {m}"); sys.exit(1)
def won2(m):
    e,man=divmod(int(m),10000)
    return ((f"{e}억"+((" " if man else "")+f"{man:,}만" if man else ""))+"원") if e else f"{man:,}만원"
def esc(s): return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
SIDO_RE = r'(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)신용보증재단'

def load():
    """공개(Y) 행만 — 페이지를 만드는 재단."""
    return [d for d in load_all() if d['사이트 공개'].upper()=='Y']

def slug(d):
    """/jaedan 허브 지역 섹션 앵커 — 재단ID 에서 'jaedan-' 을 뗀 값(퇴역 페이지 301 의 목적지 /jaedan#<slug>)."""
    return d['재단ID'].removeprefix('jaedan-')

def load_all():
    """전체 행(퇴역 N 포함) — 허브 지역 섹션은 17개 전부, 페이지는 공개 행만."""
    rows=[]
    with open(ROOT/'data'/'jaedan.source.csv',encoding='utf-8-sig',newline='') as f:
        for i,d in enumerate(csv.DictReader(f), start=2):
            d.pop(None, None)
            d={k:(v if isinstance(v,str) else '').strip() for k,v in d.items() if k}
            if not any(d.values()): continue
            for c in ('재단ID','재단명','지역(시도)','홈페이지 링크','최종 확인일','사이트 공개'):
                if not d.get(c): die(f"{i}행: '{c}' 이 비어 있습니다.")
            if not re.match(r'^[a-z0-9-]+$', d['재단ID']): die(f"{i}행 재단ID '{d['재단ID']}' — 영소문자·숫자·하이픈만.")
            j=' '.join(d.values())
            if '갚' in j: die(f"{i}행: '갚다'류 금지.")
            if re.search(r'보장', j): die(f"{i}행: '보장' 표현 금지.")
            rows.append(d)
    if not rows: die("재단 행이 없습니다.")
    ids=[d['재단ID'] for d in rows]
    if len(ids)!=len(set(ids)): die("재단ID 중복.")
    return rows

def rate_range(vals):
    nums=[]
    for v in vals:
        m=re.search(r'\d+(?:\.\d+)?', v or '')
        if m: nums.append(float(m.group(0)))
    nums=sorted(set(nums))
    if not nums: return ''
    lo=f"{nums[0]:g}"; hi=f"{nums[-1]:g}"
    return f"연 {lo}%" if lo==hi else f"연 {lo}~{hi}%"

def all_jd():
    out=[]
    with open(ROOT/'data'/'cases.source.csv',encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            keys = [('소상공인','소진공'),('재단','재단'),('기술','기보'),('신용보증기금','신보'),('중소벤처','중진공'),('중진공','중진공')]
            hits = [(r['기관'].find(a), b) for a, b in keys if a in r['기관']]
            if r['사이트 공개'].upper()=='Y' and hits and min(hits)[1] == '재단':
                # 원장 '지역(시도)' 에 도시명이 들어간 행(예: 광양·파주)이 있어 기관명의 재단 지역을 우선한다
                m = re.search(SIDO_RE, r['기관'])
                if m: r['지역(시도)'] = m.group(1)
                out.append(r)
    out.sort(key=lambda r:(r['실행 연월'], r['사례ID']), reverse=True)
    return out

def cases_for(region):
    return [r for r in all_jd() if r['지역(시도)'] == region]


def region_cities(jid):
    """이 재단에 속한 도시 페이지(/region/<slug>) — data/region.source.csv 공개 행 기준, 첫 등장 순서(규격 8-1 양방향 링크)."""
    p = ROOT/'data'/'region.source.csv'
    if not p.exists(): return []
    out = {}
    with open(p, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f):
            if (r.get('사이트 공개') or '').strip().upper()=='Y' and r['재단ID'].strip()==jid:
                out.setdefault(r['도시ID'].strip(), r['도시명'].strip())
    return list(out.items())


def render_hub_cases(rows):
    regions = len({r['지역(시도)'] for r in rows})
    total = sum(int(r['실행 금액(만원)']) for r in rows)
    heading = f'<h2>재단 경로의 받은 사례 — {regions}개 지역</h2><p>공개 원장 기준 {len(rows)}건 · {won2(total)}. 기업 수가 아닌 사례 건수입니다.'
    if rows:
        dates = sorted(r['실행 연월'] for r in rows)
        amounts = [int(r['실행 금액(만원)']) for r in rows]
        heading += f' 집계 기간 {dates[0]}~{dates[-1]}, 받은 금액 {won2(min(amounts))}~{won2(max(amounts))}, 금리 {rate_range([r["금리"] for r in rows])} (각 실행 시점 기준).'
    heading += ' 과거 사례는 현재 신청 한도·금리·승인 가능성을 뜻하지 않습니다. 복합 기관 사례는 원장에 먼저 기재된 기관으로 분류합니다.</p>'
    selected = sorted(rows, key=lambda r:(r['실행 연월'], r['사례ID']), reverse=True)[:10]
    table = ''.join(f'<tr><td>{escape(r["실행 연월"])} · {escape(r["지역(시도)"])}</td><td>{escape(r["자금명"])}</td><td>{won2(r["실행 금액(만원)"])} · {escape(r["금리"])}</td><td><a href="/cases#case-{escape(r["사례ID"], quote=True)}">사례 {escape(r["사례ID"])}</a></td></tr>' for r in selected)
    return heading + '<p>최근 사례 최대 10건을 표시합니다. 기관·상품·금액의 근거는 각 사례 링크에서 확인하세요.</p><div class="tablewrap"><table><thead><tr><th>시점·지역</th><th>상품</th><th>받은 금액·당시 금리</th><th>근거</th></tr></thead><tbody>' + table + '</tbody></table></div>'

def tel(phone): return 'tel:' + re.sub(r'[^0-9]', '', phone)

def tail_items(d):
    """title 꼬리 후보 — 지점 수(시트에 있으면)·받은 사례 건수·최근 실행 연월·금리 범위. 모두 데이터에서 나온다."""
    C=cases_for(d['지역(시도)'])
    out=[]
    if d.get('branch_count'): out.append(f"지점 {d['branch_count']}곳")
    if C:
        y,m=C[0]['실행 연월'].split('-')
        out += [f"받은 사례 {len(C)}건", f"최근 실행 {y}년 {int(m)}월"]
        r=rate_range([r['금리'] for r in C])
        if r: out.append(f"금리 {r}")
    return out

def title_tails(rows):
    """꼬리 = 후보 중 2개. 앞 페이지와 겹치면 둘째 후보를 다음 것으로 바꿔 전 페이지가 서로 다르게 한다."""
    seen, out = set(), {}
    for d in rows:
        items=tail_items(d)
        if len(items)<2: die(f"{d['재단ID']}: title 꼬리 데이터가 2개 미만(사례 0건이면 data/jaedan.overlay.csv 에서 공개 N 으로).")
        for second in items[1:]:
            t=f"{items[0]} · {second}"
            if t not in seen: break
        else: die(f"{d['재단ID']}: title 꼬리가 다른 재단과 겹칩니다 — {t}")
        seen.add(t); out[d['재단ID']]=t
    return out

def description(d, C, rates):
    lim=f" 2026 공고 한도: {d['limit_2026']}." if d.get('limit_2026') else ''
    s=(f"{d['지역(시도)']} 사업장 보증 창구 {d['재단명']} — 본점·대표전화와 재단 공고 확인 내용,"
       f" 받은 사례 {len(C)}건"+(f"({rates})" if rates else '')+f".{lim}")
    return s if len(s)<=160 else s[:157].rstrip()+'…'

def notice_facts(d):
    """(a) 재단 공고 사실 — 시트 값만, 출처 URL·확인일 병기. 확인 안 된 칸은 행을 만들지 않는다."""
    rows=[]
    if d.get('limit_2026'): rows.append(('공고 기준 보증 한도', esc(d['limit_2026'])))
    if d.get('special_guarantees'): rows.append(('운영 중인 보증 상품', esc(d['special_guarantees'])))
    if d.get('hq_address'): rows.append(('본점', esc(d['hq_address'])+(f' · <a href="{tel(d["phone"])}">{esc(d["phone"])}</a>' if d.get('phone') else '')))
    if d.get('branch_count'): rows.append(('지점', f"{esc(d['branch_count'])}곳 — 보증 상담은 사업장 소재지 관할 지점"))
    if not rows: return ''
    src=[]
    if d.get('notice_url') and d.get('notice_confirmed_at'): src.append(f'공고 확인일 {esc(d["notice_confirmed_at"])} · <a href="{esc(d["notice_url"])}" target="_blank" rel="noopener">재단 공고 원문</a>')
    if d.get('source_url') and d.get('confirmed_at'): src.append(f'본점·지점 확인일 {esc(d["confirmed_at"])} · <a href="{esc(d["source_url"])}" target="_blank" rel="noopener">재단 안내</a>')
    body=''.join(f'<tr><td style="white-space:nowrap"><b>{k}</b></td><td>{v}</td></tr>' for k,v in rows)
    return (f'<h2>{esc(d["재단명"])} 공고에서 확인한 내용</h2>\n<div class="tablewrap"><table class="kv"><tbody>{body}</tbody></table></div>\n'
            f'<p class="asof">{" · ".join(src)} · 한도·대상은 회차별 공고가 기준이며 소진 시 마감됩니다 — 접수 중 자금은 <a href="/schedule">일정 페이지</a></p>')

# 지역 페이지에서 뺀 공통 FAQ — /jaedan 허브에 한 번만 둔다(화면·FAQPage JSON-LD 함께)
HUB_FAQ = [
    ('어떻게 진행되나요?', '재단 보증 심사 → 보증서 발급 → 은행 대출 실행의 3단계입니다. 상환은 거치 후 분할 또는 만기까지 이자만 내는 구조가 일반적이며, 상품과 공고에 따라 다릅니다.'),
    ('무엇을 준비해야 하나요?', '사업자등록·매출 증빙·임대차계약 등 기본 서류에 더해 신청 상품의 공고 요건을 확인해야 합니다. 조건이 되는지부터 무료 진단으로 확인해 드립니다 — 가능성이 낮으면 낮다고 먼저 말씀드립니다.'),
]

def upsert_hub_faq(hub):
    for q,a in HUB_FAQ:
        if f'<summary>{q}</summary>' in hub: continue
        i=hub.index('<h2>자주 묻는 질문</h2>'); j=hub.index('<div class="cta-box">', i)
        hub=hub[:j]+f'<details><summary>{q}</summary><div class="body">{a}</div></details>\n    '+hub[j:]
    def ld(m):
        data=json.loads(m[1])
        if data.get('@type')=='FAQPage':
            have={x['name'] for x in data['mainEntity']}
            data['mainEntity']+=[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in HUB_FAQ if q not in have]
        return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False)+'</script>'
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', ld, hub, flags=re.S)

def render_regions(rows):
    """/jaedan 허브 지역 섹션 17개 — 앵커 id=<slug>. 퇴역 페이지(/jaedan-<slug>)는 여기로 301 된다.
    주소·전화는 각 재단 공식 사이트(source_url) 기준, 확인 안 된 칸은 렌더하지 않는다."""
    cards=[]
    for d in rows:
        C=cases_for(d['지역(시도)'])
        li=[]
        if d.get('hq_address'): li.append(f'<li><b>본점</b> {esc(d["hq_address"])}</li>')
        if d.get('phone'): li.append(f'<li><b>대표전화</b> <a href="{tel(d["phone"])}">{esc(d["phone"])}</a></li>')
        li.append(f'<li><b>홈페이지</b> <a href="{esc(d["홈페이지 링크"])}" target="_blank" rel="noopener">{esc(re.sub(r"^https?://(www\.)?", "", d["홈페이지 링크"]).rstrip("/"))}</a></li>')
        if d.get('source_url') and d.get('confirmed_at'):
            li.append(f'<li class="asof">확인일 {esc(d["confirmed_at"])} · <a href="{esc(d["source_url"])}" target="_blank" rel="noopener">재단 공식 안내</a></li>')
        if d['사이트 공개'].upper()=='Y':
            li.append(f'<li><a href="/{d["재단ID"]}">{esc(d["지역(시도)"])} 재단 상세 안내와 받은 사례 {len(C)}건 →</a></li>')
        elif C:
            refs=' · '.join(f'<a href="/cases#case-{escape(r["사례ID"], quote=True)}">사례 {escape(r["사례ID"])}</a>' for r in C[:3])
            li.append(f'<li>공개 원장 사례 {len(C)}건: {refs}</li>')
        cards.append(f'<section class="jd-region" id="{slug(d)}" aria-labelledby="jd-r-{slug(d)}"><h3 id="jd-r-{slug(d)}">{esc(d["재단명"])}</h3><ul>{"".join(li)}</ul></section>')
    return ('<h2>시도별 재단 본점·연락처</h2>\n<p>보증 신청은 사업장 소재지의 재단에서 합니다. 본점 주소와 대표전화는 각 재단 공식 사이트 기준이며 확인일을 함께 적었습니다. 공개 사례가 있는 지역은 상세 페이지에 받은 사례와 지역 공고를 정리했습니다.</p>\n'
            '<div class="jd-regions">'+''.join(cards)+'</div>')

def build():
    ALL=load_all()
    J=[d for d in ALL if d['사이트 공개'].upper()=='Y']
    style=re.search(r'<style>.*?</style>', (ROOT/'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    src=(ROOT/'jaedan.html').read_text(encoding='utf-8')
    hdr=re.search(r'<header>.*?</header>', src, re.S).group(0)
    foot=re.search(r'<footer>.*?</footer>', src, re.S).group(0)
    TBL='<style>.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}table{border-collapse:collapse;width:100%;min-width:520px;font-size:.88rem}th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}tr:nth-child(even) td{background:#FAFBFD}td a{color:var(--blue-deep);text-decoration:underline}.cta-inline{display:flex;flex-wrap:wrap;align-items:center;gap:14px;background:var(--navy);border-radius:12px;padding:18px 22px;margin:26px 0}.cta-inline p{color:#EAF0FA;margin:0;font-size:.94rem;flex:1 1 260px;line-height:1.55}.cta-inline p b{color:#fff}.cta-inline .tel{color:#fff;text-decoration:underline;font-size:.9rem;white-space:nowrap}table.kv{min-width:0}.proof{background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--blue-deep);border-radius:10px;padding:16px 20px;margin:22px 0}'+FORM_CSS+'</style>'
    tails=title_tails(J)
    for d in J:
        C=cases_for(d['지역(시도)'])
        amts=[int(r['실행 금액(만원)']) for r in C]
        rates=rate_range([r['금리'] for r in C])
        title_txt=f"{d['재단명']} 사업자대출, {tails[d['재단ID']]}"
        rows_html="".join(f'<tr><td>{r["실행 연월"]}</td><td>{esc(r["업종"]) or "—"}</td><td>{esc(r["자금명"])[:28]}</td><td>{won2(r["실행 금액(만원)"])}</td><td>{esc(r["금리"]) or "—"}</td><td><a href="/cases#case-{r["사례ID"]}">받은 사례</a></td></tr>' for r in sorted(C, key=lambda x:(x["실행 연월"], x["사례ID"]), reverse=True)[:10])
        if C:
            meas=(f'<h2>{esc(d["지역(시도)"])} 사업장이 받은 재단 보증부 대출 {len(C)}건</h2>\n<p>공개 원장에서 {esc(d["재단명"])} 보증으로 실행된 사례를 자동으로 모았습니다. 총 {won2(sum(amts))}'+(f' · 금리 {rates}' if rates else '')+f' (각 실행 시점 기준), 최근 10건을 표시합니다. 전체 맥락은 <a href="/cases">받은 사례</a>에서.</p>\n<div class="tablewrap"><table><thead><tr><th>실행</th><th>업종</th><th>상품</th><th>금액</th><th>금리</th><th>근거</th></tr></thead><tbody>{rows_html}</tbody></table></div>')
        else:
            # 사례 없는 지역은 페이지를 두지 않는다(공개 N → /jaedan#<slug> 301). 다른 지역 사례로 채우지 않는다.
            print(f"[재단 빌드 경고] {d['재단ID']}: 공개 사례 0건 — data/jaedan.overlay.csv 에서 공개를 N 으로 바꾸고 _redirects 에 301 을 추가하세요.")
            meas=''
        # 지역 FAQ 2개(시트, 재단 공식 사이트 근거) + 원장 자동 FAQ 1개. 공통 FAQ(신용점수·진행·준비)는 /jaedan 허브에만 둔다.
        faq=[(d[f'faq{i}_q'], d[f'faq{i}_a']) for i in (1,2) if d.get(f'faq{i}_q') and d.get(f'faq{i}_a')]
        if C:
            last=C[0]
            faq.append((f"{d['재단명']} 보증으로 실제 받은 금액과 금리는 어느 정도였나요?",
                        f"공개 원장 기준 {d['지역(시도)']} 사업장의 재단 보증부 대출 사례는 {len(C)}건이고, 받은 금액은 {won2(min(amts))}~{won2(max(amts))}"+(f", 금리는 {rates}" if rates else '')+f"입니다(각 실행 시점 기준). 가장 최근 사례는 {last['실행 연월']} {last['자금명']} {won2(last['실행 금액(만원)'])}입니다. 과거 사례는 현재 신청 한도·금리를 뜻하지 않습니다."))
        facts_html=notice_facts(d)
        faq_ld=json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}, ensure_ascii=False)
        svc=json.dumps({"@context":"https://schema.org","@type":"Service","name":f"{d['재단명']} 보증부 대출 진단·실행 지원","serviceType":"정책자금·보증부 대출 진단 및 실행 지원","provider":{"@type":"Organization","@id":"https://bmaker.kr/#org","name":"비즈니스 메이커","url":"https://bmaker.kr/"},"areaServed":d['지역(시도)'],"url":f"https://bmaker.kr/{d['재단ID']}"}, ensure_ascii=False)
        crumb=json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"홈","item":"https://bmaker.kr/"},{"@type":"ListItem","position":2,"name":"신용보증재단","item":"https://bmaker.kr/jaedan"},{"@type":"ListItem","position":3,"name":d['재단명'],"item":f"https://bmaker.kr/{d['재단ID']}"}]}, ensure_ascii=False)
        inline_form = form_html('/' + d['재단ID'], d['재단명'])
        faq_html="".join(f'<details><summary>{q}</summary><div class="body">{a.replace("저신용·재창업 가이드", chr(60)+chr(97)+chr(32)+"href=\'/jeosinyong\'"+chr(62)+"저신용·재창업 가이드"+chr(60)+"/a"+chr(62))}</div></details>' for q,a in faq)
        memo=(' — '+esc(d['한 줄 메모'])) if d['한 줄 메모'] else ''
        rc=region_cities(d['재단ID'])
        cities_html=('<h2>이 지역 도시별 창구</h2>\n<p>도시마다 담당 지점·소상공인지원센터·시 자체 자금 공고를 공식 출처와 함께 정리했습니다.</p>\n<ul>'
                     +''.join(f'<li><a href="/region/{cid}">{esc(name)} 소상공인 정책자금 창구</a></li>' for cid,name in rc)+'</ul>\n    ') if rc else ''   # 도시 없는 재단은 한 글자도 바뀌지 않게
        consulting = region_config(d['지역(시도)'], d['재단명'])
        page=f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title_txt)}</title>
<meta name="description" content="{esc(description(d, C, rates))}">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(title_txt)}">
<meta property="og:description" content="{esc(description(d, C, rates))}">
<meta property="og:url" content="https://bmaker.kr/{d['재단ID']}">
<meta property="og:image" content="https://bmaker.kr/assets/og.png">
<meta property="og:locale" content="ko_KR">
<link rel="canonical" href="https://bmaker.kr/{d['재단ID']}">
<link rel="icon" type="image/png" href="assets/icon-192.png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap">
<script type="application/ld+json">{svc}</script>
<script type="application/ld+json">{crumb}</script>
<script type="application/ld+json">{faq_ld}</script>
{style}
{TBL}
{STYLESHEET}
</head>
<body data-service="policy">
{hdr}
<section class="hero sc-hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> › <a href="/jaedan">신용보증재단</a> › {esc(d['재단명'])}</p>
    {hero_content('<h1 class="serif">' + esc(d['재단명']) + ' 사업자대출,<br class="pc"> 보증서로 은행 문턱을 넘습니다</h1>', '<p>사업장이 ' + esc(d['지역(시도)']) + '라면 이 재단이 창구입니다' + memo + '.</p>', consulting)}
  </div>
</section>
<main>
  <div class="wrap">
    {service_content(consulting)}
    {inline_form}
    <h2 class="sc-guide-heading" id="sc-guide">지역 재단 안내와 받은 사례</h2>
    <p><b>짧은 답:</b> {esc(d['재단명'])}은 {esc(d['지역(시도)'])}에 사업장이 있는 소상공인·소기업의 보증 창구입니다. 재단 보증 심사와 은행 대출 심사가 따로 있고 이차보전은 사업별 예산에 따라 달라지는 등, 공통 절차는 <a href="/jaedan">신용보증재단 사업자대출 안내</a>에 정리했습니다. 이 페이지는 {esc(d['지역(시도)'])} 재단 공고와 받은 사례만 다룹니다.</p>
    {facts_html}
    {meas}
{cities_html.rstrip()}
    <div class="cta-inline"><p><b>이 지역 재단 대출, 내 조건에 되는지</b> — 업종·매출·신용·이력만 주시면 방향을 잡아드립니다. 가능성이 낮으면 낮다고 먼저 말씀드립니다.</p><a class="btn btn-kakao" href="https://pf.kakao.com/_GKuxfn/chat" target="_blank" rel="noopener">카카오톡 무료 진단</a><a class="tel" href="tel:1666-2425">전화 1666-2425</a></div>
    <div class="proof"><p><b>과거 사례는 현재 심사 결과와 다릅니다.</b> 기존 보증과 현재 사업 현황, 해당 상품의 요건을 확인해야 합니다. <a href="/geojeol">신청 전 확인할 사유와 준비 순서</a>를 참고하세요.</p></div>
    <div class="callout"><p>보증부 대출은 대출이며 상환 의무가 있습니다. 보증·대출 승인 여부와 조건은 재단과 은행이 결정하고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. {FEE}</p></div>
    <h2>자주 묻는 질문</h2>
    {faq_html}
    {byline_html(esc(max(x for x in (d['최종 확인일'], d.get('confirmed_at',''), d.get('notice_confirmed_at','')) if x)))}
    <div class="related">
      <p class="t">함께 보기</p>
      <a href="/jaedan">신용보증재단 안내와 지역별 받은 사례</a>
      <a href="/schedule">정책자금 접수 일정</a>
      <a href="/cases">받은 사례</a>
      <a href="/sanghwan">상환 구조 가이드</a>
    </div>
    <div class="cta-box">
      <h3 class="serif">{esc(d['지역(시도)'])} 사업장, 내 조건이면 되는지</h3>
      <p>업종·매출·신용·이력을 주시면 재단 트랙 가능성과 예상 구조를 무료로 진단해 드립니다. 가능성이 낮으면 낮다고 먼저 말씀드립니다.</p>
      <a class="btn btn-apply" href="#apply" data-cta-location="article_end">무료 진단 신청</a>
      <a class="btn btn-kakao" href="https://pf.kakao.com/_GKuxfn/chat" target="_blank" rel="noopener">카카오톡 무료 진단</a>
      <a class="btn btn-tel" href="tel:1666-2425">전화 1666-2425</a>
    </div>
  </div>
</main>
{foot}
<script src="/assets/conversion.js" defer></script>
</body>
</html>
'''
        if '갚' in page: die(f"{d['재단ID']}: '갚' 포함")
        if re.search(r'보장(?!하지)', page.replace('결과를 보장하지','')): die(f"{d['재단ID']}: '보장' 포함")
        (ROOT/f"{d['재단ID']}.html").write_text(page, encoding='utf-8')
    # /jaedan 허브 지역 그리드 (마커 사이 주입)
    hub=(ROOT/'jaedan.html').read_text(encoding='utf-8')
    # Retire the hand-maintained legacy table once; subsequent builds replace only this block.
    evidence = '<!-- jaedan-evidence:start -->' + render_hub_cases(all_jd()) + '<!-- jaedan-evidence:end -->'
    if '<!-- jaedan-evidence:start -->' in hub:
        hub = re.sub(r'<!-- jaedan-evidence:start -->.*?<!-- jaedan-evidence:end -->', lambda _: evidence, hub, flags=re.S)
    else:
        hub = re.sub(r'<h2>기록된 재단 실측.*?(?=\s*<!--REGIONS-->)', lambda _: evidence, hub, count=1, flags=re.S)
    hub = re.sub(r'<div class="proof"><p><b>저신용·재창업이어도.*?</div>', '<div class="proof"><p><b>과거 사례와 현재 심사는 구분합니다.</b> 개인별 가능 여부는 현재 사업 현황, 기존 보증, 신청 상품의 요건에 따라 달라집니다. <a href="/geojeol">신청 전 확인할 사유와 준비 순서</a>를 함께 살펴보세요.</p></div>', hub, count=1, flags=re.S)
    answers = {
        '신용점수가 낮아도 되나요?': '신용점수 하나만으로 지원 여부를 판단할 수 없습니다. 현재 사업 현황, 기존 보증·대출, 신청 상품의 제외 조건을 확인해야 하며 최종 보증·대출 여부는 재단과 은행이 결정합니다.',
        '한도는 얼마까지 되나요?': '한도는 신청 상품과 기업 심사에 따라 정해집니다. 위 표의 받은 금액은 과거 사례이며 현재 신청 한도가 아닙니다. 기존 보증 이용액·자금 용도·기업 현황을 준비해 재단과 취급 은행의 현행 기준을 확인하세요.'}
    for question, answer in answers.items():
        hub = re.sub(r'(<summary>'+re.escape(question)+r'</summary><div class="body">).*?(</div>)', lambda m:m[1]+answer+m[2], hub, flags=re.S)
    def sync_faq(match):
        data=json.loads(match[1])
        if data.get('@type') == 'FAQPage':
            for q in data['mainEntity']:
                if q['name'] in answers:q['acceptedAnswer']['text']=answers[q['name']]
        return '<script type="application/ld+json">'+json.dumps(data,ensure_ascii=False)+'</script>'
    hub = re.sub(r'<script type="application/ld\+json">(.*?)</script>',sync_faq,hub,flags=re.S)
    hub = upsert_hub_faq(hub)
    if '<!--REGIONS-->' in hub:
        hub=re.sub(r'<!--REGIONS-->.*?<!--/REGIONS-->', lambda _: '<!--REGIONS-->\n'+render_regions(ALL)+'\n<!--/REGIONS-->', hub, flags=re.S)
        (ROOT/'jaedan.html').write_text(hub, encoding='utf-8')
    # 퇴역(공개 N) 페이지 — 파일 삭제(실존 파일이 _redirects 보다 먼저 서빙된다), sitemap 에서 제거
    sm=(ROOT/'sitemap.xml').read_text(encoding='utf-8')
    for d in ALL:
        if d in J: continue
        (ROOT/f"{d['재단ID']}.html").unlink(missing_ok=True)
        sm=re.sub(r'[ \t]*<url>\s*<loc>'+re.escape(f"https://bmaker.kr/{d['재단ID']}")+r'</loc>.*?</url>\n?', '', sm, flags=re.S)
    # sitemap upsert
    for d in J:
        loc=f"https://bmaker.kr/{d['재단ID']}"
        if loc+"</loc>" in sm:
            sm=re.sub(r'(<loc>'+re.escape(loc)+r'</loc><lastmod>)[^<]+', r'\g<1>'+str(TODAY), sm)
        else:
            sm=sm.replace('</urlset>', f'  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>0.6</priority></url>\n</urlset>')
    (ROOT/'sitemap.xml').write_text(sm, encoding='utf-8')
    # llms.txt 재단 줄 upsert
    withm_regions=[d['지역(시도)'] for d in J if cases_for(d['지역(시도)'])]
    lt=(ROOT/'llms.txt').read_text(encoding='utf-8')
    line=f"- [지역 신용보증재단 페이지 {len(J)}종](https://bmaker.kr/jaedan): 시도별 재단 사업자대출 안내 — 실측 기록 보유 {len(withm_regions)}개 지역({'·'.join(withm_regions)}), 17개 재단 본점·연락처는 /jaedan 지역 섹션"
    if re.search(r'- \[지역 신용보증재단 페이지 \d+종\]', lt): lt=re.sub(r'- \[지역 신용보증재단 페이지 \d+종\][^\n]*', lambda _: line, lt)
    else: lt=lt.replace('- [기술보증기금 대출]', line+'\n- [기술보증기금 대출]')
    (ROOT/'llms.txt').write_text(lt, encoding='utf-8')
    withm=sum(1 for d in J if cases_for(d['지역(시도)']))
    print(f"[재단 빌드 OK] {len(J)}개 지역 페이지 생성 (실측 보유 {withm}개 지역, 기준일 {TODAY})")

if __name__=='__main__':
    build()
