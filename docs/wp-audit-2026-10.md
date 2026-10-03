# 워드프레스 블로그 노출 정지 진단 + 카니발 점검 (2026-10)

- 진단일: 2026-10-04 · 6절 GSC 확인 추가(같은 날) · 진단만 수행, **코드·DNS·워드프레스 설정 변경 없음**
- 대상: `blog.bmaker.kr`(WordPress.com) · `bmaker.kr`(origin/main `8b88b73`, 2026-10-03 기준)
- 표기: **[사실]** = 이번에 직접 확인한 것 · **[추정]** = 증거에서 끌어낸 판단 · **[대표 확인 필요]** = 접근 권한이 없어 확인 못 한 것

---

## 0. 전제 확인

| 항목 | 결과 | 근거 |
|---|---|---|
| 워드프레스 주소 | **`https://blog.bmaker.kr/`** — 있음 | WP REST `/wp-json/` 응답, `Link: <https://wp.me/PhqmPi-5>` |
| 호스팅 | WordPress.com(Automattic) | A 레코드 `192.0.78.24`, `192.0.78.25` · `Server-Timing: a8c-cdn` · 사이트맵 생성기 `jetpack-16.3` |
| DNS 존 | `bmaker.kr` 은 Cloudflare(`albert`/`rayne.ns.cloudflare.com`) | 공개 NS 조회 |
| blog 프록시 상태 | **DNS 전용(회색 구름)** [추정 — 강함] | 프록시가 켜져 있으면 Cloudflare IP가 나와야 하는데 WordPress.com IP가 그대로 나옴. CNAME 아님(A 레코드) |
| Cloudflare 설정 직접 조회 | **못 함** | wrangler OAuth 토큰 만료(2026-09-13), 토큰 범위에 DNS 레코드 읽기 권한(`dns_records:read`) 없음. 갱신하면 설정 파일을 다시 써야 해서 하지 않음 |
| 저장소 흔적 | `wrangler.jsonc` 에 WP 관련 설정 없음. 본문 링크만 있음: `funding.html:63`, `docs/funding-guides.json:88` → `blog.bmaker.kr/support-programs/` | `git grep origin/main` |
| 비교 대상 `bmaker.kr/blog`·`posts/*.md` | **없음** — 어느 원격 브랜치에도 `posts/` 디렉터리가 없고, `https://bmaker.kr/blog` 는 404 | `git ls-tree` 전 브랜치, curl |

→ 3단계 대조는 `posts/*.md` 대신 **bmaker.kr 전체 페이지 90개**(루트·`/industry/`·`/region/`)와 했다.

---

## 1. 크롤 가능 여부 (크롤러의 눈)

| 검사 | 결과 | 판정 |
|---|---|---|
| `curl -sIL https://blog.bmaker.kr/` | `HTTP/1.1 200`, 리다이렉트 없음, `X-Robots-Tag` 없음 | 정상 |
| 홈 `<meta name="robots">` | 없음 · canonical = `https://blog.bmaker.kr/` | 정상 ("검색엔진 차단"이 켜져 있지 않음) |
| 글 2개(`/2027-kriss-technology-home-doctor/`, `/loan-consultation-brief/`) | 200 · `robots = max-image-preview:large`(noindex 없음) · 자기 자신 canonical | 정상 |
| `robots.txt` | `User-agent: * / Disallow: /wp-admin/` · AI 봇(GPTBot·ClaudeBot·Google-Extended·CCBot 등)만 전체 차단 · Sitemap 2개 선언 | 일반 검색봇 허용 — 정상 |
| `/sitemap.xml` | 200 (Jetpack 인덱스 → `sitemap-1.xml` 40 URL, `image-sitemap-1.xml`) · lastmod 2026-10-01 | 정상 |
| `/sitemap_index.xml`, `/wp-sitemap.xml` | 404 | 정상 (WordPress.com 은 `/sitemap.xml` 을 씀) |
| `/news-sitemap.xml` | 200 | 정상 |
| 위장 Googlebot·bingbot UA | **403** (일반 브라우저 UA·네이버 Yeti UA 는 200) | 정상일 가능성 높음 [추정]: 같은 위장 UA로 `bmaker.kr` 은 200 → Cloudflare가 아니라 WordPress.com이 **IP 검증 안 된 가짜 검색봇**을 막는 동작. 진짜 Googlebot 통과 여부는 GSC URL 검사로만 확정 가능 [대표 확인 필요] |
| Cloudflare WAF·봇 차단·캐시 규칙 | blog 가 DNS 전용이라 Cloudflare 를 거치지 않음 → 적용될 수 없음 [추정] | 차단 원인 아님 |

**1단계 결론 [사실]: noindex·robots 차단·리다이렉트·사이트맵 오류 없음. 기술적으로 크롤이 막힌 흔적은 없다.**

---

## 2. 검색엔진 등록 상태

| 항목 | 결과 |
|---|---|
| GSC `blog.bmaker.kr` 속성 존재 여부·색인 요약 | **[대표 확인 필요]** — 이 PC에 GSC API 인증(gcloud·서비스 계정) 없음, gh CLI 없음. 저장소의 GSC 원자료(`docs/search-data/2026-09/`)는 전부 `https://bmaker.kr/` 속성뿐이고 blog 속성 자료는 없음 |
| Bing `site:blog.bmaker.kr` | Bing 이 `site:` 를 무시하고 무관한 결과(농협 인터넷뱅킹)를 돌려줌 → **Bing 색인 사실상 0건에 가까움** [사실] |
| Bing `blog.bmaker.kr` 일반 검색 | blog URL **2건** 노출: `/privacy`, `/loan-consultation-brief` [사실] (나머지 결과는 bmaker.kr·네이버 블로그·스레드·인스타) |
| Bing `site:bmaker.kr` 대조군 | Bing 이 봇 확인 과제(CAPTCHA)를 띄움 — 풀지 않고 중단 |

---

## 3. 카니발(중복) 점검

### 3-1. 워드프레스 전체 목록 (WP REST API, 글 31 + 페이지 9)

출처: `https://blog.bmaker.kr/wp-json/wp/v2/posts?per_page=100` (`X-WP-Total: 31`), `/pages` (`X-WP-Total: 9`)

