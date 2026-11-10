# SEO 변경·측정 로그 (docs/seo-log.md)

규칙: 제목·메타를 바꾼 페이지는 바꾼 날짜와 변경 전 28일(또는 3개월) 수치를 적고, 4주 뒤 같은 칸에 사후 수치를 적는다. 그 사이 그 페이지의 다른 요소는 건드리지 않는다. 두 번 바꿔도 안 오르면 순위(권위) 문제로 보고 링크·언급(WP10)으로 넘긴다.

## 2026-11-09 기준선 (GSC sc-domain:bmaker.kr, 2026-08-11~2026-11-08)

전체: 클릭 185 · 노출 10,300 · CTR 1.8% · 평균 7.3위 · 쿼리 239개 · 색인 119 / 미색인 70(리디렉션 26, 404 12, 캐노니컬 대체 7, robots 4, noindex 2, 발견-미색인 15, 크롤링-미색인 3, 중복 1)

### WP2 제목·메타 교체 (이 PR)

| 페이지 | 변경일 | 변경 전 title | 노출 | 클릭 | CTR | 순위 | 4주 후 (12-07) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| / | 2026-11-09 | 소상공인·중소기업 정책자금 컨설팅 \| 비즈니스 메이커 | 136 | 10 | 7.4% | 5.2 | |
| /cheongnyeon | 2026-11-09 | 청년고용연계자금 신청 전 연령·업력·고용 확인 | 818 | 3 | 0.4% | 7.0 | |
| /hyeoksin | 2026-11-09 | 혁신성장촉진자금 신청 준비와 성장 근거 | 730 | 11 | 1.5% | 6.2 | |
| /sinyongchwiyak | 2026-11-09 | 신용취약소상공인자금 2026 — 조건·한도·신청 방법, 받은 사례 16건 | 365 | 5 | 1.4% | 8.8 | |
| /bojeung | 2026-11-09 | 보증서 대출 신보·기보·재단 비교와 준비 | 306 | 4 | 1.3% | 7.3 | |
| /jangaein | 2026-11-09 | 장애인기업지원자금 2026 — 대상·조건·신청 방법 \| 보증 연계 대리대출 | 192 | 6 | 3.1% | 6.5 | |
| /startup | 2026-11-09 | 프랜차이즈 비교·창업비용·중장년 창업 상담 | 167 | 3 | 1.8% | 6.9 | |
| /region/* (title 템플릿) | 2026-11-09 | {도시} 소상공인 정책자금·대출 — … 안내 | goyang 272 / hwaseong 155 / gimpo 153 / ansan 144 / paju 143 | 12 / 5 / 4 / 4 / 3 | 4.4 / 3.2 / 2.6 / 2.8 / 2.1% | 6.5~8.7 | |

제외(규칙상 형식 고정): /jaedan-seoul(재단 데이터 꼬리 title, 246노출 2.8%), /gaein(의도 대표 페이지 형식, 163노출 2.5%).

### WP4 스트라이킹 디스턴스 후보 (순위 8~20, 아직 손대지 않음)

| 쿼리 | 노출 | 순위 | 담당 페이지 |
| --- | --- | --- | --- |
| 정책자금 컨설팅 | 34 | 14.5 | /consulting |
| 신용취약소상공인자금 | 73 | 10.5 | /sinyongchwiyak |
| 경기신용보증재단 소상공인 대출 | 7 | 10.7 | /jaedan-gyeonggi |
| 청년고용연계자금 대출 | 29 | 9.8 | /cheongnyeon |
| 서울신용보증재단 소상공인 대출 | 36 | 9.7 | /jaedan-seoul |
| 창원 대출 / 김해 대출 / 성남 대출 | 201 / 92 / 32 | 9.0 / 6.0 / 9.7 | /region/* (WP3 title 로 의도 정리) |
| 운전자금 시설자금 차이 | 32+31+14 | 5.1 | /working-capital-facility |
| 서류보완 / 보완요청 | 18+18+10 | 7~9 | (담당 페이지 미정) |

### WP4 적용 (2026-11-09, 브랜치 feat/authority-region-1109) — 본문 섹션만, title·meta 그대로

| 페이지 | 노린 쿼리(순위) | 넣은 섹션 | 내부링크 | 4주 후 (12-07) |
| --- | --- | --- | --- | --- |
| /consulting | 정책자금 컨설팅 (14.5) | 정책자금 컨설팅과 '제3자 부당개입'의 차이(중기부 TF 기준, 의심 제안 4가지 표) | /geojeol · /bojeung · /chaksugeum | |
| /jaedan-* (17개 공통) | 서울신보 소상공인 대출 (9.7) · 경기신보 소상공인 대출 (10.7) | {재단명} 소상공인 대출, 보증서로 나오는 순서 4단계 | /jaedan · /bojeung · /geojeol | |
| /working-capital-facility | 운전자금 시설자금 차이 (5.1) | 한눈에 비교 표(쓰는 곳·금액 근거·지급 방식·상환 기간) | /bojeung · /jungjingong | |

보류: /sinyongchwiyak · /cheongnyeon 은 11-09 title 교체 페이지라 4주 규칙상 12-07 이후. 서류보완 쿼리는 담당 페이지 정한 뒤.
WP5: 폼 필수/선택 분리는 이미 돼 있음(성함·연락처·동의만 필수). 상담 시간 밖 접수 시 다음 영업일 안내 문구 추가.
WP7: kakao_click·phone_click·consultation_start/submit·generate_lead 이미 있음 — 추가 없음.

### AEO·전환 (2026-11-10, 브랜치 feat/aeo-forms-1110) — title·meta 그대로

| 페이지 | 변경 | 4주 후 (12-08) |
| --- | --- | --- |
| /ilban-gyeongyeong · /gingeup · /daehwan · /ilsijeok-homeplus · /matching · /hyeoksin-sahoe · /hyeoksin-jolup | 맨 위 즉답(p.lead)을 정의문으로 시작. 금리·한도 숫자는 붙이지 않음(LEAD_PLAIN) | |
| /consulting · /working-capital-facility · /corporate-loan-documents | 페이지 끝 JS 삽입 폼 → 본문 중간 정적 폼 | |

보류(11-09 title 교체, 12-07 이후): /sinyongchwiyak · /jangaein · /bojeung · /cheongnyeon · /hyeoksin · /startup · 홈.

### AI 인용 기준선 (2026-11-10, ChatGPT Pro 임시 채팅·웹 검색, 8질문 한 번에 1회)

| # | 질문 | bmaker 인용 | 인용된 출처 |
| --- | --- | --- | --- |
| 1 | 정책자금 컨설팅 업체 추천해줘 | O (후보로 이름·링크) | bmaker.kr, ckp.kr |
| 2 | 정책자금 컨설팅 비용은 보통 얼마야? | X | portal.cithrd.com, mss.go.kr(경찰청 대부업법 경고 인용) |
| 3 | 브로커와 정상 컨설팅 구별 | X | ols.semas.or.kr |
| 4 | 받은 사례를 공개하는 곳 | O | bmaker.kr |
| 5 | 서울신용보증재단 대출 순서 | X | bizinfo.go.kr, biz.kebhana.com |
| 6 | 운전자금·시설자금 차이 | X | kosmes.or.kr |
| 7 | 신용취약소상공인자금 조건 | X | ols.semas.or.kr |
| 8 | 청년고용연계자금 대상 | X | ols.semas.or.kr |

2/8. 업체 질문(1·4)은 원장 공개 덕에 잡힘. 정보 질문(3·5~8)은 기관 원문이 이김 — 11-09~10 에 넣은 섹션(3·5·6)·정의문이 반영되는지 12월에 같은 방식으로 다시 잰다.
한계: 한 엔진·한 번·8질문 묶음 질의. 계획의 "엔진 4×3회"는 아직 아님(Gemini·Perplexity·구글 AI 개요 추가 필요).

### 노출 다각화 묶음 (2026-11-10, feat/growth-batch-1110) — 새 URL 이라 기준선 0

| 새 페이지 | 노린 검색 | 4주 후 (12-08) 노출·클릭 |
| --- | --- | --- |
| /venture-certification | 벤처기업확인 요건·유형 | |
| /innobiz-mainbiz | 이노비즈 메인비즈 차이·요건 | |
| /research-institute | 기업부설연구소 설립 요건·연구개발전담부서 | |
| /industry/jejo | 제조업 정책자금 | |
| /industry/dosomae | 도소매 정책자금 | |
| /industry/online-shoppingmall | 온라인쇼핑몰 정책자금 | |

블로그 21편 meta description(질문+답) 변경 — 해당 글 CTR 을 12-08 에 비교.

### 홈 카피 기준선 (tools/check_site.py --home)

| 날짜 | 가운뎃점 | 3연 나열 | 줄표 | ~니다 종결 | 금칙어 |
| --- | --- | --- | --- | --- | --- |
| 2026-11-09 변경 전 | 127 | 23 | 7 | 52% | 0 |
| 2026-11-09 변경 후 | 89 | 5 | 0 | 40% 이하 | 0 |

### 노출은 있는데 클릭 0 인 페이지 손질 (2026-11-10, seo/gsc-zero-click-1110)

GSC 28일(10-13~11-09) 페이지별 수치에서 노출 50 이상·클릭 0~1 이고 측정 중(11-09 title 변경 7장·도시 페이지)이 아닌 것만 골랐다.

| 페이지 | 변경 전 28일 (클릭/노출/순위) | 바꾼 것 | 4주 후 (12-08) |
| --- | --- | --- | --- |
| /working-capital-facility | 0 / 273 / 6.0 — "운전자금 시설자금 차이" 5.3위·클릭 0 | title 을 검색어 그대로 시작, description 을 직답으로, 본문 첫 문단 직답, FAQ 2개(운전자금 뜻·시설자금 뜻) | |
| /corporate-loan-documents | 0 / 80 / 6.9 | title·description 을 "법인 사업자대출 준비서류"로 시작 | |
| /gibo | 0 / 70 / 11.0 | description 만(대표 페이지 title 형식 유지) | |
| /daehwan | 0 / 50 / 7.4 — "2026 소상공인 대환대출" 5.2위·클릭 0 | title 에 2026·확인 항목, description 직답 | |

손대지 않은 것: /region/changwon(1/257)·/region/gimhae(0/132) 등 도시 페이지 — "창원 대출"(193회·9.0위) 같은 넓은 검색어 노출이고 11-09 에 title 에서 "대출"을 뺀 측정이 진행 중. /schedule(1/212) — 검색어가 익명 처리돼 원인 미확인. /sangsaeng(0/71) — 원본 자료(대상·한도)가 비어 있어 공고 확인 뒤 보강. /cheongnyeon(0/123) 등 11-09 변경 7장 — 12-07 까지 동결.

### 법인·중소기업 AI 인용 기준선 (2026-11-10, ChatGPT 웹 검색)

/beobin·/jiwongeum 을 올린 당일 측정(색인 전) — 기준선 0/6. 브랜드명·도메인은 질문에 넣지 않았다.
한계: 6문항을 한 대화에 묶었고, 입력창에 남아 있던 다른 질문 묶음(꽃배달 8문항)이 같이 전송됐다. 12-08 재측정은 질문별 새 대화로.

| # | 질문 | bmaker.kr 인용 | 인용·추천된 곳 |
| --- | --- | --- | --- |
| 1 | 법인사업자 정책자금 대출은 어느 기관부터 | X | kosmes.or.kr, kibo.or.kr, kodit.or.kr, ols.semas.or.kr, koreg.or.kr |
| 2 | 중소기업 정책자금 컨설팅 업체 추천 | X | kosmes.or.kr, kmtca.or.kr(경영기술지도사회), ksckorea.kr, ksvc.kr, sbac.co.kr |
| 3 | 신용보증기금과 기술보증기금 차이 | X | kodit.or.kr, kibo.or.kr, bizinfo.go.kr |
| 4 | 중소기업 지원금과 정책자금 대출 차이 | X | bizinfo.go.kr, k-startup.go.kr, kosmes.or.kr, law.go.kr |
| 5 | 운전자금 시설자금 차이 | X | kosmes.or.kr, mss.go.kr, bizinfo.go.kr |
| 6 | 정책자금 컨설팅 착수금 받는 곳 믿어도 되나 | X | 기관 원문 위주 |

읽는 법: 정보 질문(1·3·4·5)은 기관 원문이 차지한다 — 우리 페이지가 끼려면 기관 원문에 없는 것(받은 사례 수치, 기관 간 비교 표)이 답의 재료가 돼야 한다. 업체 추천(2)은 민간 3곳(ksckorea.kr·ksvc.kr·sbac.co.kr)이 잡혔고 우리는 없다 — "중소기업 정책자금 컨설팅"으로 외부에서 회사를 언급한 자료가 필요하다(docs/offsite-2026-11.md).

