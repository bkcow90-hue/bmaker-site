#!/usr/bin/env python3
"""자금 팩트 페이지 + 접수 일정(/schedule) 빌드 — data/funds.source.csv 한 줄 = 페이지 하나.

실행 기록(cases.source.csv)에서 '원장 키워드'로 실측 사례를 자동 연결하고,
접수 시작/마감일을 오늘 날짜와 비교해 상태 배지를 계산한다(매일 새벽 재빌드로 자동 뒤집힘).
실행: python tools/build_funds.py
"""
import csv, json, re, sys, datetime
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
TODAY = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=9)).date()  # KST(UTC+9, 서머타임 없음) — 러너는 UTC
FEE = '착수금·진행비 등 실행 전 비용은 일절 받지 않고, 자금이 실제 실행된 경우에만 성공보수를 받습니다.'
def die(m): print(f"[자금 빌드 실패] {m}"); sys.exit(1)
def won2(m):
    e,man=divmod(int(m),10000)
    return ((f"{e}억"+((" " if man else "")+f"{man:,}만" if man else ""))+"원") if e else f"{man:,}만원"
def esc(s): return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

def load():
    rows=[]
    with open(ROOT/'data'/'funds.source.csv',encoding='utf-8-sig',newline='') as f:
        for i,d in enumerate(csv.DictReader(f), start=2):
            d={k:(v or '').strip() for k,v in d.items()}
            if not any(d.values()): continue
            for c in ('자금ID','자금명','기관','공고 링크','최종 확인일','사이트 공개'):
                if not d.get(c): die(f"{i}행: '{c}' 이 비어 있습니다.")
            if not re.match(r'^[a-z0-9-]+$', d['자금ID']): die(f"{i}행 자금ID '{d['자금ID']}' — 영소문자·숫자·하이픈만.")
            for c in ('접수 시작일','접수 마감일','최종 확인일'):
                v=d.get(c,'')
                if v and '소진' not in v and not re.match(r'^\d{4}-\d{2}-\d{2}$', v): die(f"{i}행 {c} '{v}' — YYYY-MM-DD 형식(마감일은 '예산 소진 시(까지)' 등 소진형 표현 허용).")
            j=' '.join(d.values())
            if '갚' in j: die(f"{i}행: '갚다'류 금지 — 상환으로.")
            if re.search(r'보장', j): die(f"{i}행: '보장' 표현 금지.")
            rows.append(d)
    if not rows: die("자금 행이 없습니다.")
    ids=[d['자금ID'] for d in rows]
    if len(ids)!=len(set(ids)): die("자금ID 중복이 있습니다.")
    return [d for d in rows if d['사이트 공개'].upper()=='Y']