| # | 종류 | 발행일 | URL | 제목 | 본문 글자 수 |
|---|---|---|---|---|---|
| 1 | 페이지 | 2026-09-21 | `/` | 정책자금·사업자대출 실무 가이드 | 3,336 |
| 2 | 페이지 | 2026-09-21 | `/about-editorial/` | 운영자와 편집 기준 | 1,322 |
| 3 | 페이지 | 2026-09-21 | `/application-calendar/` | 정책자금 접수 일정 | 2,752 |
| 4 | 페이지 | 2026-09-21 | `/diagnosis/` | 무료 진단은 어떻게 진행되나요? | 1,021 |
| 5 | 페이지 | 2026-09-21 | `/funding-guide/` | 정책자금·사업자대출 안내 | 1,807 |
| 6 | 페이지 | 2026-09-21 | `/policy-news/` | 사업자 정책·지원사업 뉴스 | 1,542 |
| 7 | 페이지 | 2026-09-21 | `/practical-guides/` | 실무 가이드 | 1,306 |
| 8 | 페이지 | 2026-09-21 | `/privacy/` | 개인정보·이용 안내 | 2,135 |
| 9 | 페이지 | 2026-09-21 | `/support-programs/` | 사업자 지원정보 찾기 | 3,150 |
| 10 | 글 | 2026-09-21 | `/2026-product-improvement-round5/` | 2026년 5차 소상공인 상품개선 지원사업: 대상·기간·신청 경로 | 1,377 |
| 11 | 글 | 2026-09-21 | `/2026-q4-policy-funding-schedule/` | 2026년 4분기 소상공인 정책자금 접수 일정: 10월 준비사항 | 1,273 |
| 12 | 글 | 2026-09-21 | `/application-supplement-log/` | 정책자금 서류 보완 요청을 받았을 때 정리하는 방법 | 1,680 |
| 13 | 글 | 2026-09-21 | `/business-funding-workshop/` | 기업 정책자금 교육, 대표와 실무자가 함께 준비할 워크숍 | 1,515 |
| 14 | 글 | 2026-09-21 | `/cash-flow-13-weeks/` | 사업자대출 신청 전 13주 자금계획표 만드는 법 | 1,823 |
| 15 | 글 | 2026-09-21 | `/consulting-scope-checklist/` | 정책자금 컨설팅 계약 전 확인할 업무 범위와 비용 질문 | 1,806 |
| 16 | 글 | 2026-09-21 | `/emergency-business-stability-funding/` | 소상공인 긴급경영안정자금: 재해피해·일시적경영애로 신청 경로 | 1,342 |
| 17 | 글 | 2026-09-21 | `/equipment-funding-evidence/` | 시설자금 상담 전, 장비 견적서에서 확인할 8가지 | 1,614 |
| 18 | 글 | 2026-09-21 | `/existing-business-loans-list/` | 기존 사업자대출이 있을 때, 추가 상담 전 정리할 부채 목록 | 1,600 |
| 19 | 글 | 2026-09-21 | `/general-business-stability-funding/` | 일반경영안정자금 신청 안내: 업력·접수기관·대리대출 절차 | 1,354 |
| 20 | 글 | 2026-09-21 | `/guarantee-bank-questions/` | 보증서 대출 상담, 보증기관과 은행에 따로 물어볼 질문 | 1,563 |
| 21 | 글 | 2026-09-21 | `/innovation-growth-funding/` | 혁신성장촉진자금 신청 안내: 대상·한도·기관·접수 방식 | 1,624 |
| 22 | 글 | 2026-09-21 | `/kibo-technology-guarantee/` | 기술보증기금 대출 준비: 기술평가·보증·은행 절차 | 1,748 |
| 23 | 글 | 2026-09-21 | `/kodit-business-guarantee/` | 신용보증기금 사업자대출: 보증 상담부터 은행 실행까지 | 1,484 |
| 24 | 글 | 2026-09-21 | `/kosmes-business-rebound/` | 중진공 재도약지원자금: 재창업·구조개선·사업전환 구분 | 1,540 |
| 25 | 글 | 2026-09-21 | `/kosmes-growth-foundation/` | 중진공 신성장기반자금: 제조업·시설투자 기업의 준비 순서 | 1,537 |
| 26 | 글 | 2026-09-21 | `/kosmes-startup-commercialization/` | 중진공 혁신창업사업화자금: 창업기반지원·개발기술사업화 준비 | 1,470 |
| 27 | 글 | 2026-09-21 | `/loan-consultation-brief/` | 사업자대출 상담 전, 한 장으로 정리할 7가지 | 1,759 |
| 28 | 글 | 2026-09-21 | `/manufacturing-small-business-funding/` | 소공인특화자금 일반 유형: 제조업 대상·한도·신청 방법 | 1,620 |
| 29 | 글 | 2026-09-21 | `/regional-credit-guarantee/` | 지역신용보증재단 사업자대출: 관할·보증료·신청 방법 | 1,742 |
| 30 | 글 | 2026-09-21 | `/restart-special-funding/` | 재도전특별자금 신청 안내: 일반형·희망형·도약형 차이 | 1,576 |
| 31 | 글 | 2026-09-21 | `/youth-employment-funding/` | 청년고용연계자금 신청 안내: 대상·4분기 일정·확인서 이후 절차 | 1,654 |
| 32 | 글 | 2026-09-22 | `/government-business-loans/` | 정부지원대출·정부정책자금: 사업자 신청기관 찾는 법 | 1,768 |
| 33 | 글 | 2026-09-22 | `/microfinance-business-guide/` | 미소금융재단·미소금융 대출: 공식 상담 전 준비 질문 | 1,667 |
| 34 | 글 | 2026-09-22 | `/small-business-policy-loans/` | 소상공인 정책자금 대출·소진공 대출 신청 전 확인표 | 1,618 |
| 35 | 글 | 2026-09-22 | `/sme-policy-loan-guide/` | 중소기업 대출·중진공 정책자금 대출 비교 질문 7가지 | 1,901 |
| 36 | 글 | 2026-09-28 | `/2026-kibo-factoring-september-october/` | 기보 중소기업팩토링 10월 심사 재개: 처리 순서와 실행 지연 안내 | 1,258 |
| 37 | 글 | 2026-09-28 | `/2026-kodit-ibk-startup-buildup/` | 신보·기업은행 스타트업 빌드업: 단계별 보증과 신청 전 확인사항 | 880 |
| 38 | 글 | 2026-09-28 | `/2026-kodit-woori-youth-guarantee/` | 신보·우리은행 청년창업 보증 협약: 대상·비용·접수 전 확인사항 | 872 |
| 39 | 글 | 2026-10-01 | `/2026-october-regional-business-funding/` | 10월 지역 소상공인 정책자금: 서울 중구·순천·양산·충주 신청 경로 | 2,364 |
| 40 | 글 | 2026-10-01 | `/2027-kriss-technology-home-doctor/` | 2027 KRISS 기술홈닥터: 제조 중소기업 기술지원 신청 준비 | 1,493 |

### 3-2. 발행 패턴 [사실]

- 블로그 개설(첫 글·전 페이지) **2026-09-21**. 진단일 기준 개설 13일째.
- **9/21 18:35~18:38 사이 3분 동안 8개**, **23:38~23:56 사이 18분 동안 14개**, 9/22 00:36~00:41 사이 5분 동안 4개 → **이틀간 26개**. 이후 9/28 3개, 10/1 2개. 발행이 멈춘 것은 아니다(마지막 2026-10-01).
- 본문(메뉴·푸터 등 공통 영역 제외)은 872~2,364자, 중앙값 1,600자로 짧은 편이다. 소제목 틀이 반복된다: "자주 묻는 질문" 18개 글, "신청 전 함께 준비하세요"·"우리 사업에 적용할 조건이 헷갈린다면" 각 13개 글, "공식 근거/공식 확인 경로" 12개 글.
- 모든 글이 `bmaker.kr` 로 2~5개씩 링크한다.
- WP 글끼리 본문 유사도(5어절 자카드) 최대값: 중진공 3종(`/kosmes-growth-foundation/` ↔ `/kosmes-startup-commercialization/` 0.28, `/kosmes-business-rebound/` ↔ 같은 글 0.27, ↔ `/kosmes-growth-foundation/` 0.26). 나머지는 모두 0.22 미만.

