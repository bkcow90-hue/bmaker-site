#!/usr/bin/env python3
"""정책자금 컨설팅 안내(/consulting) 빌드 — 실행 기록에서 실적 수치를 자동 집계해 생성한다. 실행: python tools/build_consulting.py"""
import csv, json, re, sys, datetime, statistics
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TODAY = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).date()  # KST
FEE = '착수금·진행비 등 실행 전 비용은 일절 받지 않고, 자금이 실제 실행된 경우에만 성공보수를 받습니다.'
def die(m): print(f"[컨설팅 페이지 빌드 실패] {m}"); sys.exit(1)
def won2(m):
    e,man=divmod(int(m),10000)
    return ((f"{e}억"+((" " if man else "")+f"{man:,}만" if man else ""))+"원") if e else f"{man:,}만원"
def esc(s): return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def build():
    rows=[r for r in csv.DictReader(open(ROOT/'data'/'cases.source.csv',encoding='utf-8-sig',newline='')) if r['사이트 공개'].upper()=='Y']
    if not rows: die("실행 기록 없음")
    a=[int(r['실행 금액(만원)']) for r in rows]; d=[float(r['소요일']) for r in rows if r['소요일']]
    N=len(rows); TOT=won2(sum(a)); MED=won2(int(statistics.median(a))); DMED=int(statistics.median(d)) if d else None
    NEV=sum(1 for r in rows if r['증빙 파일'].strip()); NIND=sum(1 for r in rows if r['사업 형태'].strip()=='개인')
    yms=sorted(r['실행 연월'] for r in rows); y0,m0=yms[0].split('-'); y1,m1=yms[-1].split('-')
    style=re.search(r'<style>.*?</style>', (ROOT/'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    src=(ROOT/'jaedan.html').read_text(encoding='utf-8')
    hdr=re.search(r'<header>.*?</header>', src, re.S).group(0); foot=re.search(r'<footer>.*?</footer>', src, re.S).group(0)
    TBL='<style>.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}table{border-collapse:collapse;width:100%;min-width:560px;font-size:.88rem}th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}tr:nth-child(even) td{background:#FAFBFD}td a{color:var(--blue-deep);text-decoration:underline}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:18px 0}.card{background:var(--paper);border:1px solid var(--line);border-radius:12px;padding:16px 18px}.card b{display:block;font-size:1.4rem;color:var(--navy);margin-bottom:4px}.card span{font-size:.82rem;color:var(--ink-soft)}.proof{background:var(--paper);border:1px solid var(--line);border-left:4px solid var(--blue-deep);border-radius:10px;padding:16px 20px;margin:22px 0}</style>'
    steps=[('① 진단','업종·매출·신용·이력·기존 대출을 보고 가능성이 있는 트랙(직접대출·재단·신보 기보)과 지금 걸리는 조건을 가려냅니다. 가능성이 낮으면 낮다고, 무엇을 먼저 바꿔야 하는지부터 말씀드립니다.','무료'),
           ('② 설계','자금·기관 선택과 순서(동시 설계 포함), 필요 금액 산출, 예상 상환 구조를 정합니다.','계약 후'),
           ('③ 준비','서류 목록, 사업계획서의 숫자 정합(용도·집행·상환 계획), 증빙 대응을 함께 만듭니다. 사실과 다른 서류는 만들지 않습니다.','계약 후'),
           ('④ 대응','신청·심사 과정의 보완 요청 대응, 약정·실행까지 동행합니다. 승인 여부와 조건은 심사 기관이 결정합니다.','실행 시 성공보수')]
    steps_html="".join(f'<tr><td style="white-space:nowrap"><b>{a}</b></td><td>{b}</td><td style="white-space:nowrap">{c}</td></tr>' for a,b,c in steps)
    nos=[('"100% 승인" 같은 약속','승인 권한은 기관에 있습니다. 결과를 약속하는 말은 컨설팅이 아니라 영업 멘트입니다.'),
         ('착수금·진행비·서류비 선불','실행 전 비용은 0원입니다. 먼저 돈부터 요구하는 구조는 결과와 무관하게 수익이 나는 구조입니다.'),
         ('서류 꾸미기','매출·재직·용도를 사실과 다르게 만드는 일은 하지 않습니다. 적발 시 회수·제재를 사업주가 집니다.'),
         ('과도한 자금 권유','상환할 수 있는 금액이 기준입니다. 받을 수 있다고 다 받게 하지 않습니다.')]
    nos_html="".join(f'<tr><td style="white-space:nowrap"><b>{a}</b></td><td>{b}</td></tr>' for a,b in nos)
    checks=[('실행 기록을 공개하는가','건수·금액·조건·증빙을 볼 수 있어야 합니다. 저희는 전건 공개합니다 — <a href="/cases">실행 기록</a>'),
            ('실행 전 비용이 0원인가','착수금·진행비 명목이 있으면 그 시점에 이미 수익 구조가 완성된 회사입니다.'),
            ('"안 된다"고 말하는가','모든 상담에서 "됩니다"만 나오면 진단이 아닙니다. 조건이 안 되면 안 된다고 말하는 곳을 고르세요.'),
            ('사업자·대표 실명이 확인되는가','사업자등록번호·대표명·주소가 페이지 하단에 있는지 보세요.')]
    checks_html="".join(f'<tr><td style="white-space:nowrap"><b>{a}</b></td><td>{b}</td></tr>' for a,b in checks)
    faq=[("정책자금 컨설팅이 꼭 필요한가요?","아닙니다. 조건이 명확하고 서류 준비가 익숙하면 직접 신청이 가장 좋습니다. 컨설팅이 값을 하는 경우는 어느 트랙이 맞는지 모를 때, 신용·이력에 사연이 있을 때, 여러 자금을 순서·동시로 설계해야 할 때입니다. 진단은 무료라 필요 여부부터 확인하는 게 맞습니다."),
         ("비용은 얼마인가요?","실행 전 비용은 0원입니다. 자금이 실제 실행된 경우에만 성공보수를 받으며, 요율은 자금 종류와 규모에 따라 계약 시 안내합니다. 실행되지 않으면 비용이 없습니다."),
         ("착수금을 왜 안 받나요?","착수금을 받으면 결과와 무관하게 수익이 나기 때문에, 가능성이 낮은 분에게도 '됩니다'라고 말할 유인이 생깁니다. 실행된 경우에만 받는 구조가 진단을 정직하게 만듭니다 — 업계 관행과 확인법은 <a href='/chaksugeum'>착수금 사기 구별법</a>에 정리했습니다."),
         (f"실적은 어떻게 확인하나요?",f"공개 실행 기록 {N}건(총 {TOT}, {int(y0)}.{int(m0)}~{int(y1)}.{int(m1)})을 조건·증빙과 함께 게시합니다. 이 중 {NEV}건은 기관 안내문 캡처를 증빙으로 붙였고, 상담 신청 916곳의 익명 통계도 공개합니다."),
         ("승인이 안 되면 어떻게 되나요?","비용이 발생하지 않습니다. 거절 사유를 같이 확인하고, 조건이 바뀌면 재신청할 시점을 잡습니다 — 실제로 조건을 만든 뒤 실행까지 간 기록이 있습니다(<a href='/geojeol'>거절 사유와 회복 경로</a>).")]
    faq_ld=json.dumps({"@context":"https://schema.org","@type":"FAQPage","mainEntity":[{"@type":"Question","name":q,"acceptedAnswer":{"@type":"Answer","text":re.sub(r'<[^>]+>','',a)}} for q,a in faq]}, ensure_ascii=False)
    svc=json.dumps({"@context":"https://schema.org","@type":"Service","name":"정책자금 컨설팅 (진단·설계·준비·심사 대응)","serviceType":"정책자금 컨설팅","provider":{"@type":"Organization","@id":"https://bmaker.kr/#org","name":"비즈니스 메이커"},"areaServed":"KR","url":"https://bmaker.kr/consulting","offers":{"@type":"Offer","description":"실행 전 비용 0원, 자금 실행 시에만 성공보수","priceCurrency":"KRW"}}, ensure_ascii=False)
    crumb=json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"홈","item":"https://bmaker.kr/"},{"@type":"ListItem","position":2,"name":"정책자금 컨설팅","item":"https://bmaker.kr/consulting"}]}, ensure_ascii=False)
    faq_html="".join(f'<details><summary>{q}</summary><div class="body">{a}</div></details>' for q,a in faq)
    page=f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>정책자금 컨설팅 — 무엇을 하고 얼마를 받나, 업체 고르는 확인법 (2026) | 비즈니스 메이커</title>