def cases_for(kw):
    out=[]
    with open(ROOT/'data'/'cases.source.csv',encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if r['사이트 공개'].upper()=='Y' and kw and kw in r['자금명']:
                out.append(r)
    out.sort(key=lambda r:(r['실행 연월'], r['사례ID']), reverse=True)
    return out

def rate_range(vals):
    nums=[]
    for v in vals:
        m=re.search(r'\d+(?:\.\d+)?', v or '')
        if m: nums.append(float(m.group(0)))
    nums=sorted(set(nums))
    if not nums: return ''
    lo=f"{nums[0]:g}"; hi=f"{nums[-1]:g}"
    return f"연 {lo}%" if lo==hi else f"연 {lo}~{hi}%"

def peer_cases(inst):
    key='소상공인' if '소상공인' in inst else inst[:3]
    out=[]
    with open(ROOT/'data'/'cases.source.csv',encoding='utf-8-sig',newline='') as f:
        for r in csv.DictReader(f):
            if r['사이트 공개'].upper()=='Y' and key in r['기관']:
                out.append(r)
    out.sort(key=lambda r:(r['실행 연월'], r['사례ID']), reverse=True)
    return out

def status_of(d):
    s,e = d['접수 시작일'], d['접수 마감일']
    def pd(v): return datetime.date.fromisoformat(v)
    if d['접수 상태']=='상시': return ('open','상시 접수', 3)
    if s and pd(s)>TODAY: return ('soon', f"접수 예정 · {s} 시작", 2)
    if s and pd(s)<=TODAY:
        if '소진' in e: return ('open','접수 중 · 예산 소진 시 마감', 1)
        if e and pd(e)>=TODAY: return ('open', f"접수 중 · {e} 마감", 0 if (pd(e)-TODAY).days<=14 else 1)
        if e and pd(e)<TODAY: return ('closed', f"접수 마감 ({e}) · 다음 공고 대기", 4)
    return ('check','접수 일정: 최신 공고 확인 필요', 3)

def build():
    F=load()
    style=re.search(r'<style>.*?</style>', (ROOT/'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    hdr=re.search(r'<header>.*?</header>', (ROOT/'jaedan.html').read_text(encoding='utf-8'), re.S).group(0)
    foot=re.search(r'<footer>.*?</footer>', (ROOT/'jaedan.html').read_text(encoding='utf-8'), re.S).group(0)
    TBL='<style>.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}table{border-collapse:collapse;width:100%;min-width:520px;font-size:.88rem}th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}tr:nth-child(even) td{background:#FAFBFD}td a,p.badge a{color:var(--blue-deep);text-decoration:underline}.badge{display:inline-block;border-radius:999px;padding:7px 16px;font-size:.86rem;font-weight:600;margin:4px 0 14px}.b-open{background:#E7F5EC;color:#116A36;border:1px solid #BFE4CC}.b-soon{background:#EAF1FF;color:#1D4FB8;border:1px solid #C9DAF8}.b-closed{background:#F3F4F7;color:#5A6474;border:1px solid var(--line)}.b-check{background:#FFF6D5;color:#7A5A00;border:1px solid #F0DFA0}</style>'
    inst_page={'소상공인시장진흥공단':'/sojingong'}
    for d in F:
        C=cases_for(d['원장 키워드'])
        badge_cls, badge_txt, _ = status_of(d)
        amts=[int(r['실행 금액(만원)']) for r in C]
        rates=sorted({r['금리'].split('(')[0].strip() for r in C if r['금리']})
        meas_sum = (f"실측 기록 {len(C)}건 · {won2(min(amts))}~{won2(max(amts))}" + (f" · {rates[0]}~{rates[-1]}" if rates else "")) if C else "실행 기록 수록 실측 준비 중"
        rows_html="".join(
          f'<tr><td>{r["실행 연월"]}</td><td>{esc(r["지역(시도)"])} {esc(r["업종"]) or ""}</td><td>{won2(r["실행 금액(만원)"])}</td><td>{esc(r["금리"]) or "—"}</td><td>{esc(r["상환 조건"]) or "—"}</td><td>{(str(int(float(r["소요일"]))) + "일") if r["소요일"] else "—"}</td><td><a href="/cases#case-{r["사례ID"]}">실행 기록</a></td></tr>' for r in C)
        if C:
            meas_html=(f'<h2>기록된 실측</h2>\n<p>저희가 실제 실행한 {esc(d["자금명"])} 기록입니다 — 금리는 각 실행 시점 기준이며, 전체 맥락은 <a href="/cases">공개 실행 기록</a>에서 확인할 수 있습니다.</p>\n<div class="tablewrap"><table><thead><tr><th>실행</th><th>지역·업종</th><th>금액</th><th>금리</th><th>상환</th><th>소요</th><th>근거</th></tr></thead><tbody>'+rows_html+'</tbody></table></div>')
        else:
            P=peer_cases(d['기관'])
            steps='신청 시스템 접수 → 공단 심사 → 약정·실행' if '직접' in d['카테고리'] else '보증기관 심사 → 보증서 발급 → 은행 대출 실행'
            if P:
                pa=[int(r['실행 금액(만원)']) for r in P]
                pr=rate_range([r['금리'] for r in P])
                prow="".join(f'<tr><td>{r["실행 연월"]}</td><td>{esc(r["자금명"])[:26]}</td><td>{won2(r["실행 금액(만원)"])}</td><td>{esc(r["금리"]) or "—"}</td><td><a href="/cases#case-{r["사례ID"]}">기록</a></td></tr>' for r in P[:3])
                meas_html=(f'<h2>{esc(d["자금명"])} 실행 기록</h2>\n<p>이 자금으로 수록된 건은 아직 없습니다. 다만 같은 {esc(d["기관"])} 경로의 공개 실행 기록이 {len(P)}건 · {won2(sum(pa))}'
                           +(f' · 금리 {pr}' if pr else '')
                           +f' 쌓여 있어, 진행 구조와 조건 감각은 거기서 잡을 수 있습니다. 진행 순서는 {steps}.</p>\n'
                           +'<div class="tablewrap"><table><thead><tr><th>실행</th><th>자금</th><th>금액</th><th>금리</th><th>근거</th></tr></thead><tbody>'+prow+'</tbody></table></div>\n'
                           +'<p><a href="/cases">공개 실행 기록 전체 보기 →</a> 이 자금의 실행 건은 고객 동의·증빙이 확보되는 대로 추가합니다.</p>')
            else:
                meas_html=f'<h2>{esc(d["자금명"])} 실행 기록</h2>\n<p>수록된 건은 아직 없습니다. 진행 순서는 {steps} 이며, 실행 건은 고객 동의·증빙이 확보되는 대로 <a href="/cases">공개 실행 기록</a>에 추가합니다.</p>'
        facts=[]
        if d['대상 요약']: facts.append(('대상', esc(d['대상 요약'])))
        if d['한도']: facts.append(('한도', esc(d['한도'])))
        if d['금리 방식']: facts.append(('금리 방식', esc(d['금리 방식'])))
        facts.append(('접수', esc(badge_txt)))
        facts.append(('공고', f'<a href="{esc(d["공고 링크"])}" target="_blank" rel="noopener">공식 공고 확인 →</a>'))
        facts_html="".join(f'<tr><td style="white-space:nowrap"><b>{k}</b></td><td>{v}</td></tr>' for k,v in facts)
        svc=json.dumps({"@context":"https://schema.org","@type":"Service","name":f"{d['자금명']} 진단·실행 지원","serviceType":"정책자금 진단 및 실행 지원","provider":{"@type":"Organization","@id":"https://bmaker.kr/#org","name":"비즈니스 메이커"},"areaServed":"KR","url":f"https://bmaker.kr/{d['자금ID']}"}, ensure_ascii=False)
        crumb=json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"홈","item":"https://bmaker.kr/"},{"@type":"ListItem","position":2,"name":"접수 일정","item":"https://bmaker.kr/schedule"},{"@type":"ListItem","position":3,"name":d['자금명'],"item":f"https://bmaker.kr/{d['자금ID']}"}]}, ensure_ascii=False)
        inst_link=inst_page.get(d['기관'],'/sojingong')
        page=f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(d['자금명'])} — 조건·실측·접수 일정 (2026) | 비즈니스 메이커</title>
