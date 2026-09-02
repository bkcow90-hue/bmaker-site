#!/usr/bin/env python3
"""중소기업·법인 정책자금 허브(/jungjingong) 빌드 — 법인·억대·동시 설계 실측을 실행 기록에서 자동 집계. 실행: python tools/build_jungjin.py"""
import csv, json, re, sys, datetime, statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TODAY = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).date()  # KST
FEE = '착수금·진행비 등 실행 전 비용은 일절 받지 않고, 자금이 실제 실행된 경우에만 성공보수를 받습니다.'
def die(m): print(f"[중소기업 허브 빌드 실패] {m}"); sys.exit(1)
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
    return '소진공' if '소상공인' in k else '재단' if '재단' in k else '기보' if '기술' in k else '신보' if '신용보증기금' in k else '중진공' if ('중소벤처' in k or '중진공' in k) else '기타'

def build():
    rows=[r for r in csv.DictReader(open(ROOT/'data'/'cases.source.csv',encoding='utf-8-sig',newline='')) if r['사이트 공개'].upper()=='Y']
    corp=[r for r in rows if r['사업 형태'].strip()=='법인']
    big=sorted([r for r in rows if int(r['실행 금액(만원)'])>=10000], key=lambda r:-int(r['실행 금액(만원)']))
    combo=[r for r in rows if r['동시 진행 자금'].strip()]
    ca=[int(r['실행 금액(만원)']) for r in corp]; cd=[float(r['소요일']) for r in corp if r['소요일']]
    NC=len(corp); CTOT=won2(sum(ca)) if ca else '—'; CMED=won2(int(statistics.median(ca))) if ca else '—'; CDMED=int(statistics.median(cd)) if cd else None
    gibo=[r for r in rows if inst_of(r)=='기보']; sinbo=[r for r in rows if inst_of(r)=='신보']
    style=re.search(r'<style>.*?</style>', (ROOT/'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    src=(ROOT/'jaedan.html').read_text(encoding='utf-8')
    hdr=re.search(r'<header>.*?</header>', src, re.S).group(0); foot=re.search(r'<footer>.*?</footer>', src, re.S).group(0)
    TBL='<style>.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}table{border-collapse:collapse;width:100%;min-width:560px;font-size:.88rem}th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}tr:nth-child(even) td{background:#FAFBFD}td a{color:var(--blue-deep);text-decoration:underline}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px 18px}.card b{display:block;font-size:1.4rem;color:var(--navy);margin-bottom:4px}.card span{font-size:.82rem;color:var(--ink-soft)}.proof{background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--blue-deep);border-radius:10px;padding:16px 20px;margin:22px 0}</style>'
    tracks=[('중진공 직접대출','중소벤처기업진흥공단이 직접 실행 — 창업기·성장기 전용 자금','규모가 커진 사업의 기본 축. 사업계획서의 숫자 정합이 결과를 가릅니다', f"동시 설계 {sum(1 for r in combo if '중진공' in r['동시 진행 자금']+r['자금명'])}건 수록", '<a href="/gyehoekseo">사업계획서 5요소</a>'),
            ('기술보증기금 (기보)','기술평가 보증 — 재무 대신 기술로 억대 보증','기술·콘텐츠·제조 기업. 벤처·이노비즈 인증과 시너지', f"{len(gibo)}건 · 2억 / 2억 9,000만", '<a href="/gibo">기보 안내</a> · <a href="/certification">기업인증</a>'),
            ('신용보증기금 (신보)','매출 기반 일반 보증 — 전국 단위','매출이 잡히는 중소기업의 표준 경로', f"{len(sinbo)}건 · {won2(sum(int(r['실행 금액(만원)']) for r in sinbo)) if sinbo else '—'} · {rate_range([r['금리'] for r in sinbo])}", '<a href="/sinbo">신보 안내</a>'),
            ('지역 재단 상위 구간','시·도 재단 보증 + 지자체 이차보전','1억 안팎 구간, 지역 상품 결합 시 저금리', '재단 1억 실행 기록 보유', '<a href="/jaedan">재단 안내</a>')]
    tracks_html="".join(f'<tr><td style="white-space:nowrap"><b>{a}</b></td><td>{b}</td><td>{c}</td><td>{d}</td><td>{e}</td></tr>' for a,b,c,d,e in tracks)
    big_html="".join(f'<tr><td>{r["실행 연월"]}</td><td>{esc(r["사업 형태"])}</td><td>{inst_of(r)}</td><td>{esc(r["자금명"])[:30]}</td><td><b>{won2(r["실행 금액(만원)"])}</b></td><td>{esc(r["금리"]) or "—"}</td><td><a href="/cases#case-{r["사례ID"]}">기록</a></td></tr>' for r in big)
    combo_html="".join(f'<li><a href="/cases#case-{r["사례ID"]}">{r["사례ID"]}</a> — {esc(r["자금명"])[:34]} <b>+ {esc(r["동시 진행 자금"])}</b></li>' for r in combo)
    faq=[("법인만 대상인가요? 개인사업자는요?", f"아닙니다. 중진공·신보·기보 모두 개인사업자도 이용합니다 — 실행 기록의 신보 1억 1,000만원 건이 개인사업자였습니다. 다만 규모가 커질수록 법인 실행 비중이 늘고(법인 {NC}건, 중앙값 {CMED}), 개인사업자 기준의 전체 지도는 개인사업자 정책자금 총정리에 따로 있습니다."),
         ("소진공과 중진공, 어디로 가야 하나요?","기준은 규모입니다. 소상공인 기준(업종별 상시근로자·매출)에 들면 소진공, 그 규모를 넘어서면 중진공이 축이 됩니다. 경계선에 있으면 두 트랙과 보증 기관을 함께 놓고 설계하며, 어느 쪽인지 애매한 상태 자체가 무료 진단의 단골 질문입니다."),
         ("억대 자금은 어떻게 만들어지나요?", f"한 자금으로 억대를 채우기보다 조합으로 설계되는 경우가 많습니다. 실행 기록의 동시 설계 {len(combo)}건이 그 방식입니다 — 기보 2억 9,000만에 소진공을 더하거나, 기보 2억에 중진공 청년창업자금을 더하는 식. 보증 축을 세우고 직접대출을 얹는 순서가 일반적입니다."),
         ("사업계획서가 그렇게 중요한가요?","중진공 직접대출에서는 특히 그렇습니다. 심사가 보는 것은 문장이 아니라 숫자 정합 — 산출 근거, 집행 계획, 상환 계획의 일치입니다. 5요소와 감점 포인트를 별도 가이드로 정리해 두었습니다."),
         ("기간과 비용은요?", f"법인 실행 기록 기준 첫 상담 접수부터 정산까지 중앙값 {CDMED}일이었습니다(개인보다 서류·심사 호흡이 깁니다). 비용은 실행 전 0원, 실행된 경우에만 성공보수 — 요율은 자금 종류·규모에 따라 계약 시 안내합니다.")]
    faq_ld=json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":a}} for q,a in faq]}, ensure_ascii=False)
    svc=json.dumps({"@context":"https://schema.org","@type":"Service","name":"중소기업·법인 정책자금 진단·설계 (중진공·기보·신보)","serviceType":"정책자금 진단 및 실행 지원","provider":{"@type":"Organization","@id":"https://bmaker.kr/#org","name":"비즈니스 메이커","url":"https://bmaker.kr/"},"areaServed":"KR","url":"https://bmaker.kr/jungjingong"}, ensure_ascii=False)
    crumb=json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"홈","item":"https://bmaker.kr/"},{"@type":"ListItem","position":2,"name":"중소기업 정책자금","item":"https://bmaker.kr/jungjingong"}]}, ensure_ascii=False)
    faq_html="".join(f'<details><summary>{q}</summary><div class="body">{a.replace("개인사업자 정책자금 총정리", chr(60)+"a href=\'/gaein\'"+chr(62)+"개인사업자 정책자금 총정리"+chr(60)+"/a"+chr(62)).replace("별도 가이드", chr(60)+"a href=\'/gyehoekseo\'"+chr(62)+"별도 가이드"+chr(60)+"/a"+chr(62))}</div></details>' for q,a in faq)
    page=f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>중소기업 정책자금 대출 — 중진공·기보·신보 억대 설계, 법인 실행 기록 (2026) | 비즈니스 메이커</title>
