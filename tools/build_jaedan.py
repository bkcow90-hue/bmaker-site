#!/usr/bin/env python3
"""지역 신용보증재단 페이지 17종 빌드 — data/jaedan.source.csv 한 줄 = 페이지 하나.
실행 기록에서 (기관에 '재단' 포함 & 지역 일치) 사례를 자동 연결하고, /jaedan 허브의 지역 그리드를 마커 사이에 주입한다.
실행: python tools/build_jaedan.py
"""
import csv, json, re, sys, datetime
from html import escape
from pathlib import Path
from builddate import build_date
ROOT = Path(__file__).resolve().parent.parent
TODAY = build_date()  # BUILD_DATE 있으면 그 날짜, 없으면 Asia/Seoul 오늘 (tools/builddate.py)
FEE = '착수금·진행비 등 실행 전 비용은 일절 받지 않고, 자금이 실제 실행된 경우에만 성공보수를 받습니다.'
def die(m): print(f"[재단 빌드 실패] {m}"); sys.exit(1)
def won2(m):
    e,man=divmod(int(m),10000)
    return ((f"{e}억"+((" " if man else "")+f"{man:,}만" if man else ""))+"원") if e else f"{man:,}만원"
def esc(s): return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def load():
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
    return [d for d in rows if d['사이트 공개'].upper()=='Y']

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
                out.append(r)
    out.sort(key=lambda r:(r['실행 연월'], r['사례ID']), reverse=True)
    return out

def cases_for(region):
    return [r for r in all_jd() if r['지역(시도)'] == region]


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

