/* Shared conversion events. No form values or arbitrary URL query strings in analytics. */
(function () {
  'use strict';
  const serviceLabels = { general: '종합 상담', policy: '정책자금·사업자대출', marketing: '기업광고·마케팅', startup: '창업컨설팅', certification: '기업인증·연구소', education: '교육·출강' };
  const markedService = document.body?.dataset?.service;
  const pageService = markedService && Object.hasOwn(serviceLabels, markedService) ? markedService
    : /^\/certification(?:\.html)?\/?$/.test(location.pathname) ? 'certification'
    : ['/', '/index.html', '/privacy', '/404'].includes(location.pathname) ? 'general' : 'policy';
  const serviceField = document.getElementById('lf-service');
  if (serviceField) {
    const requested = new URLSearchParams(location.search || '').get('service');
    serviceField.value = requested && Object.hasOwn(serviceLabels, requested) ? requested : 'general';
  }
  const updateEducationHelp = () => {
    const education = serviceField?.value === 'education';
    const help = document.getElementById('education-help');
    const memo = document.getElementById('lf-memo');
    const options = document.getElementById('lf-options');
    if (help) help.hidden = !education;
    if (memo) memo.placeholder = education ? '단체명 / 지역 / 예상 인원 / 희망 일정 / 관심 프로그램 (미정 가능)' : '예: 자금 검토, 회사 홍보, 창업 준비가 필요합니다';
    if (options && education) options.open = true;
  };
  updateEducationHelp();
  const selectedService = () => serviceField && Object.hasOwn(serviceLabels, serviceField.value) ? serviceField.value : pageService;
  // Existing policy pages also use this shared file; keep their consultation intent.
  if (!serviceField) document.querySelectorAll('a[href="/#apply"], a[href="#apply"]').forEach(link => {
    link.setAttribute('href', '/?service=' + pageService + '#apply');
  });
  // Shared by all static pages and their generators. Do not measure previews.
  const measurementId = 'G-DBGR3P6ZHD';
  if (['bmaker.kr', 'www.bmaker.kr'].includes(location.hostname) && !window.bmakerAnalyticsInitialized) {
    window.bmakerAnalyticsInitialized = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = window.gtag || function () { window.dataLayer.push(arguments); };
    // Keep campaign attribution, but discard unknown query parameters and hashes.
    const pageUrl = new URL(location.origin + location.pathname);
    const incoming = new URLSearchParams(location.search);
    for (const key of ['utm_source', 'utm_medium', 'utm_campaign', 'utm_id', 'utm_term', 'utm_content', 'gclid', 'gbraid', 'wbraid']) {
      if (incoming.has(key)) pageUrl.searchParams.set(key, incoming.get(key));
    }
    let referrer = '';
    try { const ref = new URL(document.referrer); referrer = ref.origin + ref.pathname; } catch (_) { /* Direct visit. */ }
    window.gtag('js', new Date());
    window.gtag('config', measurementId, {
      page_location: pageUrl.href,
      page_referrer: referrer,
      allow_google_signals: false,
      allow_ad_personalization_signals: false,
      service_category: pageService
    });
    const loadGtag = () => {
      const tag = document.createElement('script');
      tag.async = true;
      tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
      document.head.appendChild(tag);
    };
    // 초기 렌더 경로에서 168KB 스크립트를 치운다 — 그 사이 이벤트는 dataLayer에 쌓였다가 전송된다
    if (document.readyState === 'complete' || typeof window.addEventListener !== 'function') loadGtag();
    else window.addEventListener('load', loadGtag, { once: true });
  }
  const track = (event, details = {}) => {
    const safe = { page_path: location.pathname, service_category: selectedService(), ...details };
    if (typeof window.gtag === 'function') window.gtag('event', event, safe);
    else { window.dataLayer = window.dataLayer || []; window.dataLayer.push({ event, ...safe }); }
  };
  const form = document.getElementById('leadForm');
  let ctaLocation = 'direct_form';
  if (serviceField) serviceField.addEventListener('change', () => {
    updateEducationHelp();
    track('consultation_service_select');
  });
  document.addEventListener('click', e => {
    const link = e.target instanceof Element ? e.target.closest('a') : null;
    if (!link) return;
    const href = link.getAttribute('href') || '';
    const where = link.dataset.ctaLocation || (link.closest('header') ? 'header' : 'content');
    if (href.includes('pf.kakao.com/')) track('kakao_click', { cta_location: where });
    else if (href.startsWith('tel:')) track('phone_click', { cta_location: where });
    else if (href.endsWith('#apply')) {
      ctaLocation = where;
      track('consultation_click', { cta_location: where });
    }
  });
  if (!form) return;
  const message = document.getElementById('applyMsg');
  const button = form.querySelector('[type=submit]');
  const phone = document.getElementById('lf-phone');
  const name = document.getElementById('lf-name');
  let started = false, busy = false, completed = false, selectedTime = '';
  let requestId = '', previousPayload = '', submittedAt = '';
  const timeButtons = [...document.querySelectorAll('#lf-time .time-opt')];
  timeButtons.forEach(b => b.addEventListener('click', () => {
    const wasSelected = b.getAttribute('aria-pressed') === 'true';
    timeButtons.forEach(t => t.setAttribute('aria-pressed', 'false'));
    selectedTime = wasSelected ? '' : b.textContent.trim();
    if (!wasSelected) b.setAttribute('aria-pressed', 'true');
  }));
  form.addEventListener('input', () => {
    phone.setCustomValidity(''); name.setCustomValidity('');
    if (completed) { completed = false; message.textContent = ''; }
    if (!started) { started = true; track('consultation_start', { cta_location: ctaLocation }); }
  });
  form.addEventListener('invalid', () => track('consultation_validation_error'), true);
  const sticky = document.querySelector('.sticky-cta');
  let formInView = false;
  function updateSticky() {
    if (sticky) sticky.hidden = formInView || form.contains(document.activeElement);
  }
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      formInView = entries[0].isIntersecting; updateSticky();
    }, { threshold: 0 }).observe(form);
  }
  form.addEventListener('focusin', updateSticky);
  form.addEventListener('focusout', () => setTimeout(updateSticky, 0));
  function failure(uncertain) {
    message.className = 'apply-msg err';
    message.textContent = uncertain
      ? '접수 결과를 확인하지 못했습니다. 입력 내용은 유지됩니다. 재시도하거나 카톡·전화로 접수 여부를 확인해 주세요.'
      : '상담 신청을 전달하지 못했습니다. 입력 내용은 유지됩니다. 다시 시도하거나 아래로 연락해 주세요.';
    const links = document.createElement('div'); links.className = 'apply-fallback';
    for (const [label, href, cls] of [['카톡 상담', 'https://pf.kakao.com/_GKuxfn/chat', 'fb-kakao'], ['전화 1666-2425', 'tel:1666-2425', 'fb-tel']]) {
      const a = document.createElement('a'); a.textContent = label; a.href = href; a.className = cls;
      a.dataset.ctaLocation = 'form_error';
      if (href.startsWith('https:')) { a.target = '_blank'; a.rel = 'noopener'; }
      links.appendChild(a);
    }
    message.appendChild(links); message.focus();
  }
  form.addEventListener('submit', async e => {
    e.preventDefault();
    if (busy || completed) return;
    name.setCustomValidity(name.value.trim() ? '' : '성함을 입력해 주세요.');
    const digits = phone.value.replace(/[\s()-]/g, '');
    phone.setCustomValidity(/^0\d{8,10}$/.test(digits) ? '' : '연락 가능한 전화번호를 확인해 주세요.');
    if (!form.reportValidity()) return;
    const industry = document.getElementById('lf-biz').value.trim();
    const memo = document.getElementById('lf-memo').value.trim();
    const preferredTime = selectedTime || '아무 때나';
    const serviceKey = selectedService();
    const serviceLabel = serviceLabels[serviceKey];
    const payload = {
      kind: 'consult', service: serviceKey === 'policy' ? 'pfm' : serviceKey, service_name: serviceLabel, delivery_required: true,
      consultation_service: serviceKey,
      name: name.value.trim(), phone: digits,
      preferred_time: preferredTime,
      answers_text: ['[문의 분야] ' + serviceLabel, '[예약] 통화 희망: ' + preferredTime, '업종: ' + (industry || '미입력'), '문의: ' + (memo || '미입력')].join(' · '),
      diagnosis: { '문의 분야': serviceLabel, '통화 희망 시간': preferredTime, industry, memo },
      consent_privacy: document.getElementById('lf-consent').checked,
      consent_marketing: false, consent_version: 'v1.1-2026-09-07-service-selection',
      website: document.getElementById('lf-website').value,
      source: 'bmaker.kr 홈페이지 간편신청'
    };
    // Reuse the ID and exact payload across uncertain retries; never persist contact data.
    const fingerprint = JSON.stringify(payload);
    if (fingerprint !== previousPayload) {
      requestId = crypto.randomUUID(); previousPayload = fingerprint; submittedAt = new Date().toISOString();
    }
    payload.request_id = requestId; payload.submitted_at = submittedAt;
    busy = true; button.disabled = true; button.textContent = '전송 중…';
    form.setAttribute('aria-busy', 'true'); message.textContent = '';
    track('consultation_submit', { cta_location: ctaLocation });
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 22000);
    try {
      const response = await fetch('https://codedaum.pages.dev/api/lead', {
        method: 'POST', headers: { 'Content-Type': 'text/plain;charset=utf-8' },
        body: JSON.stringify(payload), signal: controller.signal
      });
      const result = await response.json();
      if (!response.ok || result.ok !== true || result.delivery !== 'accepted') throw new Error('delivery_failed');
      completed = true;
      message.className = 'apply-msg ok';
      message.textContent = '상담 신청이 접수됐습니다. 평일 09:00–18:00에 연락드리며, 선택하신 통화 시간대를 참고합니다. 급한 문의는 1666-2425로 연락해 주세요.';
      form.reset(); selectedTime = ''; timeButtons.forEach(b => b.setAttribute('aria-pressed', 'false'));
      track('generate_lead', { cta_location: ctaLocation, method: 'consultation_form', service_category: serviceKey });
      message.focus();
    } catch (error) {
      const reason = error.name === 'AbortError' ? 'timeout' : error.message === 'delivery_failed' ? 'delivery_failed' : 'network_or_response';
      track('consultation_error', { reason }); failure(reason !== 'delivery_failed');
    } finally {
      clearTimeout(timeout); busy = false; form.removeAttribute('aria-busy'); button.disabled = false;
      button.textContent = completed ? '신청 접수 완료' : '무료 상담 신청하기';
    }
  });
})();

