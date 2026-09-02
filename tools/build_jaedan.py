#!/usr/bin/env python3
"""지역 신용보증재단 페이지 17종 빌드 — data/jaedan.source.csv 한 줄 = 페이지 하나.
실행 기록에서 (기관에 '재단' 포함 & 지역 일치) 사례를 자동 연결하고, /jaedan 허브의 지역 그리드를 마커 사이에 주입한다.
실행: python tools/build_jaedan.py
"""
import csv, json, re, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TODAY = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).date()  # KST
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
            if r['사이트 공개'].upper()=='Y' and '재단' in r['기관']:
                out.append(r)
    out.sort(key=lambda r:(r['실행 연월'], r['사례ID']), reverse=True)
    return out

def cases_for(region):
    out=[]
    with open(ROOT/'data'/'cases.source.csv',encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if r['사이트 공개'].upper()=='Y' and '재단' in r['기관'] and r['지역(시도)']==region:
                out.append(r)
    out.sort(key=lambda r:(r['실행 연월'], r['사례ID']), reverse=True)
    return out

def build():
    J=load()
    style=re.search(r'<style>.*?</style>', (ROOT/'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    src=(ROOT/'jaedan.html').read_text(encoding='utf-8')
    hdr=re.search(r'<header>.*?</header>', src, re.S).group(0)
    foot=re.search(r'<footer>.*?</footer>', src, re.S).group(0)
    TBL='<style>.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}table{border-collapse:collapse;width:100%;min-width:520px;font-size:.88rem}th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}tr:nth-child(even) td{background:#FAFBFD}td a{color:var(--blue-deep);text-decoration:underline}.proof{background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--blue-deep);border-radius:10px;padding:16px 20px;margin:22px 0}</style>'
    for d in J:
        C=cases_for(d['지역(시도)'])
        amts=[int(r['실행 금액(만원)']) for r in C]
        rates=rate_range([r['금리'] for r in C])
        rows_html="".join(f'<tr><td>{r["실행 연월"]}</td><td>{esc(r["업종"]) or "—"}</td><td>{esc(r["자금명"])[:28]}</td><td>{won2(r["실행 금액(만원)"])}</td><td>{esc(r["금리"]) or "—"}</td><td><a href="/cases#case-{r["사례ID"]}">실행 기록</a></td></tr>' for r in C)
        if C:
            meas=(f'<h2>{esc(d["재단명"])} 실측 — 실행 기록</h2>\n<p>저희가 {esc(d["지역(시도)"])} 사업장으로 실제 실행한 재단 보증부 대출입니다. 총 {len(C)}건 · {won2(sum(amts))}'+(f' · 금리 {rates}' if rates else '')+f' (각 실행 시점 기준). 전체 맥락은 <a href="/cases">공개 실행 기록</a>에서.</p>\n<div class="tablewrap"><table><thead><tr><th>실행</th><th>업종</th><th>상품</th><th>금액</th><th>금리</th><th>근거</th></tr></thead><tbody>{rows_html}</tbody></table></div>')
        else:
            A=all_jd(); aa=[int(r['실행 금액(만원)']) for r in A]
            ar=rate_range([r['금리'] for r in A])
            arow="".join(f'<tr><td>{r["지역(시도)"]}</td><td>{esc(r["자금명"])[:24]}</td><td>{won2(r["실행 금액(만원)"])}</td><td>{esc(r["금리"]) or "—"}</td><td><a href="/cases#case-{r["사례ID"]}">기록</a></td></tr>' for r in A[:3])
            meas=(f'<h2>{esc(d["재단명"])} 실행 기록</h2>\n<p>{esc(d["지역(시도)"])} 지역으로 수록된 건은 아직 없습니다. 다만 재단 경로 자체는 저희가 가장 많이 실행한 트랙입니다 — 전국 재단 공개 실행 기록 {len(A)}건 · {won2(sum(aa))}'
                  +(f' · 금리 {ar}' if ar else '')
                  +f' (각 실행 시점 기준). 보증 심사 기준과 진행 구조는 지역이 달라도 같습니다.</p>\n'
                  +'<div class="tablewrap"><table><thead><tr><th>지역</th><th>상품</th><th>금액</th><th>금리</th><th>근거</th></tr></thead><tbody>'+arow+'</tbody></table></div>\n'
                  +f'<p><a href="/cases">공개 실행 기록 전체 →</a> {esc(d["지역(시도)"])} 실행 건은 고객 동의·증빙이 확보되는 대로 추가합니다.</p>')
        faq=[(f"{d['지역(시도)']} 사업자인데 이 재단으로 가면 되나요?", f"네, 재단은 사업장 소재지 기준입니다. 사업장이 {d['지역(시도)']}에 있으면 {d['재단명']}이 창구이고, 지자체 이차보전(이자 지원) 상품도 해당 지자체 소재 사업자만 대상입니다."),
             ("신용점수가 낮아도 가능한가요?", "재단 보증은 신용점수만으로 결정되지 않습니다. 저희 실행 기록에는 신용 600점대에서 재단 보증부 대출이 실행된 기록이 있습니다. 다만 현재 금융 연체 중이거나 세금 체납이 정리되지 않았다면 그 회복이 먼저입니다 — 기준은 저신용·재창업 가이드에 실측으로 정리돼 있습니다."),
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
<title>{esc(d['재단명'])} 사업자대출 — 보증부 대출 조건·실측 (2026) | 비즈니스 메이커</title>
<meta name="description" content="{esc(d['재단명'])}({esc(d['지역(시도)'])}) 보증부 사업자대출 — 구조·대상·진행 방법{('과 실제 실행 기록 '+str(len(C))+'건') if C else ''}. 사업장 소재지 기준 이용, 지자체 이차보전 연계까지.">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(d['재단명'])} 사업자대출 — 조건·실측 (2026)">
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
    <p><b>짧은 답:</b> {esc(d['재단명'])}은 {esc(d['지역(시도)'])} 소재 소상공인·소기업을 위한 보증 기관입니다. 재단이 보증서를 발급하면 은행이 대출을 실행하는 구조라, 담보가 없어도 은행 대출이 열립니다. 지자체 이차보전(이자 지원) 상품이 결합되면 체감 금리가 크게 내려가며, 이용 자격의 핵심은 하나 — <b>사업장 소재지가 {esc(d['지역(시도)'])}인가</b>입니다.</p>
    <p class="asof">최종 확인일 {esc(d['최종 확인일'])} · 상품·요건은 각 공고 기준 — <a href="{esc(d['홈페이지 링크'])}" target="_blank" rel="noopener">공식 안내 확인 →</a> · 접수 중 자금은 <a href="/schedule">일정 페이지</a></p>
    {meas}
    <div class="proof"><p><b>저신용·재창업이어도 재단 경로는 열려 있는 편입니다.</b> 실행 기록의 재단 실행 건에는 신용 600점대, 폐업 후 재창업 사례가 포함돼 있습니다 — <a href="/jeosinyong">저신용·재창업 가이드</a>에서 실측으로 확인하세요.</p></div>
    <div class="callout"><p>보증부 대출은 대출이며 상환 의무가 있습니다. 보증·대출 승인 여부와 조건은 재단과 은행이 결정하고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. {FEE}</p></div>
    <h2>자주 묻는 질문</h2>
    {faq_html}
    <div class="related">
      <p class="t">함께 보기</p>
      <a href="/jaedan">신용보증재단 안내 (9개 지역 실측)</a>
      <a href="/schedule">정책자금 접수 일정</a>
      <a href="/cases">실행 기록</a>
      <a href="/sanghwan">상환 구조 가이드</a>
    </div>
    <div class="cta-box">
      <h3 class="serif">{esc(d['지역(시도)'])} 사업장, 내 조건이면 되는지</h3>
      <p>업종·매출·신용·이력을 주시면 재단 트랙 가능성과 예상 구조를 무료로 진단해 드립니다. 가능성이 낮으면 낮다고 먼저 말씀드립니다.</p>
      <a class="btn btn-kakao" href="http://pf.kakao.com/_GKuxfn/chat" target="_blank" rel="noopener">카카오톡 무료 진단</a>
      <a class="btn btn-tel" href="tel:1666-2425">전화 1666-2425</a>
    </div>
  </div>
</main>
{foot}
</body>
</html>
'''
        if '갚' in page: die(f"{d['재단ID']}: '갚' 포함")
        if re.search(r'보장(?!하지)', page.replace('결과를 보장하지','')): die(f"{d['재단ID']}: '보장' 포함")
        (ROOT/f"{d['재단ID']}.html").write_text(page, encoding='utf-8')
    # /jaedan 허브 지역 그리드 (마커 사이 주입)
    hub=(ROOT/'jaedan.html').read_text(encoding='utf-8')
    if '<!--REGIONS-->' in hub:
        cells=[]
        for d in J:
            n=len(cases_for(d['지역(시도)']))
            tag=f' <span style="color:var(--blue-deep);font-size:.8rem">실측 {n}건</span>' if n else ''
            cells.append(f'<a href="/{d["재단ID"]}" style="display:block;background:#fff;border:1px solid var(--line);border-radius:10px;padding:12px 14px;text-decoration:none;color:var(--navy);font-weight:600;font-size:.92rem">{esc(d["재단명"])}{tag}</a>')
        grid=('<h2>지역별 재단 페이지</h2>\n<p>사업장 소재지의 재단을 선택하세요 — 실측이 있는 지역은 해당 기록이 함께 실려 있습니다.</p>\n'
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