<meta name="description" content="{esc(d['자금명'])}({esc(d['기관'])}) — {esc(d['한 줄 메모']) if d['한 줄 메모'] else '조건과 신청 경로'}. {esc(meas_sum)}. 접수 일정과 공식 공고 링크, 실제 실행 기록까지.">
<meta property="og:type" content="website">
<meta property="og:title" content="{esc(d['자금명'])} — 조건·실측·접수 일정 (2026)">
<meta property="og:description" content="{esc(meas_sum)} · {esc(badge_txt)}">
<meta property="og:url" content="https://bmaker.kr/{d['자금ID']}">
<meta property="og:image" content="https://bmaker.kr/assets/og.png">
<meta property="og:locale" content="ko_KR">
<link rel="canonical" href="https://bmaker.kr/{d['자금ID']}">
<link rel="icon" type="image/png" href="assets/icon-192.png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap">
<script type="application/ld+json">{svc}</script>
<script type="application/ld+json">{crumb}</script>
{style}
{TBL}
</head>
<body>
{hdr}
<section class="hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> › <a href="/schedule">접수 일정</a> › {esc(d['자금명'])}</p>
    <h1 class="serif">{esc(d['자금명'])}</h1>
    <p>{esc(d['기관'])} · {esc(d['카테고리'])}{(' — '+esc(d['한 줄 메모'])) if d['한 줄 메모'] else ''}</p>
  </div>
