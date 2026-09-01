#!/usr/bin/env python3
"""개인사업자 정책자금 총정리 허브(/gaein) 빌드 — 실행 기록(cases.source.csv)과 자금 시트(funds.source.csv)에서
개인사업자 실측·현재 접수 중 자금을 계산해 생성한다. 실행: python tools/build_gaein.py
"""
import csv, json, re, sys, datetime, statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TODAY = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).date()  # KST
FEE = '착수금·진행비 등 실행 전 비용은 일절 받지 않고, 자금이 실제 실행된 경우에만 성공보수를 받습니다.'
def die(m): print(f"[개인사업자 허브 빌드 실패] {m}"); sys.exit(1)
def won2(m):
    e,man=divmod(int(m),10000)
    return ((f"{e}억"+((" " if man else "")+f"{man:,}만" if man else ""))+"원") if e else f"{man:,}만원"
def esc(s): return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
def rate_range(vals):
    nums=[]
    for v in vals:
        m=re.search(r'\d+(?:\.\d+)?', v or '')
        if m: nums.append(float(m.group(0)))
    nums=sorted(set(nums))
    if not nums: return ''
    lo=f"{nums[0]:g}"; hi=f"{nums[-1]:g}"
    return f"연 {lo}%" if lo==hi else f"연 {lo}~{hi}%"
def inst_of(r):
    k=r['기관']
    return '소진공' if '소상공인' in k else '재단' if '재단' in k else '기보' if '기술' in k else '신보' if '신용보증기금' in k else '중진공' if '중소벤처' in k or '중진공' in k else '기타'

