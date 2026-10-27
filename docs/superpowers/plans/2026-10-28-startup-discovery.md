# Startup discovery implementation

Goal: 실제 프랜차이즈 비교·선정 지원 서비스를 홈, /startup, 창업 블로그에서 발견하고 상담할 수 있게 한다.
Architecture: 기존 정적 페이지·블로그 빌더를 유지한다. /startup 본문은 전용 템플릿, 블로그는 posts 원본에서 생성한다.
Tech stack: Python generators, HTML, existing conversion.js.
Spec: 2026-10-28 사용자 확인 — 실제 비교 서비스, 지역별 수수료 차이, 대표 창업상권분석지도사 1급 보유.
Global constraints: 정책자금 홈 핵심 유지, 기존 URL·동의·전송 유지, 허위 수익/순위/자격/검토 주장 금지. 브랜치+PR, merge 전 대표 검토.
Review focus: 창업 문의가 정책자금으로 바뀌지 않는지, FAQ와 스키마 일치, 신뢰 주장·날짜, 반복 빌드 보존, 내부 링크.

## Task 1 — 창업 서비스와 탐색 경로
- [x] 홈페이지 기존 별도 서비스에서 /startup을 구체적으로 소개.
- [x] /startup: 프랜차이즈 후보 비교, 총비용, 중장년 운영 조건, 지역별 별도 견적 FAQ, 대표 소개 링크.
- [x] 기존 비용 가이드에 지역별 견적 원칙 반영.

## Task 2 — 블로그와 문의 연결
- [x] 창업 카테고리와 /blog#business-start, 서로 다른 질문의 글 3편.
- [x] 신규 창업 페이지의 문의 분야는 startup, 기존 글은 policy 유지.
- [x] 미검토 글의 대표 검토 표시는 생략(명시적 reviewed: false); 출처 확인일만 표시.
- [x] 라우팅·검토 여부·반복 빌드 테스트를 먼저 실패 확인 후 구현. 단순 문구는 기존 검사로 검증.

## Task 3 — 검증과 전달
- [x] 공식 출처·HTML/FAQ/메타 검수. 빌더 체인 두 번, 불필요한 날짜 변경 확인.
- [x] 전체 pytest, conversion/analytics JS, 브라우저 확인.
- [ ] 독립 최종 검토 1회 후 수정, 커밋·PR·첨부. 공개 반영으로 보고하지 않는다.

## Execution ledger
- Base: 4d46bbd. 작업 전 pull 완료, clean main에서 feat/startup-comparison-20261028 생성.
- Ruling: 별도 worktree 대신 기존 clean checkout의 feature branch를 사용한다. 사용자는 반복 질문 없이 실행을 요청했고 worktree 생성은 별도 동의가 필요하므로 추가 생성하지 않는다.
- Ruling: PowerShell 환경에서 스킬의 Bash ledger wrappers 대신 이 문서에 작업·검증·판단을 직접 기록한다. 변경은 한 최종 커밋으로 묶는다.
- Ruling: 명시적 reviewed:false는 신규 글에만 적용한다. 실제 검토 없는 대표 이름을 주장하지 않으며 기존 승인 글 표시는 변경하지 않는다.
- Baseline: 916 passed / 22 subtests. 신규 동작 검사 3 failures → 4 passed. FAQ 링크의 조사 위치를 라벨 안으로 옮겨 텍스트 정규화 일치 확인, 집중 검사 496 passed.
- 공식 근거 확인 2026-10-28: 인천시 https://www.incheon.go.kr/eco/ECO030302 (정보공개서 의미), 창업진흥원 https://www.kised.or.kr/menu.es?mid=a10211060000 (중장년 기술창업 대상·공간/교육/보육). FTC 비교 화면은 접근 제한으로 브랜드별 데이터 확인 근거로 사용하지 않았다. 개별 브랜드 순위·금액은 제시하지 않았다.
- Build: 전체 12단계 체인 반복 결과 파일 해시 변화 0. 기존 글 본문·검토일은 유지되고 홈/창업/목록/허브 및 신규 URL만 갱신.
- Final review: startup_final_review(gpt-6-astra), read-only. Critical/Important/Minor 0, PR 준비 적합 판정. 기존 동적 창업 폼 문구, 카테고리 목록 중복, 기존 검토 기본값/carousel은 판단 유보 목록으로 명시.
- Final Ruling: 기존 동적 폼 문구도 실제 서비스 안내와 맞춰야 하므로 /startup에 같은 정본의 창업 인라인 폼을 적용. 모바일 검사에서 기존 버튼 문구 실패 → 창업 문구/분류/동의 확인 통과. 정적 폼 전환에 맞춰 동적 페이지 목록과 정적 폼 허용 목록을 갱신했다. 기존 policy 기본값과 JS 전송 코드는 유지한다.
- Final Ruling: 카테고리 추천 3편과 전체 목록 중복은 목록이 늘어나도 남는 안내 경로이므로 유지. 기존 검토 글·carousel 기본값은 이번에 재검증하지 않아 변경하지 않는다.
- 모바일 실제 viewport 검사: 390px에서 헤더가 393px으로 넘치는 실패 재현 → 신규 창업 글/카테고리와 블로그 목록에 모바일 중복 헤더 CTA 숨김 적용 → 통과. 표는 기존 가로 스크롤 안에 유지. 1440/390px 5페이지씩 총 10개 조합과 /blog#business-start 화면 확인.
- 검사 과정의 병행 빌드가 일부 날짜 검사에 간섭하여 최종 검사는 모든 빌드 종료 후 별도로 다시 실행한다. 동작 실패를 숨기거나 테스트를 생략하지 않는다.
- Final verification: 빌드 종료 후 REQUIRE_BROWSER=1 python -m pytest -q → **952 passed, 22 subtests passed, skip 0**. node tests/test_conversion.mjs, node tests/test_analytics.mjs 모두 통과. /startup·신규 블로그의 실제 전송 payload는 로컬에서 가로채 startup 분류를 확인했으며 운영 문의는 발송하지 않았다.
- Ruling: 사용자의 실행 요청과 저장소 규칙에 따라 finishing skill의 선택 메뉴를 반복하지 않고 브랜치 push+PR까지만 진행한다. 대표 확인 없이 merge/배포하지 않는다.
