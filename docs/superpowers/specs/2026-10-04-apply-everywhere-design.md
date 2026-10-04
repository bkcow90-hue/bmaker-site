# 어느 페이지에서도 바로 신청 — bmaker.kr 설계 세부

- 날짜: 2026-10-04 · 상태: **설계 세부 검토 대기**(1단계). 2단계(구현 계획)·3단계(구현)는 대표 지시대로 PR #31 머지 후 —
  PR #31(`trust-pages-2026-10`)은 2026-10-04 `a3ef76a` 로 **이미 머지됨**을 확인했다.
- 상위 설계(승인됨): policy-fund-crm `docs/superpowers/specs/2026-10-04-landing-conversion-design.md` 2-4절.
  codedaum(파워링크 랜딩)은 그 설계로 먼저 배포됐다(`lp.js`, 2026-10-04).
- 기준: 규격 정본 `docs/homepage-standard.md`. 이 문서가 규격과 다른 곳은 **4절 고정 바 한 군데뿐**이고, 구현 PR 에서
  규격을 먼저 고친다(아래 7절).

---

## 1. 지키는 것 (규격 정본에서)

| 규칙 | 이 설계에서 |
|---|---|
| CTA 문구 "무료 진단 신청" | 바·중간 버튼·창 제출 버튼 모두 이 문구 하나 |
| 신청은 브랜드 블루 `#234780` | 바 신청 버튼·중간 버튼 배경 `#234780`, 글자 흰색 |
| 카카오 옐로는 실제 카카오 이동에만 | 카톡 아이콘 하나만 `#FEE500`. 다른 곳에 노랑을 쓰지 않는다 |
| 비용 문구는 "진단은 무료입니다."까지 | 바·창·중간 버튼에 비용·착수금·성과 보수 문구를 넣지 않는다. 창 부제는 기존 인라인 폼 문구 그대로 |
| 폼은 성함+연락처+동의 최소 | 필수는 이 셋. 사업자 형태·통화 희망 시간은 **선택**(기존 인라인 폼과 같다). 서류 첨부 요구 없음 |
| 홈 히어로 구조 유지 | 홈 히어로·폼 위치·`#heroCta` 는 그대로. 홈 바는 지금처럼 히어로 CTA 가 보이는 동안 숨긴다 |
| conversion.js 1회 · h1 1개 | 새 코드는 전부 `assets/conversion.js` 안. 새 `<script>` 를 만들지 않는다 |
| 과장 표현 금지 | 무조건·100%·보장 계열 없음(기존 금칙어 검사가 그대로 잡는다) |
| 메타 동결 6장(~10/6) | title·description·og:title 을 건드리지 않는다(이 설계는 본문 아래 부품만 붙인다) |

## 2. 페이지 분류 — 중복 없이 대상 확정 (2026-10-04 `main` 실측, sitemap 110장)

| 분류 | 장수 | 무엇이 붙나 |
|---|---|---|
| **A. 홈** (`/`) | 1 | 기존 홈 폼(`#apply`) 유지. 하단 바를 3버튼으로 바꾸고 숨김 규칙은 그대로 |
| **B. 인라인 폼 있음** (`tools/inline_form.py` 출력, `#apply.inline-diag` + `#leadForm`) | **76** | **페이지 끝 폼을 붙이지 않는다.** 하단 바 + 그 자리 신청 창(기존 폼을 창으로 옮김) |
| **C. 폼 없음** | **33** | 하단 바 + **페이지 끝 폼 1개**(인라인 폼과 같은 마크업) + 긴 페이지는 중간 버튼 1개 + 신청 창 |

B 의 내역: 자금 상세(빌더 funds) · 재단 17(`/jaedan-*`) · 지역 19(`/region/*`) · 블로그 19(`/blog/*`) · 허브 · 4분기 안내.
(`inline_form.py` 머리말의 '35장'은 자금 15·재단 18·허브 2 시절 숫자다. 지금은 지역·블로그·4분기까지 같은 폼을 쓴다)

