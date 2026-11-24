/* 중소기업 기준 판정기 (/jungsogieop-gijun, 2026-11-25)
 *
 * 기준 숫자의 출처:
 *  - 중소기업 매출 기준: 중소기업기본법 시행령 [별표 1] <개정 2025. 9. 1.> 44개 업종·7구간(400억~1,800억 원)
 *  - 소기업 매출 기준: 같은 시행령 [별표 3] — /sosangin-gijun 과 같은 값
 *  - 자산총액 5,000억 원 미만, 독립성 기준(대기업 집단 소속·자산 5천억 이상 법인의 30% 이상 최다출자·관계기업 합산)
 * 결과는 참고 안내다. 공식 판정은 중소기업현황정보시스템의 중소기업 확인서로 한다.
 * tests/test_tool_jungsogieop_gijun.py 가 이 표의 업종 수와 구간별 개수, 소기업 값의 일치를 지킨다.
 */
(function () {
  'use strict';
  // [분류기호, 업종명, 중소기업 매출 기준(억원 이하), 소기업 매출 기준(억원 이하)]
  var ROWS = [
    ['C17', '펄프·종이·종이제품 제조업', 1800, 80],
    ['C24', '1차 금속 제조업', 1800, 140],
    ['C28', '전기장비 제조업', 1800, 120],
    ['C14', '의복·의복 액세서리·모피제품 제조업', 1500, 120],
    ['C15', '가죽·가방·신발 제조업', 1500, 120],
    ['C32', '가구 제조업', 1500, 120],
    ['C10', '식료품 제조업', 1200, 120],
    ['C20', '화학물질·화학제품 제조업(의약품 제외)', 1200, 120],
    ['C22', '고무·플라스틱제품 제조업', 1200, 80],
    ['C25', '금속가공제품 제조업(기계·가구 제외)', 1200, 120],
    ['C29', '기타 기계·장비 제조업', 1200, 120],
    ['C30', '자동차·트레일러 제조업', 1200, 120],
    ['C31', '기타 운송장비 제조업', 1200, 80],
    ['F', '건설업', 1200, 80],
    ['G', '도매·소매업', 1200, 60],
    ['A', '농업·임업·어업', 1000, 80],
    ['B', '광업', 1000, 80],
    ['C12', '담배 제조업', 1000, 80],
    ['C13', '섬유제품 제조업(의복 제외)', 1000, 80],
    ['C16', '목재·나무제품 제조업(가구 제외)', 1000, 80],
    ['C19', '코크스·연탄·석유정제품 제조업', 1000, 140],
    ['C26', '전자부품·컴퓨터·영상·음향·통신장비 제조업', 1000, 120],
    ['C33', '기타 제품 제조업', 1000, 80],
    ['D', '전기·가스·증기·공기조절 공급업', 1000, 120],
    ['E36', '수도업', 1000, 120],
    ['H', '운수·창고업', 1000, 100],
    ['J', '정보통신업', 1000, 50],
    ['C11', '음료 제조업', 800, 120],
    ['C18', '인쇄·기록매체 복제업', 800, 80],
    ['C21', '의료용 물질·의약품 제조업', 800, 120],
    ['C23', '비금속 광물제품 제조업', 800, 120],
    ['C27', '의료·정밀·광학기기·시계 제조업', 800, 80],
    ['E', '수도·하수·폐기물 처리, 원료 재생업(수도업 제외)', 800, 40],
    ['N', '사업시설 관리·사업 지원 서비스업(임대업 제외)', 800, 30],
    ['C34', '산업용 기계·장비 수리업', 600, 15],
    ['M', '전문·과학·기술 서비스업', 600, 30],
    ['Q', '보건업·사회복지 서비스업', 600, 15],
    ['R', '예술·스포츠·여가 관련 서비스업', 600, 30],
    ['S', '수리·기타 개인 서비스업(협회·단체 제외)', 600, 15],
    ['I', '숙박·음식점업', 400, 15],
    ['K', '금융·보험업', 400, 100],
    ['L', '부동산업', 400, 40],
    ['N76', '임대업(부동산 임대업 제외)', 400, 30],
    ['P', '교육 서비스업', 400, 15]
  ];
  var ASSET_CAP = 5000;
  var COMMON = ['C25', 'C29', 'C26', 'C10', 'G', 'F', 'J', 'M', 'H', 'I'];

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
    var asset = parseFloat(document.getElementById('tool-asset').value);
    var grp = document.getElementById('tool-group').value;
    if (i < 0) return fail('주된 업종을 골라 주세요.');
    if (!(sales >= 0)) return fail('3년 평균 매출액을 억원 단위로 적어 주세요.');
    if (!(asset >= 0)) return fail('자산총액을 억원 단위로 적어 주세요.');
    var row = ROWS[i], cap = row[2], smallCap = row[3];
    var verdict, body, next, code;
    if (grp === 'yes') {
      code = 'group';
      verdict = '규모와 상관없이 중소기업에서 빠질 수 있습니다';
      body = '대기업 집단에 속하거나 자산총액 5천억 원 이상인 법인이 지분 30% 이상을 가진 최대주주이면, 매출이 기준 안이어도 중소기업으로 보지 않습니다.';
      next = '지분 구조에 따라 달라지므로 확인서 신청 단계에서 판정받는 것이 정확합니다. ' + link('/jungsogieop', '중소기업 자금 경로');
    } else if (asset >= ASSET_CAP) {
      code = 'asset';
      verdict = '자산총액 기준을 넘습니다';
      body = '중소기업은 자산총액이 5,000억 원 미만이어야 합니다. 적어 주신 자산총액은 ' + asset + '억 원입니다.';
      next = '중견기업 대상 제도를 함께 보셔야 합니다. ' + link('/jungsogieop', '중소기업 자금 경로');
    } else if (sales > cap) {
      code = 'over';
      verdict = '중소기업 매출 기준을 넘습니다';
      body = row[1] + '의 중소기업 매출 기준은 ' + cap.toLocaleString('ko-KR') + '억 원 이하인데, 적어 주신 매출은 ' + sales + '억 원입니다. 기준을 넘은 뒤에도 일정 기간 중소기업으로 보는 유예 제도가 있습니다.';
      next = '유예 적용 여부는 확인서 신청 단계에서 확인됩니다. ' + link('/jungsogieop', '중소기업 자금 경로') + link('/sinbo', '신용보증기금');
    } else if (sales <= smallCap) {
      code = 'small';
      verdict = '중소기업이고, 그중 소기업입니다';
      body = row[1] + '의 중소기업 매출 기준은 ' + cap.toLocaleString('ko-KR') + '억 원 이하, 소기업 기준은 ' + smallCap + '억 원 이하입니다. 적어 주신 매출 ' + sales + '억 원은 소기업 기준 안입니다.';
      next = '상시근로자 수에 따라 소상공인일 수도 있습니다. ' + link('/sosangin-gijun', '소상공인 기준 판정기') + link('/jungjingong', '중진공 정책자금');
    } else {
      code = 'medium';
      verdict = '중소기업이고, 그중 중기업입니다';
      body = row[1] + '의 중소기업 매출 기준 ' + cap.toLocaleString('ko-KR') + '억 원 이하에는 들고, 소기업 기준 ' + smallCap + '억 원은 넘습니다.';
      next = '중소기업 대상 자금과 보증을 함께 봅니다. ' + link('/jungjingong', '중진공 정책자금') + link('/sinbo', '신용보증기금') + link('/gibo', '기술보증기금');
    }
    var extra = grp === 'unsure' ? '<p>지분·계열 관계를 모르신다면 모회사나 자회사가 있는지부터 확인하세요. 있으면 관계기업 매출을 합산해 다시 봅니다.</p>' : '';
    out.innerHTML = '<strong class="verdict">' + verdict + '</strong><p>' + body + '</p>' + extra + '<p class="next">' + next + '</p>' +
      '<p class="tool-note">참고 안내입니다. 공식 판정은 중소기업현황정보시스템에서 발급하는 중소기업 확인서로 하며, 관계기업이 있으면 결과가 달라질 수 있습니다.</p>';
    out.hidden = false;
    var lead = document.querySelector('form#leadForm, section.inline-diag form');
    if (lead) {
      var memo = document.getElementById('lf-memo');
      if (!memo) { memo = document.createElement('input'); memo.type = 'hidden'; memo.id = 'lf-memo'; lead.appendChild(memo); }
      memo.value = '[중소기업 판정기] ' + verdict + ' / 업종 ' + row[1] + ', 매출 ' + sales + '억원, 자산 ' + asset + '억원';
    }
    track('tool_result', { tool: 'jungsogieop_gijun', result: code });
    out.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
})();