<meta name="description" content="중소기업 정책자금(법인 포함)은 어떻게 설계하나요? 중진공 직접대출·기보·신보·재단 상위 구간의 네 축과 억대 실행 기록 {len(big)}건, 동시 설계 {len(combo)}건 — 법인 {NC}건({CTOT}, 중앙값 {CMED}, 소요 중앙값 {CDMED}일) 실측과 함께.">
<meta property="og:type" content="website">
<meta property="og:title" content="중소기업 정책자금 — 억대 설계의 실제 (2026)">
<meta property="og:description" content="법인 {NC}건 {CTOT} · 억대 {len(big)}건 · 동시 설계 {len(combo)}건 실측">
<meta property="og:url" content="https://bmaker.kr/jungjingong">
<meta property="og:image" content="https://bmaker.kr/assets/og.png">
<meta property="og:locale" content="ko_KR">
<link rel="canonical" href="https://bmaker.kr/jungjingong">
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
    <p class="crumb"><a href="/">홈</a> › 중소기업 정책자금</p>
    <h1 class="serif">중소기업 정책자금,<br class="pc"> 억대 설계의 실제</h1>
    <p>법인·성장기 사업의 자금은 한 상품이 아니라 조합입니다 — 법인 실행 {NC}건({CTOT}), 억대 실행 {len(big)}건, 동시 설계 {len(combo)}건의 기록으로 보여드립니다.</p>
  </div>