def build():
    J=load()
    style=re.search(r'<style>.*?</style>', (ROOT/'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    src=(ROOT/'jaedan.html').read_text(encoding='utf-8')
    hdr=re.search(r'<header>.*?</header>', src, re.S).group(0)
    foot=re.search(r'<footer>.*?</footer>', src, re.S).group(0)
    TBL='<style>.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}table{border-collapse:collapse;width:100%;min-width:520px;font-size:.88rem}th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}tr:nth-child(even) td{background:#FAFBFD}td a{color:var(--blue-deep);text-decoration:underline}.cta-inline{display:flex;flex-wrap:wrap;align-items:center;gap:14px;background:var(--navy);border-radius:12px;padding:18px 22px;margin:26px 0}.cta-inline p{color:#EAF0FA;margin:0;font-size:.94rem;flex:1 1 260px;line-height:1.55}.cta-inline p b{color:#fff}.cta-inline .tel{color:#fff;text-decoration:underline;font-size:.9rem;white-space:nowrap}.proof{background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--blue-deep);border-radius:10px;padding:16px 20px;margin:22px 0}</style>'
    for d in J:
        C=cases_for(d['지역(시도)'])
        amts=[int(r['실행 금액(만원)']) for r in C]
        rates=rate_range([r['금리'] for r in C])
        rows_html="".join(f'<tr><td>{r["실행 연월"]}</td><td>{esc(r["업종"]) or "—"}</td><td>{esc(r["자금명"])[:28]}</td><td>{won2(r["실행 금액(만원)"])}</td><td>{esc(r["금리"]) or "—"}</td><td><a href="/cases#case-{r["사례ID"]}">실행 기록</a></td></tr>' for r in sorted(C, key=lambda x:(x["실행 연월"], x["사례ID"]), reverse=True)[:10])
        if C:
            meas=(f'<h2>{esc(d["재단명"])} 실측 — 실행 기록</h2>\n<p>저희가 {esc(d["지역(시도)"])} 사업장으로 실제 실행한 재단 보증부 대출입니다. 총 {len(C)}건 · {won2(sum(amts))}'+(f' · 금리 {rates}' if rates else '')+f' (각 실행 시점 기준). 전체 맥락은 <a href="/cases">공개 실행 기록</a>에서.</p>\n<div class="tablewrap"><table><thead><tr><th>실행</th><th>업종</th><th>상품</th><th>금액</th><th>금리</th><th>근거</th></tr></thead><tbody>{rows_html}</tbody></table></div>')
        else:
            A=all_jd(); aa=[int(r['실행 금액(만원)']) for r in A]
            ar=rate_range([r['금리'] for r in A])
            arow="".join(f'<tr><td>{r["지역(시도)"]}</td><td>{esc(r["자금명"])[:24]}</td><td>{won2(r["실행 금액(만원)"])}</td><td>{esc(r["금리"]) or "—"}</td><td><a href="/cases#case-{r["사례ID"]}">기록</a></td></tr>' for r in A[:3])
            meas=(f'<h2>해당 지역 공개 사례 없음 — 전국 재단 사례 참고</h2>\n<p>현재 공개 원장에 {esc(d["지역(시도)"])} 사례는 없습니다. 아래는 다른 지역의 참고 사례이며 해당 지역 실적이 아닙니다. 전국 재단 경로 {len(A)}건 · {won2(sum(aa))}'
                  +(f' · 금리 {ar}' if ar else '')
                  +f' (각 실행 시점 기준). 보증 후 은행 대출이라는 기본 구조와 별개로 지역·상품별 대상과 세부 요건은 다릅니다.</p>\n'
                  +'<div class="tablewrap"><table><thead><tr><th>지역</th><th>상품</th><th>금액</th><th>금리</th><th>근거</th></tr></thead><tbody>'+arow+'</tbody></table></div>\n'
                  +'<p><a href="/cases">공개 실행 기록 전체 보기 →</a></p>')
        faq=[(f"{d['지역(시도)']} 소상공인 대출, 은행과 재단 중 어디부터 알아봐야 하나요?", f"은행 자체 대출과 {d['재단명']} 보증부 대출은 확인하는 절차가 다릅니다. 보증 상품의 신청 창구와 취급 은행을 먼저 확인하고, 기존 보증 이용액·필요 금액·자금 용도를 정리하세요. 이차보전은 해당 사업의 대상·예산·지원 기간을 따로 확인해야 합니다."),
         (f"{d['지역(시도)']} 사업자인데 이 재단으로 가면 되나요?", f"사업장이 {d['지역(시도)']}에 있다면 {d['재단명']}의 안내를 우선 확인하세요. 소재지만으로 대상이 확정되지는 않습니다. 기업 규모, 업종, 기존 보증, 상품별 제외 조건과 접수 상태도 확인해야 합니다."),
             ("신용점수가 낮아도 가능한가요?", "신용점수만으로 가능 여부를 단정할 수 없습니다. 현재 사업 현황, 기존 보증·대출, 신청 상품의 제외 조건을 함께 확인해야 합니다. 최종 보증·대출 여부는 재단과 은행이 결정합니다."),
             ("어떻게 진행되나요?", "재단 보증 심사 → 보증서 발급 → 은행 대출 실행의 3단계입니다. 상환은 거치 후 분할 또는 만기까지 이자만 내는 구조가 일반적이며, 상품과 공고에 따라 다릅니다."),
             ("무엇을 준비해야 하나요?", "사업자등록·매출 증빙·임대차계약 등 기본 서류에 더해, 신청 상품의 공고 요건을 확인해야 합니다. 조건이 되는지부터 무료 진단으로 확인해 드립니다 — 가능성이 낮으면 낮다고 먼저 말씀드립니다.")]
        faq_ld=json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}, ensure_ascii=False)
        svc=json.dumps({"@context":"https://schema.org","@type":"Service","name":f"{d['재단명']} 보증부 대출 진단·실행 지원","serviceType":"정책자금·보증부 대출 진단 및 실행 지원","provider":{"@type":"Organization","@id":"https://bmaker.kr/#org","name":"비즈니스 메이커","url":"https://bmaker.kr/"},"areaServed":d['지역(시도)'],"url":f"https://bmaker.kr/{d['재단ID']}"}, ensure_ascii=False)
        crumb=json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"홈","item":"https://bmaker.kr/"},{"@type":"ListItem","position":2,"name":"신용보증재단","item":"https://bmaker.kr/jaedan"},{"@type":"ListItem","position":3,"name":d['재단명'],"item":f"https://bmaker.kr/{d['재단ID']}"}]}, ensure_ascii=False)
        faq_html="".join(f'<details><summary>{q}</summary><div class="body">{a.replace("저신용·재창업 가이드", chr(60)+chr(97)+chr(32)+"href=\'/jeosinyong\'"+chr(62)+"저신용·재창업 가이드"+chr(60)+"/a"+chr(62))}</div></details>' for q,a in faq)
        memo=(' — '+esc(d['한 줄 메모'])) if d['한 줄 메모'] else ''
        page=f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(d['재단명'])} 사업자대출 2026 — {esc(d['지역(시도)'])} 소상공인 대출 조건·보증 절차·실측 금리</title>
<meta name="description" content="{esc(d['지역(시도)'])} 소상공인 대출 알아보시나요? {esc(d['재단명'])} 보증부 사업자대출 — 구조·대상·진행 방법{('과 실제 실행 기록 '+str(len(C))+'건') if C else ''}. 사업장 소재지 기준 이용, 지자체 이차보전 연계까지.">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(d['재단명'])} — {esc(d['지역(시도)'])} 소상공인 대출·사업자대출 (2026)">
<meta property="og:description" content="{esc(d['지역(시도)'])} 사업장 보증부 대출{(' · 실측 '+str(len(C))+'건') if C else ''}">
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
</head>
<body>
{hdr}
<section class="hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> › <a href="/jaedan">신용보증재단</a> › {esc(d['재단명'])}</p>
    <h1 class="serif">{esc(d['재단명'])} 사업자대출,<br class="pc"> 보증서로 은행 문턱을 넘습니다</h1>
    <p>사업장이 {esc(d['지역(시도)'])}라면 이 재단이 창구입니다{memo}.</p>
  </div>