def build():
    rows=[r for r in csv.DictReader(open(ROOT/'data'/'cases.source.csv',encoding='utf-8-sig',newline='')) if r['사이트 공개'].upper()=='Y']
    ind=[r for r in rows if r['사업 형태'].strip()=='개인']
    corp=[r for r in rows if r['사업 형태'].strip()=='법인']
    if not ind: die("개인사업자 실행 건이 없습니다.")
    a=[int(r['실행 금액(만원)']) for r in ind]; d=[float(r['소요일']) for r in ind if r['소요일']]
    N=len(ind); TOT=won2(sum(a)); MED=won2(int(statistics.median(a))); LO=won2(min(a)); HI=won2(max(a)); DMED=int(statistics.median(d)) if d else None
    cnt={k:sum(1 for r in ind if inst_of(r)==k) for k in ('재단','소진공','신보','기보','중진공')}
    low=sum(1 for r in ind if r['신용점수 구간'] in ('600점대','500점대 이하'))
    rest=sum(1 for r in ind if r['폐업 이력'].strip() in ('있음','재창업'))
    tax=sum(1 for r in ind if r['체납 이력'].strip()=='있음')
    young=sum(1 for r in ind if r['업력(년)'] and float(r['업력(년)'])<=1)
    small=sum(1 for r in ind if '3천만원 미만' in r['연매출 구간'])
    rr_all=rate_range([r['금리'] for r in ind])
    rr={k:rate_range([r['금리'] for r in ind if inst_of(r)==k]) for k in ('재단','소진공','신보')}
    recent=sorted(ind, key=lambda r:(r['실행 연월'], r['사례ID']), reverse=True)[:8]
    # 현재 접수 중 자금 (자금 시트 기준, 소진형/마감일 계산은 build_funds 와 동일 규칙)
    open_funds=[]
    fp=ROOT/'data'/'funds.source.csv'
    if fp.exists():
        for f in csv.DictReader(open(fp,encoding='utf-8-sig',newline='')):
            f={k:(v or '').strip() for k,v in f.items() if k}
            if f.get('사이트 공개','').upper()!='Y': continue
            s,e=f.get('접수 시작일',''),f.get('접수 마감일','')
            try:
                ok = f.get('접수 상태')=='상시' or (s and datetime.date.fromisoformat(s)<=TODAY and (('소진' in e) or (e and datetime.date.fromisoformat(e)>=TODAY)))
            except ValueError: ok=False
            if ok: open_funds.append(f)
    style=re.search(r'<style>.*?</style>', (ROOT/'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    src=(ROOT/'jaedan.html').read_text(encoding='utf-8')
    hdr=re.search(r'<header>.*?</header>', src, re.S).group(0); foot=re.search(r'<footer>.*?</footer>', src, re.S).group(0)
    TBL='<style>.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}table{border-collapse:collapse;width:100%;min-width:560px;font-size:.88rem}th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}tr:nth-child(even) td{background:#FAFBFD}td a{color:var(--blue-deep);text-decoration:underline}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px 18px}.card b{display:block;font-size:1.4rem;color:var(--navy);margin-bottom:4px}.card span{font-size:.82rem;color:var(--ink-soft)}.proof{background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--blue-deep);border-radius:10px;padding:16px 20px;margin:22px 0}</style>'
    kinds=[('소진공 직접대출','신용취약·재도전특별·혁신성장촉진·일시적경영애로 등 공단이 직접 실행','신용·이력에 사연이 있어도 조건에 맞는 전용 자금이 있을 때', f"{cnt['소진공']}건 · {rr['소진공'] or '—'}", '<a href="/sojingong">소상공인 정책자금</a> · <a href="/schedule">자금별 페이지</a>'),
           ('지역 신용보증재단 보증부 대출','재단 보증서로 은행이 실행, 지자체 이차보전 결합 시 저금리','담보 없이 은행 대출이 필요한 소상공인·소기업 (개인사업자 실행 최다)', f"{cnt['재단']}건 · {rr['재단'] or '—'}", '<a href="/jaedan">신용보증재단 사업자대출</a> · 17개 지역 페이지'),
           ('신용보증기금·기술보증기금 보증','매출 기반(신보) 또는 기술평가(기보)로 억대 설계','매출이 잡히기 시작했거나 기술이 무기인 사업', f"신보 {cnt['신보']}건 · {rr['신보'] or '—'} / 기보 {cnt['기보']}건", '<a href="/sinbo">신보</a> · <a href="/gibo">기보</a>'),
           ('대리대출·이차보전','일반경영안정·긴급경영안정·소공인특화·대환 등 보증 연계로 은행 실행','기본 운전자금, 고금리 대환, 업종 특화', '자금별 페이지 참조', '<a href="/schedule">접수 일정의 대리대출 섹션</a>')]
    kinds_html="".join(f'<tr><td><b>{a}</b></td><td>{b}</td><td>{c}</td><td style="white-space:nowrap">{d_}</td><td>{e}</td></tr>' for a,b,c,d_,e in kinds)
    rec_html="".join(f'<tr><td>{r["실행 연월"]}</td><td>{esc(r["업종"]) or "—"}</td><td>{inst_of(r)}</td><td>{esc(r["자금명"])[:26]}</td><td>{won2(r["실행 금액(만원)"])}</td><td>{esc(r["금리"]) or "—"}</td><td><a href="/cases#case-{r["사례ID"]}">기록</a></td></tr>' for r in recent)
    open_html=("".join(f'<li><a href="/{esc(f["자금ID"])}">{esc(f["자금명"])}</a> — {esc(f["기관"])}' + (f' · {esc(f["카테고리"])}' if f.get("카테고리") else '') + '</li>' for f in open_funds)) if open_funds else '<li>현재 접수 중으로 확인된 자금이 없습니다 — 일정 페이지에서 예정 자금을 확인하세요.</li>'
    faq=[("개인사업자도 정책자금이 되나요, 법인만 되는 것 아닌가요?", f"됩니다. 저희 공개 실행 기록 {len(rows)}건 중 {N}건이 개인사업자입니다 — 총 {TOT}, 건당 중앙값 {MED}. 소진공 직접대출과 지역 재단 보증부 대출은 오히려 개인사업자가 주 이용자입니다."),
         ("매출이 얼마부터 가능한가요?", f"자금마다 다릅니다. 실행 기록의 개인사업자 {N}건에는 연매출 3천만원 미만 {small}건도 있습니다. 매출보다는 연체·체납 여부와 자금 용도의 정합이 더 자주 결과를 가릅니다."),
         ("사업자등록 1년이 안 됐는데요?", f"업력 1년 이하로 실행된 개인사업자 기록이 {young}건 있습니다. 창업 초기 전용 자금(청년·재도전 등)이나 재단 특례보증이 대상이 되는 경우가 많고, 자금 용도와 집행 계획을 구체적으로 준비하는 것이 관건입니다."),
         ("신용점수가 낮거나 예전에 폐업했어도 되나요?", f"기록으로 답하면 — 개인사업자 실행 {N}건 중 신용 600점대 {low}건, 폐업 후 재창업 {rest}건, 세금 체납 이력 정리 후 실행 {tax}건입니다. 다만 현재 연체·미정리 체납은 먼저 해소해야 합니다. 기준은 저신용·재창업 가이드에 실측으로 정리돼 있습니다."),
         ("얼마나 걸리고, 비용은요?", f"개인사업자 기록 기준 첫 상담 접수부터 정산까지 중앙값 {DMED}일입니다. 저희는 착수금·진행비 등 실행 전 비용을 받지 않고, 실제 실행된 경우에만 성공보수를 받습니다 — 착수금 사기 구별법 페이지에서 업계 관행과 확인법을 볼 수 있습니다.")]
    faq_ld=json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}, ensure_ascii=False)
    art=json.dumps({"@context":"https://schema.org","@type":"Article","headline":f"개인사업자 정책자금 총정리 — 종류·기관·조건·실행 기록 {N}건 (2026)","datePublished":"2026-09-02","dateModified":str(TODAY),"inLanguage":"ko","author":{"@type":"Organization","@id":"https://bmaker.kr/#org","name":"비즈니스 메이커"},"publisher":{"@type":"Organization","@id":"https://bmaker.kr/#org","name":"비즈니스 메이커"},"mainEntityOfPage":"https://bmaker.kr/gaein"}, ensure_ascii=False)
    crumb=json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"홈","item":"https://bmaker.kr/"},{"@type":"ListItem","position":2,"name":"개인사업자 정책자금","item":"https://bmaker.kr/gaein"}]}, ensure_ascii=False)
    faq_html="".join(f'<details><summary>{q}</summary><div class="body">{a.replace("저신용·재창업 가이드", chr(60)+"a href=\'/jeosinyong\'"+chr(62)+"저신용·재창업 가이드"+chr(60)+"/a"+chr(62)).replace("착수금 사기 구별법 페이지", chr(60)+"a href=\'/chaksugeum\'"+chr(62)+"착수금 사기 구별법 페이지"+chr(60)+"/a"+chr(62))}</div></details>' for q,a in faq)
    page=f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>개인사업자 정책자금 총정리 — 종류·기관·조건·실행 기록 {N}건 (2026) | 비즈니스 메이커</title>