/* Scroll reveal — 전 페이지 공통. CSS 를 주입해 정적 페이지까지 커버한다.
   기존 홈의 .reveal/.on 구현과 충돌하지 않도록 .rv/.rv-in 네임스페이스를 쓴다. */
(function () {
  'use strict';
  if (!('IntersectionObserver' in window)) return;
  if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  var css = '.rv{opacity:0;transform:translateY(12px);transition:opacity .5s cubic-bezier(.22,.61,.36,1),transform .5s cubic-bezier(.22,.61,.36,1);transition-delay:var(--rv-d,0ms)}'
          + '.rv-in{opacity:1;transform:none}'
          + '@media(prefers-reduced-motion:reduce){.rv{opacity:1;transform:none;transition:none}}';
  var st = document.createElement('style');
  st.setAttribute('data-rv', '');
  st.appendChild(document.createTextNode(css));
  (document.head || document.documentElement).appendChild(st);

  // 제외: 히어로 · 상담 폼 · 인라인 CTA · 모바일 고정 CTA · 헤더/푸터/내비,
  //      그리고 홈의 기존 .reveal 구현이 이미 맡은 요소
  var EXCLUDE = '.hero, .hero *, #leadForm, #leadForm *, .cta-inline, .cta-inline *,'
              + '.sticky-cta, .sticky-cta *, header, header *, footer, footer *, nav, nav *,'
              + '.reveal, .reveal *';
  function excluded(el) { return el.closest(EXCLUDE) !== null; }

  var targets = [];
  function add(el) {
    if (!el || excluded(el) || targets.indexOf(el) !== -1) return;
    targets.push(el);
  }

  document.querySelectorAll('main section, body > section').forEach(function (sec) {
    if (excluded(sec)) return;
    sec.querySelectorAll(':scope > .wrap > h2, :scope > .wrap > .sec-label, :scope > .wrap > p').forEach(add);
    sec.querySelectorAll('.card, .stat, .svc, .exp, details').forEach(add);
  });

  // 표: 본문 20행 이하만 행 단위 순차, 그 이상은 표 컨테이너 단위
  document.querySelectorAll('table').forEach(function (tb) {
    if (excluded(tb)) return;
    var rows = tb.querySelectorAll('tbody tr');
    if (rows.length && rows.length <= 20) rows.forEach(add);
    else add(tb);
  });

  if (!targets.length) return;

  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add('rv-in');
      io.unobserve(e.target);
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -10% 0px' });

  var vh = window.innerHeight || document.documentElement.clientHeight;
  var groups = new Map();
  var below = [];
  targets.forEach(function (el) { if (el.getBoundingClientRect().top >= vh) below.push(el); }); // 읽기 일괄
  below.forEach(function (el) {
    // 이미 화면 안이면 숨기지 않는다 — defer 실행이라 깜빡임이 생기기 때문 (위에서 걸러짐)
    var parent = el.parentElement;
    var i = groups.get(parent) || 0;
    groups.set(parent, i + 1);
    el.style.setProperty('--rv-d', Math.min(i, 8) * 40 + 'ms');
    el.classList.add('rv');
    io.observe(el);
  });
})();