### 3-3. bmaker.kr 과 겹치는 쌍

**방법.** ① 제목 핵심 명사(조사 떼고 2자 이상, "안내·신청·2026" 같은 일반어 제외) 3개 이상 일치 ② 본문 첫 200자 일치 ③ WP 본문 5어절 조각 중 bmaker 페이지에 있는 비율(아래 "본문 겹침")을 기계로 돌렸다.
- ② 첫 200자 일치: **0쌍.** ③ 본문 겹침 최대값 **3.1%**(미소금융). → **복붙 중복은 없다.**
- ① 기계 매칭은 "대출·보증·절차" 같은 일반어 때문에 `/kibo-technology-guarantee/` 가 재단 페이지 17개와 오탐됐다. 그래서 아래 표는 **자금·기관 이름(검색 의도) 기준으로 사람이 다시 짝지은 결과**다 — 이게 실제 카니발이다.

"먼저 발행": WP 발행일(첫 열 괄호)과 bmaker 생성일을 비교. GSC 노출은 bmaker.kr 쪽만 있다(WP 쪽은 [대표 확인 필요]). bmaker GSC 28일은 2026-08-21~09-17(수집 9/20)이라 WP 개설 전 기간이다.

| 강도 | WP 글 (발행일) | bmaker.kr 대응 페이지 | bmaker 생성일(git 최초 커밋) | bmaker GSC 28일 (클릭/노출/순위) | bmaker GSC 9/14~27 (클릭/노출) | 본문 겹침 |
|---|---|---|---|---|---|---|
| **강** | `/innovation-growth-funding/` 혁신성장촉진자금 신청 안내: 대상·한도·기관·접수 방식 (2026-09-21) | `/hyeoksin` 혁신성장촉진자금 신청 준비와 성장 근거 | 2026-08-29 | 8/279/5.9 | 3/147 | 0.0% |
| **강** | `/restart-special-funding/` 재도전특별자금 신청 안내: 일반형·희망형·도약형 차이 (2026-09-21) | `/jaedojeon` 재도전특별자금 재창업·채무조정 준비자료 | 2026-08-29 | 12/438/7.1 | 7/176 | 0.0% |
| **강** | `/youth-employment-funding/` 청년고용연계자금 신청 안내: 대상·4분기 일정·확인서 이후 절차 (2026-09-21) | `/cheongnyeon` 청년고용연계자금 신청 전 연령·업력·고용 확인 | 2026-08-29 | 5/460/7.3 | 3/427 | 0.0% |
| **강** | `/manufacturing-small-business-funding/` 소공인특화자금 일반 유형: 제조업 대상·한도·신청 방법 (2026-09-21) | `/sogongin` 소공인특화자금 제조업 설비·운전자금 준비 | 2026-08-29 | 3/126/6.5 | 2/59 | 0.0% |
| **강** | `/general-business-stability-funding/` 일반경영안정자금 신청 안내: 업력·접수기관·대리대출 절차 (2026-09-21) | `/ilban-gyeongyeong` 일반경영안정자금 2026 — 대상·조건·신청 방법 | 보증 연계 대리대출 | 2026-08-29 | 1/39/7.1 | 1/201 | 0.0% |
| **강** | `/emergency-business-stability-funding/` 소상공인 긴급경영안정자금: 재해피해·일시적경영애로 신청 경로 (2026-09-21) | `/gingeup` 긴급경영안정자금(일시적경영애로·대리대출) 2026 — 대상·조건·신청 방법 | 보증 연계 대리대출 | 2026-08-29 | 2/61/7.4 | 0/34 | 0.0% |
| **강** | `/emergency-business-stability-funding/` 소상공인 긴급경영안정자금: 재해피해·일시적경영애로 신청 경로 (2026-09-21) | `/ilsijeok` 일시적경영애로자금 2026 — 대상·조건·신청 방법 | 소진공 직접대출 | 2026-08-29 | 2/88/7.3 | 1/27 | 0.0% |
| **강** | `/kosmes-startup-commercialization/` 중진공 혁신창업사업화자금: 창업기반지원·개발기술사업화 준비 (2026-09-21) | `/jungjingong` 중소기업 정책자금 대출·중진공 대출 신청 준비 | 2026-08-20 | 1/177/6.2 | 0/86 | 0.0% |
| **강** | `/kosmes-growth-foundation/` 중진공 신성장기반자금: 제조업·시설투자 기업의 준비 순서 (2026-09-21) | `/jungjingong` 중소기업 정책자금 대출·중진공 대출 신청 준비 | 2026-08-20 | 1/177/6.2 | 0/86 | 0.0% |
| **강** | `/kosmes-business-rebound/` 중진공 재도약지원자금: 재창업·구조개선·사업전환 구분 (2026-09-21) | `/jungjingong` 중소기업 정책자금 대출·중진공 대출 신청 준비 | 2026-08-20 | 1/177/6.2 | 0/86 | 0.0% |
| **강** | `/kodit-business-guarantee/` 신용보증기금 사업자대출: 보증 상담부터 은행 실행까지 (2026-09-21) | `/sinbo` 신용보증기금 사업자대출 조건·한도 2026 — 신청 순서와 받은 사례 | 2026-08-29 | 0/62/8.1 | 1/77 | 0.0% |
| **강** | `/kibo-technology-guarantee/` 기술보증기금 대출 준비: 기술평가·보증·은행 절차 (2026-09-21) | `/gibo` 기술보증기금 대출 기술·사업 자료 준비 | 2026-08-29 | 1/43/9.3 | 2/50 | 0.0% |
| **강** | `/regional-credit-guarantee/` 지역신용보증재단 사업자대출: 관할·보증료·신청 방법 (2026-09-21) | `/jaedan` 신용보증재단 사업자대출 2026 — 17개 지역 조건·실측 금리·신청 절차 (보증부) | 2026-08-29 | 0/38/8.9 | 0/43 | 0.0% |
| **강** | `/small-business-policy-loans/` 소상공인 정책자금 대출·소진공 대출 신청 전 확인표 (2026-09-22) | `/sojingong` 소상공인 정책자금 대출 2026 — 직접대출·대리대출 조건·금리, 실행 기록 기준 | 2026-08-20 | 2/213/8.3 | 1/169 | 0.0% |
| **강** | `/sme-policy-loan-guide/` 중소기업 대출·중진공 정책자금 대출 비교 질문 7가지 (2026-09-22) | `/sme-business-loans` 중소기업 대출 비교 — 정책자금·보증부·은행 | 2026-09-22 | — (수집 후 생성) | 1/26 | 0.0% |
| **강** | `/sme-policy-loan-guide/` 중소기업 대출·중진공 정책자금 대출 비교 질문 7가지 (2026-09-22) | `/jungjingong` 중소기업 정책자금 대출·중진공 대출 신청 준비 | 2026-08-20 | 1/177/6.2 | 0/86 | 0.5% |
| **강** | `/government-business-loans/` 정부지원대출·정부정책자금: 사업자 신청기관 찾는 법 (2026-09-22) | `/funding` 정부지원대출·정부정책자금 사업자 상담 안내 | 2026-09-07 | 2/38/6.1 | 1/35 | 0.5% |
| **강** | `/microfinance-business-guide/` 미소금융재단·미소금융 대출: 공식 상담 전 준비 질문 (2026-09-22) | `/microfinance-business` 미소금융재단 대출 — 창업·운영자금 상담 준비 | 2026-09-22 | — (수집 후 생성) | 0/1 | 3.1% |
| **강** | `/2026-q4-policy-funding-schedule/` 2026년 4분기 소상공인 정책자금 접수 일정: 10월 준비사항 (2026-09-21) | `/2026-4q-sosangin` 2026년 4분기 소상공인 정책자금 접수 일정과 대상 | 2026-09-28 | — (수집 후 생성) | — | 0.0% |
| **강** | `/2026-q4-policy-funding-schedule/` 2026년 4분기 소상공인 정책자금 접수 일정: 10월 준비사항 (2026-09-21) | `/schedule` 정책자금 접수 일정 2026 — 공고상 신청 기간·확인일 | 2026-08-29 | 2/273/6.5 | 0/141 | 0.0% |
| **강** | `/application-calendar/` 정책자금 접수 일정 (2026-09-21) | `/schedule` 정책자금 접수 일정 2026 — 공고상 신청 기간·확인일 | 2026-08-29 | 2/273/6.5 | 0/141 | 0.0% |
| 인접 | `/existing-business-loans-list/` 기존 사업자대출이 있을 때, 추가 상담 전 정리할 부채 목록 (2026-09-21) | `/daehwan` 소상공인 대환대출 기존 대출 확인과 비교 | 2026-08-29 | 5/76/6.8 | 3/30 | 0.0% |
| 인접 | `/equipment-funding-evidence/` 시설자금 상담 전, 장비 견적서에서 확인할 8가지 (2026-09-21) | `/working-capital-facility` 운전자금·시설자금 차이와 대출 준비 예시 | 2026-09-21 | — (수집 후 생성) | 0/27 | 0.0% |
| 인접 | `/guarantee-bank-questions/` 보증서 대출 상담, 보증기관과 은행에 따로 물어볼 질문 (2026-09-21) | `/bojeung` 보증서 대출 신보·기보·재단 비교와 준비 | 2026-08-20 | 5/291/7.9 | 4/59 | 0.0% |
| 인접 | `/consulting-scope-checklist/` 정책자금 컨설팅 계약 전 확인할 업무 범위와 비용 질문 (2026-09-21) | `/chaksugeum` 정책자금 컨설팅 착수금·수수료 사기, 거르는 법 — 2026년 체크리스트 | 2026-08-28 | 0/24/5.1 | 0/21 | 0.0% |
| 인접 | `/application-supplement-log/` 정책자금 서류 보완 요청을 받았을 때 정리하는 방법 (2026-09-21) | `/geojeol` 정책자금 거절 사유 6가지와 회복 경로 — 다시 신청하기 전에 (2026) | 2026-08-28 | 2/31/4.3 | 2/37 | 0.0% |
| 인접 | `/business-funding-workshop/` 기업 정책자금 교육, 대표와 실무자가 함께 준비할 워크숍 (2026-09-21) | `/education` 소상공인·중소기업 정책자금 교육·출강 | 2026-09-09 | 1/10/4.8 | 1/14 | 0.0% |
| 인접 | `/2026-kibo-factoring-september-october/` 기보 중소기업팩토링 10월 심사 재개: 처리 순서와 실행 지연 안내 (2026-09-28) | `/gibo` 기술보증기금 대출 기술·사업 자료 준비 | 2026-08-29 | 1/43/9.3 | 2/50 | 0.0% |
| 인접 | `/2026-kodit-woori-youth-guarantee/` 신보·우리은행 청년창업 보증 협약: 대상·비용·접수 전 확인사항 (2026-09-28) | `/sinbo` 신용보증기금 사업자대출 조건·한도 2026 — 신청 순서와 받은 사례 | 2026-08-29 | 0/62/8.1 | 1/77 | 0.0% |
| 인접 | `/2026-kodit-ibk-startup-buildup/` 신보·기업은행 스타트업 빌드업: 단계별 보증과 신청 전 확인사항 (2026-09-28) | `/sinbo` 신용보증기금 사업자대출 조건·한도 2026 — 신청 순서와 받은 사례 | 2026-08-29 | 0/62/8.1 | 1/77 | 0.0% |
| **강** | `/funding-guide/` 정책자금·사업자대출 안내 (2026-09-21) | `/funding` 정부지원대출·정부정책자금 사업자 상담 안내 | 2026-09-07 | 2/38/6.1 | 1/35 | 0.0% |
| 인접 | `/diagnosis/` 무료 진단은 어떻게 진행되나요? (2026-09-21) | `/consulting` 정책자금 컨설팅, 무엇을 하고 어떻게 진행하나 | 2026-09-02 | 5/59/6.2 | 3/66 | 0.0% |