<meta name="description" content="개인사업자 정책자금, 됩니까? 공개 실행 기록 {len(rows)}건 중 {N}건이 개인사업자 — 총 {TOT}, 건당 중앙값 {MED}, 소요 중앙값 {DMED}일. 정책자금 종류(직접대출·재단 보증·신보 기보·대리대출)와 기관, 조건, 지금 접수 중인 자금까지 한 장에.">
<meta property="og:type" content="article">
<meta property="og:title" content="개인사업자 정책자금 총정리 — 실행 기록 {N}건 (2026)">
<meta property="og:description" content="총 {TOT} · 중앙값 {MED} · 소요 {DMED}일 — 종류·기관·조건을 실측으로.">
<meta property="og:url" content="https://bmaker.kr/gaein">
<meta property="og:image" content="https://bmaker.kr/assets/og.png">
<meta property="og:locale" content="ko_KR">
<link rel="canonical" href="https://bmaker.kr/gaein">
<link rel="icon" type="image/png" href="assets/icon-192.png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap">
<script type="application/ld+json">{art}</script>
<script type="application/ld+json">{crumb}</script>
<script type="application/ld+json">{faq_ld}</script>
{style}
{TBL}
</head>
<body>
{hdr}
<section class="hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> › 개인사업자 정책자금</p>
    <h1 class="serif">개인사업자 정책자금,<br class="pc"> 종류부터 실행 기록까지 한 장에</h1>
    <p>법인만 되는 제도가 아닙니다 — 공개 실행 기록 {len(rows)}건 중 <b>{N}건이 개인사업자</b>입니다. 총 {TOT}, 건당 중앙값 {MED}, 첫 상담부터 정산까지 중앙값 {DMED}일.</p>
  </div>