**C 대상 33장(확정 목록)** — 판정: HTML 에 `id="leadForm"` 도 `id="lf-page"` 도 없음.

```
/sojingong /jungjingong /bojeung /certification /industry/eumsikjeom /cases /stats /jeosinyong
/chaksugeum /sanghwan /gyehoekseo /geojeol /gibo /sinbo /faq /schedule /gaein /consulting
/funding /marketing /startup /work /business-guide /online-ad-guide /blog-marketing-cost
/viral-marketing-guide /startup-consulting-cost /education /education-program
/corporate-loan-documents /working-capital-facility /sme-business-loans /microfinance-business
```

- **중복 방지는 목록이 아니라 실행 시 판정으로 한다**: `conversion.js` 가 그 페이지에 `#leadForm` 이 **없을 때만** 페이지 끝
  폼을 만든다. 그래서 나중에 빌더가 어떤 페이지에 인라인 폼을 넣으면 그 페이지는 자동으로 B 가 되고, 폼이 두 개가 되지 않는다.
  위 33장 목록은 테스트의 기대값으로 쓴다(테스트가 판정 결과와 목록을 대조).
- `/chaksugeum`·`/consulting` 은 PR #31 이 본문을 고친 페이지다 — 이 설계는 그 본문을 건드리지 않고 **본문 뒤**에만 붙인다.

## 3. 부품

### 3-1. 하단 신청 바 `.sticky-cta` (A·B·C 전부, 110장)

- **모양** — 휴대폰(≤840px): 화면 아래 한 줄.
  `[ 무료 진단 신청 (넓게, #234780) ] (카톡 ◯ #FEE500) (전화 ◯ 테두리)` — 신청 버튼이 줄 폭 대부분, 아이콘은 지름 46px.
  PC(>840px): 우측 하단 상자(폭 300px, 아래·오른쪽 24px). 같은 우선순위.
- **아이콘 접근성** — 카톡 `aria-label="카카오톡 상담"`(새 탭), 전화 `aria-label="전화 상담 1666-2425"`(`tel:1666-2425`).
- **클래스 이름은 기존 `.sticky-cta` 를 유지**한다(홈 테스트·CSS·계측의 이름이 이어진다). 홈의 정적 마크업은
  3버튼 마크업으로 바꾸고, 홈이 아닌 페이지는 `conversion.js` 가 같은 마크업을 만든다.
- **숨김 규칙**(하나라도 참이면 `hidden` 속성):
  1. 히어로 CTA(`#heroCta`)가 화면에 보임 — 홈과 히어로 CTA 가 있는 페이지(기존 규칙 그대로)
  2. 그 페이지의 폼(`#leadForm`)이 화면에 보임 — **인라인 폼 76장 + 페이지 끝 폼 33장 모두**
  3. 신청 창이 열려 있음
  4. **키보드가 올라와 있음** — 페이지 어디서든 `input·textarea·select` 에 초점이 있거나(`focusin`/`focusout`),
     `visualViewport.height < innerHeight × 0.75` (iOS 가 초점 없이 키보드를 남기는 경우). 키보드 위로 바가 떠서
     입력칸·제출 버튼을 가리는 것을 막는다.
- **본문을 가리지 않기**(390×844 기준):
  - 휴대폰에서 `body` 아래 여백 = 바 높이 + `env(safe-area-inset-bottom)` — 맨 아래까지 내려도 푸터 마지막 링크가 바 위에 온다
  - `html { scroll-padding-bottom: 바 높이 }` — `#faq` 같은 앵커로 이동하거나 FAQ `<details>` 를 펼칠 때 바 아래로 들어가지 않는다
  - 층 순서: 바(z-index 50) < 신청 창(80). 페이지에 그보다 높은 기존 층이 있는지는 구현 계획에서 전수 확인한다
    (개인정보처리방침 링크는 `/privacy` 새 탭이라 모달이 아니다)
