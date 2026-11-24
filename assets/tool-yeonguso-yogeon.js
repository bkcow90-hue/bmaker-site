/* 기업부설연구소 설립요건 체크 (/research-institute, 2026-11-25)
 *
 * 연구전담요원 인원 기준(기업부설연구소법 시행령, KOITA 신고 안내 — /research-institute 본문과 같은 값, 2026-11-10 확인):
 *  - 소기업 3명(창업 후 3년까지 2명) · 중기업 5명 · 중견기업 7명 · 벤처기업, 연구원·교원 창업 기업 2명
 *  - 연구개발전담부서는 기업 규모와 관계없이 1명
 * 인정 여부는 KOITA 심사로 정해진다. 결과는 참고 안내다. tests/test_tools_batch2.py 가 인원 기준을 지킨다.
 */
(function () {
  'use strict';

  var REQ = { small3: 2, small: 3, medium: 5, mid: 7 }, REQ_VENTURE = 2, REQ_DEPT = 1;
  function required(size, venture) {
    var base = REQ[size];
    return venture && size !== 'mid' ? Math.min(base, REQ_VENTURE) : base;
  }
  function judge(size, venture, staff) {
    var need = required(size, venture);
    return { need: need, code: staff >= need ? 'lab' : (staff >= REQ_DEPT ? 'dept' : 'none') };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { required: required, judge: judge, REQ: REQ };

  if (typeof document === 'undefined') return;
  var form = document.getElementById('toolForm');
  var out = document.getElementById('toolOut');
  var err = document.getElementById('toolErr');
  if (!form || !out) return;
  function track(name, params) {
    try { if (typeof window.gtag === 'function') window.gtag('event', name, params || {}); } catch (e) { /* 측정 실패는 무시 */ }
  }
  function fail(msg) { err.textContent = msg; err.hidden = false; out.hidden = true; }
  function link(href, text) { return '<a href="' + href + '">' + text + '</a>'; }
  function val(id) { var el = document.getElementById(id); return el ? el.value : ''; }
  function memo(text) {
    var lead = document.querySelector('form#leadForm, section.inline-diag form');
    if (!lead) return;
    var m = document.getElementById('lf-memo');
    if (!m) { m = document.createElement('input'); m.type = 'hidden'; m.id = 'lf-memo'; lead.appendChild(m); }
    m.value = text;
  }
  function show(html, tool, code, memoText) {
    out.innerHTML = html; out.hidden = false; err.hidden = true;
    memo(memoText); track('tool_result', { tool: tool, result: code });
    out.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  var NAME = { small3: '소기업(창업 후 3년 이내)', small: '소기업', medium: '중기업', mid: '중견기업' };
  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var size = val('tool-size'), venture = val('tool-venture') === 'yes', staff = parseInt(val('tool-staff'), 10), space = val('tool-space');
    if (!(staff >= 0)) return fail('연구전담요원으로 둘 수 있는 인원 수를 적어 주세요.');
    var r = judge(size, venture, staff);
    var verdict, body;
    if (r.code === 'lab') {
      verdict = '기업부설연구소 인원 기준에 듭니다';
      body = NAME[size] + (venture && size !== 'mid' ? '이면서 벤처기업·연구원 창업 기업' : '') + '의 연구전담요원 기준은 ' + r.need + '명 이상이고, 적어 주신 인원은 ' + staff + '명입니다.';
    } else if (r.code === 'dept') {
      verdict = '연구개발전담부서부터 시작할 수 있는 인원입니다';
      body = '기업부설연구소는 연구전담요원 ' + r.need + '명 이상이 필요한데 적어 주신 인원은 ' + staff + '명입니다. 연구개발전담부서는 1명 이상이면 신청 대상입니다.';
    } else {
      verdict = '연구전담요원을 먼저 확보해야 합니다';
      body = '연구개발전담부서도 연구전담요원 1명 이상이 필요합니다. 기업부설연구소 기준은 ' + r.need + '명 이상입니다.';
    }
    var sp = space === 'room' ? '공간은 벽과 별도 출입문으로 나뉜 독립 공간이 원칙이라, 적어 주신 조건이 원칙에 맞습니다.'
      : (space === 'partition' ? '칸막이로 나눈 공간은 연구공간 면적 등 정해진 조건에서만 인정됩니다. 도면으로 먼저 확인해야 합니다.'
        : '인원과 함께 독립된 연구공간을 갖춰야 신고할 수 있습니다.');
    show('<strong class="verdict">' + verdict + '</strong><p>' + body + '</p><p>' + sp + '</p>' +
      '<p class="next">인원 수보다 자주 걸리는 것은 연구전담요원의 자격과 겸직 여부입니다. ' + link('/venture-certification', '벤처기업확인') + link('/certification', '기업인증 안내') + '</p>' +
      '<p class="tool-note">참고 안내입니다. 인정 여부는 한국산업기술진흥협회(KOITA)의 심사로 정해지며, 학력·자격·겸직·공간 요건을 함께 봅니다.</p>',
      'yeonguso_yogeon', r.code,
      '[연구소 설립요건 체크] ' + verdict + ' / ' + NAME[size] + (venture ? ', 벤처·연구원 창업' : '') + ', 전담요원 ' + staff + '명, 공간 ' + space);
  });
})();
