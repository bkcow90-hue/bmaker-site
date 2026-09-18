# 작업 규칙 — bmaker.kr

이 저장소는 Claude·Codex 가 번갈아 편집하고, `main` 에 푸시하면 Cloudflare 가 바로 배포한다.
사고가 났던 것만 적는다. 서비스·카피·컴플라이언스 맥락은 `.agents/product-marketing.md`,
원장·빌더 절차는 `tools/ledger-update.md` 를 본다.

## git

- **작업 중 되돌릴 땐 `git checkout -- .` 금지.** 파일 경로를 명시하거나 `git stash` 를 쓴다
  — 산출물 되돌리다 소스 수정이 같이 날아간 사례(2026-09-19).
- 작업 시작 전 `git pull --ff-only`. ledger 봇이 매시 `main` 에 커밋하므로, 안 하면 봇 결과를
  되돌리는 커밋이 생긴다.
- `index.html` 은 통파일 덮어쓰기 금지 — 고치는 부분만 수정한다(병행 편집 충돌 방지).

## 빌드

- HTML 을 손으로 고쳤으면 커밋 전에 `python tools/build_lastmod.py`. 안 하면
  `tests/test_lastmod.py` 가 "본문이 바뀌었는데 갱신일이 그대로" 로 막는다.
- 빌더 체인은 `build_lastmod.py` 를 **마지막**에 돌린다. 자금·재단·교육 빌더가 서로의
  `<footer>`·`<head>` 를 복사해 가므로 순서가 결과를 바꾼다.
- 날짜는 `tools/builddate.py` 의 `build_date()` 만 쓴다. 빌더마다 따로 계산하지 않는다.

## 배포 안전장치

- `.assetsignore` 가 `.git/`·`tools/`·`docs/`·`.github/`·이 파일 등을 서빙에서 빼는 유일한
  방어선이다. 루트에 새 파일을 만들면 **공개 URL 로 그대로 노출되는지** 먼저 확인한다.
- `python -m pytest -q` 와 `node tests/test_conversion.mjs`·`test_analytics.mjs` 가 게이트다.
  브라우저 동작 테스트는 `pr-check` 워크플로에서 `REQUIRE_BROWSER=1` 로 돌아간다.
