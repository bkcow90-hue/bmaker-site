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

## B2. 자금 시트 연결 (한 번)
대표가 같은 스프레드시트에 '자금' 탭을 만들어 게시하면(웹에 게시→해당 시트+CSV), 그 주소를 data/funds-source.url 로 저장·커밋한다. 이후 자금 페이지·/schedule 은 원장과 같은 파이프라인으로 자동 반영되고, 매일 06:07 KST에 접수 배지가 날짜 기준으로 재계산된다. 검증: `python tools/build_funds.py` → "[자금 빌드 OK]".

## B3. 재단 시트 연결 (선택)
'재단' 탭을 게시(CSV)하고 주소를 data/jaedan-source.url 로 저장·커밋하면 지역 재단 17페이지도 시트가 원본이 된다. 연결 전에는 저장소의 data/jaedan.source.csv 가 원본이며, 개별 재단 홈페이지 URL·메모는 시트(또는 CSV)에서 수정한다. 검증: `python tools/build_jaedan.py`.

## C. 로컬에서 고치는 경우 (시트 없이)
1. data/cases.source.csv (또는 data/cases.xlsx) 수정 — 시트가 연결된 뒤에는 로컬 수정 금지(시트가 덮어씀), 시트에서 고치라고 안내
2. `python -c "import openpyxl, PIL"` — 실패 시 `pip install openpyxl pillow`
3. `python tools/build_cases.py` — "[원장 빌드 OK]" 확인. 실패 메시지는 행·열 그대로 대표에게 전달하고 멈춤
3-1. `python tools/build_lastmod.py` — 푸터 '최종 업데이트' 와 JSON-LD dateModified 재스탬프 (D 참고). 빌드 체인의 마지막 단계다
4. `python -m pytest -q` 전부 통과 → 커밋 `chore(cases): 원장 갱신 — N건` → 푸시 → https://bmaker.kr/cases 반영 확인

## D. 페이지 갱신일 스탬프 (build_lastmod.py)
전 페이지 푸터의 `최종 업데이트: YYYY-MM-DD` 한 줄과 각 페이지 JSON-LD(WebPage·Article)의 `dateModified` 를 같은 값으로 붙인다.

- 날짜 기준: 사례 페이지(/cases)는 **원장 빌드일**(cases.html Dataset dateModified), 그 밖의 홈·상세·블로그는 **그 페이지 내용이 마지막으로 바뀐 날**.
- 근거는 data/page-updated.json 에 `{날짜, 본문 해시}` 로 남는다. 해시는 스탬프를 뺀 본문으로 계산하므로 스탬프를 넣는 커밋이 날짜를 또 올리지 않는다. 레지스트리에 없는 새 페이지는 git 최종 커밋일(KST)로 채운다.
- **HTML 을 손으로 고쳤으면 커밋 전에 반드시 실행한다.** 안 하면 tests/test_lastmod.py 가 "본문이 바뀌었는데 갱신일이 그대로" 로 막는다.
- 다른 build_*.py(자금·재단·교육)가 서로의 `<footer>`·`<head>` 를 복사해 가므로 **항상 체인의 마지막**에 실행한다. Actions 의 ledger 워크플로에는 이미 마지막 단계로 들어가 있다.

주의: data/cases.xlsx·cases.source.csv·ledger-source.url·tools/·.github/ 는 .assetsignore 로 서빙 제외 유지. 시트에는 익명 정보만 넣는다(상호·이름 금지) — 게시 CSV는 주소를 아는 사람은 볼 수 있다. 증빙 이미지는 가림 처리된 webp만 assets/cases/ 에 넣는다.