**정리 [사실]:**
- WP 글 31개 중 **26개**가 bmaker.kr 기존 페이지와 주제가 겹친다. 그중 **17개는 강한 겹침**(제목에 같은 자금·기관 이름 — 같은 검색어를 노림), 9개는 인접 주제(보증서 질문↔`/bojeung`, 서류 보완↔`/geojeol` 등). 페이지 `/funding-guide/`·`/application-calendar/` 도 강한 겹침, `/diagnosis/` 는 인접.
- 강한 겹침 17개 중 **15개는 bmaker 쪽이 2~4주 먼저**(8/20~9/7) 있었고(나머지 2개: 미소금융은 같은 날, 4분기 일정은 `/schedule` 이 먼저·`/2026-4q-sosangin` 은 WP가 먼저) 이미 GSC 노출이 있다 — 예: 재도전특별자금 `/jaedojeon` 28일 클릭 12·노출 438(사이트 1위 페이지), 청년고용연계자금 `/cheongnyeon` 노출 460, 혁신성장촉진자금 `/hyeoksin` 노출 279, 소진공 `/sojingong` 노출 213.
- **같은 날 양쪽에 동시에 생긴 쌍**: 미소금융(WP 9/22 ↔ bmaker 9/22), 중소기업 대출 비교(WP 9/22 ↔ `/sme-business-loans` 9/22), 시설자금(WP 9/21 ↔ `/working-capital-facility` 9/21).
- **WP가 먼저인 쌍**: 4분기 일정(WP 9/21 ↔ `/2026-4q-sosangin` 9/28).
- 겹치지 않는 고유 글: `/2026-product-improvement-round5/`, `/2026-october-regional-business-funding/`, `/2027-kriss-technology-home-doctor/`, `/cash-flow-13-weeks/`, `/loan-consultation-brief/` 와 페이지 `/support-programs/`·`/policy-news/`·`/about-editorial/`·`/practical-guides/`·`/privacy/`·홈.

