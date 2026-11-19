/* 정책자금 자가진단 (/jagajindan, 2026-11-19)
 *
 * 질문 7개는 HTML 에 라디오 버튼으로 전부 들어 있다(스크립트가 없으면 한 화면에 다 보인다).
 * 이 파일은 그것을 한 번에 한 질문씩 보여주고, 답으로 결과 문장을 고르고, 답 요약을 신청 폼의
 * 숨은 칸(lf-memo·lf-biz)에 넣는다 — 전송은 conversion.js 가 그대로 한다.
 *
 * 결과는 승인 판정이 아니다. 걸리는 항목이 있는지와 "정리하면 다시 볼 수 있는지"까지만 말하고,
 * 판정 기준·한도·금리는 쓰지 않는다(규격 1절·2절). 규격 1절 금지 표현을 쓰지 않는다.
 */
(function () {
  'use strict';
  var form = document.getElementById('scForm');
  var result = document.getElementById('scResult');
  if (!form || !result) return;

  var steps = [].slice.call(form.querySelectorAll('fieldset.sc-q'));
  var bar = document.getElementById('scBar');
  var count = document.getElementById('scCount');
  var back = document.getElementById('scBack');
  var started = false;
  var answers = {};
  var order = [];   // 지나온 질문 번호 — '이전'이 건너뛴 질문을 다시 건너뛰게
  var current = 0;

  function track(name, params) {
    try { if (typeof window.gtag === 'function') window.gtag('event', name, params || {}); } catch (_) { /* 계측 실패가 진단을 막지 않게 */ }
  }
  function label(key) {
    var input = form.querySelector('input[name="' + key + '"]:checked');
    return input ? input.parentNode.textContent.trim() : '';
  }
  // 창업 예정이면 업력·매출 질문은 묻지 않는다
  function skipped(i) {
    var key = steps[i].getAttribute('data-key');
    return answers.form === 'pre' && (key === 'years' || key === 'revenue');
  }
  function visibleTotal() {
    var n = 0;
    for (var i = 0; i < steps.length; i++) if (!skipped(i)) n++;
    return n;
  }
  function position(i) {
    var n = 0;
    for (var j = 0; j <= i; j++) if (!skipped(j)) n++;
    return n;
  }
  function show(i) {
    current = i;
    steps.forEach(function (s, j) { s.hidden = j !== i; });
    var total = visibleTotal();
    var pos = position(i);
    if (count) count.textContent = pos + ' / ' + total;
    if (bar) bar.style.width = Math.round(((pos - 1) / total) * 100) + '%';
    if (back) back.hidden = order.length === 0;
  }
  function next() {
    var i = current + 1;
    while (i < steps.length && skipped(i)) i++;
    if (i >= steps.length) return finish();
    order.push(current);
    show(i);
    var legend = steps[i].querySelector('legend');
    if (legend) { legend.setAttribute('tabindex', '-1'); legend.focus({ preventScroll: true }); }
  }

  // ── 결과 ──────────────────────────────────────────────────────────────
  // level: stop(지금은 정리가 먼저) > fix(먼저 정리할 것) > note(참고)
  var NOTES = {
    pre: { level: 'note', title: '사업자등록 전',
      text: '대부분의 자금은 사업자등록을 한 뒤에 신청해요. 다만 등록 전에 업종과 자금 용도를 정리해 두면, 등록 직후에 볼 수 있는 창업 초기 자금이 있습니다.' },
    young: { level: 'note', title: '업력 1년 미만',
      text: '업력이 짧으면 볼 수 있는 자금이 따로 있어요. 매출 실적 대신 무엇을 보는지가 기관마다 달라서, 어디부터 두드리느냐가 중요합니다.' },
    norev: { level: 'note', title: '매출이 아직 없음',
      text: '매출 실적을 보는 자금은 지금은 어렵습니다. 매출 기준이 없는 초기 자금부터 살펴봐요.' },
    restricted: { level: 'stop', title: '제한될 수 있는 업종',
      text: '유흥, 사행성, 부동산 임대처럼 정책자금에서 빠지는 업종이 있어요. 다만 사업자등록증의 업태와 종목, 실제 영업 내용에 따라 달리 보는 경우가 있어 한 번은 확인해 볼 만합니다.' },
    taxpay: { level: 'fix', title: '세금 체납 (정리할 수 있음)',
      text: '체납이 남아 있는 동안은 대부분의 심사가 멈춥니다. 완납하거나 분납 승인을 받아 납세증명서가 나오는 상태가 되면 다시 볼 수 있는 자금이 있어요. 어느 쪽이 맞는지는 체납 세목과 금액에 따라 달라집니다.' },
    taxhard: { level: 'stop', title: '세금 체납 (당장 정리가 어려움)',
      text: '이 상태로 접수하면 서류 단계에서 멈춥니다. 한 번에 내지 못해도 분납으로 길이 열리는 경우가 있으니, 체납 세목과 금액부터 같이 살펴봐요. 방법이 없으면 없다고 말씀드립니다.' },
    taxunknown: { level: 'fix', title: '세금 체납 여부를 모름',
      text: '적은 금액이라도 체납이 있으면 심사가 멈춰요. 홈택스(국세)와 위택스(지방세)에서 바로 확인할 수 있습니다.' },
    overpast: { level: 'fix', title: '예전 연체 (지금은 정리됨)',
      text: '연체가 있었다고 결과가 모두 같지는 않아요. 며칠 동안이었는지, 정리한 지 얼마나 됐는지, 기록이 아직 남아 있는지에 따라 기관이 보는 것이 다릅니다.' },
    overnow: { level: 'stop', title: '지금 연체 중',
      text: '연체가 진행 중이면 대부분의 기관이 먼저 정리를 요구해요. 정리한 뒤 언제, 어느 기관부터 다시 볼 수 있는지는 연체 일수와 남은 기록에 따라 달라집니다.' },
    overunknown: { level: 'fix', title: '연체 여부를 모름',
      text: '카드 대금이나 대출 이자가 며칠 밀린 적이 있다면 기록이 남아 있을 수 있어요. 신청 전에 한 번 조회해 보는 편이 안전합니다.' }
  };
  var HEAD = {
    clear: ['지금 조건이면 바로 살펴볼 수 있어요', '걸리는 항목이 보이지 않습니다. 남은 것은 어느 기관의 어떤 자금부터 볼지예요.'],
    note: ['살펴볼 수 있어요. 다만 볼 자금이 좁혀집니다', '막히는 항목은 없지만, 조건에 맞는 자금이 따로 있는 경우입니다.'],
    fix: ['먼저 정리할 것이 {n}가지 있어요', '정리하면 다시 볼 수 있는 항목들입니다. 순서가 중요해요.'],
    stop: ['지금은 신청보다 정리가 먼저예요', '이대로 접수하면 멈출 가능성이 큽니다. 다만 정리 순서에 따라 다시 볼 수 있는 경우가 있어요.']
  };

  function collect() {
    var keys = [];
    if (answers.form === 'pre') keys.push('pre');
    if (answers.years === 'u1') keys.push('young');
    if (answers.revenue === 'none') keys.push('norev');
    if (answers.industry === 'restricted') keys.push('restricted');
    if (answers.tax === 'payable') keys.push('taxpay');
    if (answers.tax === 'hard') keys.push('taxhard');
    if (answers.tax === 'unknown') keys.push('taxunknown');
    if (answers.overdue === 'past') keys.push('overpast');
    if (answers.overdue === 'now') keys.push('overnow');
    if (answers.overdue === 'unknown') keys.push('overunknown');
    return keys;
  }
  function levelOf(keys) {
    var rank = { clear: 0, note: 1, fix: 2, stop: 3 };
    var level = 'clear';
    keys.forEach(function (k) { if (rank[NOTES[k].level] > rank[level]) level = NOTES[k].level; });
    return level;
  }
  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }
  function stat(key) {
    var span = document.querySelector('#scStats [data-stat="' + key + '"]');
    return span ? span.textContent.trim() : '';
  }

  function finish() {
    var keys = collect();
    var level = levelOf(keys);
    var blocking = keys.filter(function (k) { return NOTES[k].level !== 'note'; });
    var head = HEAD[level];

    result.innerHTML = '';
    result.setAttribute('data-level', level);
    result.appendChild(el('p', 'sc-r-kicker', '자가진단 결과'));
    var h = el('h2', 'serif', head[0].replace('{n}', String(blocking.length)));
    h.id = 'scResultTitle'; h.setAttribute('tabindex', '-1');
    result.appendChild(h);
    result.appendChild(el('p', 'sc-r-sub', head[1]));

    if (keys.length) {
      var list = el('ul', 'sc-r-list');
      keys.forEach(function (k) {
        var li = el('li', 'sc-r-' + NOTES[k].level);
        li.appendChild(el('b', null, NOTES[k].title));
        li.appendChild(el('span', null, NOTES[k].text));
        list.appendChild(li);
      });
      result.appendChild(list);
    }

    // 같은 사업 형태로 받은 사례 — 숫자는 build_cases 가 원장에서 넣은 data-stat
    var n = answers.form === 'corp' ? stat('corp-n') : answers.form === 'ind' ? stat('ind-n') : '';
    if (n) {
      var who = answers.form === 'corp' ? '법인사업자' : '개인사업자';
      var p = el('p', 'sc-r-cases');
      p.appendChild(document.createTextNode('저희를 거쳐 ' + who + '가 받은 사례는 ' + n + '건입니다. '));
      var a = el('a', null, '받은 사례 보기'); a.href = '/cases'; p.appendChild(a);
      result.appendChild(p);
    }

    // 여기서 묻지 않은 것 — 전화에서 듣는 것
    var ask = ['지금 있는 대출과 보증 잔액'];
    if (answers.tax === 'payable' || answers.tax === 'hard') ask.push('체납 세목과 금액');
    if (answers.overdue === 'past' || answers.overdue === 'now') ask.push('연체 일수와 정리한 시점');
    ask.push('자금이 필요한 시기와 금액');
    var box = el('div', 'sc-r-ask');
    box.appendChild(el('p', null, '자가진단에서 묻지 않은 것'));
    var ul = el('ul');
    ask.forEach(function (t) { ul.appendChild(el('li', null, t)); });
    box.appendChild(ul);
    box.appendChild(el('p', 'sc-r-ask-foot', '전화에서 이것만 들으면 신청해 볼 기관과 자금 후보, 준비 순서를 말씀드릴 수 있어요. 진단은 무료입니다.'));
    result.appendChild(box);

    var go = el('a', 'sc-r-cta', '이 결과로 무료 진단 신청');
    go.href = '#apply'; go.setAttribute('data-cta-location', 'selfcheck_result');
    result.appendChild(go);
    var again = el('button', 'sc-r-again', '처음부터 다시 하기');
    again.type = 'button';
    again.addEventListener('click', restart);
    result.appendChild(again);
    result.appendChild(el('p', 'sc-r-fine', '이 결과는 답하신 내용만으로 본 참고 안내입니다. 승인 여부와 조건은 각 심사 기관이 결정합니다.'));

    form.hidden = true;
    result.hidden = false;
    if (bar) bar.style.width = '100%';
    fillLeadForm(level, keys);
    track('selfcheck_complete', { result_level: level, flag_count: keys.length });
    h.focus({ preventScroll: true });
    result.scrollIntoView({ block: 'start', behavior: 'smooth' });
  }

  // 답 요약을 신청 폼에 싣는다 — 알림 메일·CRM 에 '문의' 로 찍힌다
  function fillLeadForm(level, keys) {
    var names = { clear: '바로 검토', note: '검토 가능(자금 좁혀짐)', fix: '정리 후 검토', stop: '정리 먼저' };
    var parts = [
      '형태 ' + label('form'),
      answers.years ? '업력 ' + label('years') : '',
      '업종 ' + label('industry'),
      answers.revenue ? '매출 ' + label('revenue') : '',
      '체납 ' + label('tax'),
      '연체 ' + label('overdue'),
      '용도 ' + label('purpose')
    ].filter(Boolean);
    var memo = document.getElementById('lf-memo');
    if (memo) memo.value = '[자가진단] 결과: ' + names[level] + ' / ' + parts.join(', ');
    var biz = document.getElementById('lf-biz');
    if (biz) biz.value = label('industry');
    // 사업자 형태 버튼을 답에 맞춰 눌러 둔다(다시 묻지 않게)
    var want = { ind: '개인사업자', corp: '법인사업자', pre: '창업 예정' }[answers.form];
    [].slice.call(document.querySelectorAll('#lf-biztype .biz-opt')).forEach(function (b) {
      if (b.textContent.trim() === want && b.getAttribute('aria-pressed') !== 'true') b.click();
    });
    var title = document.getElementById('inline-diag-title');
    if (title) title.textContent = '이 결과로 무료 진단 받기';
  }

  function restart() {
    form.reset();
    answers = {}; order = [];
    result.hidden = true; form.hidden = false;
    show(0);
    form.scrollIntoView({ block: 'start', behavior: 'smooth' });
  }

  // ── 시작 ──────────────────────────────────────────────────────────────
  form.classList.add('sc-live');
  form.addEventListener('change', function (e) {
    var input = e.target;
    if (!input || input.type !== 'radio') return;
    answers[input.name] = input.value;
    if (!started) { started = true; track('selfcheck_start', {}); }
    // 고른 것이 눈에 보인 뒤 넘어간다
    window.setTimeout(next, 180);
  });
  if (back) back.addEventListener('click', function () {
    if (!order.length) return;
    var i = order.pop();
    // 돌아간 질문은 답을 비운다 — 같은 답을 다시 눌러도 change 가 나서 넘어가게
    [].slice.call(steps[i].querySelectorAll('input')).forEach(function (r) { r.checked = false; });
    delete answers[steps[i].getAttribute('data-key')];
    show(i);
  });
  form.addEventListener('submit', function (e) { e.preventDefault(); });
  show(0);
})();
