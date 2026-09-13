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
    # 시트 원본은 보존하고 공식 공고 대조 결과만 별도로 적용한다.
    verification_path = ROOT / "data" / "funds.verification.json"
    checks = json.loads(verification_path.read_text(encoding="utf-8")) if verification_path.exists() else {}
    for row in rows:
        row.update(checks.get(row["자금ID"], {}))
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
    observed = d.get('접수 관측')
    checked = d.get('접수 확인일', '미확인')
    if observed == '분기마감':
        return ('closed', f'3분기 마감 · 4분기 추후 안내 ({checked} 확인)', 4)
    if observed == '접수중표시':
        return ('check', f'공식화면 접수중 표시 ({checked} 확인) · 소진 여부 재확인', 3)
    if observed == '예정':
        if datetime.date.fromisoformat(d['접수 시작일']) > TODAY:
            return ('soon', f"공고상 {d['접수 시작일']} 10:00 예정 · 변경 가능", 2)
        return ('check', f'공고상 시작일 경과 · 현재 접수 재확인 ({checked} 확인)', 3)
    if d.get('회차 확인') == '미확인':
        return ('check', '회차 공고·현재 접수 여부 확인 필요', 3)
    s,e = d['접수 시작일'], d['접수 마감일']
    def pd(v): return datetime.date.fromisoformat(v)
    if d['접수 상태'] in ('마감', '종료'): return ('closed','기관 확인 마감 · 다음 공고 확인', 4)
    if d['접수 상태']=='상시': return ('check','상시형 · 현재 접수 여부 확인 필요', 3)
    if s and pd(s)>TODAY: return ('soon', f"접수 예정 · {s} 시작", 2)
    if s and pd(s)<=TODAY:
        if '소진' in e: return ('check','공고상 시작일 경과 · 잔여 예산 확인 필요', 3)
        if e and pd(e)>=TODAY: return ('open', f"공고상 접수 기간 · {e} 마감", 0 if (pd(e)-TODAY).days<=14 else 1)
        if e and pd(e)<TODAY: return ('closed', f"접수 마감 ({e}) · 다음 공고 대기", 4)
    return ('check','접수 일정: 최신 공고 확인 필요', 3)

TITLE_OVERRIDES = {
 'hyeoksin-jolup': '혁신성장촉진자금(소상공인졸업후보) 2026 — 졸업후보기업 조건·확인법·신청 방법',
}
EXTRA_SECTIONS = {
 'hyeoksin-jolup': """<h2>소상공인 졸업후보기업이란 — 조건과 확인법</h2>
<p><b>졸업후보기업</b>은 소상공인 기준(업종별 상시근로자 수·매출 규모)을 막 넘어서거나 넘어서기 직전인 <b>성장 단계 사업자</b>를 뜻합니다. 소상공인 지원의 문턱은 넘었는데 중소기업 정책자금의 규모에는 아직 못 미치는 구간이라, 이 구간을 위해 설계된 자금이 혁신성장촉진자금(소상공인졸업후보)입니다.</p>
<p><b>확인법:</b> ① 최근 결산 기준 매출과 상시근로자 수를 업종별 소상공인 기준과 대조 ② 공고의 대상 요건(졸업 시점·업력·제외 업종) 확인 ③ 소상공인확인서 발급 이력 확인. 요건 해석이 갈리는 경계 사업자가 많아, 진단에서 자주 다루는 질문입니다.</p>
<p><b>함께 보는 자금:</b> 매출이 이미 소기업 규모면 <a href="/jungjingong">중소기업 정책자금(중진공·기보·신보)</a>, 아직 소상공인 구간이면 <a href="/sojingong">소상공인 정책자금 직접대출</a>, 사회적 성격의 조직이면 <a href="/hyeoksin-sahoe">혁신성장촉진자금(사회연대경제조직)</a>이 대안 경로입니다.</p>"""
}