---

## 4. bmaker.kr 도어웨이·카니발 위험 점검

### 4-1. `/region/*` 도시 페이지 19개 (2026-10-01 생성, 사이트맵 19/19 등록, 실서버 200·자기 canonical)

검사 함수는 저장소의 `tests/test_region.py`(규격 8-1)를 그대로 썼다. 고유 문장 비율 = 도시명을 지운 본문 문장 중 다른 도시 페이지에 없는 문장의 글자 비중. 템플릿 문장 비율 = 19개 중 절반 이상 페이지에 똑같이 있는 문장의 글자 비중.

| 도시 | 본문 글자 | 고유 문장 비율 | 템플릿 문장 비율 | 셈 사실 | 시·군 자금 | 재단 지점 | 소진공 센터 | 규칙 1 |
|---|---|---|---|---|---|---|---|---|
| `pyeongtaek` 평택시 | 2,417 | 51% | 49% | **3** | 1 | 1 | 1 | 통과 |
| `paju` 파주시 | 2,519 | 48% | 47% | **4** | 2 | 1 | 1 | 통과 |
| `yongin` 용인시 | 2,870 | 53% | 42% | **4** | 2 | 1 | 1 | 통과 |
| `seoul-gangseo` 서울 강서구 | 2,909 | 74% | 24% | **4** | 2 | 1 | 1 | 통과 |
| `ansan` 안산시 | 2,810 | 45% | 42% | **5** | 3 | 1 | 1 | 통과 |
| `seongnam` 성남시 | 2,662 | 48% | 45% | **5** | 3 | 1 | 1 | 통과 |
| `jeonju` 전주시 | 2,612 | 61% | 35% | **5** | 2 | 2 | 1 | 통과 |
| `gimhae` 김해시 | 3,349 | 64% | 27% | **5** | 3 | 1 | 1 | 통과 |
| `pohang` 포항시 | 2,819 | 64% | 32% | **5** | 3 | 1 | 1 | 통과 |
| `siheung` 시흥시 | 3,084 | 54% | 39% | **6** | 4 | 1 | 1 | 통과 |
| `bucheon` 부천시 | 3,076 | 55% | 39% | **6** | 4 | 1 | 1 | 통과 |
| `goyang` 고양시 | 2,926 | 58% | 38% | **6** | 3 | 2 | 1 | 통과 |
| `suwon` 수원시 | 3,057 | 60% | 36% | **6** | 3 | 2 | 1 | 통과 |
| `changwon` 창원시 | 3,228 | 62% | 28% | **6** | 2 | 3 | 1 | 통과 |
| `cheongju` 청주시 | 3,638 | 72% | 25% | **6** | 3 | 2 | 1 | 통과 |
| `anyang` 안양시 | 3,097 | 50% | 39% | **7** | 5 | 1 | 1 | 통과 |
| `gimpo` 김포시 | 3,047 | 54% | 39% | **7** | 5 | 1 | 1 | 통과 |
| `hwaseong` 화성시 | 3,378 | 63% | 33% | **7** | 4 | 2 | 1 | 통과 |
| `namyangju` 남양주시 | 3,766 | 68% | 32% | **8** | 6 | 1 | 1 | 통과 |

- 규칙 1(공식 출처 사실 3개 이상·시군 자금 1건 이상)·규칙 5(확인일 90일): **19/19 통과**
- 규칙 2(사실 조합 중복): **0쌍**
- 규칙 3(도시명 제외 5어절 자카드 > 0.6): **0쌍** · 평균 0.361

도시 간 본문 유사도 상위 5쌍 (기준 0.6):

| 순위 | 쌍 | 유사도 | 기준까지 |
|---|---|---|---|
| 1 | 안산 ↔ 성남 | 0.543 | 0.057 |
| 2 | 평택 ↔ 성남 | 0.508 | 0.092 |
| 3 | 안산 ↔ 평택 | 0.501 | 0.099 |
| 4 | 파주 ↔ 평택 | 0.495 | 0.105 |
| 5 | 파주 ↔ 용인 | 0.494 | 0.106 |

**경계선에 걸린 페이지 [사실]:** 평택(사실 3개 = 최소 기준, 시군 자금 1건, 템플릿 문장 49%), 파주(사실 4, 템플릿 47%), 성남(템플릿 45%, 유사도 1·2위에 모두 등장), 안산(템플릿 43%, 유사도 1위), 용인·서울 강서(사실 4). 규칙은 통과하지만 상위 유사 5쌍이 모두 이 페이지들 사이에서 나온다 — 경기도 공통 문장이 많기 때문으로 보인다 [추정].

### 4-2. GSC 색인 상태 (`/region/*`·`/jaedan-*`·`/seoul`·`/gyeonggi`·`/incheon`)

- `/seoul`·`/gyeonggi`·`/incheon` 은 **존재하지 않는 URL**(실서버 404, 사이트맵·저장소에 없음). 광역 페이지는 `/jaedan-seoul`·`/jaedan-gyeonggi`·`/jaedan-incheon` 이다.
- "크롤링됨 - 현재 색인 생성되지 않음" 비율: **[대표 확인 필요]** — 색인 상태(페이지 색인 생성 리포트)는 저장소 GSC 원자료에 없고 API 접근도 없다.
  - 확인 방법: GSC(bmaker.kr) → 색인 생성 → 페이지 → "크롤링됨 - 현재 색인 생성되지 않음" 클릭 → 예시 URL 내보내기. 전체 미색인 URL 중 `/region/`·`/jaedan-` 비율과 전체 사이트맵 URL 중 이들 비율(`/region/` 19 + `/jaedan-*` 17 + `/jaedan` 1 = 37개 / 사이트맵 전체)을 비교하면 된다.
- 간접 증거 [사실]: 재단 페이지 18개(`/jaedan` 포함) **전부** 28일 GSC 노출이 있다(3~201회) → 적어도 9/17 기준 색인돼 있었다. `/region/*` 는 10/1 생성이라 9/27에 끝나는 GSC 자료에 아직 없다.

### 4-3. 같은 검색어에 우리 URL 2개 이상 (GSC 28일)

**[대표 확인 필요]** — 저장소 자료는 "페이지별"·"검색어별"이 따로 저장돼 있고 "검색어 × 페이지" 교차가 없어 표를 만들 수 없다. GSC → 실적 → 검색어 탭에서 검색어 하나를 클릭한 뒤 페이지 탭을 보거나, Looker Studio/API로 `query,page` 두 차원을 같이 내려받아야 한다.

이름이 겹쳐 카니발 **후보**인 bmaker.kr 내부 묶음(GSC로 확인 전, 제목 기준) [추정]:

