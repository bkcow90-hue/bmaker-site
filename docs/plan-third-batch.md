# 세 번째 묶음 — 롱테일 랜딩 (대표 지시, 2026-09-20 수령)

착수 조건: **9/27 PR #5 머지 후 `search-growth` 를 main 에 리베이스하고 2단계 7번으로 진행.**
지금 착수하지 않는다. 확정 키워드는 `keywords-2026-09.md`, 규격은 `homepage-standard.md` 가 우선한다.

## 1. 신규 6장 — 규격 2·3·4절 전부 적용

전용 title/description, 즉답 3줄, FAQ 5개 + FAQPage, 폼, Service·BreadcrumbList JSON-LD, "함께 보면 좋은 안내" 링크.

| URL | 핵심 검색어 | 보조 | 내용 |
|---|---|---|---|
| `/situation/daeri` | 소상공인 정책자금 대리대출 | 직접대출 | 둘의 차이, 표 1개 |
| `/seoul` | 서울 정책자금 컨설팅 | 서울시 정책자금 | 지자체 자금 + 지역 허브, 강서구 마곡 사무실 섹션, areaServed 서울, `/jaedan-seoul` 링크 |
| `/gyeonggi` | 경기도 정책자금 컨설팅 | 경기도 정책자금 | `/jaedan-gyeonggi` 링크 |
| `/incheon` | 인천 정책자금 컨설팅 | 인천 소상공인 정책자금 | `/jaedan-incheon` 링크 |
| `/industry/unsu` | 운수업 정책자금 | — | hero-diet industry 템플릿 |
| `/cheongnyeon-changeop` | 청년전용창업자금 | — | **중진공 공고 기준**. 네이버 월 3,090. `/cheongnyeon`(소진공 청년고용연계자금)과 **다른 자금**이라 별도 페이지. 양쪽에서 서로 링크하고 차이를 FAQ 로 설명 |

- 지역 3장은 같은 템플릿을 쓴다. 사무실 섹션은 `/seoul` 만.
- 받은 사례 요약은 원장의 지역 범주로 집계 가능하면 넣고, 아니면 "—".
- **지역어는 이 3장·`/jaedan-*`·회사소개·푸터·JSON-LD 에만 쓴다**(규격 2절).

## 2. 기존 보강 — 검수 없이 커밋

- `/daehwan`: 즉답 · FAQ 5 · 기관 표
- `/sosangin`: FAQ 1개 "신청은 어디서" + 거절·부결 한 줄
- `/jungsogieop`: FAQ "중소기업 대출 조건" + 거절·부결
- `/jungjingong`: FAQ "신청 절차"
- `/gaein`: FAQ "개인사업자 대출 조건"
- `/jaedan`: title 보조 "개인사업자 보증서 대출"
- `/schedule`: title "{N}분기 소상공인 정책자금 접수 일정" — N 은 `data_date` 기준, 빌더가 계산
- `/funding`: title 보조 "정부 정책자금 대출"
- `/sojingong`: title 정식명칭 병기 확인
- `/jaedojeon`·`/cheongnyeon`: title 에 자금명 포함 확인
- `/certification`: 여성기업 섹션 + FAQ 1
- 제조 industry title 확인

## 3. 블로그 2편 (블로그 셸)

- "정책자금 컨설팅 비용은 어떻게 정해지나"
- "정책자금 브로커와 컨설팅을 구별하는 법"

보장성 표현·타사 비방 금지. 우리 방식은 사실만. 이미지는 `[캡처: 무엇]` 자리로 둔다.

## 4. 기술

sitemap·llms·llms-full 갱신. **내비 변경 없음** — 허브에서 상황·지역 페이지로 내부링크만. `test_nav` 통과.

## 5. 순서

1. 신규 6장 + 블로그 2편 **문구 선출력 → 검수 → 커밋**
2. 기존 보강은 검수 없이 커밋
3. 백링크는 다루지 않는다 — **사이트 내부링크만**

## 검증

pytest · pr-check · churn 0 · 내부 링크 404 0 ·
금칙어 0("갚다" 계열 · 보장성 표현 · "지원센터" · "실행 기록") · 지역어 검출 위치 확인 ·
신규 6장 390×844 스크린샷.