</section>
<main>
  <div class="wrap">
    <p class="badge b-{badge_cls}">{esc(badge_txt)}</p>
    <div class="tablewrap"><table><tbody>{facts_html}</tbody></table></div>
    <p class="asof">최종 확인일 {esc(d['최종 확인일'])} · 대상·한도·금리 등 세부 요건은 각 회차 공고가 기준입니다 — 위 공식 공고 링크에서 확인하세요. 접수 일정 전체는 <a href="/schedule">일정 페이지</a>에 있습니다.</p>
    {meas_html}
    <div class="callout"><p>정책자금은 대출이며 상환 의무가 있습니다. 승인 여부와 조건은 각 심사 기관이 결정하고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. {FEE}</p></div>
    <div class="related">
      <p class="t">함께 보기</p>
      <a href="{inst_link}">{esc(d['기관'])} 안내</a>
      <a href="/schedule">전체 접수 일정</a>
      <a href="/cases">실행 기록</a>
      <a href="/sanghwan">상환 구조 가이드</a>
    </div>
    <div class="cta-box">
      <h3 class="serif">이 자금, 내 조건이면 되는지</h3>
      <p>업종·매출·신용·이력을 주시면 이 자금이 맞는 트랙인지, 아니면 다른 경로가 나은지 무료로 진단해 드립니다. 가능성이 낮으면 낮다고 먼저 말씀드립니다.</p>
      <a class="btn btn-kakao" href="http://pf.kakao.com/_GKuxfn/chat" target="_blank" rel="noopener">카카오톡 무료 진단</a>
      <a class="btn btn-tel" href="tel:1666-2425">전화 1666-2425</a>
    </div>
  </div>
