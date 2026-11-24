/* 보증료 계산기 (/bojeungryo-gyesangi, 2026-11-25)
 *
 * 산식: 보증료 = 보증금액 × 보증료율(연) × 보증기간(일수/365). 연 단위로 넣으면 금액 × 요율 × 연수.
 * 보증료율은 보증기관이 기업의 신용도·보증금액·기간·상품에 따라 약정 때 정한다. 이 도구는 요율을 추정하지 않는다.
 * 결과는 참고 안내다. tests/test_tools_batch2.py 가 계산을 지킨다.
 */
(function () {
  'use strict';

  // amountMan: 만원, ratePct: 연 %, years: 년, loanRatePct: 연 %(선택)
  function calc(amountMan, ratePct, years, loanRatePct) {
    var won = amountMan * 10000;
    var perYear = Math.round(won * ratePct / 100);
    var total = Math.round(won * ratePct / 100 * years);
    var interest = loanRatePct > 0 ? Math.round(won * loanRatePct / 100) : null;
    return { perYear: perYear, total: total, interest: interest, firstYear: interest === null ? null : interest + perYear };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { calc: calc };

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

  function won(n) { return n.toLocaleString('ko-KR') + '원'; }
  form.addEventListener('submit', function (ev) {
    ev.preventDefault();
    var a = parseFloat(val('tool-amount')), rt = parseFloat(val('tool-rate')), y = parseFloat(val('tool-years')), lr = parseFloat(val('tool-loanrate'));
    if (!(a > 0)) return fail('보증금액을 만원 단위로 적어 주세요.');
    if (!(rt >= 0) || rt > 5) return fail('보증료율을 연 0~5% 사이로 적어 주세요.');
    if (!(y > 0)) return fail('보증기간을 년 단위로 적어 주세요.');
    var r = calc(a, rt, y, lr);
    var verdict = '보증료는 1년에 약 ' + won(r.perYear) + '입니다';
    var rows = '<tr><th scope="row">1년 보증료</th><td>' + won(r.perYear) + '</td></tr>' +
      '<tr><th scope="row">' + y + '년 보증료 합계</th><td>' + won(r.total) + '</td></tr>';
    if (r.interest !== null) rows += '<tr><th scope="row">1년 이자(연 ' + lr + '%)</th><td>' + won(r.interest) + '</td></tr>' +
      '<tr><th scope="row">첫해 이자 + 보증료</th><td>' + won(r.firstYear) + '</td></tr>';
    show('<strong class="verdict">' + verdict + '</strong>' +
      '<p>보증금액 ' + a.toLocaleString('ko-KR') + '만 원, 보증료율 연 ' + rt + '% 기준입니다. 원금을 나눠 상환하면 줄어든 잔액만큼 보증료도 줄어듭니다.</p>' +
      '<table><tbody>' + rows + '</tbody></table>' +
      '<p class="next">실제 보증료율은 기관과 기업 상황에 따라 달라집니다. ' + link('/jaedan', '지역신용보증재단') + link('/sinbo', '신용보증기금') + link('/gibo', '기술보증기금') + '</p>' +
      '<p class="tool-note">참고 안내입니다. 보증료율과 내는 방식(한 번에 또는 해마다)은 보증기관이 약정 때 정합니다. 지자체가 보증료를 지원하는 상품도 있으니 신청 전에 확인하세요.</p>',
      'bojeungryo_gyesangi', 'calc',
      '[보증료 계산기] 보증금액 ' + a + '만원, 요율 ' + rt + '%, ' + y + '년 → 1년 ' + won(r.perYear));
  });
})();
