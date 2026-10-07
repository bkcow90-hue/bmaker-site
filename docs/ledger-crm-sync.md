# 원장 복구와 CRM 연결 (2026-10-07)

`tools/sync_ledger.py`는 세 CSV를 모두 내려받아 검증한 뒤 빌드 입력으로 옮긴다. 다운로드·빌드·전체 테스트 중 실패하면 원본과 부분 생성 페이지를 마지막 정상 커밋으로 되돌린다. 실패 상태만 커밋하며 다음 실행은 소스가 같아도 다시 빌드한다. 전체 테스트 게이트는 유지한다. Actions의 success만으로 반영 여부를 판단하지 말고 fetch 출력의 `source_changed`/`rebuild`, build·commit 단계와 공개 상태를 함께 확인한다.

공개 상태 파일은 `data/ledger-status.txt`와 `data/ledger-sync-status.json`: 실패 코드/단계, `failed_at`, `last_success_at`만 기록하며 입력 행·서버 응답·전체 테스트 로그를 공개하지 않는다. 최초 성공 전 마지막 성공 시각은 `unknown`/null로 남긴다. 상세 오류는 인증된 GitHub Actions 로그에서 확인한다.

CRM 연결 URL과 토큰은 미설정 상태다. 승인된 CRM `/api/public-ledger` 최종 HTTPS URL은 repository variable `BMAKER_CRM_LEDGER_URL`, 전용 읽기 토큰은 repository secret `BMAKER_CRM_LEDGER_TOKEN`으로 설정한다. URL에 토큰·query·fragment를 넣지 않으며 인증 요청의 리다이렉트는 모두 거부한다. 토큰은 CRM 요청에만 보내고 Google CSV 요청에는 보내지 않는다. 기존 자동입력 토큰·Supabase 키·원본 고객 테이블 REST 주소를 직접 연결하지 않는다. 설정 후 CRM 실패를 오래된 시트 성공으로 숨기지 않는다.

공개용 CSV 필드 명세(승인 대기):

| 필드 | 조건 |
|---|---|
| 사례ID | 기존 원장 ID 보존, 고객/lead UUID 대신 공개용 ID |
| 실행 연월 | 실제 자금 실행일의 YYYY-MM, 보수 입금일 대신 사용 금지 |
| 기관·자금명 | 실제 실행 기관·자금, 고객명/내부 메모 금지 |
| 실행 금액(만원) | 확인된 실제 실행액, 양의 정수, 보수·입금액·계획액 대체 금지 |
| 지역(시도) | 익명화된 시도 범주, 상세 주소 금지 |
| 사이트 공개 | 검수·공개 승인된 행의 Y만 |
| 업종·사업 형태 | 검수된 범주값, 선택 필드 |

그 외 열은 거부한다. CRM 경로에 수수료·입금액·입금일·신용·매출·체납·폐업 구간, 자유 메모를 새로 싣지 않는다. CSV는 검수된 공개 행만 보내며 기존 마지막 정상 원장에 신규 `CRM-<무작위 32 hex>` ID를 추가한다. 기존 사례와 같은 ID·같은 입력은 재추가하지 않고, 값이 달라지면 `EXISTING_CASE_CHANGED`, 없는 기존 ID이면 `UNKNOWN_LEGACY_CASE`로 중단한다. 승인 0건의 헤더 CSV는 정상으로 받아 기존 전체 원장을 보존한다. 데이터 정정·비공개 전환·기존 사례 철회는 별도 검토 후 처리하며 이 옵션으로 묵시 삭제하지 않는다. CRM과 기존 원장의 중복 대조를 확정한 뒤 연결한다.

운영 CRM `nthguforuefgczlbfitk`에는 실제 실행 필드/공개 endpoint가 아직 없다. 별도 CRM PR은 `lead_fund_executions` 저장 구조, 실제 실행 입력, 관리자 익명 검수·승인, 전용 토큰 CSV endpoint를 준비하며 기본 비활성이다. `lead_funds.received_amount`·`paid_at`·`base_amount`는 수수료 기록으로 절대 이관하지 않는다. 운영 migration/RLS·비밀 설정·endpoint 활성화·머지/배포·고객 공개는 승인 전 실행하지 않는다. 적용 절차와 미실행 DB 검증은 CRM의 `docs/public-ledger-integration.md`에 있다.

진단 근거:

- [실패 실행 37400641047](https://github.com/bkcow90-hue/bmaker-site/actions/runs/37400641047): 승인된 블로그 CTA와 `test_no_retired_cta_wording_anywhere`의 충돌, 1 failed / 460 passed. 이후 CTA 검사 예외는 이미 별도 변경으로 복구됐다.
- [최신 확인 실행 37569340975](https://github.com/bkcow90-hue/bmaker-site/actions/runs/37569340975): 시트 다운로드 success, 빌드·커밋 skipped. 이 success는 데이터 반영 성공을 뜻하지 않는다.
- 공개 `ledger-status.txt`는 진단 시 HTTP 200 OK, 385건 / 439억5500만원 / 증빙12건. 현재 새 실패를 재현한 것은 아니며 과거 실패 후 재시도 결함을 확인했다.
- CRM 집계: 정산 상태의 활성 자금 32건(고객 행·개별 금액을 읽지 않은 count 집계). 홈페이지의 기존 사례와 대응 여부는 미확정.
