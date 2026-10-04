# 어느 페이지에서도 바로 신청 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** bmaker.kr 110장 어디서든 페이지를 떠나지 않고 신청할 수 있게 — 3버튼 하단 바, 폼 없는 33장의 페이지 끝 폼, 긴 페이지 중간 버튼, 그 자리 신청 창 — 을 `assets/conversion.js` 한 곳에서 붙이고, 신청 버튼 색을 `#234780` 하나로 통일한다.

**Architecture:** 모든 페이지가 이미 한 번 불러오는 `assets/conversion.js` 에 부품을 더한다(새 `<script>` 없음). 페이지 끝 폼의 마크업·CSS 정본은 `tools/inline_form.py` 이고, `tools/build_lastmod.py`(체인 마지막)가 그 출력을 `conversion.js` 의 표시 구간에 써 넣은 뒤 `?v=` 해시를 찍는다 — 파이썬과 JS 가 갈라질 수 없다. 기존 제출 코드는 그대로 두고, 폼이 없으면 그 코드보다 **먼저** 폼을 만들어 둔다.

**Tech Stack:** 정적 HTML · 바닐라 JS(`conversion.js`) · Python 빌더 · pytest + Playwright Chromium(390×844) · Node VM(`tests/test_conversion.mjs`).

**Spec:** `docs/superpowers/specs/2026-10-04-apply-everywhere-design.md` (상위: policy-fund-crm `docs/superpowers/specs/2026-10-04-landing-conversion-design.md` 2-4)

## Global Constraints

- CTA 문구 `무료 진단 신청`. 신청 버튼 색 **`#234780`** 하나(바·중간 버튼·창·인라인 폼 제출 버튼). 글자 흰색.
- 카카오 옐로 `#FEE500`(글자 `#191600`)는 카톡 아이콘에만. 전화 아이콘은 흰 바탕 + 네이비 테두리 `#0E1B33`.
- 카톡 `https://pf.kakao.com/_GKuxfn/chat`(새 탭) · 전화 `tel:1666-2425`.
- 비용 문구는 `진단은 무료입니다.` 까지(중간 버튼 아래 한 줄만). 무조건·100%·보장 계열 금지.
- 필수 입력은 성함·연락처·동의. 사업자 형태·통화 희망 시간은 선택.
- 홈 히어로·홈 폼 위치 불변. 메타 동결 6장의 title·description·og:title 불변.
- 새 스크립트 파일 금지 · 빌더 체인 순서 불변 · HTML 을 손으로 고치지 않는다(생성물은 빌더/`build_lastmod`).
- 휴대폰 기준 ≤840px(기존 `.nav-cta-book` 경계와 같다), PC 상자는 >840px.
- `main` 직접 푸시 금지 — 브랜치 `docs/apply-everywhere-design`(PR) 에 올린다.

## Review Focus

1. **iOS 에서 초점 없이 키보드가 남는 경우** — `visualViewport.height < innerHeight × 0.75` 면 바를 숨긴다. → Task 3 테스트(`visualViewport` 흉내).
2. **창을 연 채 뒤로가기** — 페이지를 떠나지 않고 창만 닫힌다. 닫은 뒤 다시 뒤로가기는 정상 이전 페이지. → Task 5 테스트.
3. **창 안에서 신청 완료 뒤 닫기 → 다시 열기** — 완료 문구가 남아 있고 두 번 보내지 않는다(기존 `completed` 규칙). → Task 5 테스트.
4. **자바스크립트가 꺼진 환경** — 기존 링크 `href` 가 그대로라 예전처럼 홈 폼으로 간다(페이지 끝 폼은 안 생긴다 — `noscript` 안내는 인라인 폼에만). → Task 5 테스트(링크 href 불변 확인).
5. **`#apply` 앵커로 직접 들어온 C 페이지** — 페이지 끝 폼이 만들어진 뒤 그 위치로 스크롤된다. → Task 4 테스트.

---

### Task 1: 규격 4절 개정 + 신청 버튼 한 색