def build():
    F=load()
    style=re.search(r'<style>.*?</style>', (ROOT/'sojingong.html').read_text(encoding='utf-8'), re.S).group(0)
    hdr=re.search(r'<header>.*?</header>', (ROOT/'jaedan.html').read_text(encoding='utf-8'), re.S).group(0)
    foot=re.search(r'<footer>.*?</footer>', (ROOT/'jaedan.html').read_text(encoding='utf-8'), re.S).group(0)
    TBL='<style>.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;margin:18px 0}table{border-collapse:collapse;width:100%;min-width:520px;font-size:.88rem}th{background:var(--navy);color:#fff;padding:10px 12px;text-align:left;white-space:nowrap;font-weight:600}td{padding:10px 12px;border-top:1px solid var(--line);color:#3A4356;vertical-align:top}tr:nth-child(even) td{background:#FAFBFD}td a,p.badge a{color:var(--blue-deep);text-decoration:underline}.cta-inline{display:flex;flex-wrap:wrap;align-items:center;gap:14px;background:var(--navy);border-radius:12px;padding:18px 22px;margin:26px 0}.cta-inline p{color:#EAF0FA;margin:0;font-size:.94rem;flex:1 1 260px;line-height:1.55}.cta-inline p b{color:#fff}.cta-inline .tel{color:#fff;text-decoration:underline;font-size:.9rem;white-space:nowrap}.badge{display:inline-block;border-radius:999px;padding:7px 16px;font-size:.86rem;font-weight:600;margin:4px 0 14px}.b-open{background:#E7F5EC;color:#116A36;border:1px solid #BFE4CC}.b-soon{background:#EAF1FF;color:#1D4FB8;border:1px solid #C9DAF8}.b-closed{background:#F3F4F7;color:#5A6474;border:1px solid var(--line)}.b-check{background:#FFF6D5;color:#7A5A00;border:1px solid #F0DFA0}</style>'
    inst_page={'소상공인시장진흥공단':'/sojingong'}
    for d in F:
        C=cases_for(d['원장 키워드'])
        badge_cls, badge_txt, _ = status_of(d)
        amts=[int(r['실행 금액(만원)']) for r in C]
        rates=sorted({r['금리'].split('(')[0].strip() for r in C if r['금리']})
        rng=(won2(min(amts)) if min(amts)==max(amts) else f"{won2(min(amts))}~{won2(max(amts))}") if C else ""
        rr=("" if not rates else (f" · {rates[0]}" if rates[0]==rates[-1] else f" · {rates[0]}~{rates[-1]}"))
        meas_sum = (f"실행 기록 {len(C)}건 · {rng}{rr}") if C else "같은 기관 실행 기록으로 보는 심사·진행 구조"
        kind_short = "소진공 직접대출" if "직접" in d["카테고리"] else ("보증 연계 대리대출" if "대리" in d["카테고리"] else d["카테고리"])
        title_txt = (f"{d['자금명']} 2026 — 조건·한도·신청 방법, 실행 기록 {len(C)}건" if C else f"{d['자금명']} 2026 — 대상·조건·신청 방법 | {kind_short}")
        title_txt = TITLE_OVERRIDES.get(d['자금ID'], title_txt)
        Cshow=sorted(C, key=lambda r:(r["실행 연월"], r["사례ID"]), reverse=True)[:10]
        rows_html="".join(
          f'<tr><td>{r["실행 연월"]}</td><td>{esc(r["지역(시도)"])} {esc(r["업종"]) or ""}</td><td>{won2(r["실행 금액(만원)"])}</td><td>{esc(r["금리"]) or "—"}</td><td>{esc(r["상환 조건"]) or "—"}</td><td>{(str(int(float(r["소요일"]))) + "일") if r["소요일"] else "—"}</td><td><a href="/cases#case-{r["사례ID"]}">실행 기록</a></td></tr>' for r in Cshow)
        if C:
            meas_html=(f'<h2>기록된 실측</h2>\n<p>저희가 실제 실행한 {esc(d["자금명"])} 기록입니다 — 금리는 각 실행 시점 기준이며, 전체 맥락은 <a href="/cases">공개 실행 기록</a>에서 확인할 수 있습니다.</p>\n<div class="tablewrap"><table><thead><tr><th>실행</th><th>지역·업종</th><th>금액</th><th>금리</th><th>상환</th><th>소요</th><th>근거</th></tr></thead><tbody>'+rows_html+'</tbody></table></div>')
        else:
            P=peer_cases(d['기관'])
            steps='신청 시스템 접수 → 공단 심사 → 약정·실행' if '직접' in d['카테고리'] else '상품별 신청요건 확인 → 필요 시 보증심사 → 은행 심사·대출 실행'
            if P:
                pa=[int(r['실행 금액(만원)']) for r in P]
                pr=rate_range([r['금리'] for r in P])
                prow="".join(f'<tr><td>{r["실행 연월"]}</td><td>{esc(r["자금명"])[:26]}</td><td>{won2(r["실행 금액(만원)"])}</td><td>{esc(r["금리"]) or "—"}</td><td><a href="/cases#case-{r["사례ID"]}">기록</a></td></tr>' for r in P[:3])
                kind_desc='소상공인시장진흥공단이 직접 심사하고 직접 실행하는 자금입니다. 은행 문턱과 별개의 정책 심사라, 조건이 맞으면 신용·이력에 사연이 있어도 열립니다.' if '직접' in d['카테고리'] else '은행이 심사·실행하는 자금입니다. 상품에 따라 보증서·신용·담보 방식이 다르며, 보증료와 이차보전 여부도 확인합니다.'
                memo_line=(esc(d['한 줄 메모'])+'. ') if d['한 줄 메모'] else ''
                meas_html=(f'<h2>{esc(d["자금명"])}은 어떤 자금인가</h2>\n<p>{memo_line}{kind_desc} 진행 순서는 {steps} — 대상·한도 등 세부 요건은 위 공식 공고가 기준입니다.</p>\n'
                           +f'<h2>{esc(d["기관"])} 실행 기록</h2>\n<p>같은 기관 경로로 저희가 실행한 기록 중 최근 3건입니다({len(P)}건 · {won2(sum(pa))}'
                           +(f' · 금리 {pr}' if pr else '')
                           +f'). 자금별 조건은 달라도 심사 감각과 진행 구조의 기준점이 됩니다 — 전체는 <a href="/cases">공개 실행 기록</a>에.</p>\n'
                           +'<div class="tablewrap"><table><thead><tr><th>실행</th><th>자금</th><th>금액</th><th>금리</th><th>근거</th></tr></thead><tbody>'+prow+'</tbody></table></div>')
            else:
                kind_desc='소상공인시장진흥공단이 직접 심사·실행하는 자금입니다.' if '직접' in d['카테고리'] else '은행이 심사·실행하며 보증서 필요 여부는 상품별로 확인합니다.'
                meas_html=f'<h2>{esc(d["자금명"])}은 어떤 자금인가</h2>\n<p>{(esc(d["한 줄 메모"])+". ") if d["한 줄 메모"] else ""}{kind_desc} 진행 순서는 {steps} — 세부 요건은 위 공식 공고가 기준이며, 실행 기록 전체는 <a href="/cases">여기</a>에 있습니다.</p>'
        facts=[]
        if d['대상 요약']: facts.append(('대상', esc(d['대상 요약'])))
        if d['한도']: facts.append(('한도', esc(d['한도'])))
        if d['금리 방식']: facts.append(('금리 방식', esc(d['금리 방식'])))
        facts.append(('접수', esc(badge_txt)))
        facts.append(('공고', f'<a href="{esc(d["공고 링크"])}" target="_blank" rel="noopener">{esc(d.get("공고 표기", "기관 안내"))} 확인 →</a>'))
        facts_html="".join(f'<tr><td style="white-space:nowrap"><b>{k}</b></td><td>{v}</td></tr>' for k,v in facts)
        svc=json.dumps({"@context":"https://schema.org","@type":"Service","name":f"{d['자금명']} 진단·실행 지원","serviceType":"정책자금 진단 및 실행 지원","provider":{"@type":"Organization","@id":"https://bmaker.kr/#org","name":"비즈니스 메이커","url":"https://bmaker.kr/"},"areaServed":"KR","url":f"https://bmaker.kr/{d['자금ID']}"}, ensure_ascii=False)
        crumb=json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"홈","item":"https://bmaker.kr/"},{"@type":"ListItem","position":2,"name":"접수 일정","item":"https://bmaker.kr/schedule"},{"@type":"ListItem","position":3,"name":d['자금명'],"item":f"https://bmaker.kr/{d['자금ID']}"}]}, ensure_ascii=False)
        inst_link=inst_page.get(d['기관'],'/sojingong')
        page=f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{esc(title_txt)}</title>
