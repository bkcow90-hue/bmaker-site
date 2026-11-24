/* 소상공인 기준 판정기 (/sosangin-gijun, 2026-11-25)
 *
 * 기준 숫자의 출처:
 *  - 소기업 매출 기준: 중소기업기본법 시행령 [별표 3] <개정 2025. 9. 1.> 43개 업종·9구간(억원)
 *  - 소상공인 상시근로자 기준: 소상공인기본법 시행령 — 광업·제조업·건설업·운수업 10명 미만, 그 밖 5명 미만
 * 결과는 참고 안내다. 공식 판정은 중소기업현황정보시스템의 확인서로 한다.
 * tests/test_tool_sosangin_gijun.py 가 이 표의 업종 수와 구간별 개수를 지킨다.
 */
(function () {
  'use strict';
  // [분류기호, 업종명, 소기업 매출 기준(억원 이하), 상시근로자 10명 기준 업종 여부]
  var ROWS = [
    ['C19', '코크스·연탄·석유정제품 제조업', 140, 1],
    ['C24', '1차 금속 제조업', 140, 1],
    ['C10', '식료품 제조업', 120, 1],
    ['C11', '음료 제조업', 120, 1],
    ['C14', '의복·의복 액세서리·모피제품 제조업', 120, 1],
    ['C15', '가죽·가방·신발 제조업', 120, 1],
    ['C20', '화학물질·화학제품 제조업(의약품 제외)', 120, 1],
    ['C21', '의료용 물질·의약품 제조업', 120, 1],
    ['C23', '비금속 광물제품 제조업', 120, 1],
    ['C25', '금속가공제품 제조업(기계·가구 제외)', 120, 1],
    ['C26', '전자부품·컴퓨터·영상·음향·통신장비 제조업', 120, 1],
    ['C28', '전기장비 제조업', 120, 1],
    ['C29', '기타 기계·장비 제조업', 120, 1],
    ['C30', '자동차·트레일러 제조업', 120, 1],
    ['C32', '가구 제조업', 120, 1],
    ['D', '전기·가스·증기·공기조절 공급업', 120, 0],
    ['E36', '수도업', 120, 0],
    ['H', '운수·창고업', 100, 1],
    ['K', '금융·보험업', 100, 0],
    ['A', '농업·임업·어업', 80, 0],
    ['B', '광업', 80, 1],
    ['C12', '담배 제조업', 80, 1],
    ['C13', '섬유제품 제조업(의복 제외)', 80, 1],
    ['C16', '목재·나무제품 제조업(가구 제외)', 80, 1],
    ['C17', '펄프·종이·종이제품 제조업', 80, 1],
    ['C18', '인쇄·기록매체 복제업', 80, 1],
    ['C22', '고무·플라스틱제품 제조업', 80, 1],
    ['C27', '의료·정밀·광학기기·시계 제조업', 80, 1],
    ['C31', '기타 운송장비 제조업', 80, 1],
    ['C33', '기타 제품 제조업', 80, 1],
    ['F', '건설업', 80, 1],
    ['G', '도매·소매업', 60, 0],
    ['J', '정보통신업', 50, 0],
    ['E', '수도·하수·폐기물 처리, 원료 재생업(수도업 제외)', 40, 0],
    ['L', '부동산업', 40, 0],
    ['M', '전문·과학·기술 서비스업', 30, 0],
    ['N', '사업시설 관리·사업 지원·임대 서비스업', 30, 0],
    ['R', '예술·스포츠·여가 관련 서비스업', 30, 0],
    ['C34', '산업용 기계·장비 수리업', 15, 1],
    ['I', '숙박·음식점업', 15, 0],
    ['P', '교육 서비스업', 15, 0],
    ['Q', '보건업·사회복지 서비스업', 15, 0],
    ['S', '수리·기타 개인 서비스업(협회·단체 제외)', 15, 0]
  ];
  // 고르기 쉽게 자주 찾는 업종을 앞에 둔다(표 순서와 무관, 값은 ROWS 의 번호)
  var COMMON = ['I', 'G', 'S', 'P', 'F', 'J', 'M', 'H', 'Q', 'C10'];

  var form = document.getElementById('toolForm');
  var out = document.getElementById('toolOut');
  var err = document.getElementById('toolErr');
  var sel = document.getElementById('tool-industry');
  if (!form || !out || !sel) return;

  function opt(i) { var o = document.createElement('option'); o.value = String(i); o.textContent = ROWS[i][1]; return o; }
  function group(label, idx) {
    var g = document.createElement('optgroup'); g.label = label;
    idx.forEach(function (i) { g.appendChild(opt(i)); }); sel.appendChild(g);
  }
  var commonIdx = COMMON.map(function (c) { for (var i = 0; i < ROWS.length; i++) if (ROWS[i][0] === c) return i; return -1; })
    .filter(function (i) { return i >= 0; });
  var rest = ROWS.map(function (_, i) { return i; }).filter(function (i) { return commonIdx.indexOf(i) < 0; });
  group('자주 찾는 업종', commonIdx);
  group('제조업', rest.filter(function (i) { return ROWS[i][0].charAt(0) === 'C'; }));
  group('그 밖의 업종', rest.filter(function (i) { return ROWS[i][0].charAt(0) !== 'C'; }));

  function track(name, params) {
    try { if (typeof window.gtag === 'function') window.gtag('event', name, params || {}); } catch (e) { /* 측정 실패는 무시 */ }
  }
  function fail(msg) { err.textContent = msg; err.hidden = false; out.hidden = true; }
  function link(href, text) { return '<a href="' + href + '">' + text + '</a>'; }

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    err.hidden = true;
    var i = sel.value === '' ? -1 : Number(sel.value);
    var sales = parseFloat(document.getElementById('tool-sales').value);
    var staff = parseFloat(document.getElementById('tool-staff').value);
    if (i < 0) return fail('주된 업종을 골라 주세요.');
    if (!(sales >= 0)) return fail('3년 평균 매출액을 억원 단위로 적어 주세요.');
    if (!(staff >= 0)) return fail('상시근로자 수를 적어 주세요. 직원이 없으면 0입니다.');
    var row = ROWS[i], cap = row[2], staffCap = row[3] ? 10 : 5;
    var small = sales <= cap, micro = small && staff < staffCap;
    var verdict, body, next;
    if (micro) {
      verdict = '소상공인 기준 안에 있습니다';
      body = row[1] + '의 소기업 매출 기준은 ' + cap + '억원 이하, 소상공인 상시근로자 기준은 ' + staffCap + '명 미만입니다. 적어 주신 매출 ' + sales + '억원, 상시근로자 ' + staff + '명은 두 기준 안입니다.';
      next = '소상공인 대상 자금부터 보시면 됩니다. ' + link('/sosangin', '소상공인 자금 경로') + link('/jagajindan', '1분 자가진단');
    } else if (small) {
      verdict = '소기업이지만 소상공인 기준은 넘습니다';
      body = row[1] + '의 소기업 매출 기준 ' + cap + '억원 이하에는 들지만, 상시근로자 ' + staff + '명은 소상공인 기준(' + staffCap + '명 미만)을 넘습니다.';
      next = '소상공인 전용 자금 대신 중소기업 대상 자금을 봅니다. ' + link('/jungsogieop', '중소기업 자금 경로') + link('/jungjingong', '중진공 정책자금');
    } else {
      verdict = '소기업 매출 기준을 넘습니다';
      body = row[1] + '의 소기업 매출 기준은 ' + cap + '억원 이하인데, 적어 주신 매출은 ' + sales + '억원입니다. 중기업에 해당하는지는 별도 매출 기준과 자산·계열 관계까지 봐야 합니다.';
      next = '중소기업 대상 자금과 보증을 함께 봅니다. ' + link('/jungsogieop', '중소기업 자금 경로') + link('/sinbo', '신용보증기금');
    }
    out.innerHTML = '<strong class="verdict">' + verdict + '</strong><p>' + body + '</p><p class="next">' + next + '</p>' +
      '<p class="tool-note">참고 안내입니다. 공식 판정은 중소기업현황정보시스템에서 발급하는 확인서로 하며, 상시근로자 수는 세는 방법에 따라 달라질 수 있습니다.</p>';
    out.hidden = false;
    // 결과를 신청 폼에 같이 넘긴다(전송은 conversion.js 가 그대로 한다)
    var lead = document.querySelector('form#leadForm, section.inline-diag form');
    if (lead) {
      var memo = document.getElementById('lf-memo');
      if (!memo) { memo = document.createElement('input'); memo.type = 'hidden'; memo.id = 'lf-memo'; lead.appendChild(memo); }
      memo.value = '[기준 판정기] ' + verdict + ' / 업종 ' + row[1] + ', 매출 ' + sales + '억원, 상시근로자 ' + staff + '명';
    }
    track('tool_result', { tool: 'sosangin_gijun', result: micro ? 'micro' : (small ? 'small' : 'over') });
    out.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
})();