| 묶음 | 페이지 |
|---|---|
| 혁신성장촉진자금 | `/hyeoksin` · `/hyeoksin-jolup` · `/hyeoksin-sahoe` |
| 경영 애로 | `/gingeup` · `/ilsijeok` · `/ilsijeok-homeplus` |
| 접수 일정 | `/schedule` · `/2026-4q-sosangin` |
| 중소기업 정책자금 | `/jungjingong` · `/jungsogieop` · `/sme-business-loans` |
| 소상공인 정책자금 | `/sojingong` · `/sosangin` · `/gaein` |
| 정부지원대출 | `/funding` · `/gaein` |

---

## 5. 보고

### 5-1. 판단 — 워드프레스 정지 원인

| 후보 | 판정 | 근거 |
|---|---|---|
| noindex | **아님** [사실] | 홈·글 모두 noindex 없음, X-Robots-Tag 없음 |
| 차단 | **아님** [사실/추정] | robots.txt 일반 봇 허용, Cloudflare 미경유(DNS 전용). 위장 봇 403 은 WordPress.com 의 가짜 봇 차단으로 보임 — GSC URL 검사로 최종 확인 필요 |
| 발행 중단 | **아님** [사실] | 마지막 발행 2026-10-01, 사이트맵 lastmod 10-01 |
| 미등록 | **확인 못 함** [대표 확인 필요] | GSC blog 속성 유무를 볼 수 없음. Bing 색인은 2건만 확인 |
| **중복(검색 의도 카니발) + 신규 서브도메인 대량 발행** | **가장 유력** [추정] | ① 같은 소유자의 bmaker.kr 이 이미 3~4주 먼저, GSC 노출까지 있는 주제를 WP 글 17개가 같은 제목어로 다시 다룸 ② 개설 첫 이틀에 26개(3분에 8개, 18분에 14개) ③ 소제목 틀 반복 ④ 서브도메인은 검색엔진이 별도 사이트로 보는 경우가 많아 이력 없음 |

**판단:** 기술적 차단은 없다. 정지 원인은 **"이미 있는 bmaker.kr 대표 페이지와 같은 검색어를 겨냥한 글이, 이력 없는 새 서브도메인에 한꺼번에 올라간 것"**으로 본다. 이 경우 Google 은 대개 먼저 있던 bmaker.kr 쪽을 고르고 WP 글은 "크롤링됨/발견됨 - 현재 색인 생성되지 않음"으로 둔다. 다만 "정지"가 실제로 일어났는지(처음 노출 뒤 감소인지, 처음부터 미노출인지)는 이번 진단에서 데이터로 확인하지 못했다.

**확정하려면 대표가 GSC에서 확인할 것 (3가지):**
1. blog.bmaker.kr 속성이 있는가. 없으면 원인은 "미등록"이 1순위로 바뀐다.
2. 페이지 색인 리포트의 미색인 사유 상위 3개. "중복 페이지, Google이 사용자와 다른 표준을 선택함" 또는 "크롤링됨 - 현재 색인 생성되지 않음"이 다수면 위 판단이 확정된다.
3. `https://blog.bmaker.kr/restart-special-funding/` URL 검사 → "Google이 선택한 표준" 칸. bmaker.kr URL이 나오면 중복으로 확정.

### 5-2. 제안 A안 — 워드프레스 폐쇄, bmaker.kr 로 통합 (권고안)

- 강한 겹침 글은 새 블로그로 옮기지 않고 **bmaker.kr 대표 페이지로 301**. 대표 페이지에 없는 단락(예: 재도전특별자금 일반·희망·도약형 차이)만 골라 합친다.
- 겹치지 않는 글·소식·인접 글은 `bmaker.kr/blog/<같은 slug>` 로 이전. 이때 `posts/*.md` 변환 초안 + 블로그 빌더(빌더 체인 편입)가 필요하다 — **승인 후 작성**.
- 기술 조건: WordPress.com 은 글별 301을 지원하지 않는다(사이트 리디렉트는 도메인 단위, 경로 그대로 넘김 → bmaker.kr 쪽은 대부분 404). 따라서 `blog` 레코드를 Cloudflare **프록시 켜기 + Bulk Redirects(아래 표 40줄)** 로 처리해야 한다. 이건 DNS 변경이라 승인 대상이다.
- 함께 바꿀 것: `funding.html:63`, `docs/funding-guides.json:88` 의 `blog.bmaker.kr/support-programs/` 링크.
- 장점: 개설 13일·색인 미미한 서브도메인이라 잃는 게 거의 없고, 대표 페이지 신호가 한곳으로 모인다. 단점: 블로그 빌더를 새로 만들어야 한다.

### 5-3. 제안 B안 — 워드프레스 유지

- 아래 표의 B안 열 기준: **삭제(301→bmaker) 7 · 합치기 13 · 주제 변경 2 · 유지/조정 18**.
- 유지한다면 WP 역할을 **"공고 소식·기간 한정 글"로 좁히고**, 자금 이름 단독 제목("○○자금 신청 안내")은 쓰지 않는다. 이 제목들은 bmaker.kr 대표 페이지 몫이다.
- 남은 글도 하루 몰아 발행 대신 간격을 둔다. 소제목 틀 반복을 줄인다.

### 5-4. 글별 301 매핑표(A안) · 권고(B안) — 실행은 승인 후