</section>
<main>
  <div class="wrap">
    <p><b>짧은 답:</b> 개인사업자가 실제로 쓰는 정책자금(정부지원 대출)은 세 갈래입니다 — ① 소상공인시장진흥공단 <b>직접대출</b>, ② 지역 신용보증재단의 <b>보증부 대출</b>(개인사업자 실행이 가장 많은 경로), ③ 신용보증기금·기술보증기금 <b>보증</b>(매출·기술 기반, 억대 설계). 여기에 은행이 실행하는 대리대출·이차보전 상품이 붙습니다. 어느 갈래가 맞는지는 매출 규모, 신용·이력, 자금 용도로 정해지며, 아래 표와 실행 기록이 그 판단 기준입니다.</p>
    <p class="asof">기준일 {TODAY.year}년 {TODAY.month}월 {TODAY.day}일 · 실측은 <a href="/cases">공개 실행 기록</a>에서 자동 집계되며 기록이 늘면 함께 갱신됩니다.</p>

    <div class="cards">
      <div class="card"><b>{N}건</b><span>개인사업자 실행 (전체 {len(rows)}건 중)</span></div>
      <div class="card"><b>{TOT}</b><span>개인사업자 실행 총액</span></div>
      <div class="card"><b>{MED}</b><span>건당 중앙값 ({LO}~{HI})</span></div>
      <div class="card"><b>{DMED}일</b><span>첫 상담 → 정산 중앙값</span></div>
    </div>

    <h2>정책자금 종류 — 개인사업자 기준</h2>
    <div class="tablewrap"><table><thead><tr><th>갈래</th><th>어떤 자금</th><th>누구에게 맞나</th><th>개인사업자 실측</th><th>상세</th></tr></thead><tbody>{kinds_html}</tbody></table></div>

    <h2>개인사업자 실행 기록 — 최근 {len(recent)}건</h2>
    <div class="tablewrap"><table><thead><tr><th>실행</th><th>업종</th><th>기관</th><th>자금</th><th>금액</th><th>금리</th><th>근거</th></tr></thead><tbody>{rec_html}</tbody></table></div>
    <p>개인사업자 {N}건 전체 금리 범위는 {rr_all}(각 실행 시점 기준)이고, 법인 {len(corp)}건과 비교하면 건당 규모는 작지만 진행 기간은 짧았습니다(개인 중앙값 {DMED}일). 전체 목록과 증빙은 <a href="/cases">공개 실행 기록</a>에 있습니다.</p>

    <h2>개인사업자가 자주 걸리는 조건 — 기록으로 답하면</h2>
    <div class="proof"><p>개인사업자 실행 {N}건 안에는 <b>신용 600점대 {low}건</b>, <b>폐업 후 재창업 {rest}건</b>, <b>세금 체납 이력 정리 후 실행 {tax}건</b>, <b>업력 1년 이하 {young}건</b>, <b>연매출 3천만원 미만 {small}건</b>이 있습니다. 즉 점수·이력·업력이 낮다고 닫히는 제도가 아니라, 현재 연체·미정리 체납처럼 <em>지금</em> 걸리는 조건이 있느냐가 관건입니다. 기준은 <a href="/jeosinyong">저신용·재창업 가이드</a>와 <a href="/geojeol">거절 사유와 회복 경로</a>에 정리했습니다.</p></div>

    <h2>지금 접수 중인 자금</h2>
    <ul>{open_html}</ul>
    <p>접수 상태는 날짜 기준으로 매일 갱신됩니다 — 전체 일정은 <a href="/schedule">정책자금 접수 일정</a>에서.</p>

    <h2>진행 순서와 비용</h2>
    <p><b>① 무료 진단</b>(조건·용도 확인, 가능성이 낮으면 낮다고 먼저 말씀드립니다) → <b>② 자금·기관 선택</b>(직접대출·재단·신보 기보 중 맞는 갈래) → <b>③ 서류·계획서 준비</b>(<a href="/gyehoekseo">심사가 보는 5요소</a>) → <b>④ 신청·심사·실행</b>. 비용 구조는 단순합니다: 실행 전 비용 0원, 실행된 경우에만 성공보수 — 착수금을 먼저 요구하는 곳과의 차이는 <a href="/chaksugeum">착수금 사기 구별법</a>에 있습니다.</p>

    <div class="callout"><p>정책자금은 대출이며 상환 의무가 있습니다. 승인 여부와 조건은 각 심사 기관이 결정하고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. {FEE}</p></div>

    <h2>자주 묻는 질문</h2>
    {faq_html}

    <div class="related">
      <p class="t">함께 보기</p>
      <a href="/sojingong">소상공인 정책자금 (소진공 직접대출)</a>
      <a href="/jaedan">신용보증재단 사업자대출</a>
      <a href="/schedule">정책자금 접수 일정</a>
      <a href="/cases">실행 기록 전체</a>
      <a href="/sanghwan">상환 구조 가이드</a>
    </div>
    <div class="cta-box">
      <h3 class="serif">내 조건이면 어느 갈래인지</h3>
      <p>업종·매출·신용·이력을 주시면 직접대출·재단·신보 기보 중 맞는 트랙과 예상 구조를 무료로 진단해 드립니다.</p>
      <a class="btn btn-kakao" href="http://pf.kakao.com/_GKuxfn/chat" target="_blank" rel="noopener">카카오톡 무료 진단</a>
      <a class="btn btn-tel" href="tel:1666-2425">전화 1666-2425</a>
    </div>
  </div>
