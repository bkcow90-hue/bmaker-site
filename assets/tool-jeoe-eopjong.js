/* 정책자금 제외 업종 확인 (/jeoe-eopjong, 2026-11-25)
 *
 * 목록의 출처(2026-11-25 확인):
 *  - 소진공(S): 소상공인 정책자금 누리집 '정책자금 지원 제외업종' 표(ols.semas.or.kr), 2026년 소상공인 정책자금 융자계획 공고(중기부 공고 제2025-656호) 별표 1
 *  - 중진공(K): 2026년도 중소기업 정책자금 융자계획 공고(중기부 공고 제2025-649호) 별표 1 '융자제외 대상 업종 및 예외'
 * 상태값: 'x' 제외 목록에 있음 · 'c' 조건·예외가 붙음 · 'o' 제외 목록에 없음
 * '목록에 없음'은 신청 가능하다는 뜻이 아니다. 대상 여부는 규모·업력·신용 등 다른 요건으로 다시 본다.
 * 목록은 해마다 공고로 바뀐다. 2027년 융자계획이 공고되면 이 표를 다시 대조한다.
 * tests/test_tools_batch2.py 가 행 수와 주요 업종의 상태를 지킨다.
 */
(function () {
  'use strict';
  // [id, 묶음, 업종명, 찾기 낱말, 소진공, 중진공, 소진공 설명, 중진공 설명]
  var ROWS = [
    ['food', '자주 찾는 업종', '일반 음식점·카페·제과점', '식당 한식 커피 치킨 분식 배달', 'o', 'o', '', ''],
    ['retail', '자주 찾는 업종', '일반 도매·소매업, 온라인 쇼핑몰', '도소매 편의점 스마트스토어 쇼핑몰 유통', 'o', 'o', '', ''],
    ['mfg', '자주 찾는 업종', '제조업(일반)', '공장 제조 가공', 'o', 'o', '', '도박기계·사행성 오락기구 제조는 제외입니다.'],
    ['beauty', '자주 찾는 업종', '미용실·네일·피부관리', '미용 헤어 네일 피부', 'o', 'o', '', ''],
    ['lodging', '자주 찾는 업종', '숙박업(모텔·펜션·게스트하우스)', '숙박 모텔 펜션 호텔', 'o', 'o', '', ''],
    ['pcroom', '자주 찾는 업종', 'PC방·노래연습장', '피시방 노래방 코인노래방', 'o', 'o', '성인PC방·성인용 게임장은 제외입니다.', ''],
    ['screengolf', '자주 찾는 업종', '골프연습장·스크린골프', '골프 스크린', 'o', 'o', '누리집 안내에 지원 가능 업종으로 적혀 있습니다.', ''],
    ['transport', '자주 찾는 업종', '운수·화물·택배', '운송 화물 택배 용달', 'o', 'o', '', ''],
    ['academy', '자주 찾는 업종', '학원·교습소', '학원 교습소 입시 보습 교육', 'o', 'c', '', '일반교과·입시 교육(855~856 중 일부)과 초·중·고 교육기관은 제외입니다.'],
    ['construction', '자주 찾는 업종', '건설업·인테리어 공사', '건설 인테리어 시공 전기공사 설비', 'o', 'c', '', '건설업(41~42)은 제외가 원칙이고, 산업생산시설·환경설비·조경·배관·냉난방·승강설비·소방시설·전기·통신 공사업 등은 예외입니다.'],
    ['pub', '주점·유흥', '호프·소주방 등 일반 주점', '술집 호프 맥주 포차 이자카야 바 주점', 'o', 'x', '제외 목록에는 유흥주점만 있습니다.', '주점업(5621) 전체가 제외입니다.'],
    ['nightclub', '주점·유흥', '일반유흥주점·무도유흥주점', '유흥주점 룸살롱 단란주점 클럽 나이트', 'x', 'x', '재해 피해 자금은 관광특구 소재에 한해 예외가 있습니다.', '주점업(5621)에 포함됩니다.'],
    ['dancehall', '주점·유흥', '무도장(콜라텍 등)', '무도장 콜라텍', 'x', 'x', '', ''],
    ['liquor', '주류·담배', '주류 도매업', '주류 술 도매', 'o', 'x', '', '주류 도매업(46331)이 제외입니다. 주류 소매는 일부가 제외입니다.'],
    ['tobacco', '주류·담배', '담배 도매·중개(전자담배 포함)', '담배 전자담배 액상', 'x', 'x', '전자담배 등 담배 대용물 도매도 포함합니다.', '담배 도매(46333)·중개가 제외입니다.'],
    ['realestate-rent', '부동산', '부동산 임대업', '임대 건물주 임대사업자 상가 임대', 'x', 'x', '공유오피스·공유주방을 운영하는 비주거용 건물 임대업은 예외입니다.', '부동산업(68) 전체가 제외입니다.'],
    ['realestate-agent', '부동산', '부동산 중개업(공인중개사)', '공인중개사 중개 부동산', 'c', 'x', '같은 장소에서 신청일 기준 6개월 이상 영업 중이면 신청 대상입니다.', '부동산업(68) 전체가 제외입니다.'],
    ['realestate-sales', '부동산', '분양 대행업', '분양 대행', 'c', 'x', '같은 장소에서 신청일 기준 6개월 이상 영업 중이면 신청 대상입니다.', '부동산업(68) 전체가 제외입니다.'],
    ['realestate-mgmt', '부동산', '부동산 관리업', '건물 관리 주택 관리', 'o', 'x', '부동산업 가운데 부동산 관리업(6821)은 제외에서 빠져 있습니다.', '부동산업(68) 전체가 제외입니다.'],
    ['finance', '금융·보험', '금융업·대부업', '금융 대부 투자 대출 중개', 'x', 'c', '금융업(64)과 금융·보험 관련 서비스업(66)이 제외입니다.', '금융 및 보험업(64~66)이 제외이고, 정보통신기술을 활용한 핀테크 기업 일부(66199)는 예외입니다.'],
    ['insurance', '금융·보험', '보험업·보험대리점', '보험 대리점 설계사 GA', 'x', 'x', '보험 및 연금업(65), 금융·보험 관련 서비스업(66)에 포함됩니다.', '금융 및 보험업(64~66)에 포함됩니다.'],
    ['crypto', '금융·보험', '가상자산 매매·중개업', '코인 가상화폐 암호화폐 거래소', 'x', 'x', '', ''],
    ['law', '전문직', '법무·회계·세무 서비스업', '변호사 법무사 세무사 회계사 노무사 변리사', 'x', 'x', '재해 피해 자금은 특별재난지역 소재에 한해 예외가 있습니다.', '법무·회계·세무 관련 서비스업(711~712)이 제외입니다.'],
    ['customs', '전문직', '관세사·통관업', '관세사 통관', 'x', 'o', '', ''],
    ['appraisal', '전문직', '감정평가업', '감정평가사', 'x', 'o', '', ''],
    ['hq', '전문직', '회사본부(지주회사 등)', '지주 본부 홀딩스', 'o', 'x', '', '회사본부(7151)가 제외입니다.'],
    ['medical', '보건·의료', '병원·의원·치과·한의원', '병원 의원 치과 한의원 의사 요양병원', 'x', 'c', '보건업(86)이 제외이고, 유사의료업(86902)은 예외입니다. 재해 피해 자금은 특별재난지역 소재에 한해 예외가 있습니다.', '보건업(86)이 제외이고, 사회적경제기업은 예외입니다.'],
    ['pharmacy', '보건·의료', '약국·한약국', '약국 약사 한약', 'x', 'o', '재해 피해 자금은 특별재난지역 소재에 한해 예외가 있습니다.', ''],
    ['vet', '보건·의료', '동물병원(수의업)', '동물병원 수의사 수의', 'x', 'x', '', '수의업(731)이 제외입니다.'],
    ['massage', '보건·의료', '증기탕·안마시술소', '안마 마사지 증기탕', 'c', 'o', '시각장애인이 운영하는 안마원·안마시술소는 신청 대상입니다.', ''],
    ['adult-goods', '사행·성인', '성인용품 판매', '성인용품', 'x', 'x', '', ''],
    ['adult-game', '사행·성인', '성인용 게임장·성인PC방·전화방', '성인오락실 성인게임 전화방', 'x', 'c', '', '도박·향락 등 불건전 업종으로 보면 제외입니다. 개별 확인이 필요합니다.'],
    ['gamble-machine', '사행·성인', '도박기계·사행성 오락기구 제조·판매·임대', '도박 사행성 오락기 슬롯', 'x', 'x', '', ''],
    ['casino', '사행·성인', '카지노·사행시설·경주장 운영', '카지노 경마 경륜 경정 복권', 'x', 'x', '', ''],
    ['game-item', '사행·성인', '온라인게임 아이템 중개업', '아이템 거래 게임머니', 'x', 'x', '', ''],
    ['giftcard', '사행·성인', '경품용 상품권 발행·판매업', '상품권 경품', 'x', 'x', '', ''],
    ['video-room', '사행·성인', '비디오물 감상실', '비디오방 DVD방', 'o', 'x', '', '비디오물 감상실 운영업(59142)이 제외입니다.'],
    ['golf-course', '그 밖의 업종', '골프장 운영업', '골프장 컨트리클럽', 'x', 'o', '골프연습장·스크린골프는 제외가 아닙니다.', ''],
    ['mlm', '그 밖의 업종', '다단계 방문판매', '다단계 네트워크 마케팅 방문판매', 'c', 'x', '방문판매법에 따라 다단계판매업을 등록해 운영하면 신청 대상입니다.', ''],
    ['detective', '그 밖의 업종', '흥신소·탐정업', '흥신소 탐정 조사', 'x', 'x', '', ''],
    ['collection', '그 밖의 업종', '신용조사·추심 대행업', '추심 신용조사 채권', 'x', 'o', '', ''],
    ['fortune', '그 밖의 업종', '점술·사주·타로', '점집 사주 타로 철학관 운세', 'x', 'x', '', '점술 및 유사 서비스업(96992)이 제외입니다.'],
    ['association', '그 밖의 업종', '협회·단체', '협회 단체 조합', 'o', 'c', '', '협회 및 단체(94)가 제외이고, 중소기업기본법상 중소기업자에 해당하면 예외입니다.']
  ];

  var LABEL = { x: '제외 목록에 있음', c: '조건·예외 있음', o: '제외 목록에 없음' };
  function find(id) { for (var i = 0; i < ROWS.length; i++) if (ROWS[i][0] === id) return ROWS[i]; return null; }
  function search(text) {
    var t = (text || '').replace(/\s+/g, '');
    if (!t) return ROWS.slice();
    return ROWS.filter(function (r) { return (r[2] + r[3]).replace(/\s+/g, '').indexOf(t) >= 0; });
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { ROWS: ROWS, find: find, search: search };

  if (typeof document === 'undefined') return;
  var form = document.getElementById('toolForm');
  var out = document.getElementById('toolOut');
  var err = document.getElementById('toolErr');
  var sel = document.getElementById('tool-industry');
  var box = document.getElementById('tool-q');
  if (!form || !out || !sel) return;

  function fill(list) {
    while (sel.options.length > 1) sel.remove(1);
    Array.prototype.slice.call(sel.querySelectorAll('optgroup')).forEach(function (g) { sel.removeChild(g); });
    var groups = {};
    list.forEach(function (r) {
      if (!groups[r[1]]) { groups[r[1]] = document.createElement('optgroup'); groups[r[1]].label = r[1]; sel.appendChild(groups[r[1]]); }
      var o = document.createElement('option'); o.value = r[0]; o.textContent = r[2]; groups[r[1]].appendChild(o);
    });
    if (list.length === 1) sel.value = list[0][0];
  }
  fill(ROWS);
  if (box) box.addEventListener('input', function () {
    var list = search(box.value);
    fill(list);
    if (!list.length) { err.textContent = '목록에 없는 낱말입니다. 비슷한 업종을 고르거나, 아래 상담 신청에 업종을 적어 주세요.'; err.hidden = false; }
    else err.hidden = true;
  });

  function track(name, params) {
    try { if (typeof window.gtag === 'function') window.gtag('event', name, params || {}); } catch (e) { /* 측정 실패는 무시 */ }
  }
  function link(href, text) { return '<a href="' + href + '">' + text + '</a>'; }
  function cell(st, note) { return '<span class="st-' + st + '">' + LABEL[st] + '</span>' + (note ? '<br>' + note : ''); }

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var r = find(sel.value);
    if (!r) { err.textContent = '업종을 골라 주세요.'; err.hidden = false; out.hidden = true; return; }
    err.hidden = true;
    var s = r[4], k = r[5], verdict, next;
    if (s === 'x' && k === 'x') verdict = '두 곳 모두 융자제외 업종 목록에 있습니다';
    else if (s === 'o' && k === 'o') verdict = '두 곳 모두 융자제외 업종 목록에 없습니다';
    else if (s === 'x') verdict = '소상공인 정책자금의 제외 업종 목록에 있습니다';
    else if (k === 'x') verdict = '중소기업 정책자금(중진공)의 제외 업종 목록에 있습니다';
    else verdict = '조건이나 예외가 붙는 업종입니다';
    if (s === 'x' && k === 'x') next = '정책자금이 아닌 경로를 봐야 하는 경우입니다. 겸업 중인 다른 업종이 있다면 주된 업종부터 다시 확인하세요. ' + link('/funding', '자금 조달 방법 안내');
    else if (s === 'o' && k === 'o') next = '업종 다음으로 보는 것은 규모와 업력입니다. ' + link('/sosangin-gijun', '소상공인 기준 판정기') + link('/eopryeok-gyesangi', '업력 계산기') + link('/jagajindan', '1분 자가진단');
    else next = '어느 기관 대상인지는 규모로 갈립니다. ' + link('/sosangin-gijun', '소상공인 기준 판정기') + link('/jungsogieop-gijun', '중소기업 기준 판정기');
    out.innerHTML = '<strong class="verdict">' + verdict + '</strong>' +
      '<table><thead><tr><th scope="col">구분</th><th scope="col">' + r[2] + '</th></tr></thead><tbody>' +
      '<tr><th scope="row">소상공인 정책자금<br>(소진공)</th><td>' + cell(s, r[6]) + '</td></tr>' +
      '<tr><th scope="row">중소기업 정책자금<br>(중진공)</th><td>' + cell(k, r[7]) + '</td></tr></tbody></table>' +
      '<p class="next">' + next + '</p>' +
      '<p class="tool-note">참고 안내입니다. 2026년 공고의 융자제외 업종 목록과 대조한 결과이며, 목록에 없다고 해서 대상이 되는 것은 아닙니다. 제외 여부는 사업자등록증의 주된 업종 코드로 기관이 판단하고, 중진공은 소상공인을 원칙적으로 대상에서 뺍니다.</p>';
    out.hidden = false;
    var lead = document.querySelector('form#leadForm, section.inline-diag form');
    if (lead) {
      var m = document.getElementById('lf-memo');
      if (!m) { m = document.createElement('input'); m.type = 'hidden'; m.id = 'lf-memo'; lead.appendChild(m); }
      m.value = '[제외 업종 확인] ' + r[2] + ' / 소진공 ' + LABEL[s] + ', 중진공 ' + LABEL[k];
    }
    track('tool_result', { tool: 'jeoe_eopjong', result: s + k });
    out.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  });
})();