| WP URL | A안 301 대상 | A안 처리 | B안 권고 |
|---|---|---|---|
| `https://blog.bmaker.kr/` | `https://bmaker.kr/business-guide` | 허브 → 허브 | 유지 |
| `https://blog.bmaker.kr/funding-guide/` | `https://bmaker.kr/funding` | 강한 겹침 → 대표 페이지 | 삭제(301→bmaker /funding) |
| `https://blog.bmaker.kr/application-calendar/` | `https://bmaker.kr/schedule` | 강한 겹침 → 대표 페이지 | 합치기(/schedule 로) |
| `https://blog.bmaker.kr/support-programs/` | `https://bmaker.kr/blog/support-programs` | 고유 → 이전 (bmaker funding.html:63 링크도 교체) | 유지 |
| `https://blog.bmaker.kr/policy-news/` | `https://bmaker.kr/blog` | 목록 → 블로그 목록 | 유지 |
| `https://blog.bmaker.kr/practical-guides/` | `https://bmaker.kr/blog` | 목록 → 블로그 목록 | 유지 |
| `https://blog.bmaker.kr/about-editorial/` | `https://bmaker.kr/blog/about-editorial` | 고유 → 이전 | 유지 |
| `https://blog.bmaker.kr/diagnosis/` | `https://bmaker.kr/consulting` | 인접 → 대표 페이지 | 삭제(301→bmaker /consulting) |
| `https://blog.bmaker.kr/privacy/` | `https://bmaker.kr/privacy` | 같은 성격 → 대표 페이지 | 유지 |
| `https://blog.bmaker.kr/innovation-growth-funding/` | `https://bmaker.kr/hyeoksin` | 강한 겹침 → 대표 페이지(유형·접수 방식 단락 합치기) | 합치기(/hyeoksin) |
| `https://blog.bmaker.kr/restart-special-funding/` | `https://bmaker.kr/jaedojeon` | 강한 겹침 → 대표 페이지(일반·희망·도약형 비교 합치기) | 합치기(/jaedojeon — 사이트 1위 페이지) |
| `https://blog.bmaker.kr/youth-employment-funding/` | `https://bmaker.kr/cheongnyeon` | 강한 겹침 → 대표 페이지 | 합치기(/cheongnyeon) |
| `https://blog.bmaker.kr/manufacturing-small-business-funding/` | `https://bmaker.kr/sogongin` | 강한 겹침 → 대표 페이지 | 합치기(/sogongin) |
| `https://blog.bmaker.kr/general-business-stability-funding/` | `https://bmaker.kr/ilban-gyeongyeong` | 강한 겹침 → 대표 페이지 | 합치기(/ilban-gyeongyeong) |
| `https://blog.bmaker.kr/emergency-business-stability-funding/` | `https://bmaker.kr/gingeup` | 강한 겹침 → 대표 페이지(재해피해 경로는 /gingeup 에 추가) | 합치기(/gingeup) |
| `https://blog.bmaker.kr/kosmes-startup-commercialization/` | `https://bmaker.kr/jungjingong` | 강한 겹침 → 대표 페이지 | 주제 변경(자금 소개 → "창업기반지원 사업계획 작성 사례"처럼 실무 하나로) |
| `https://blog.bmaker.kr/kosmes-growth-foundation/` | `https://bmaker.kr/jungjingong` | 강한 겹침 → 대표 페이지 | 주제 변경(시설투자 견적·투자계획 실무로) |
| `https://blog.bmaker.kr/kosmes-business-rebound/` | `https://bmaker.kr/jungjingong` | 강한 겹침 → 대표 페이지 | 합치기(/jungjingong — WP 중진공 3종끼리도 유사 0.26~0.28) |
| `https://blog.bmaker.kr/kodit-business-guarantee/` | `https://bmaker.kr/sinbo` | 강한 겹침 → 대표 페이지 | 합치기(/sinbo) |
| `https://blog.bmaker.kr/kibo-technology-guarantee/` | `https://bmaker.kr/gibo` | 강한 겹침 → 대표 페이지 | 합치기(/gibo) |
| `https://blog.bmaker.kr/regional-credit-guarantee/` | `https://bmaker.kr/jaedan` | 강한 겹침 → 대표 페이지 | 합치기(/jaedan) |
| `https://blog.bmaker.kr/small-business-policy-loans/` | `https://bmaker.kr/sojingong` | 강한 겹침 → 대표 페이지 | 삭제(301→/sojingong) |
| `https://blog.bmaker.kr/sme-policy-loan-guide/` | `https://bmaker.kr/sme-business-loans` | 강한 겹침 → 대표 페이지 | 삭제(301→/sme-business-loans, 같은 날 생성) |
| `https://blog.bmaker.kr/government-business-loans/` | `https://bmaker.kr/funding` | 강한 겹침(제목 앞부분 동일) → 대표 페이지 | 삭제(301→/funding) |
| `https://blog.bmaker.kr/microfinance-business-guide/` | `https://bmaker.kr/microfinance-business` | 강한 겹침 → 대표 페이지 | 삭제(301→/microfinance-business, 같은 날 생성) |
| `https://blog.bmaker.kr/2026-q4-policy-funding-schedule/` | `https://bmaker.kr/2026-4q-sosangin` | 강한 겹침 → 대표 페이지(WP가 7일 먼저 — 내용 비교 후 나은 쪽 문장 채택) | 합치기(/2026-4q-sosangin) |
| `https://blog.bmaker.kr/existing-business-loans-list/` | `https://bmaker.kr/blog/existing-business-loans-list` | 인접 → 이전 | 주제 유지, /daehwan 링크 강화 |
| `https://blog.bmaker.kr/equipment-funding-evidence/` | `https://bmaker.kr/blog/equipment-funding-evidence` | 인접 → 이전 | 주제 유지, /working-capital-facility 와 역할 구분 |
| `https://blog.bmaker.kr/guarantee-bank-questions/` | `https://bmaker.kr/blog/guarantee-bank-questions` | 인접 → 이전 | 유지 |
| `https://blog.bmaker.kr/consulting-scope-checklist/` | `https://bmaker.kr/chaksugeum` | 인접 → 대표 페이지(계약 전 질문 8가지 합치기) | 합치기(/chaksugeum) |
| `https://blog.bmaker.kr/application-supplement-log/` | `https://bmaker.kr/blog/application-supplement-log` | 인접 → 이전 | 유지 |
| `https://blog.bmaker.kr/business-funding-workshop/` | `https://bmaker.kr/education` | 인접 → 대표 페이지 | 삭제(301→/education) |
| `https://blog.bmaker.kr/2026-kibo-factoring-september-october/` | `https://bmaker.kr/blog/2026-kibo-factoring-september-october` | 소식 → 이전 | 유지(소식형) |
| `https://blog.bmaker.kr/2026-kodit-woori-youth-guarantee/` | `https://bmaker.kr/blog/2026-kodit-woori-youth-guarantee` | 소식 → 이전 | 유지(소식형) |
| `https://blog.bmaker.kr/2026-kodit-ibk-startup-buildup/` | `https://bmaker.kr/blog/2026-kodit-ibk-startup-buildup` | 소식 → 이전 | 유지(소식형) |
| `https://blog.bmaker.kr/2026-product-improvement-round5/` | `https://bmaker.kr/blog/2026-product-improvement-round5` | 고유 → 이전 (공고 기간 지남 — 이전 대신 410도 검토) | 유지 또는 기간 종료 표시 |
| `https://blog.bmaker.kr/2026-october-regional-business-funding/` | `https://bmaker.kr/blog/2026-october-regional-business-funding` | 고유 → 이전 (도시 페이지와 링크 연결 후보) | 유지 |
| `https://blog.bmaker.kr/2027-kriss-technology-home-doctor/` | `https://bmaker.kr/blog/2027-kriss-technology-home-doctor` | 고유 → 이전 | 유지 |
| `https://blog.bmaker.kr/cash-flow-13-weeks/` | `https://bmaker.kr/blog/cash-flow-13-weeks` | 고유 → 이전 | 유지 |
| `https://blog.bmaker.kr/loan-consultation-brief/` | `https://bmaker.kr/blog/loan-consultation-brief` | 고유 → 이전 (Bing 색인 확인된 글) | 유지 |

### 5-5. 도시 페이지 — 확장 일시 정지 권고

- **고유 사실 미달 페이지: 0개** (19/19 규칙 통과). 기준선에 걸린 페이지는 평택(사실 3), 파주·용인·서울 강서(사실 4).
- **권고: 신규 도시 추가는 일시 정지, 기존 19개는 유지.**
  1. 사이트 전체에 2주 사이 새 URL이 몰렸다: WP 31개(9/21~10/1) + bmaker 신규 페이지 8개(9/21~9/28) + 도시 19개(10/1 하루). 도시 페이지의 색인 결과가 나오기 전에 더 늘리면 "도시명만 바뀐 페이지 묶음"으로 판정될 위험을 키운다 [추정].
  2. 유사도 상위 5쌍이 전부 경기·평택·파주 묶음에서 나왔고 1위가 기준까지 0.057 남았다. 경기 도시를 더 추가하면 기준을 넘는 쌍이 생길 가능성이 높다 [추정].
  3. 재개 조건(제안): 4주(약 11/1) 뒤 GSC에서 `/region/*` 19개 중 색인 비율이 사이트 평균 이상이고 "크롤링됨 - 현재 색인 생성되지 않음"이 사이트 평균보다 높지 않을 것. 그 전에 평택에 시·군 자금 공고를 1건 이상 보강.