- **계측**(GA4, 기존 이벤트 이름): 신청 `cta_click{cta_location:'sticky_bar'}` · 카톡 `kakao_click{cta_location:'sticky_bar'}` ·
  전화 `phone_click{cta_location:'sticky_bar'}`(새 이벤트 이름 — 전화 클릭은 지금까지 안 셌다).

### 3-2. 페이지 끝 간편 신청 폼 (C 33장만)

- **마크업은 `tools/inline_form.py` `form_html(path, label, TITLE_GENERAL)` 출력과 같다** — `#apply.inline-diag` 안의
  `#leadForm`, ID 규약(`lf-name·lf-phone·lf-consent·lf-website·lf-service·lf-page·applyMsg·#lf-time·#lf-biztype`) 그대로.
  그래서 `conversion.js` 의 기존 제출 코드(`/api/lead` · 동의 · 허니팟 · 요청 ID · `landing_url` · `generate_lead`)가
  **한 줄도 바뀌지 않고** 이 폼을 쓴다.
- 스타일은 `inline_form.CSS` 를 같이 넣는다(이 33장에는 그 CSS 가 없다 — 2026-09-28 허브 2장이 HTML 만 복사해 브라우저
  기본 모양으로 배포됐던 사고와 같은 모양을 막는다).
- 두 곳(파이썬 빌더 · JS)이 같은 마크업을 갖게 되므로 **같음 검사**를 둔다: 브라우저로 C 페이지를 열어 만들어진 `#apply`
  의 구조(요소·ID·문구)를 `form_html()` 출력과 대조한다. 한쪽만 고치면 테스트가 실패한다.
- **위치**: `<footer>` 바로 앞(본문이 끝난 뒤, 푸터 위). `lf-page` = `경로 (h1 텍스트 앞 40자)`.
  `lf-service` = 그 페이지의 문의 분야(`body[data-service]` 또는 기존 `pageService` 판정) — 정책자금 페이지는 `policy`.
- 제목은 `TITLE_GENERAL`('우리 회사도 되는지 무료로 확인'), 부제·안내 문구는 인라인 폼 그대로(비용 문구 없음).

### 3-3. 본문 중간 신청 버튼 (C 중 휴대폰 5화면 초과)

- 실행 시 판정: 390 기준 문서 높이 > 화면 높이 × 5 일 때만. (2026-10-04 실측으로 C 33장 중 약 20장 — `/jungjingong` 23화면,
  `/cases` 120화면 등)
