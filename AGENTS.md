# 작업 규칙 — bmaker.kr (Codex·기타 에이전트용)

> **Codex 포함 모든 에이전트는 `main` 직접 푸시 금지. 브랜치 + PR 로 올리고, 머지는 대표 확인 후.**
> (2026-09-28 대표 지시 — 9/21 에 규격·홈·conversion.js 가 `main` 직접 푸시로 바뀌어
> 진행 중이던 CTR 실험 3장의 title 이 측정 구간 중간에 교체된 사고가 있었다.)

규칙 본문은 [`CLAUDE.md`](CLAUDE.md) 하나로 관리한다. Claude·Codex 가 같은 규칙을 보도록
여기서는 중복 서술하지 않고, 사고로 이어졌던 항목만 다시 적는다.

- **페이지·카피·CSS·빌더를 만지기 전 [`docs/homepage-standard.md`](docs/homepage-standard.md) 를
  읽는다. 작업이 규격과 충돌하면 코드가 아니라 규격 파일을 먼저 고친다(변경 이력 남김).**
- **작업 중 되돌릴 땐 `git checkout -- .` 금지** (.claude/settings.json deny 로 차단됨 — 파일 경로를 명시한 checkout/restore 만 허용). 파일 경로를 명시하거나 `git stash` 를 쓴다
  — 산출물 되돌리다 소스 수정이 같이 날아간 사례(2026-09-19).
- 작업 시작 전 `git pull --ff-only` (ledger 봇이 매시 `main` 에 커밋한다).
- `index.html` 은 통파일 덮어쓰기 금지 — 고치는 부분만 수정한다.

## 메타 동결 — 2026-10-06 까지 (2026-09-28 대표 지시)

아래 6장의 **`<title>` · `meta description` · `og:title` 을 고치지 않는다.** CTR 실험 판정 데이터가
섞이기 때문이다. 본문·FAQ·구조화 데이터·내부 링크는 평소대로 고쳐도 된다.

| 페이지 | 이유 | 판정일 |
|---|---|---|
| `/jaedan` · `/gyehoekseo` | 9/13 title v1 이 구간 내내 유지됨 — 유효 표본 | 2026-09-30 (9/14~9/27 구간) |
| `/sanghwan` · `/bojeung` | Codex `f41cac0`(9/21)가 구간 중간에 v2 로 교체 | 2026-10-05 (9/21+14일) |
| `/jungjingong` | `f41cac0`(9/21)·`5c5c577`(9/22) 2회 교체 | 2026-10-06 (9/22+14일) |
| `/cheongnyeon` | title v2 배포(2026-09-20 `ada0fea`) +14일 재측정 | 2026-10-04 |

빌더가 title·og:title 을 생성하는 페이지(`/jaedan` 은 정적, 나머지는 빌더)는 **빌더 쪽 문구도**
건드리지 않는다. 금칙어 "실행 기록" 일괄 치환(54장·title 7개)이 이 6장을 건드리므로 **B묶음은
10/6 이후**에 시작한다.

빌더 순서·`build_lastmod.py`·`builddate.py`·`.assetsignore`·CSS 전파 등 제작 규칙은
`docs/homepage-standard.md`, 저장소 운영(pull·테스트 게이트·pr-check)은 `CLAUDE.md` 를 따른다.
서비스·카피 맥락은 `.agents/product-marketing.md`, 원장 절차는 `tools/ledger-update.md`.
