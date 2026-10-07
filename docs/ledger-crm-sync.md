# 원장 복구와 CRM 연결 (2026-10-07)

`tools/sync_ledger.py`는 세 CSV를 모두 내려받아 검증한 뒤 빌드 입력으로 옮긴다. 다운로드·빌드·전체 테스트 중 실패하면 원본과 부분 생성 페이지를 마지막 정상 커밋으로 되돌린다. 실패 상태만 커밋하며 다음 실행은 소스가 같아도 다시 빌드한다. 전체 테스트 게이트는 유지한다. Actions의 success만으로 반영 여부를 판단하지 말고 fetch 출력의 `source_changed`/`rebuild`, build·commit 단계와 공개 상태를 함께 확인한다.

공개 상태 파일은 `data/ledger-status.txt`와 `data/ledger-sync-status.json`: 실패 코드/단계, `failed_at`, `last_success_at`만 기록하며 입력 행·서버 응답·전체 테스트 로그를 공개하지 않는다. 최초 성공 전 마지막 성공 시각은 `unknown`/null로 남긴다. 상세 오류는 인증된 GitHub Actions 로그에서 확인한다.

CRM 옵션 `BMAKER_CRM_LEDGER_URL`은 미설정 상태다. 승인된 HTTPS 공개 CSV endpoint가 생긴 후에만 GitHub repository variable로 설정한다. CRM 원본 고객 테이블이나 Supabase REST 주소를 직접 연결하지 않는다. 설정 후 CRM 실패를 오래된 시트 성공으로 숨기지 않는다.

공개용 CSV 필드 명세(승인 대기):

| 필드 | 조건 |
|---|---|
| 사례ID | 기존 원장 ID 보존, 고객/lead UUID 대신 공개용 ID |
| 실행 연월 | 실제 자금 실행일의 YYYY-MM, 보수 입금일 대신 사용 금지 |
| 기관·자금명 | 실제 실행 기관·자금, 고객명/내부 메모 금지 |
| 실행 금액(만원) | 확인된 실제 실행액, 양의 정수, 보수·입금액·계획액 대체 금지 |
| 지역(시도) | 익명화된 시도 범주, 상세 주소 금지 |
| 사이트 공개 | 검수·공개 승인된 행의 Y만 |
| 금리·상환 조건 | 기존 공개 범위 내 확인된 조건, 선택 필드 |
| 업종·사업 형태·업력(년) | 검수된 범주값, 선택 필드 |
| 증빙 파일 | 기존 마스킹 검수 완료 로컬 자산 이름만, 선택 필드 |

그 외 열은 거부한다. CRM 경로에 신용·매출·체납·폐업 구간, 자유 메모를 새로 싣지 않는다. CRM CSV는 검수된 공개 행만 보내며 기존 마지막 정상 원장에 신규 ID를 추가한다. 기존 사례와 같은 ID·같은 입력은 재추가하지 않고, 값이 달라지면 `EXISTING_CASE_CHANGED`로 중단한다. CSV에 없는 기존 사례도 모두 보존한다. 데이터 정정·비공개 전환·기존 사례 철회는 별도 검토 후 처리하며 이 옵션으로 묵시 삭제하지 않는다. CRM과 기존 원장의 중복 ID 대조를 확정한 뒤 연결한다.

현재 CRM `nthguforuefgczlbfitk`에는 공개 원장 테이블/뷰/endpoint가 확인되지 않았다. `lead_funds.received_amount`는 보수 입금, `paid_at`은 보수 입금일이고 `base_amount`는 보수 산정 기준이다. 실제 실행액/실행일과 동일하다고 단정할 수 없다. 연결을 완료하려면 CRM 측 실제 실행 필드·공개 승인·익명화 저장 구조, endpoint 접근 권한, 기존 ID 대조 방식이 먼저 확정되어야 한다. DB 쓰기·트리거/RLS·새 키/비밀 설정·endpoint 활성화·머지/배포는 승인 전 실행하지 않는다.

진단 근거:

- [실패 실행 37400641047](https://github.com/bkcow90-hue/bmaker-site/actions/runs/37400641047): 승인된 블로그 CTA와 `test_no_retired_cta_wording_anywhere`의 충돌, 1 failed / 460 passed. 이후 CTA 검사 예외는 이미 별도 변경으로 복구됐다.
- [최신 확인 실행 37569340975](https://github.com/bkcow90-hue/bmaker-site/actions/runs/37569340975): 시트 다운로드 success, 빌드·커밋 skipped. 이 success는 데이터 반영 성공을 뜻하지 않는다.
- 공개 `ledger-status.txt`는 진단 시 HTTP 200 OK, 385건 / 439억5500만원 / 증빙12건. 현재 새 실패를 재현한 것은 아니며 과거 실패 후 재시도 결함을 확인했다.
- CRM 집계: 정산 상태의 활성 자금 32건(고객 행·개별 금액을 읽지 않은 count 집계). 홈페이지의 기존 사례와 대응 여부는 미확정.