- 위치: `<main>`(없으면 본문)의 `h2` 중 문서 높이 40% 지점에 가장 가까운 것 **바로 앞**에 한 번. 표·FAQ `<details>` 안에는 넣지 않는다.
- 모양: 본문 폭 버튼 하나 `무료 진단 신청`(#234780) + 아래 작은 글씨 "진단은 무료입니다." 한 줄. 누르면 신청 창.
- 계측 `cta_click{cta_location:'mid_content'}`.

### 3-4. 그 자리 신청 창 (B·C 전부, 홈 제외)

- **여는 것**: 하단 바 신청 버튼 · 중간 버튼 · **다른 페이지로 보내던 기존 신청 링크**(`/#apply`, `/?service=…#apply`,
  `/index.html#apply` — 33장에 있는 '무료 진단 신청' 링크들). 같은 페이지 `#apply` 앵커는 지금처럼 스크롤(창을 열지 않음).
  - 링크의 `href` 는 그대로 둔다(자바스크립트가 없으면 예전처럼 홈으로 간다). 클릭만 가로챈다.
  - `?service=X` 가 있으면 창 안 폼의 `lf-service` 를 X 로 맞춘다(기존 '의도 보존' 규칙과 같은 결과).
- **폼은 페이지마다 하나**: 창을 열면 그 페이지의 `#apply`(B 는 인라인 폼, C 는 페이지 끝 폼)를 **창 안으로 옮기고**,
  닫으면 원래 자리(남겨 둔 빈 자리표시 요소)로 되돌린다. 입력하던 값·신청 완료 상태가 그대로 따라간다.
- **휴대폰**: 아래에서 올라오는 시트(높이는 내용만큼, 최대 `92svh`, 안에서 스크롤, 위쪽 모서리 둥글게, 손잡이 표시).
  **PC**: 가운데 창(폭 최대 480px). 뒤 배경은 반투명.
- **닫기**: 오른쪽 위 [닫기] 버튼 · `Esc` · 배경 탭 · **휴대폰 뒤로가기**(열 때 `history.pushState`, `popstate` 에 닫음 —
  뒤로가기로 페이지를 떠나지 않게). 닫으면 연 버튼으로 초점을 돌려준다.
- **접근성**: `role="dialog" aria-modal="true" aria-labelledby="inline-diag-title"`, 열면 첫 입력(사업자 형태 첫 버튼)에 초점,
  `Tab` 이 창 밖으로 나가지 않음, 열려 있는 동안 뒤 페이지 스크롤 잠금(닫으면 원래 스크롤 위치 그대로).
- **키보드**: 창 안 입력에 초점이 가면 `visualViewport` 높이에 맞춰 창 최대 높이를 줄이고 초점 칸을 보이는 곳으로
  스크롤한다(키보드가 제출 버튼을 가리지 않게).
- **신청 완료 뒤**: 성공 문구(규격 4절 확정 문구)를 창 안에 보여 주고, [닫기]만 남긴다. `generate_lead` 는 기존 코드가 한 번 보낸다.
- 계측 `apply_sheet_open{cta_location}`(어디서 열었나), 기존 `consultation_start`·`consultation_submit`·`generate_lead` 그대로.

## 4. 데이터 흐름 (바뀌지 않는 것)

신청 → 기존 `conversion.js` 제출 → `codedaum.pages.dev/api/lead` (요청 ID·`landing_url` 포함) → CRM 직접 등록 + 하이웍스 메일.
CRM 출처 규칙도 그대로(`n_media`/`utm_source=powerlink` → 6.홈페이지 근거 '파워링크', 메타 → 7.메타, 나머지 6.홈페이지).

## 5. 측정 기준선 — `docs/measure-log.md` 에 옮길 초안

구현 PR 에서 아래 칸을 `docs/measure-log.md` 에 옮겨 적는다(이 PR 은 measure-log 를 건드리지 않는다 — PR #31 이 같은 파일을
고쳤다). **구현 배포 직전**에 값을 채우고, 배포 +14일·+28일에 같은 방법으로 다시 잰다.

| 지표 | 기간 | 값 | 재는 방법 |
|---|---|---|---|
| bmaker.kr 경유 신청 수 (CRM) | 배포 전 28일 | ⬜ | `auto_intake_records` 중 `source_kind='mail-homepage'` 이고 `payload.fields.유입 페이지` 가 `bmaker.kr` 로 시작, 상태 `inserted`/`reinflow`(테스트 번호 `010-0000-00xx` 제외) |
| 참고: 출처 6.홈페이지 신규 고객 (CRM, 경로 구분 없음) | 배포 전 28일 | ⬜ (2026-10-04 기준 11) | `leads` × `sources.intake_role='homepage'`, `created_at` 28일 |
| GA4 `generate_lead` (호스트 bmaker.kr) | 배포 전 28일 | ⬜ | GA4 → 탐색 → 이벤트 이름 `generate_lead`, 필터 `hostname = bmaker.kr` |
| GA4 `generate_lead` 위치별 | 배포 후 | ⬜ | 같은 보고서에 `cta_location` 측정기준(sticky_bar · mid_content · page_end · 기존 값) |
| 참고: codedaum `generate_lead` | 배포 후 | ⬜ | 같은 속성, `hostname = codedaum.pages.dev` (2026-10-04 부터 측정) |

⚠️ **기준선의 한계(확인된 사실)**: CRM 의 유입 경로 기록은 **2026-10-04 부터**다(그 전 홈페이지 신청은 메일 → 손 입력이라
경로가 없고, 있었다 해도 Referrer-Policy 때문에 `https://bmaker.kr/` 로만 남았다). 그래서 '배포 전 28일'을 2026-10-04 이후로
채우려면 **구현 배포를 2026-11-01 이후로 미루거나**, 그보다 이르면 짧은 기간(예: 14일)으로 기준선을 잡고 그 사실을 적는다.
2026-10-04 현재 bmaker.kr 경유 자동 등록은 테스트 2건(C·D)뿐이다.

## 6. 테스트 (구현 PR 에서 — 규격 10절: 전환 동작은 브라우저 동작 검사)

| 검사 | 어디서 |
|---|---|
| 390×844: 110장 모두 바가 화면 안에 보임(히어로 CTA 가 있으면 그 아래로 스크롤 뒤) · 가로 넘침 없음 | 새 `tests/test_apply_everywhere.py` (Playwright Chromium) |
| 바: 신청 버튼 폭 ≥ 아이콘 3배 · 아이콘 2개 `aria-label` · 신청 버튼 색 `#234780` · 카톡만 노랑 | 같은 파일 |
| 바 숨김: 폼 보임 · 창 열림 · 입력칸 초점(키보드) · `visualViewport` 축소 흉내 | 같은 파일 |
| 가리지 않음: 맨 아래에서 푸터 마지막 링크·FAQ 마지막 `<summary>` 가 바 위 · `#faq` 앵커 이동 후 제목이 바 위 | 같은 파일 |
| 중복 없음: B 76장 `#leadForm` 1개(페이지 끝 폼 안 생김) · C 33장 `#leadForm` 1개(생김) — 33장 목록과 대조 | 같은 파일 |
| 같음: C 페이지에서 만들어진 `#apply` 구조 = `inline_form.form_html()` | 같은 파일(파이썬에서 `form_html` 호출) |
| 창: 열림 · 폼이 창으로 옮겨지고 닫으면 제자리 · `Esc`/배경/뒤로가기 닫기 · 초점 가둠·복귀 · 스크롤 위치 보존 · `?service=` 반영 | 같은 파일 |
| 신청: 창 안 제출 → `/api/lead` 가로채 본문에 `request_id`·`landing_url`·기존 필드 · `generate_lead` 1건 | 같은 파일 + 기존 `tests/test_conversion.mjs` |
| 홈 회귀: 기존 `tests/test_sticky_cta.py` — 링크 개수 기대값만 1 → (신청 1 + 아이콘 2)로 고치고 나머지 그대로 | 수정 |
| 금칙어·비용 문구 | 기존 `test_fee_copy.py` 등 그대로 통과 |

## 7. 규격 개정 (구현 PR 에서 먼저)

`docs/homepage-standard.md` 4절 "모바일 고정 바(.sticky-cta)도 버튼 1개" →
"모바일 고정 바(.sticky-cta)는 **신청 버튼 1개(크게, 브랜드 블루) + 카톡·전화 작은 보조 아이콘**. PC 는 우측 하단 상자.
히어로 CTA·폼이 보이거나 키보드가 올라와 있으면 숨긴다. 폼 없는 페이지는 페이지 끝에 인라인 폼과 같은 간편 신청 폼,
신청 버튼은 다른 페이지로 보내지 않고 그 자리 신청 창을 연다." + 변경 이력 "승인: 대표 2026-10-04".

## 8. 하지 않는 것

- 기존 인라인 폼 76장의 위치·문구·모양 변경(창으로 옮겨 쓰기만 한다).
- 홈 히어로·홈 폼 위치 변경.
- 새 스크립트 파일·빌더 체인 변경(빌더는 손대지 않는다. `?v=` 해시 갱신만 `build_lastmod`).
- 페이지별 카피·메타 변경.

## 9. 열린 질문

- 신청 버튼 색: 대표 지정 `#234780`(홈 `--blue-deep`)으로 한다. 기존 인라인 폼 제출 버튼은 `#2454bc` 라 **같은 화면에 파랑 두 가지**가
  보인다(창 안 제출 버튼 `#2454bc`, 바 `#234780`). 인라인 폼도 `#234780` 으로 맞출지는 구현 계획에서 대표 확인.