<meta name="description" content="정책자금 컨설팅 업체는 무엇을 하고 비용은 어떻게 받나요? 진단·설계·준비·심사 대응 4단계, 실행 전 비용 0원·성공보수 구조, 하지 않는 일 4가지, 업체 확인법 4가지 — 공개 실행 기록 {N}건({TOT})과 함께.">
<meta property="og:type" content="website">
<meta property="og:title" content="정책자금 컨설팅 — 무엇을 하고 얼마를 받나 (2026)">
<meta property="og:description" content="실행 전 비용 0원 · 실행 시 성공보수 · 공개 실행 기록 {N}건">
<meta property="og:url" content="https://bmaker.kr/consulting">
<meta property="og:image" content="https://bmaker.kr/assets/og.png">
<meta property="og:locale" content="ko_KR">
<link rel="canonical" href="https://bmaker.kr/consulting">
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
    <p class="crumb"><a href="/">홈</a> › 정책자금 컨설팅</p>
    <h1 class="serif">정책자금 컨설팅,<br class="pc"> 무엇을 하고 얼마를 받나</h1>
    <p>승인은 기관이 하고, 컨설팅은 그 전 단계를 맡습니다. 실행 전 비용 0원, 실행된 경우에만 성공보수 — 공개 실행 기록 {N}건({TOT})이 이 방식의 결과입니다.</p>
  </div>