**Files:**
- Modify: `docs/homepage-standard.md` (4절 고정 바 문장 · 변경 이력)
- Modify: `tools/inline_form.py` (`CSS` 의 `button[type=submit]` 두 곳 `#2454bc` → `#234780`)
- Regenerate: 빌더 체인 12개 → 인라인 폼 쓰는 생성 페이지
- Modify(정적, 함수 출력을 붙여 넣은 페이지): `2026-4q-sosangin.html` 의 같은 규칙
- Test: `tests/test_apply_everywhere.py` (새 파일, 첫 테스트)

- [ ] Step 1 — 실패 테스트: 모든 HTML 의 `.inline-diag button[type=submit]` 규칙에 `#234780` 이 있고 `#2454bc` 가 없다; `inline_form.CSS` 도 같다.
- [ ] Step 2 — 실패 확인 `python -m pytest -q tests/test_apply_everywhere.py -k color`
- [ ] Step 3 — `inline_form.py` 수정 → 체인 실행 → 4분기 정적 페이지 같은 줄 수정 → `build_lastmod`
- [ ] Step 4 — 통과 + `git diff` 가 그 CSS 규칙 줄만 바꿨는지 확인(다른 줄 0) + 체인 두 번째 실행 churn 0
- [ ] Step 5 — 규격 4절·변경 이력 수정 후 커밋 `style(form): 신청 버튼 한 색 #234780 + 규격 4절 고정 바 개정`

### Task 2: 인라인 폼 템플릿을 conversion.js 로 (정본은 inline_form.py)

**Files:**
- Create: `tools/sync_inline_form_js.py` — `form_html('__PATH__', '__LABEL__', TITLE_GENERAL)` 와 `CSS` 를 JSON 문자열로 만들어 `assets/conversion.js` 의 `/* @inline-form:start */ … /* @inline-form:end */` 사이를 바꿔 쓴다. 바뀐 게 없으면 파일을 건드리지 않는다.
- Modify: `tools/build_lastmod.py` — 해시 계산 **전에** `sync_inline_form_js.sync()` 호출
- Modify: `assets/conversion.js` — 표시 구간(`const INLINE_FORM_HTML = …; const INLINE_FORM_CSS = …;`)
- Test: `tests/test_apply_everywhere.py`

**Interfaces:** Produces `INLINE_FORM_HTML`(자리표시 `__PATH__ (__LABEL__)` 포함) · `INLINE_FORM_CSS` (JS 상수)

- [ ] Step 1 — 실패 테스트: `conversion.js` 표시 구간 내용 == `sync_inline_form_js.render()`; `inline_form.py` 를 바꾸고 동기화를 안 하면 실패(테스트 안에서 임시 문자열로 확인).
- [ ] Step 2~4 — 구현·통과·`build_lastmod` 두 번 churn 0
- [ ] Step 5 — 커밋 `build: inline form template synced into conversion.js by build_lastmod`

### Task 3: 3버튼 하단 바 (110장)

**Files:**
- Modify: `assets/conversion.js` — 바 만들기(홈은 기존 `.sticky-cta` 를 3버튼으로 채움, 그 밖은 새로 만듦) · 숨김 규칙 · 아래 여백 · `scroll-padding-bottom` · 계측
- Modify: `index.html` — `.sticky-cta` 정적 마크업 한 줄 단위로 3버튼으로 (CSS 블록 해당 줄만)
- Modify: `tests/test_sticky_cta.py` — `to_have_count(1)` → 신청 1 + 아이콘 2
- Test: `tests/test_apply_everywhere.py`

- [ ] Step 1 — 실패 테스트(390×844, 대표 페이지 `index.html`·`jaedan-seoul.html`·`sojingong.html`·`blog.html` + 110장 순회 1개):
  바 보임(홈은 스크롤 뒤) · 화면 안 · 가로 넘침 0 · 신청 폭 ≥ 아이콘×3 · 신청 배경 `rgb(35, 71, 128)` · 카톡 아이콘만 노랑 ·
  폼 보이면 숨김 · `input` 초점이면 숨김 · `visualViewport` 축소 흉내(`Object.defineProperty`)면 숨김 ·
  맨 아래에서 푸터 마지막 링크 bottom ≤ 바 top · `#faq` 이동 뒤 대상 제목이 바 위 · PC 1366: 우측 하단 상자.
