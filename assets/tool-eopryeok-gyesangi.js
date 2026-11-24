/* 업력 계산기 (/eopryeok-gyesangi, 2026-11-25)
 *
 * 기준의 출처: 중소벤처기업진흥공단 누리집 사업 안내·2026년 중소기업 정책자금 융자계획(중기부 공고 제2025-649호)
 *  - 업력 산정: 사업 개시일부터 정책자금 융자신청서 제출일까지. 법인전환 등은 최초 창업한 기업의 사업 개시일부터
 *  - 청년전용창업자금 업력 3년 미만 · 창업기반지원자금 7년 미만(신산업 창업 분야는 10년 이내) · 신성장기반자금 7년 이상
 * 결과는 참고 안내다. tests/test_tools_batch2.py 가 구간과 계산을 지킨다.
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

  var T_YOUTH = 3, T_STARTUP = 7, T_NEW = 10;
  function calc(start, ref) {
    var y = fullYears(start, ref);
    var m = 0;
    while (addMonths(addYears(start, y), m + 1) <= ref) m += 1;
    var base = addMonths(addYears(start, y), m);
    var d = Math.round((ref - base) / 86400000);
    var band = y < T_YOUTH ? 'under3' : (y < T_STARTUP ? 'under7' : (y < T_NEW ? 'under10' : 'over10'));
    return { years: y, months: m, days: d, band: band, at3: fmt(addYears(start, T_YOUTH)), at7: fmt(addYears(start, T_STARTUP)) };
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = { calc: calc, parseDate: parseDate };

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
    var start = parseDate(val('tool-start'));
    var ref = val('tool-ref') ? parseDate(val('tool-ref')) : today();
    var type = val('tool-type');
    if (!start) return fail('사업 개시일을 골라 주세요.');
    if (!ref) return fail('기준일을 다시 골라 주세요.');
    if (start > ref) return fail('사업 개시일이 기준일보다 뒤입니다. 아직 창업 전이라면 예비창업자로 봅니다.');
    var r = calc(start, ref);
    var verdict = '업력 ' + r.years + '년 ' + r.months + '개월 ' + r.days + '일입니다';
    var body, next;
    if (r.band === 'under3') {
      body = '업력 3년 미만입니다. ' + r.at3 + '에 3년, ' + r.at7 + '에 7년이 됩니다.';
      next = '대표자가 만 39세 이하이면 청년 자금도 함께 봅니다. ' + link('/cheongnyeon-nai', '청년창업 나이 계산기') + link('/cheongnyeon-changeop', '청년전용창업자금') + link('/changeop-giban', '창업기반지원자금');
    } else if (r.band === 'under7') {
      body = '업력 3년 이상 7년 미만입니다. ' + r.at7 + '에 7년이 됩니다.';
      next = '창업기업 대상 자금을 보는 구간입니다. ' + link('/changeop-giban', '창업기반지원자금') + link('/jungjingong', '중진공 정책자금');
    } else if (r.band === 'under10') {
      body = '업력 7년 이상 10년 미만입니다. 신산업 창업 분야는 사업 개시일부터 10년 이내까지 창업기업으로 보는 기준이 있습니다.';
      next = '업력 7년 이상이 먼저 보는 자금입니다. ' + link('/sinseongjang', '신성장기반자금') + link('/changeop-giban', '창업기반지원자금');
    } else {
      body = '업력 10년 이상입니다.';
      next = '업력 7년 이상이 먼저 보는 자금입니다. ' + link('/sinseongjang', '신성장기반자금') + link('/jungjingong', '중진공 정책자금');
    }
    var extra = type === 'jeonhwan' ? '<p>법인전환은 처음 창업한 개인사업자의 사업 개시일부터 셉니다. 법인 설립일을 넣으셨다면 개인사업자 개업일로 다시 계산하세요.</p>'
      : (type === 'beobin' ? '<p>법인은 법인등기부의 설립등기일을 사업 개시일로 봅니다.</p>' : '');
    show('<strong class="verdict">' + verdict + '</strong><p>' + fmt(ref) + ' 기준입니다. ' + body + '</p>' + extra +
      '<p class="next">' + next + '</p>' +
      '<p class="tool-note">참고 안내입니다. 중진공은 사업 개시일부터 융자신청서 제출일까지를 업력으로 셉니다. 기관과 자금에 따라 세는 방법이 다를 수 있으니 신청 전에 확인하세요.</p>',
      'eopryeok_gyesangi', r.band,
      '[업력 계산기] ' + verdict + ' (' + fmt(ref) + ' 기준, 개시일 ' + fmt(start) + ')');
  });
})();
