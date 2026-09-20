# B묶음 — 9/27 이후 일괄 처리 목록

9/13 CTR 실험 판정(9/27) 전에는 라이브 title·description 을 건드리지 않는다.
판정이 끝나면 아래를 한 묶음으로 처리한다. 착수 조건과 순서는 `plan-third-batch.md` 와 겹치지 않게 관리한다.

## 1. 금칙어 "실행 기록" 전 페이지 치환 (2026-09-20 대표 확정)

- 대상: 본문 54개 페이지 · **title 7개**(`/cheongnyeon` `/gaein` `/hyeoksin` `/jaedojeon` `/sinyongchwiyak` `/sogongin` `/sojingong`)
  · `tests/test_conversion_flow.py:20` 의 `실행 기록 (전체 N건)` 문자열 · `llms.txt`·`llms-full.txt` · 빌더 템플릿
- 치환: `실행 기록` → `받은 사례` · `중앙값` → `건당 평균` · `실행 건수` → `보통 N일`(문맥에 따라)
- 생성 페이지는 빌더 문자열을 고쳐야 한다. 정적 페이지는 직접 치환.
- 치환 후 `pytest` 의 금칙어 검사(`tests/test_faq_consistency.py`)를 전 페이지로 확대할지 같이 판단한다.

## 2. FAQPage 마크업 통일 + 일치 검사 전 페이지 확장

현재 FAQPage JSON-LD 를 가진 페이지는 46장인데, 화면 마크업이 세 갈래다.

| 마크업 | 페이지 수 | 검사 상태 |
|---|---:|---|
| `<details><summary>Q</summary><p class="body">A</p></details>` (자금 빌더) | 15 | ✅ `test_faq_consistency` |
| `<details><summary>Q</summary><div class="body">A</div></details>` (정적) | 5 | ✅ `test_faq_consistency` |
| 그 외(재단 18장 · `/gaein` · `/jungjingong` · `/consulting` · `/gibo` · `/jeosinyong` · 블로그·마케팅 계열) | 26 | ❌ 미검사 |

할 일
1. 26장의 FAQ 화면 마크업을 `details` + `class="body"` 로 통일한다(재단 18장은 `build_jaedan.py` 템플릿 한 곳).
2. `tests/test_faq_consistency.py` 의 `ALL_FAQ_PAGES` 를 "FAQPage 를 가진 전 페이지" 로 바꾼다.
3. 통일 과정에서 화면↔JSON-LD 가 이미 갈라진 곳이 나오면 **화면 텍스트를 기준**으로 JSON-LD 를 다시 만든다.

## 3. title v2 적용 — og:title 동시 변경

- 9/27 판정 결과에 따라 `/jaedan` `/jungjingong` `/bojeung` `/sanghwan` `/gyehoekseo` 의 title 을 유지·되돌림·v2 적용 중 하나로 결정한다(판정 규칙은 `search-audit-2026-09.md` 6절).
- **`og:title` 을 title 과 같은 값으로 맞춘다.** 2026-09-20 실측에서 구글이 `<title>` 이 아니라 `og:title` 을 검색결과 제목으로 쓰고 있었다.
- 현재 `og:title ≠ title` 인 페이지는 **49장**이다(거의 전부). 대부분 빌더가 별도 패턴으로 생성한다:
  - 자금 15장: `{자금명} — 조건·실측·접수 일정 (2026)` (`build_funds.py`)
  - 재단 18장: `{재단명} — {지역} 소상공인 대출·사업자대출 (2026)` (`build_jaedan.py`)
  - 정적 16장: 손으로 쓴 값
- 규격 2절에 "og:title 은 title 과 동일, 빌더가 생성" 을 넣었으므로, B묶음에서 빌더 두 곳과 정적 16장을 한 번에 맞춘다.
- 주의: 49장의 `<head>` 가 바뀌면 `build_lastmod` 해시 범위(`<main>`·title·description)에는 안 들어가므로 **갱신일은 바뀌지 않는다**. 의도된 동작이다.

## 4. 롱테일 FAQ 나머지

`keywords-2026-09.md` 의 「네이버 검증 롱테일」 중 이번 묶음에서 처리하지 못한 항목이 생기면 여기로 옮긴다.
(2026-09-20 기준 10건 중 10건 처리 완료 — 자금 dict 4장 · 정적 5장.)
