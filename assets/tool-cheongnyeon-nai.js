/* 청년창업 나이 계산기 (/cheongnyeon-nai, 2026-11-25)
 *
 * 기준의 출처:
 *  - 만 39세 이하: 2026년 중소기업 정책자금 융자계획(중기부 공고 제2025-649호) 청년전용창업자금, 대표자 만 39세 이하, 업력 3년 미만
 *  - 15세 이상 34세 이하, 병역 이행 기간 최대 6년 차감: 조세특례제한법 시행령 제5조(청년창업중소기업 세액감면), 국세청 안내
 * 나이를 세는 기준일은 제도와 공고마다 다르다. 결과는 참고 안내다.
 * tests/test_tools_batch2.py 가 기준 숫자와 계산을 지킨다.
 */
(function () {
  'use strict';

  function parseDate(s) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(s || '');
    if (!m) return null;
    var d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    return (d.getFullYear() === Number(m[1]) && d.getMonth() === Number(m[2]) - 1) ? d : null;
  }
  function fmt(d) {
    return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  // 기준일까지 꽉 채운 햇수(만 나이·업력 연수). 2월 29일은 평년에 3월 1일로 넘긴다.
  function fullYears(from, to) {
    var y = to.getFullYear() - from.getFullYear();
    var anniv = new Date(from.getFullYear() + y, from.getMonth(), from.getDate());
    if (anniv > to) y -= 1;
    return y;
  }
  function addYears(d, n) { return new Date(d.getFullYear() + n, d.getMonth(), d.getDate()); }
  function addMonths(d, n) {
    var t = new Date(d.getFullYear(), d.getMonth() + n, 1);
    var last = new Date(t.getFullYear(), t.getMonth() + 1, 0).getDate();
    return new Date(t.getFullYear(), t.getMonth(), Math.min(d.getDate(), last));
  }
  function today() { var n = new Date(); return new Date(n.getFullYear(), n.getMonth(), n.getDate()); }

  var LOAN_AGE = 39, TAX_MIN = 15, TAX_MAX = 34, MIL_CAP = 72;
  function calc(birth, ref, milMonths) {
    var age = fullYears(birth, ref);
    var mil = Math.max(0, Math.min(MIL_CAP, Math.floor(milMonths || 0)));
    var taxAge = fullYears(addMonths(birth, mil), ref);
    var lastLoanDay = addYears(birth, LOAN_AGE + 1); lastLoanDay.setDate(lastLoanDay.getDate() - 1);
    return { age: age, loanOk: age <= LOAN_AGE, lastLoanDay: fmt(lastLoanDay), mil: mil, taxAge: taxAge,
      taxOk: age >= TAX_MIN && taxAge <= TAX_MAX };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { calc: calc, parseDate: parseDate, LOAN_AGE: LOAN_AGE, TAX_MAX: TAX_MAX, MIL_CAP: MIL_CAP };

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

  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var birth = parseDate(val('tool-birth'));
    var ref = val('tool-ref') ? parseDate(val('tool-ref')) : today();
    if (!birth) return fail('생년월일을 골라 주세요.');
    if (!ref) return fail('기준일을 다시 골라 주세요.');
    if (birth > ref) return fail('생년월일이 기준일보다 뒤입니다.');
    var r = calc(birth, ref, parseFloat(val('tool-mil')));
    var verdict = fmt(ref) + ' 기준 만 ' + r.age + '세입니다';
    var loan = r.loanOk
      ? '<span class="st-o">기준 안</span> · ' + r.lastLoanDay + '까지 만 39세입니다'
      : '<span class="st-x">기준 밖</span> · 만 39세를 넘었습니다';
    var tax = r.taxOk
      ? '<span class="st-o">기준 안</span>' + (r.mil ? ' · 병역 ' + r.mil + '개월을 빼면 만 ' + r.taxAge + '세' : '')
      : '<span class="st-x">기준 밖</span>' + (r.mil ? ' · 병역 ' + r.mil + '개월을 빼도 만 ' + r.taxAge + '세' : ' · 병역을 이행했다면 기간을 적어 다시 보세요');
    var next = r.loanOk
      ? '나이 다음으로 보는 것은 업력입니다. ' + link('/eopryeok-gyesangi', '업력 계산기') + link('/cheongnyeon-changeop', '청년전용창업자금')
      : '나이 기준이 없는 창업자금을 봅니다. ' + link('/changeop-giban', '창업기반지원자금') + link('/jagajindan', '1분 자가진단');
    show('<strong class="verdict">' + verdict + '</strong>' +
      '<table><tbody><tr><th scope="row">만 39세 이하<br>(중진공 청년전용창업자금 등)</th><td>' + loan + '</td></tr>' +
      '<tr><th scope="row">만 34세 이하<br>(청년창업 세액감면)</th><td>' + tax + '</td></tr></tbody></table>' +
      '<p class="next">' + next + '</p>' +
      '<p class="tool-note">참고 안내입니다. 나이를 세는 기준일은 제도와 공고마다 다르고, 세액감면은 창업 당시 나이로 봅니다. 신청 전에 해당 공고와 기관에서 확인하세요.</p>',
      'cheongnyeon_nai', r.loanOk ? 'in39' : 'over39',
      '[청년창업 나이 계산기] ' + verdict + ' / 만 39세 ' + (r.loanOk ? '이하' : '초과'));
  });
})();