<meta name="description" content="{esc(d['자금명'])} — {esc(d['기관'])} {esc(kind_short)}. {esc(d['한 줄 메모']) if d['한 줄 메모'] else '대상·한도·금리·신청 기간과 공식 공고 기준 요건'}. {esc(meas_sum)}. 착수금 없이 무료 진단, 실행 시에만 성공보수.">
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
    <p class="asof">기존 조건자료 확인일 {esc(d['최종 확인일'])} · 연간 공고 대조일 {esc(d.get('연간공고 확인일', '미확인'))} · 접수 안내 확인일 {esc(d.get('접수 확인일', '미확인'))}. 접수 표시는 확인 시점의 안내이며 잔여 예산을 뜻하지 않습니다. 대상·한도·금리 등 세부 요건은 각 회차 공고가 기준입니다 — 위 공식 공고 링크에서 확인하세요. 접수 일정 전체는 <a href="/schedule">일정 페이지</a>에 있습니다.</p>
    {meas_html}
    {EXTRA_SECTIONS.get(d["자금ID"],"")}
    <div class="cta-inline"><p><b>이 자금, 내 조건에 되는지</b> — 업종·매출·신용·이력만 주시면 방향을 잡아드립니다. 가능성이 낮으면 낮다고 먼저 말씀드립니다.</p><a class="btn btn-kakao" href="https://pf.kakao.com/_GKuxfn/chat" target="_blank" rel="noopener">카카오톡 무료 진단</a><a class="tel" href="tel:1666-2425">전화 1666-2425</a></div>
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
        if '갚' in page: die(f"{d['자금ID']}: 생성물에 '갚' 포함")
        if re.search(r'보장(?!하지)', page.replace('결과를 보장하지','')): die(f"{d['자금ID']}: 생성물에 '보장' 포함")
        (ROOT/f"{d['자금ID']}.html").write_text(page, encoding='utf-8')
    # /schedule
    order={'open':0,'soon':1,'check':2,'closed':3}
    def cat_of(d):
        c=d['카테고리']
        return '직접대출' if '직접' in c else ('대리대출' if '대리' in c else '기타')
    CAT_DESC={'직접대출':'소상공인시장진흥공단이 직접 대출을 실행하는 트랙입니다.',
              '대리대출':'은행이 심사·실행하는 경로입니다. 상품에 따라 보증서·신용·담보 방식 등을 확인합니다.',
              '기타':'그 외 트랙입니다.'}
    sch_rows=""
    for cat in ('직접대출','대리대출','기타'):
        group=sorted(((d, *status_of(d)) for d in F if cat_of(d)==cat), key=lambda x:(order[x[1]], x[3]))
        if not group: continue
        rows="".join(f'<tr><td><a href="/{d["자금ID"]}"><b>{esc(d["자금명"])}</b></a></td><td>{esc(d["기관"])}</td><td><span class="badge b-{cls}" style="margin:0">{esc(txt)}</span></td><td>{esc(d["다음 회차 메모"]) or "—"}</td><td>{esc(d["최종 확인일"])}</td><td><a href="{esc(d["공고 링크"])}" target="_blank" rel="noopener">{esc(d.get("공고 표기", "기관 안내"))}</a></td></tr>' for d,cls,txt,_ in group)
        sch_rows+=f'<h2>{cat} ({len(group)})</h2>\n<p>{CAT_DESC[cat]}</p>\n<div class="tablewrap"><table><thead><tr><th>자금</th><th>기관</th><th>상태</th><th>메모</th><th>자료 확인일</th><th>출처</th></tr></thead><tbody>{rows}</tbody></table></div>\n'
    crumb=json.dumps({"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":[{"@type":"ListItem","position":1,"name":"홈","item":"https://bmaker.kr/"},{"@type":"ListItem","position":2,"name":"정책자금 접수 일정","item":"https://bmaker.kr/schedule"}]}, ensure_ascii=False)
    sch=f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>정책자금 접수 일정 2026 — 접수 중·예정 자금 한눈에, 공고 기준 신청 기간 (매일 갱신) | 비즈니스 메이커</title>