</section>
<main>
  <div class="wrap">
    <p><b>짧은 답:</b> {esc(d['재단명'])}은 {esc(d['지역(시도)'])} 소재 소상공인·소기업 등이 보증 상담을 확인할 기관입니다. 보증기관 심사와 은행 대출 심사는 구분되며 보증만으로 대출 실행이 확정되는 것은 아닙니다. 사업장 소재지뿐 아니라 업종·기업 규모·기존 보증·상품별 제외 조건을 확인하세요. 지자체 이차보전(이자 지원)은 해당 사업의 대상·예산·지원 기간에 따라 적용 여부가 달라집니다.</p>
    <p class="asof">최종 확인일 {esc(d['최종 확인일'])} · 상품·요건은 각 공고 기준 — <a href="{esc(d['홈페이지 링크'])}" target="_blank" rel="noopener">공식 안내 확인 →</a> · 접수 중 자금은 <a href="/schedule">일정 페이지</a></p>
    {meas}
    <div class="cta-inline"><p><b>이 지역 재단 대출, 내 조건에 되는지</b> — 업종·매출·신용·이력만 주시면 방향을 잡아드립니다. 가능성이 낮으면 낮다고 먼저 말씀드립니다.</p><a class="btn btn-kakao" href="https://pf.kakao.com/_GKuxfn/chat" target="_blank" rel="noopener">카카오톡 무료 진단</a><a class="tel" href="tel:1666-2425">전화 1666-2425</a></div>
    <div class="proof"><p><b>과거 사례는 현재 심사 결과와 다릅니다.</b> 기존 보증과 현재 사업 현황, 해당 상품의 요건을 확인해야 합니다. <a href="/geojeol">신청 전 확인할 사유와 준비 순서</a>를 참고하세요.</p></div>
    <div class="callout"><p>보증부 대출은 대출이며 상환 의무가 있습니다. 보증·대출 승인 여부와 조건은 재단과 은행이 결정하고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. {FEE}</p></div>
    <h2>자주 묻는 질문</h2>
    {faq_html}
    <div class="related">
      <p class="t">함께 보기</p>
      <a href="/jaedan">신용보증재단 안내와 지역별 받은 사례</a>
      <a href="/schedule">정책자금 접수 일정</a>
      <a href="/cases">실행 기록</a>
      <a href="/sanghwan">상환 구조 가이드</a>
    </div>
    <div class="cta-box">
      <h3 class="serif">{esc(d['지역(시도)'])} 사업장, 내 조건이면 되는지</h3>
      <p>업종·매출·신용·이력을 주시면 재단 트랙 가능성과 예상 구조를 무료로 진단해 드립니다. 가능성이 낮으면 낮다고 먼저 말씀드립니다.</p>
      <a class="btn btn-apply" href="/#apply" data-cta-location="article_end">내 조건 무료 상담 신청</a>
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
    if '<!--REGIONS-->' in hub:
        cells=[]
        for d in J:
            n=len(cases_for(d['지역(시도)']))
            tag=f' <span style="color:var(--blue-deep);font-size:.8rem">실측 {n}건</span>' if n else ''
            cells.append(f'<a href="/{d["재단ID"]}" style="display:block;background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--navy);font-weight:600;font-size:.92rem">{esc(d["재단명"])}{tag}</a>')
        grid=('<h2>지역별 재단 페이지</h2>\n<p>지역 소상공인 대출·사업자 대출의 공적 경로를 시도별로 정리했습니다 — 사업장 소재지의 재단을 선택하세요. 실측이 있는 지역은 해당 기록이 함께 실려 있습니다.</p>\n'
              '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:10px;margin:16px 0 26px">'+''.join(cells)+'</div>')
        hub=re.sub(r'<!--REGIONS-->.*?<!--/REGIONS-->', '<!--REGIONS-->\n'+grid+'\n<!--/REGIONS-->', hub, flags=re.S)
        (ROOT/'jaedan.html').write_text(hub, encoding='utf-8')
    # sitemap upsert
    sm=(ROOT/'sitemap.xml').read_text(encoding='utf-8')
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
    line=f"- [지역 신용보증재단 페이지 17종](https://bmaker.kr/jaedan): 시도별 재단 사업자대출 안내 — 실측 기록 보유 {len(withm_regions)}개 지역({'·'.join(withm_regions)})"
    if '- [지역 신용보증재단 페이지 17종]' in lt: lt=re.sub(r'- \[지역 신용보증재단 페이지 17종\][^\n]*', line, lt)
    else: lt=lt.replace('- [기술보증기금 대출]', line+'\n- [기술보증기금 대출]')
    (ROOT/'llms.txt').write_text(lt, encoding='utf-8')
    withm=sum(1 for d in J if cases_for(d['지역(시도)']))
    print(f"[재단 빌드 OK] {len(J)}개 지역 페이지 생성 (실측 보유 {withm}개 지역, 기준일 {TODAY})")

if __name__=='__main__':
    build()