- [ ] Step 2~4 — 구현·통과 · 기존 `test_sticky_cta.py` 통과
- [ ] Step 5 — 커밋 `feat(apply): 3-button sticky bar on every page (apply dominant, hides on form/keyboard)`

### Task 4: 페이지 끝 폼 (C 33장) + 중간 버튼

**Files:**
- Modify: `assets/conversion.js` — `#leadForm` 이 없으면 기존 `const form = …` **앞에서** `<footer>` 앞에 `INLINE_FORM_HTML` 을 넣고 `INLINE_FORM_CSS` `<style>` 추가, `lf-page`=`경로 (h1 앞 40자)`, `lf-service`=페이지 분야. 문서 높이 > 화면×5 면 40% 지점 `h2` 앞에 중간 버튼.
- Test: `tests/test_apply_everywhere.py`

- [ ] Step 1 — 실패 테스트: 33장 목록(설계서 2절) 각각 `#leadForm` 정확히 1개 · 나머지 77장도 1개(새로 안 생김) ·
  C 페이지의 `#apply` 구조(태그·id·문구) == `inline_form.form_html(path, label, TITLE_GENERAL)` ·
  `/sojingong.html#apply` 로 들어오면 폼이 화면에 · 5화면 초과 C 페이지에만 중간 버튼 1개, 표·`details` 안에 없음.
- [ ] Step 2~4 — 구현·통과 · `node tests/test_conversion.mjs` 통과(VM 에 `<footer>` 없음 → 폼 안 만듦을 확인)
- [ ] Step 5 — 커밋 `feat(apply): page-end form on the 33 form-less pages + one mid-content button on long pages`

### Task 5: 그 자리 신청 창

**Files:**
- Modify: `assets/conversion.js` — 창(시트/가운데) · 폼 옮기기·되돌리기(자리표시 요소) · 닫기(버튼·Esc·배경·`popstate`) · 초점 가둠·복귀 · 스크롤 잠금·보존 · `visualViewport` 에 맞춘 높이 · 다른 페이지 `#apply` 링크 가로채기(`?service=` 반영) · `apply_sheet_open` 계측
- Test: `tests/test_apply_everywhere.py`

- [ ] Step 1 — 실패 테스트: 바 신청 → 창 열림·`#leadForm` 이 창 안·바 숨김 / 닫기 3가지 · 뒤로가기 → 창 닫히고 주소 그대로 ·
  초점 첫 입력·Tab 가둠·닫으면 연 버튼 초점 · 스크롤 위치 보존 · `/?service=marketing#apply` 링크 → 창 + `lf-service=marketing`, 링크 `href` 불변 ·
  창 안 제출(`/api/lead` 가로챔) → 본문에 `request_id`·`landing_url`·기존 필드, `generate_lead` 1건 · 닫았다 다시 열면 완료 문구 유지·재전송 없음 ·
  홈은 창 대신 기존 스크롤.
- [ ] Step 2~4 — 구현·통과
- [ ] Step 5 — 커밋 `feat(apply): in-place apply sheet (form moves into it; Esc/backdrop/back close)`

### Task 6: 마무리

- [ ] 빌더 체인 2회 churn 0 · `python -m pytest -q` · `node tests/test_conversion.mjs` · `node tests/test_analytics.mjs`
- [ ] 휴대폰 캡처 4장(대표 지시): ① 폼 없던 페이지(`/sojingong`) 페이지 끝 폼+바 ② 인라인 폼 페이지(`/jaedan-seoul`) ③ 신청 창 열린 모습 ④ 키보드 올라왔을 때(입력 초점 + `visualViewport` 축소 흉내) → 대표에게
- [ ] 브랜치 push → 대표 머지 → 배포 확인(`?v=` 해시 · 대표 페이지 바) → measure-log 기준선 칸 옮기기(배포 직전 GA4 28일 값)