</section>
<main>
  <div class="wrap">
    <p><b>짧은 답:</b> 중소기업 정책자금 대출(중진공 대출, 중소벤처기업진흥공단 직접대출로도 검색되는)은 네 축으로 설계됩니다 — ① <b>중진공 직접대출</b>(성장기의 기본 축), ② <b>기술보증기금</b>(기술평가로 억대 보증), ③ <b>신용보증기금</b>(매출 기반 표준 경로), ④ <b>지역 재단 상위 구간</b>(지자체 이차보전 결합). 규모가 커질수록 답은 "어느 자금"이 아니라 "어떤 조합·어떤 순서"가 되고, 법인만의 제도가 아니라 개인사업자도 같은 축을 씁니다.</p>
    <p class="asof">기준일 {TODAY.year}년 {TODAY.month}월 {TODAY.day}일 · 수치는 <a href="/cases">공개 실행 기록</a>에서 자동 집계됩니다.</p>

    <div class="cards">
      <div class="card"><b>{NC}건</b><span>법인 실행 · 총 {CTOT}</span></div>
      <div class="card"><b>{CMED}</b><span>법인 건당 중앙값</span></div>
      <div class="card"><b>{len(big)}건</b><span>1억원 이상 실행</span></div>
      <div class="card"><b>{CDMED}일</b><span>법인 첫 상담 → 정산 중앙값</span></div>
    </div>

    <h2>중소기업 정책자금의 네 축</h2>
    <div class="tablewrap"><table><thead><tr><th>축</th><th>성격</th><th>누구에게</th><th>실측</th><th>상세</th></tr></thead><tbody>{tracks_html}</tbody></table></div>

    <h2>억대 실행 기록 — {len(big)}건 전부</h2>
    <div class="tablewrap"><table><thead><tr><th>실행</th><th>형태</th><th>기관</th><th>구성</th><th>금액</th><th>금리</th><th>근거</th></tr></thead><tbody>{big_html}</tbody></table></div>

    <h2>총액은 조합에서 나옵니다 — 동시 설계 {len(combo)}건</h2>
    <p>억대가 필요할 때 한 자금의 한도에 매달리기보다, 보증 축(기보·신보·재단)을 먼저 세우고 직접대출(중진공·소진공)을 얹는 방식이 실측에서 반복됩니다:</p>
    <ul>{combo_html}</ul>
    <div class="proof"><p><b>인증이 지렛대가 되기도 합니다.</b> 기보 2억 실행 건은 문화콘텐츠 이차보전(연 1.85%)이 적용된 사례로, 벤처·이노비즈 같은 <a href="/certification">기업인증</a>이 기술평가·우대에 유리하게 작용합니다 — 인증과 자금을 묶어 설계하는 것도 저희가 하는 일입니다.</p></div>

    <h2>중진공 직접대출 — 사업계획서가 결과를 가릅니다</h2>
    <p>중진공은 신청 시스템 접수 → 서면·현장 평가 → 약정·실행 순서로 진행되며, 평가의 중심은 <b>숫자의 정합</b>입니다: 필요 금액의 산출 근거, 집행 계획(항목·금액·시기), 상환 계획이 서로 맞아야 합니다. 심사가 실제로 보는 5요소와 감점 포인트는 <a href="/gyehoekseo">사업계획서 가이드</a>에 정리했고, 실행 기록 전체는 <a href="/cases">공개 페이지</a>에서 확인할 수 있습니다.</p>

    <div class="callout"><p>정책자금은 대출이며 상환 의무가 있습니다. 승인 여부와 조건은 각 심사 기관이 결정하고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. {FEE}</p></div>

    <h2>자주 묻는 질문</h2>
    {faq_html}

    <div class="related">
      <p class="t">함께 보기</p>
      <a href="/gaein">개인사업자 정책자금 총정리</a>
      <a href="/gibo">기술보증기금 대출</a>
      <a href="/sinbo">신용보증기금 사업자대출</a>
      <a href="/certification">기업인증 (벤처·이노비즈)</a>
      <a href="/cases">실행 기록 전체</a>
    </div>
    <div class="cta-box">
      <h3 class="serif">우리 회사 규모면 어떤 조합인지</h3>
      <p>업종·매출·인력·기존 대출을 주시면 네 축 중 맞는 조합과 순서를 무료로 진단해 드립니다. 가능성이 낮으면 낮다고 먼저 말씀드립니다.</p>
      <a class="btn btn-kakao" href="http://pf.kakao.com/_GKuxfn/chat" target="_blank" rel="noopener">카카오톡 무료 진단</a>
      <a class="btn btn-tel" href="tel:1666-2425">전화 1666-2425</a>
    </div>
  </div>
