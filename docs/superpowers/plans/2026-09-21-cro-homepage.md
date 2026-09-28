# CRO homepage implementation plan

> **For agentic workers:** Implement sequentially with test-driven-development and verification-before-completion. Research reporting is an independent delegated task; homepage/builder/conversion changes share interfaces and stay together.

**Goal:** Make the policy-funding diagnosis offer understandable and measurable without misleading costs, customer counts, or approval promises.
**Architecture:** Preserve the static multi-service homepage, existing form/API/analytics. Replace the hero and upper content only; derive proof and three case summaries from the existing ledger builder. Extend shared sticky visibility and explicit CTA service selection. No new dependencies or backend.
**Tech Stack:** Static HTML/CSS, shared JavaScript, Python ledger builders, pytest, Playwright.
**Spec:** User-approved recommended direction in conversation (2026-09-21), and updated docs/homepage-standard.md.

## Global constraints

- Free diagnosis; policy funding has no upfront/progress fees, success fee after disbursement. No fee rates, promised amounts, approval claims, new response-time promises or fabricated reviews.
- 385 records are not 385 unique customers. All quantitative proof comes from data/cases.source.csv through build_cases.py.
- Preserve all other company services, service selection/routing, guidebook event, news heading, search ownership tags, URLs, privacy and form failure exits.
- No competitor ranking/actual conversion-rate claims without evidence. Google search blocked, Naver results directly observed; Ohou blocked and replaced with Zipdoc.
- No real third-party form submissions; browser tests intercept our external lead request.
- Work on cro/2026-09-21-homepage, do not publish as part of unreviewed edits.

## Task 1: Research and update standard

- [x] Capture 10 accessible competitors, desktop 1440×900 and mobile 390×844, initial and dismissed overlays; retain raw evidence outside served assets.
- [x] Save docs/cro-competitor-review-2026-09-21.md with exact limits and observed patterns, not conversion guarantees.
- [x] Update standard: diagnosis-led hero; costs together; hero/diagnosis/cases; blue form action distinct from Kakao; explicit team responsibility.

## Task 2: Regression tests before implementation

Files: tests/test_sticky_cta.py, tests/test_homepage_experience.py, tests/test_cases_ledger.py.

- [x] Add real browser checks at 390×844: only one hero action; sticky hidden while hero button intersects, visible after hero leaves, hidden with form or input focus; resize/pageshow recomputes; absence of IntersectionObserver still works.
- [x] Click policy-specific hero action after a marketing service selection: form selects policy and consultation_click retains policy and hero location; general links must not reset a user's choice.
- [x] Intercept /api/lead and verify accepted delivery emits exactly one generate_lead with policy and hero attribution; errors must not emit it.
- [x] Generated case summary test consumes three fixture records and checks each link targets its own ID, values and label belong to that row, HTML escaping works. No hard-coded client counts.
- [x] Run tests and record expected failure before production edits. Replace obsolete exact-copy tests with semantics (one H1, correctly labeled ledger facts, preserved services/event).

## Task 3: Implement minimal approved scope

Files: index.html, assets/conversion.js, tools/build_cases.py.

- [x] Hero H1: 우리 사업에 맞는 / 정책자금, / 가능성부터 확인하세요. Sub: 사업 현황을 확인해 검토할 자금과 준비할 순서를 안내합니다. 진행이 어렵다면 그 이유부터 말씀드립니다.
- [x] Primary #heroCta links #apply with data-consultation-service=policy. Remove competing hero Kakao button; retain Kakao below in form/contact.
- [x] Visible scoped fee text and final institutional decision disclaimer. Keep photo, sourced proof link; no animated claim of customer count.
- [x] Upper sections: hero → 3 diagnostic checks (business context, funding purpose, institutional eligibility/preparation) → 3 ledger-backed cases with own anchors. Institution strip and evidence below these sections, followed by existing service content.
- [x] Remove unsupported 'typical competitor' comparison; replace absolute personal-management claims with staff consultation and representative participation.
- [x] Use explicit service intent only for tagged CTAs, updating select/help before analytics. General anchors preserve prior selection.
- [x] Sticky initially hidden in HTML; on load/pageshow/resize/scroll, determine hero CTA or form intersection using rectangles; IntersectionObserver schedules the same computation, focused form suppresses sticky. Use hidden attribute. Keep common script compatible with pages lacking form/hero.
- [x] Builder refreshes proof and case cards but never overwrites diagnosis H1 or counts cases as people. FAQ answers and JSON-LD stay identical when adding direct-application/cost/eligibility objections.

## Task 4: Verify and hand off

- [x] Run python -m pytest -q, node tests/test_conversion.mjs, node tests/test_analytics.mjs.
- [x] Run cases → funds → jaedan → gaein → consulting → jungjin → editorial → education → lastmod twice with actual date; compare hashes for churn 0.
- [x] Inspect 390×844 and desktop screenshots, additionally 360/320 widths for wrapping and sticky overlap. Verify all changed links, one H1, valid schema, no missing old services/event.
- [x] Independent code review, resolve substantive findings, rerun covering/full tests.
- [x] Report local revision and evidence; production publishing requires deliberate integration after verification. No claim of increased real conversion rate without analytics.

## Execution record

- Baseline: main clean, git pull --ff-only reports up to date; pytest 54 passed, 25 subtests passed.
- System Python has pytest; bundled Python does not. Use system Python for tests/builders.
- Research evidence: C:/Users/qornt/AppData/Local/Temp/bmaker-cro-20260921/.

### Final verification

- Initial new browser regressions: 4 failed, 1 passed before implementation; expected duplicate-action/service-intent/card coverage failures.
- Final required-browser suite: 61 passed, 20 subtests passed; no skips. Node conversion and analytics suites passed.
- Full 9-builder chain executed twice with actual date: second-run tracked-file hash churn 0.
- Chromium/Edge screenshots at 320, 360, 390 and 1440px: no horizontal overflow, one H1, initial sticky hidden, zero page errors. Cases and form inspected visually.
- Independent review found and resolved optional-browser CI compatibility, existing success-copy assertion, and historical evidence filename/current-ID mismatches (E9/E18). Re-review: ready to merge, no unresolved actionable findings.
- Evidence anchors checked against original source ledger, not filenames. Three fixture cards test amounts, institution, date, age, industry and escaped markup.
- Preview: http://127.0.0.1:8765/. No production deployment or real lead email submission performed. Main/remote unchanged; integration awaits user choice.