</main>
{foot}
</body>
</html>
'''
        if '갚' in page: die(f"{d['자금ID']}: 생성물에 '갚' 포함")
        if re.search(r'보장(?!하지)', page.replace('결과를 보장하지','')): die(f"{d['자금ID']}: 생성물에 '보장' 포함")
        (ROOT/f"{d['자금ID']}.html").write_text(page, encoding='utf-8')
    # /schedule
    order={'open':0,'soon':1,'check':2,'closed':3}
    def cat_of(d):
        c=d['카테고리']
        return '직접대출' if '직접' in c else ('대리대출' if '대리' in c else '기타')
    CAT_DESC={'직접대출':'소상공인시장진흥공단이 직접 대출을 실행하는 트랙입니다.',
              '대리대출':'보증기관 보증서를 바탕으로 은행이 실행하는 트랙입니다.',
              '기타':'그 외 트랙입니다.'}
    sch_rows=""
    for cat in ('직접대출','대리대출','기타'):
        group=sorted(((d, *status_of(d)) for d in F if cat_of(d)==cat), key=lambda x:(order[x[1]], x[3]))
        if not group: continue
        rows="".join(f'<tr><td><a href="/{d["자금ID"]}"><b>{esc(d["자금명"])}</b></a></td><td>{esc(d["기관"])}</td><td><span class="badge b-{cls}" style="margin:0">{esc(txt)}</span></td><td>{esc(d["다음 회차 메모"]) or "—"}</td><td>{esc(d["최종 확인일"])}</td></tr>' for d,cls,txt,_ in group)
        sch_rows+=f'<h2>{cat} ({len(group)})</h2>\n<p>{CAT_DESC[cat]}</p>\n<div class="tablewrap"><table><thead><tr><th>자금</th><th>기관</th><th>상태</th><th>메모</th><th>최종 확인</th></tr></thead><tbody>{rows}</tbody></table></div>\n' 
    crumb=json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"홈","item":"https://bmaker.kr/"},{"@type":"ListItem","position":2,"name":"정책자금 접수 일정","item":"https://bmaker.kr/schedule"}]}, ensure_ascii=False)
    sch=f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>정책자금 접수 일정 — 지금 신청 가능한 자금 한눈에 (매일 갱신) | 비즈니스 메이커</title>
<meta name="description" content="소상공인·중소기업 정책자금 접수 일정을 상태별로 정리합니다 — 접수 중·예정·마감. 각 자금의 조건·실측·공식 공고 링크와 함께, 날짜 기준 자동 갱신.">
<meta property="og:type" content="website">
<meta property="og:title" content="정책자금 접수 일정 — 지금 신청 가능한 자금">
<meta property="og:description" content="접수 중·예정·마감 상태별 정리, 날짜 기준 자동 갱신.">
<meta property="og:url" content="https://bmaker.kr/schedule">
<meta property="og:image" content="https://bmaker.kr/assets/og.png">
<meta property="og:locale" content="ko_KR">
<link rel="canonical" href="https://bmaker.kr/schedule">
<link rel="icon" type="image/png" href="assets/icon-192.png">
<link rel="apple-touch-icon" href="assets/apple-touch-icon.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Noto+Serif+KR:wght@600;700&display=swap">
<script type="application/ld+json">{crumb}</script>
{style}
{TBL}
</head>
<body>
{hdr}
<section class="hero">
  <div class="wrap">
    <p class="crumb"><a href="/">홈</a> › 접수 일정</p>
    <h1 class="serif">정책자금 접수 일정</h1>
    <p>상태는 날짜 기준으로 매일 자동 갱신됩니다. 세부 조건은 각 자금 페이지와 공식 공고가 기준입니다.</p>
  </div>
</section>
<main>
  <div class="wrap">
    <p class="asof">기준일 {TODAY.year}년 {TODAY.month}월 {TODAY.day}일 · 일정은 기관 공고에 따라 변경될 수 있으며, 각 항목의 '최종 확인일'을 함께 보세요. 목록은 계속 추가됩니다.</p>
    {sch_rows}
    <div class="callout"><p>정책자금은 대출이며 상환 의무가 있습니다. 접수 기간·요건은 각 기관 공고가 기준이고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. {FEE}</p></div>
    <div class="related">
      <p class="t">함께 보기</p>
      <a href="/cases">실행 기록</a>
      <a href="/sojingong">소상공인 정책자금</a>
      <a href="/jaedan">신용보증재단 사업자대출</a>
      <a href="/chaksugeum">착수금 사기 구별법</a>
    </div>
    <div class="cta-box">
      <h3 class="serif">어느 자금이 내 차례인지</h3>
      <p>지금 열려 있는 자금 중 내 조건에 맞는 트랙을 무료로 진단해 드립니다.</p>
      <a class="btn btn-kakao" href="http://pf.kakao.com/_GKuxfn/chat" target="_blank" rel="noopener">카카오톡 무료 진단</a>
      <a class="btn btn-tel" href="tel:1666-2425">전화 1666-2425</a>
    </div>
  </div>
</main>
{foot}
</body>
</html>
'''
    (ROOT/'schedule.html').write_text(sch, encoding='utf-8')
    # llms.txt 일정 줄 갱신 (있으면 교체, 없으면 삽입)
    lt=(ROOT/'llms.txt').read_text(encoding='utf-8')
    open_names=[d['자금명'] for d in F if status_of(d)[0]=='open']
    line=f"- [정책자금 접수 일정](https://bmaker.kr/schedule): 상태별 자동 갱신 일정표 — 자금별 팩트 페이지(실측·공고 링크) {len(F)}종 연결" + (f". 현재 접수 중: {', '.join(open_names)}" if open_names else "")
    if '- [정책자금 접수 일정]' in lt: lt=re.sub(r'- \[정책자금 접수 일정\][^\n]*', line, lt)
    else: lt=lt.replace('- [신용보증재단 사업자대출]', line+'\n- [신용보증재단 사업자대출]')
    (ROOT/'llms.txt').write_text(lt, encoding='utf-8')
    # sitemap upsert (schedule + 자금 페이지)
    sm=(ROOT/'sitemap.xml').read_text(encoding='utf-8')
    for slug in ['schedule']+[d['자금ID'] for d in F]:
        loc=f"https://bmaker.kr/{slug}"
        if loc+"</loc>" in sm:
            sm=re.sub(r'(<loc>'+re.escape(loc)+r'</loc><lastmod>)[^<]+', r'\g<1>'+str(TODAY), sm)
        else:
            sm=sm.replace('</urlset>', f'  <url><loc>{loc}</loc><lastmod>{TODAY}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>\n</urlset>')
    (ROOT/'sitemap.xml').write_text(sm, encoding='utf-8')
    print(f"[자금 빌드 OK] {len(F)}개 자금 페이지 + schedule.html 생성 (기준일 {TODAY})")

if __name__=='__main__':
    build()