---

## 6. GSC 확인 (2026-10-04, Claude in Chrome 으로 읽기만 — 색인 요청·설정 변경 없음)

### 6-1. blog.bmaker.kr 속성 — **있음**

| 항목 | 값 |
|---|---|
| 페이지 색인 | **색인됨 1 · 미색인 11** (사이트맵 40 URL 중 Google 이 아는 것은 12개) |
| 미색인 사유 | **"발견됨 - 현재 색인이 생성되지 않음" 11** (Google 시스템 판단, 사유는 이 1개뿐) |
| 실적(9/20~) | 웹 검색 클릭 0 |
| URL 검사 `/restart-special-funding/` | "URL이 Google에 등록되어 있지 않음" · 발견됨-미색인 · **최근 크롤링: 해당사항 없음** · 참조 페이지 없음 · 사이트맵 `sitemap.xml` 에서 발견 · **Google 선택 표준 URL: 해당사항 없음** |

**판단 갱신 [사실 기반]:** 미등록이 아니다. Google 이 URL 을 사이트맵으로 알고 있지만 **아직 한 번도 크롤링하지 않았다.** 그래서 "중복 판정(Google 이 다른 표준 선택)" 단계에 가지도 않았다. 5-1 의 "중복 확정" 조건(표준 URL이 bmaker.kr)은 성립하지 않는다.
정확한 원인은 **"새 서브도메인에 이틀간 26개를 몰아 올려, Google 이 이 사이트의 크롤링을 미뤄 둔 상태(발견됨-미색인)"** 다. 카니발은 크롤링 이후에 문제가 될 위험으로 남는다. A안(통합) 결론은 그대로다 — 크롤링이 시작되면 bmaker.kr 자금 페이지와 같은 검색어를 두고 경쟁하게 된다.

### 6-2. bmaker.kr 속성 — 페이지 색인 (리포트 최종 업데이트 2026-09-21)

| 항목 | 값 |
|---|---|
| 색인됨 / 미색인 | 72 / 22 |
| 미색인 사유 | 리디렉션 포함 8 · 404 4(유효성 검사 실패) · robots.txt 차단 4 · 대체 페이지(적절한 표준) 3 · noindex 2 · 중복(Google이 다른 표준 선택) 1 |
| 크롤링됨 - 현재 색인 생성되지 않음 | **0** |
| 발견됨 - 현재 색인 생성되지 않음 | 0 |

### 6-3. `/region/*` 19장 색인 상태 (URL 검사, 2026-10-04)

리포트가 9/21 기준이라 10/1 생성한 도시 페이지는 URL 검사로 한 장씩 봤다.

| 상태 | 수 | 페이지 |
|---|---|---|
| 색인됨 ("URL이 Google에 등록되어 있음") | **16** | 안산·안양·부천·창원·청주·김포·고양·화성·남양주·파주·포항·평택·성남·시흥·수원·용인 |
| 발견됨 - 현재 색인 생성되지 않음 | **3** | 김해·전주·서울 강서 |
| 크롤링됨 - 현재 색인 생성되지 않음 | **0** | — |

- 도시 미색인 비율 3/19 = **16%**. 사이트 전체 미색인 22/94 = 23% 이지만 대부분 의도된 제외(리디렉션·noindex·robots)다. "크롤링됨-미색인" 기준으로는 도시 0% = 사이트 0%.
- 경계선 페이지(평택·파주·성남·안산)는 모두 색인됐다. 미색인 3장은 경기 묶음이 아니라 다른 광역(경남·전북·서울)이다 — 아직 크롤링 대기.

### 6-4. 같은 검색어에 우리 URL 2개 이상 (bmaker.kr, 2026-09-02~09-29, 28일)

노출 상위 검색어 27개를 하나씩 페이지 분해했다. **2개 이상이 뜬 검색어는 5개뿐**(요청한 "상위 10쌍"에 못 미침 — 나머지 22개는 URL 1개).

| 검색어 | URL (클릭/노출/평균순위) |
|---|---|
| 혁신성장촉진자금 | `/hyeoksin` 5/155/5.4 · `/hyeoksin-jolup` 1/19/9.2 · `/hyeoksin-sahoe` 1/2/9.0 |
| 혁신성장촉진자금 2026 | `/hyeoksin` 0/38/6.0 · `/hyeoksin-jolup` 0/12/9.2 · `/hyeoksin-sahoe` 0/1/5.0 |
| 소상공인 혁신성장촉진자금 | `/hyeoksin-jolup` 0/8/7.4 · `/hyeoksin` 0/7/5.7 |
| 신용보증기금 대출 | `/bojeung` 1/14/8.1 · `/sinbo` 0/3/22.3 |
| 신용보증재단 사업자대출 | `/jaedan` 0/10/9.7 · `/jaedan-seoul` 0/7/11.7 |

URL 1개만 뜬 검색어(확인 완료): 청년고용연계자금(+대출·2026·소상공인), 재도전특별자금(+띄어쓰기), 소공인특화자금, 서울신용보증재단 사업자 대출·소상공인 대출·대출, 상생성장지원자금, 장애인기업지원자금, 신용보증기금 사업자대출, 부산 소상공인 대출, 소진공 직접대출, 2026 소상공인 대환대출, 일시적경영애로자금, 일반경영안정자금 2026, 보증재단 사업자대출, 보증서대출, 보증서 대출, 긴급경영안정자금, 소상공인 졸업후보기업.

**판단:** 내부 카니발은 혁신성장촉진자금 3장 묶음이 유일하게 뚜렷하다(본체가 상위, 하위 2장이 같은 검색어에 9위권으로 함께 노출). 처리 판단은 이번 범위 밖 — 별도 보고.

---

## 부록 — 재현 방법

- WP 목록: `curl "https://blog.bmaker.kr/wp-json/wp/v2/posts?per_page=100&_fields=id,date,link,title,content"`
- bmaker 기준 트리: `git archive origin/main`(8b88b73)을 임시 폴더에 풀어 분석. 작업 트리(`hero-diet` 브랜치)는 건드리지 않음.
- 도시 검사: `tests/test_region.py` 의 `parse`·`fact_errors`·`duplicate_errors`·`similarity` 를 그대로 호출(빌드일 대신 2026-10-04).
- 본문 겹침: 스크립트·스타일·nav·header·footer 를 뺀 본문 텍스트의 5어절 조각 포함률.
- 이번 진단에서 바꾼 것: 이 문서 1개 추가. 코드·DNS·워드프레스·Cloudflare 설정 변경 없음.
