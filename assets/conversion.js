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
    const tag = document.createElement('script');
    tag.async = true;
    tag.src = 'https://www.googletagmanager.com/gtag/js?id=' + measurementId;
    document.head.appendChild(tag);
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
