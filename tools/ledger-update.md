# 실행 사례 원장 갱신 절차

원본 우선순위: 구글시트(연결돼 있으면) → data/cases.source.csv → data/cases.xlsx

## A. 구글시트가 연결된 뒤 (평상시)
대표가 시트를 고치면 매시 17분 GitHub Actions(ledger)가 자동으로 반영한다 — 할 일 없음.
"지금 바로 반영해줘" 요청을 받으면: `gh workflow run ledger` (gh 없으면 GitHub 웹 Actions 탭 → ledger → Run workflow 안내), 이후 https://bmaker.kr/data/ledger-status.txt 로 결과 확인.

## B. 구글시트 최초 연결 (한 번)
대표가 게시 CSV 주소를 주면:
1. 그 주소 한 줄을 data/ledger-source.url 로 저장 (공백·줄바꿈 없이)
2. `curl -fsSL "$(cat data/ledger-source.url)" | head -3` 으로 헤더가 '사례ID,실행 연월,…' 인지 확인. 아니면 멈추고 대표에게 알림
3. 커밋 `chore(cases): 구글시트 연결` → 푸시 → Actions 탭에서 ledger 실행 성공 확인

## C. 로컬에서 고치는 경우 (시트 없이)
1. data/cases.source.csv (또는 data/cases.xlsx) 수정 — 시트가 연결된 뒤에는 로컬 수정 금지(시트가 덮어씀), 시트에서 고치라고 안내
2. `python -c "import openpyxl, PIL"` — 실패 시 `pip install openpyxl pillow`
3. `python tools/build_cases.py` — "[원장 빌드 OK]" 확인. 실패 메시지는 행·열 그대로 대표에게 전달하고 멈춤
4. `python -m pytest -q` 전부 통과 → 커밋 `chore(cases): 원장 갱신 — N건` → 푸시 → https://bmaker.kr/cases 반영 확인

주의: data/cases.xlsx·cases.source.csv·ledger-source.url·tools/·.github/ 는 .assetsignore 로 서빙 제외 유지. 시트에는 익명 정보만 넣는다(상호·이름 금지) — 게시 CSV는 주소를 아는 사람은 볼 수 있다. 증빙 이미지는 가림 처리된 webp만 assets/cases/ 에 넣는다.