</section>
<main>
  <div class="wrap">
    <p><b>짧은 답:</b> 정책자금 컨설팅이 실제로 하는 일은 네 가지입니다 — 조건 <b>진단</b>, 자금·기관 <b>설계</b>, 서류·계획서 <b>준비</b>, 심사 <b>대응</b>. 승인 여부와 조건은 소진공·재단·신보 같은 심사 기관이 결정하며, 컨설팅이 바꿀 수 있는 것은 "맞는 트랙에, 맞는 서류로, 맞는 시점에" 들어가느냐입니다. 비용은 업계에 두 방식이 있습니다: 착수금을 먼저 받는 방식과 실행된 경우에만 받는 방식. 저희는 후자입니다.</p>
    <p class="asof">기준일 {TODAY.year}년 {TODAY.month}월 {TODAY.day}일 · 실적 수치는 <a href="/cases">공개 실행 기록</a>에서 자동 집계됩니다.</p>

    <div class="cards">
      <div class="card"><b>{N}건</b><span>공개 실행 기록 ({int(y0)}.{int(m0)}~{int(y1)}.{int(m1)})</span></div>
      <div class="card"><b>{TOT}</b><span>실행 총액 · 중앙값 {MED}</span></div>
      <div class="card"><b>{DMED}일</b><span>첫 상담 → 정산 중앙값</span></div>
      <div class="card"><b>0원</b><span>실행 전 비용 (전건 동일)</span></div>
    </div>

    <h2>컨설팅이 하는 일 — 4단계</h2>
    <div class="tablewrap"><table><thead><tr><th>단계</th><th>내용</th><th>비용</th></tr></thead><tbody>{steps_html}</tbody></table></div>

    <h2>하지 않는 일 — 이 네 가지가 보이면 다른 곳입니다</h2>
    <div class="tablewrap"><table><thead><tr><th>하지 않는 것</th><th>이유</th></tr></thead><tbody>{nos_html}</tbody></table></div>

    <h2>비용 구조</h2>
    <p>진단은 무료이고, 계약 후에도 실행 전에 받는 돈은 없습니다. 자금이 실제로 실행된 경우에만 성공보수를 받으며 요율은 자금 종류·규모에 따라 계약 시 안내합니다. 실행되지 않으면 비용은 0원 — 이 구조의 핵심은 <b>가능성이 낮은 분에게 "됩니다"라고 말할 이유가 없다는 것</b>입니다. 그래서 저희 진단의 일부는 "지금은 넣지 마세요, 이것부터 바꾸세요"로 끝납니다.</p>

    <h2>컨설팅 업체 고르는 확인법</h2>
    <div class="tablewrap"><table><thead><tr><th>확인 항목</th><th>기준</th></tr></thead><tbody>{checks_html}</tbody></table></div>
    <div class="proof"><p>위험 신호 7가지와 확인법 5가지는 <a href="/chaksugeum">착수금·수수료 사기 구별법</a>에 따로 정리했습니다. 개인사업자라면 <a href="/gaein">개인사업자 정책자금 총정리</a>에서 어느 갈래가 맞는지부터 보세요 — 실행 기록 {N}건 중 {NIND}건이 개인사업자입니다.</p></div>

    <div class="callout"><p>정책자금은 대출이며 상환 의무가 있습니다. 승인 여부와 조건은 각 심사 기관이 결정하고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. {FEE}</p></div>

    <h2>자주 묻는 질문</h2>
    {faq_html}

    <div class="related">
      <p class="t">함께 보기</p>
      <a href="/chaksugeum">착수금·수수료 사기 구별법</a>
      <a href="/cases">공개 실행 기록 {N}건</a>
      <a href="/stats">상담 신청 통계</a>
      <a href="/gaein">개인사업자 정책자금 총정리</a>
      <a href="/sojingong">소상공인 정책자금</a>
    </div>
    <div class="cta-box">
      <h3 class="serif">먼저 진단부터 — 비용 없이</h3>
      <p>조건을 주시면 가능한 트랙과 지금 걸리는 조건을 말씀드립니다. 가능성이 낮으면 낮다고 먼저 말씀드립니다.</p>
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
    (ROOT/'consulting.html').write_text(page, encoding='utf-8')
    sm=(ROOT/'sitemap.xml').read_text(encoding='utf-8'); loc="https://bmaker.kr/consulting"
    if loc+"</loc>" in sm: sm=re.sub(r'(<loc>'+re.escape(loc)+r'</loc><lastmod>)[^<]+', r'\g<1>'+str(TODAY), sm)
    else: sm=sm.replace('</urlset>', f'  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod><changefreq>monthly</changefreq><priority>0.9</priority></url>\n</urlset>')
    (ROOT/'sitemap.xml').write_text(sm, encoding='utf-8')
    lt=(ROOT/'llms.txt').read_text(encoding='utf-8')
    line=f"- [정책자금 컨설팅 안내](https://bmaker.kr/consulting): 하는 일 4단계(진단·설계·준비·대응), 하지 않는 일 4가지, 비용 구조(실행 전 0원·실행 시 성공보수), 업체 확인법 — 공개 실행 기록 {N}건·{TOT} 근거"
    if '- [정책자금 컨설팅 안내]' in lt: lt=re.sub(r'- \[정책자금 컨설팅 안내\][^\n]*', line, lt)
    else: lt=lt.replace('- [개인사업자 정책자금 총정리]', line+'\n- [개인사업자 정책자금 총정리]')
    (ROOT/'llms.txt').write_text(lt, encoding='utf-8')
    print(f"[컨설팅 페이지 빌드 OK] 실행 기록 {N}건 · {TOT} · 소요 중앙값 {DMED}일 (기준일 {TODAY})")

if __name__=='__main__':
    build()