<meta name="description" content="소상공인·중소기업 정책자금의 공고상 신청 기간과 자료 확인일을 정리합니다. 기관의 현재 접수 여부와 잔여 예산은 신청 전 최신 공고에서 확인하세요.">
<meta property="og:type" content="website">
<meta property="og:title" content="정책자금 접수 일정 — 공고상 신청 기간·확인일">
<meta property="og:description" content="공고상 일정과 자료 확인일 안내. 현재 접수 여부·잔여 예산은 기관 확인이 필요합니다.">
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
    <p>예정 일정은 날짜 기준으로 계산합니다. 기관의 실시간 접수·예산 상태를 자동 확인하는 것은 아닙니다. 신청 전 기관 안내의 최신 공고를 확인해 주세요.</p>
  </div>
</section>
<main>
  <div class="wrap">
    <p class="asof">일정 계산일 {TODAY.year}년 {TODAY.month}월 {TODAY.day}일 · 조건자료 확인일은 각 행에 보존하고, 접수 안내 확인일은 메모에 구분합니다. 접수중 표시는 확인 시점의 공식 안내이며 잔여 예산을 뜻하지 않습니다. 신청 전 소상공인정책자금의 회차 공고를 확인하세요.</p>
    {sch_rows}
    <div class="callout"><p>정책자금은 대출이며 상환 의무가 있습니다. 접수 기간·요건은 각 기관 공고가 기준이고, 비즈니스 메이커는 특정 결과를 보장하지 않습니다. {FEE}</p></div>
    <div class="related">
      <p class="t">함께 보기</p>
      <a href="/gaein">개인사업자 정책자금 총정리</a>
      <a href="/cases">실행 기록</a>
      <a href="/sojingong">소상공인 정책자금</a>
      <a href="/jaedan">신용보증재단 사업자대출</a>
      <a href="/chaksugeum">착수금 사기 구별법</a>
    </div>
    <div class="cta-box">
      <h3 class="serif">어느 자금이 내 차례인지</h3>
      <p>사업 조건과 자금 용도를 바탕으로 검토할 경로와 확인할 공고를 정리해 드립니다. 상담은 무료입니다.</p>
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
