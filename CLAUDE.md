# 작업 규칙 — bmaker.kr

이 저장소는 Claude·Codex 가 번갈아 편집하고, `main` 에 푸시하면 Cloudflare 가 바로 배포한다.

- **페이지·카피·CSS·빌더를 만지기 전 [`docs/homepage-standard.md`](docs/homepage-standard.md) 를
  읽는다. 작업이 규격과 충돌하면 코드가 아니라 규격 파일을 먼저 고친다(변경 이력 남김).**

규격에 담긴 내용(콘텐츠 금지어, SEO·GEO, 전환·홈 구조, 디자인, 모바일, 광고 랜딩,
빌드·코드 규칙, 테스트·검증)은 여기에 다시 적지 않는다. 아래는 저장소 운영 규칙만이다.
서비스·카피 맥락은 `.agents/product-marketing.md`, 원장 절차는 `tools/ledger-update.md`.

## 저장소 운영

- 작업 시작 전 `git pull --ff-only`. ledger 봇이 매시 `main` 에 커밋하므로, 안 하면 봇 결과를
  되돌리는 커밋이 생긴다.
- 게이트: `python -m pytest -q` 와 `node tests/test_conversion.mjs`·`test_analytics.mjs`.
  푸시 전에 로컬에서 돌린다.
- `pr-check` 워크플로가 `main` 푸시·PR 마다 pytest + 브라우저 동작 테스트(`REQUIRE_BROWSER=1`)
  + 빌더 체인 churn 검사를 돌린다. churn 검사는 첫 주 경고만(`continue-on-error`).
- 배포는 `main` 푸시 즉시다. 되돌릴 일이 생기면 되돌리는 커밋을 올린다.
