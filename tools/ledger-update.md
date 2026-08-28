# 실행 사례 원장 갱신 절차 (클로드 코드용)

전제: 대표가 data/cases.xlsx 의 '원장' 시트를 수정·추가하고 저장한 상태.

1. `python -c "import openpyxl, PIL"` — 실패하면 `pip install openpyxl pillow` 후 재시도
2. `python tools/build_cases.py` — "[원장 빌드 OK]" 가 나와야 함. 실패 메시지가 나오면 그 행·열을 대표에게 그대로 보여주고 멈춤 (임의 수정 금지)
3. `python -m pytest -q` — 전부 통과해야 함
4. 커밋 메시지: `chore(cases): 원장 갱신 — N건` (N은 빌드 출력의 공개 건수)
5. main 푸시 → 새 Worker 버전 확인 → `curl -s https://bmaker.kr/cases` 에 새 사례ID 포함 확인
6. 대표에게 보고: 공개 건수·총액·바뀐 파일 목록

주의: data/cases.xlsx 와 tools/ 는 .assetsignore 로 서빙 제외 상태를 유지한다. 증빙 이미지는 가림 처리된 webp 만 assets/cases/ 에 넣는다.
