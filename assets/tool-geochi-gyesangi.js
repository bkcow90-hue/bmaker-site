/* 거치기간 상환 계산기 (/geochi-gyesangi, 2026-11-25)
 *
 * 거치기간에는 이자만 내고, 거치가 끝나면 남은 기간에 원금을 나눠 상환한다.
 *  - 원금균등: 매달 같은 원금 + 줄어드는 이자
 *  - 원리금균등: 매달 같은 금액
 * 월 단위·월 이자 = 잔액 × 연 금리 / 12 로 단순 계산한다. 실제 납입일·일수 계산, 금리 변동, 분기 상환은 반영하지 않는다.
 * 결과는 참고 안내다. tests/test_tools_batch2.py 가 계산을 지킨다.
 */
(function () {
  'use strict';

  // amountMan: 만원, ratePct: 연 %, totalYears·graceYears: 년
  function calc(amountMan, ratePct, totalYears, graceYears, method) {
    var P = amountMan * 10000, i = ratePct / 100 / 12;
    var g = Math.round(graceYears * 12), n = Math.round(totalYears * 12) - g;
    var graceMonthly = Math.round(P * i);
    var first, last, interest = P * i * g;
    if (method === 'annuity') {
      var pay = i === 0 ? P / n : P * i / (1 - Math.pow(1 + i, -n));
      first = last = Math.round(pay);
      interest += pay * n - P;
    } else {
      var prin = P / n;
      first = Math.round(prin + P * i);
      last = Math.round(prin + prin * i);
      interest += P * i * (n + 1) / 2;
    }
    return { graceMonths: g, payMonths: n, graceMonthly: graceMonthly, first: first, last: last, totalInterest: Math.round(interest) };
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
    var a = parseFloat(val('tool-amount')), rt = parseFloat(val('tool-rate')), t = parseFloat(val('tool-total')), g = parseFloat(val('tool-grace')), method = val('tool-method');
    if (!(a > 0)) return fail('대출금을 만원 단위로 적어 주세요.');
    if (!(rt >= 0) || rt > 20) return fail('금리를 연 0~20% 사이로 적어 주세요.');
    if (!(t >= 1)) return fail('전체 대출 기간을 년 단위로 적어 주세요.');
    if (!(g >= 0)) return fail('거치기간을 년 단위로 적어 주세요. 없으면 0입니다.');
    if (g >= t) return fail('거치기간은 전체 대출 기간보다 짧아야 합니다.');
    var r = calc(a, rt, t, g, method);
    var verdict = r.graceMonths > 0 ? '거치 중에는 매달 이자 약 ' + won(r.graceMonthly) + '입니다' : '거치 없이 첫 달 약 ' + won(r.first) + '입니다';
    var rows = (r.graceMonths > 0 ? '<tr><th scope="row">거치 ' + r.graceMonths + '개월</th><td>매달 이자 ' + won(r.graceMonthly) + '</td></tr>' : '') +
      '<tr><th scope="row">상환 ' + r.payMonths + '개월, 첫 달</th><td>' + won(r.first) + '</td></tr>' +
      '<tr><th scope="row">상환 마지막 달</th><td>' + won(r.last) + '</td></tr>' +
      '<tr><th scope="row">전체 기간 이자 합계</th><td>' + won(r.totalInterest) + '</td></tr>';
    show('<strong class="verdict">' + verdict + '</strong>' +
      '<p>대출금 ' + a.toLocaleString('ko-KR') + '만 원, 연 ' + rt + '%, ' + (method === 'annuity' ? '원리금균등' : '원금균등') + ' 기준입니다. 거치가 끝나는 달부터 납입액이 크게 늘어납니다.</p>' +
      '<table><tbody>' + rows + '</tbody></table>' +
      '<p class="next">거치가 끝난 뒤 부담이 걱정이라면 미리 구조를 봅니다. ' + link('/sanghwan', '상환 부담 안내') + link('/daehwan', '대환대출') + '</p>' +
      '<p class="tool-note">참고 안내입니다. 월 단위로 단순 계산한 값이며 실제 납입액은 납입일, 금리 변동, 분기 상환 여부에 따라 달라집니다. 정확한 금액은 대출 기관의 상환 일정표로 확인하세요.</p>',
      'geochi_gyesangi', method,
      '[거치기간 계산기] ' + a + '만원, 연 ' + rt + '%, ' + t + '년(거치 ' + g + '년) → 거치 중 월 ' + won(r.graceMonthly) + ', 이후 첫 달 ' + won(r.first));
  });
})();