/* 접수 일정(/schedule) — 시작일이 지난 건은 방문 시점 날짜로 문장을 바꿔 끼운다.
   빌드 시점에 예정/경과를 갈라 굳히면 다음 재빌드까지 지난 상태가 그대로 남는다.
   JS 가 없는 크롤러·AI 는 서버가 쓴 '공고상 YYYY-MM-DD 예정' 을 읽는다 — 날짜가 그대로 있어
   굳은 배지보다 정확하다. 기관 확인 관측(분기마감·접수중표시)은 사람이 기록한 사실이라 손대지 않는다. */
(function () {
  'use strict';
  var cells = document.querySelectorAll('[data-sched-start][data-sched-passed]');
  if (!cells.length) return;
  var parse = function (v) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || '');
    return m ? new Date(+m[1], +m[2] - 1, +m[3]) : null;
  };
  var now = new Date();
  var today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  Array.prototype.forEach.call(cells, function (el) {
    var start = parse(el.getAttribute('data-sched-start'));
    if (!start || today < start) return;                 // 아직 시작 전 — 서버 문장 유지
    var passed = el.getAttribute('data-sched-passed');
    if (!passed) return;
    var cls = el.getAttribute('data-sched-passed-class') || 'check';
    el.className = el.className.replace(/\bb-[a-z]+\b/, 'b-' + cls);
    el.textContent = passed;
    el.setAttribute('data-sched-state', 'passed');
  });
})();