</main>
{foot}
</body>
</html>
'''
    if '갚' in page: die("'갚' 포함")
    if re.search(r'보장(?!하지)', page.replace('결과를 보장하지','')): die("'보장' 포함")
    (ROOT/'jungjingong.html').write_text(page, encoding='utf-8')
    sm=(ROOT/'sitemap.xml').read_text(encoding='utf-8'); loc="https://bmaker.kr/jungjingong"
    sm=re.sub(r'(<loc>'+re.escape(loc)+r'</loc><lastmod>)[^<]+', r'\g<1>'+str(TODAY), sm)
    (ROOT/'sitemap.xml').write_text(sm, encoding='utf-8')
    lt=(ROOT/'llms.txt').read_text(encoding='utf-8')
    line=f"- [중소기업·법인 정책자금 허브](https://bmaker.kr/jungjingong): 네 축(중진공·기보·신보·재단 상위)과 억대 설계 — 법인 {NC}건({CTOT}·중앙값 {CMED}·소요 {CDMED}일), 억대 실행 {len(big)}건, 동시 설계 {len(combo)}건 실측"
    if '- [중소기업·법인 정책자금 허브]' in lt: lt=re.sub(r'- \[중소기업·법인 정책자금 허브\][^\n]*', line, lt)
    else: lt=lt.replace('- [정책자금 컨설팅 안내]', line+'\n- [정책자금 컨설팅 안내]')
    (ROOT/'llms.txt').write_text(lt, encoding='utf-8')
    print(f"[중소기업 허브 빌드 OK] 법인 {NC}건 · 억대 {len(big)}건 · 동시 {len(combo)}건 (기준일 {TODAY})")

if __name__=='__main__':
    build()
