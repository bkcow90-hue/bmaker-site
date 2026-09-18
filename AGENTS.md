# 작업 규칙 — bmaker.kr (Codex·기타 에이전트용)

규칙 본문은 [`CLAUDE.md`](CLAUDE.md) 하나로 관리한다. Claude·Codex 가 같은 규칙을 보도록
여기서는 중복 서술하지 않고, 사고로 이어졌던 항목만 다시 적는다.

- **페이지·카피·CSS·빌더를 만지기 전 [`docs/homepage-standard.md`](docs/homepage-standard.md) 를
  읽는다. 작업이 규격과 충돌하면 코드가 아니라 규격 파일을 먼저 고친다(변경 이력 남김).**
- **작업 중 되돌릴 땐 `git checkout -- .` 금지.** 파일 경로를 명시하거나 `git stash` 를 쓴다
  — 산출물 되돌리다 소스 수정이 같이 날아간 사례(2026-09-19).
- 작업 시작 전 `git pull --ff-only` (ledger 봇이 매시 `main` 에 커밋한다).
- `index.html` 은 통파일 덮어쓰기 금지 — 고치는 부분만 수정한다.

빌더 순서·`build_lastmod.py`·`builddate.py`·`.assetsignore`·CSS 전파 등 제작 규칙은
`docs/homepage-standard.md`, 저장소 운영(pull·테스트 게이트·pr-check)은 `CLAUDE.md` 를 따른다.
서비스·카피 맥락은 `.agents/product-marketing.md`, 원장 절차는 `tools/ledger-update.md`.