</main>
{foot}
</body>
</html>
'''
    if '갚' in page: die("생성물에 '갚' 포함")
    if re.search(r'보장(?!하지)', page.replace('결과를 보장하지','')): die("생성물에 '보장' 포함")
    (ROOT/'gaein.html').write_text(page, encoding='utf-8')
    sm=(ROOT/'sitemap.xml').read_text(encoding='utf-8')
    loc="https://bmaker.kr/gaein"
    if loc+"</loc>" in sm: sm=re.sub(r'(<loc>'+re.escape(loc)+r'</loc><lastmod>)[^<]+', r'\g<1>'+str(TODAY), sm)
    else: sm=sm.replace('</urlset>', f'  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.9</priority></url>\n</urlset>')
    (ROOT/'sitemap.xml').write_text(sm, encoding='utf-8')
    lt=(ROOT/'llms.txt').read_text(encoding='utf-8')
    line=f"- [개인사업자 정책자금 총정리](https://bmaker.kr/gaein): 실행 기록 {len(rows)}건 중 개인사업자 {N}건(총 {TOT}, 중앙값 {MED}, 소요 중앙값 {DMED}일) — 종류(직접대출·재단·신보 기보·대리대출)·조건(600점대 {low}·재창업 {rest}·업력 1년 이하 {young})·현재 접수 중 자금"
    if '- [개인사업자 정책자금 총정리]' in lt: lt=re.sub(r'- \[개인사업자 정책자금 총정리\][^\n]*', line, lt)
    else: lt=lt.replace('- [정책자금 접수 일정]', line+'\n- [정책자금 접수 일정]')
    (ROOT/'llms.txt').write_text(lt, encoding='utf-8')
    print(f"[개인사업자 허브 빌드 OK] 개인 {N}건 · {TOT} · 접수 중 {len(open_funds)}개 (기준일 {TODAY})")

if __name__=='__main__':
    build()
