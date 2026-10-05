/* Shared conversion events. No form values or arbitrary URL query strings in analytics. */
(function () {
  'use strict';
  /* @inline-form:start — tools/sync_inline_form_js.py 가 tools/inline_form.py 에서 만든다. 손으로 고치지 않는다. */
  const INLINE_FORM_HTML = "<section id=\"apply\" class=\"inline-diag\" aria-label=\"무료 진단 예약\">\n  <form id=\"leadForm\" aria-labelledby=\"inline-diag-title\">\n    <h2 id=\"inline-diag-title\" class=\"serif\">우리 회사도 되는지 무료로 확인</h2>\n    <p class=\"sub\">연락처를 남겨주시면 사업 조건으로 이 경로가 맞는지 확인해 알려드립니다.</p>\n    <input type=\"text\" name=\"website\" id=\"lf-website\" tabindex=\"-1\" autocomplete=\"off\" style=\"position:absolute;left:-9999px;opacity:0\" aria-hidden=\"true\">\n    <input type=\"hidden\" id=\"lf-service\" name=\"consultation_service\" value=\"policy\">\n    <input type=\"hidden\" id=\"lf-page\" value=\"__PATH__ (__LABEL__)\">\n    <p class=\"field-label\" id=\"lf-biztype-label\">사업자 형태</p>\n    <div class=\"opts\" role=\"group\" aria-labelledby=\"lf-biztype-label\" id=\"lf-biztype\"><button type=\"button\" class=\"biz-opt\" aria-pressed=\"false\">개인사업자</button><button type=\"button\" class=\"biz-opt\" aria-pressed=\"false\">법인사업자</button><button type=\"button\" class=\"biz-opt\" aria-pressed=\"false\">창업 예정</button></div>\n    <div class=\"row group\">\n      <div><label for=\"lf-name\">성함 (필수)</label><input id=\"lf-name\" name=\"name\" type=\"text\" placeholder=\"홍길동\" required autocomplete=\"name\"></div>\n      <div><label for=\"lf-phone\">연락처 (필수)</label><input id=\"lf-phone\" name=\"phone\" type=\"tel\" placeholder=\"010-0000-0000\" required autocomplete=\"tel\" inputmode=\"tel\" maxlength=\"20\"></div>\n    </div>\n    <div class=\"group\">\n      <p class=\"field-label\" id=\"lf-time-label\">통화 희망 시간</p>\n      <div class=\"opts\" role=\"group\" aria-labelledby=\"lf-time-label\" id=\"lf-time\"><button type=\"button\" class=\"time-opt\" aria-pressed=\"false\">오전 (9~12시)</button><button type=\"button\" class=\"time-opt\" aria-pressed=\"false\">오후 (12~6시)</button><button type=\"button\" class=\"time-opt\" aria-pressed=\"false\">아무 때나</button></div>\n    </div>\n    <label class=\"consent\"><input type=\"checkbox\" id=\"lf-consent\" required> <span>개인정보 수집·이용에 동의합니다. 상담 목적으로만 사용됩니다. <a href=\"/privacy\" target=\"_blank\" rel=\"noopener\">개인정보처리방침 보기</a></span></label>\n    <button type=\"submit\">무료 진단 신청</button>\n    <p class=\"apply-msg\" id=\"applyMsg\" role=\"status\" aria-live=\"polite\" tabindex=\"-1\"></p>\n    <p class=\"note\">서류 첨부는 필요하지 않습니다. 평일 09:00–18:00에 연락드립니다. 승인 여부와 조건은 각 심사 기관이 결정합니다.</p>\n    <noscript>온라인 신청에는 자바스크립트가 필요합니다. 전화 1666-2425 또는 카톡 상담을 이용해 주세요.</noscript>\n  </form>\n</section>\n";
  const INLINE_FORM_CSS = ".inline-diag{border-top:2px solid var(--navy,#0E1B33);border-bottom:1px solid var(--line,#E1DED6);background:var(--paper,#F7F5F0);padding:26px 24px;margin:28px 0}.inline-diag h2{margin:0 0 6px;padding:0;border:0;font-size:1.18rem;line-height:1.45;color:var(--navy,#0E1B33)}.inline-diag .sub{margin:0 0 18px;font-size:.92rem;color:#4a5669;line-height:1.6}.inline-diag .row{display:grid;grid-template-columns:1fr 1fr;gap:14px}.inline-diag label,.inline-diag .field-label{display:block;font-size:.9rem;font-weight:700;color:#263951;margin:0 0 7px}.inline-diag input[type=text],.inline-diag input[type=tel]{width:100%;padding:13px 14px;border-radius:4px;border:1px solid #aeb9ca;background:#fff;color:#1A2233;font-size:1rem;font-family:inherit;min-height:46px}.inline-diag input::placeholder{color:#8792a5}.inline-diag input:focus{outline:2px solid var(--blue,#2B5BE3);border-color:var(--blue,#2B5BE3)}.inline-diag .opts{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.inline-diag .opts button{padding:12px 4px;border-radius:4px;border:1px solid #bdc7d8;background:#fff;color:#263951;font-size:.88rem;font-weight:600;font-family:inherit;cursor:pointer;min-height:44px}.inline-diag .opts button[aria-pressed=true]{background:#2454bc;border-color:#2454bc;color:#fff}.inline-diag .group{margin-top:16px}.inline-diag .consent{display:flex;align-items:flex-start;gap:9px;margin-top:16px;font-size:.86rem;line-height:1.6;color:#4a5669;font-weight:400}.inline-diag .consent input{width:20px;height:20px;flex-shrink:0;margin-top:2px;accent-color:#2454bc}.inline-diag .consent a{color:#1e44b8;text-decoration:underline}.inline-diag button[type=submit]{width:100%;margin-top:18px;background:#234780;color:#fff;border:1px solid #234780;border-radius:4px;padding:16px;font-size:1.04rem;font-weight:700;cursor:pointer;font-family:inherit}.inline-diag button[type=submit]:disabled{opacity:.65;cursor:wait}.inline-diag .note{margin-top:12px;font-size:.84rem;color:#526077;line-height:1.55}.inline-diag .apply-msg{margin-top:14px;font-size:.9rem;text-align:center;display:none}.inline-diag .apply-msg.ok{display:block;color:#126435}.inline-diag .apply-msg.err{display:block;color:#b32b28}.inline-diag .apply-fallback{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:14px}.inline-diag .apply-fallback a{display:flex;align-items:center;justify-content:center;font-weight:700;font-size:.9rem;border-radius:4px;padding:12px 8px;text-decoration:none}.inline-diag .apply-fallback .fb-kakao{background:var(--kakao,#FEE500);color:#191600}.inline-diag .apply-fallback .fb-tel{border:1px solid #aeb9ca;color:#263951}@media(max-width:680px){.inline-diag{padding:22px 18px;margin:24px 0}.inline-diag .row{grid-template-columns:1fr;gap:0}.inline-diag .row>div+div{margin-top:16px}.inline-diag .opts{grid-template-columns:1fr}}";
  /* @inline-form:end */
  // 페이지 끝 간편 신청 폼 — 폼이 없는 페이지(33장)에만. 인라인 폼(76장)·홈 폼이 있으면 만들지 않는다(폼은 페이지마다 하나).
  // 설계 docs/superpowers/specs/2026-10-04-apply-everywhere-design.md 3-2. 아래 기존 코드가 #lf-service·#leadForm 을
  // 맨 처음에 찾으므로 그보다 먼저 만든다. 마크업·CSS 는 위 구간(정본 tools/inline_form.py) 그대로다.
  (function pageEndForm() {
    if (document.body?.dataset?.blogCarousel === 'true') return;
    if (document.getElementById('leadForm') || typeof INLINE_FORM_HTML !== 'string' || !document.body) return;
    const footer = document.querySelector('body > footer') || document.querySelector('footer');
    if (!footer || typeof footer.insertAdjacentHTML !== 'function') return;
    // 문의 분야는 그 페이지의 것을 그대로 쓴다 — 예전엔 신청 링크를 /?service=<분야>#apply 로 바꿔 홈 폼에 넘겼다.
    if (!document.body.dataset.service) {
      document.body.dataset.service = /^\/certification(?:\.html)?\/?$/.test(location.pathname) ? 'certification'
        : ['/', '/index.html', '/privacy', '/404'].includes(location.pathname) ? 'general' : 'policy';
    }
    const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' }[c]));
    const h1 = (document.querySelector('h1')?.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 40);
    const path = location.pathname.replace(/\.html$/, '').replace(/\/index$/, '/') || '/';
    const style = document.createElement('style');
    style.setAttribute('data-inline-form', '');
    style.textContent = INLINE_FORM_CSS;
    document.head.appendChild(style);
    footer.insertAdjacentHTML('beforebegin', '<div class="wrap page-end-apply">'
      + INLINE_FORM_HTML.replace('__PATH__ (__LABEL__)', esc(path + ' (' + h1 + ')')) + '</div>');
    const section = document.getElementById('apply');
    if (section) section.setAttribute('data-page-end', '');
    // /sojingong#apply 처럼 폼을 가리켜 들어왔으면, 폼이 이제 생겼으니 그 자리로 간다.
    if (location.hash === '#apply' && section) setTimeout(() => section.scrollIntoView(), 0);
  })();
  const serviceLabels = { general: '종합 상담', policy: '정책자금·사업자대출', marketing: '기업광고·마케팅', startup: '창업컨설팅', certification: '기업인증·연구소', education: '교육·출강' };
  const markedService = document.body?.dataset?.service;
  const pageService = markedService && Object.hasOwn(serviceLabels, markedService) ? markedService
    : /^\/certification(?:\.html)?\/?$/.test(location.pathname) ? 'certification'
    : ['/', '/index.html', '/privacy', '/404'].includes(location.pathname) ? 'general' : 'policy';
  const serviceField = document.getElementById('lf-service');
  if (serviceField) {
    const requested = new URLSearchParams(location.search || '').get('service');
    // 쿼리 > 페이지 기본값(body[data-service]) > 종합 상담. 정책자금 전용 페이지의 폼은
    // 문의 분야도 정책자금으로 열려야 한다(규격 4절). 홈은 data-service="general" 이라 그대로다.
    serviceField.value = requested && Object.hasOwn(serviceLabels, requested) ? requested
      : markedService && Object.hasOwn(serviceLabels, markedService) ? markedService : 'general';
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
  if (!serviceField && document.body?.dataset?.blogCarousel !== 'true') document.querySelectorAll('a[href="/#apply"], a[href="#apply"]').forEach(link => {
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
  // 유입 경로 — 신청과 함께 /api/lead 로 보내 CRM 이 출처(6.홈페이지·7.메타)와 근거(파워링크/자연
  // 유입)를 가린다. 우리 Referrer-Policy(strict-origin-when-cross-origin) 때문에 codedaum 이 받는
  // Referer 헤더에는 https://bmaker.kr/ 까지만 실려, utm·n_media 가 CRM 에 한 번도 닿지 않았다(2026-10-04).
  // 광고로 /jungjingong?n_media=… 에 착지한 뒤 홈으로 옮겨 신청해도 남도록 탭 단위로 기억한다.
  // 광고 파라미터만 남기고 나머지 쿼리·해시는 버린다(분석과 같은 원칙). 연락처는 담지 않는다.
  const AD_PARAMS = ['utm_source', 'utm_medium', 'utm_campaign', 'utm_id', 'utm_term', 'utm_content',
    'n_media', 'n_query', 'n_rank', 'n_ad_group', 'n_ad', 'n_keyword_id', 'n_keyword', 'n_campaign_type', 'napm',
    'gclid', 'gbraid', 'wbraid', 'fbclid'];
  const LANDING_KEY = 'bmaker_landing_url';
  const landingNow = () => {
    if (!location.origin) return '';
    const url = new URL(location.origin + location.pathname);
    const incoming = new URLSearchParams(location.search || '');
    for (const key of AD_PARAMS) if (incoming.has(key)) url.searchParams.set(key, incoming.get(key));
    return url.href;
  };
  const hasAdParams = () => AD_PARAMS.some(key => new URLSearchParams(location.search || '').has(key));
  // 광고를 타고 온 착지는 늘 덮어쓴다(같은 탭에서 다른 광고를 다시 누르면 그 광고가 근거).
  // 광고 없는 페이지 이동은 첫 착지를 덮지 않는다 — 그래야 광고 착지 → 홈 → 신청이 파워링크로 남는다.
  try {
    const store = window.sessionStorage;
    if (store && (hasAdParams() || !store.getItem(LANDING_KEY))) {
      const now = landingNow();
      if (now) store.setItem(LANDING_KEY, now);
    }
  } catch (_) { /* 저장소를 못 쓰면(사생활 모드 등) 신청 시점 주소로 대신한다 */ }
  const landingUrl = () => {
    try { const saved = window.sessionStorage?.getItem(LANDING_KEY); if (saved) return saved; } catch (_) { /* 위와 같다 */ }
    return landingNow();
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
      const intent = link.dataset.consultationService;
      if (serviceField && intent && Object.hasOwn(serviceLabels, intent)) {
        serviceField.value = intent;
        updateEducationHelp();
      }
      ctaLocation = where;
      track('consultation_click', { cta_location: where });
    }
  });
  if (!form) return;
  const message = document.getElementById('applyMsg');
  const button = form.querySelector('[type=submit]');
  // 폼마다 버튼 문구가 다르다(홈·인라인 진단 폼). 하드코딩하면 전송 실패 뒤 문구가 바뀌어버린다.
  const buttonLabel = button?.textContent || '';
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
  const bizButtons = [...document.querySelectorAll('#lf-biztype .biz-opt')];
  bizButtons.forEach(b => b.addEventListener('click', () => {
    const wasSelected = b.getAttribute('aria-pressed') === 'true';
    bizButtons.forEach(t => t.setAttribute('aria-pressed', 'false'));
    if (!wasSelected) b.setAttribute('aria-pressed', 'true');
    if (!started) { started = true; track('consultation_start', { cta_location: ctaLocation }); }
  }));
  form.addEventListener('input', () => {
    phone?.setCustomValidity(''); name?.setCustomValidity('');
    if (completed && message) { completed = false; message.textContent = ''; }
    if (!started) { started = true; track('consultation_start', { cta_location: ctaLocation }); }
  });
  form.addEventListener('invalid', () => track('consultation_validation_error'), true);
  // ── 하단 신청 바 · 본문 중간 버튼 · 그 자리 신청 창 (설계 3-1·3-3·3-4, 규격 4절 2026-10-04 개정) ──
  // 신청 버튼 1개(크게, #234780) + 카톡·전화 작은 아이콘. 신청은 다른 페이지로 보내지 않고 그 페이지 폼을 창으로 연다
  // (홈은 기존처럼 폼으로 스크롤). 히어로 CTA·폼이 보이거나, 창이 열렸거나, 키보드가 올라와 있으면 바를 숨긴다.
  const isHome = ['/', '/index.html'].includes(location.pathname);
  const ICON_KAKAO = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M12 3C6.5 3 2 6.5 2 10.8c0 2.8 1.9 5.2 4.7 6.6l-1 3.6c-.1.3.3.6.6.4l4.2-2.8c.5.1 1 .1 1.5.1 5.5 0 10-3.5 10-7.9S17.5 3 12 3z"/></svg>';
  const ICON_TEL = '<svg viewBox="0 0 24 24" aria-hidden="true"><path fill="currentColor" d="M6.6 10.8a15.1 15.1 0 0 0 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.1.4 2.3.6 3.6.6.6 0 1 .4 1 1V20c0 .6-.4 1-1 1A17 17 0 0 1 3 4c0-.6.4-1 1-1h3.5c.6 0 1 .4 1 1 0 1.2.2 2.4.6 3.6.1.3 0 .7-.2 1L6.6 10.8z"/></svg>';
  const APPLY_CSS = '.sticky-cta.apply-bar{position:fixed;left:0;right:0;bottom:0;z-index:50;display:flex!important;align-items:center;gap:8px;'
    + 'padding:10px 12px calc(10px + env(safe-area-inset-bottom));background:#fff;border-top:1px solid #E1DED6;'
    + 'box-shadow:0 -6px 18px rgba(14,27,51,.08);box-sizing:border-box;grid-template-columns:none!important}'
    + '.sticky-cta.apply-bar[hidden]{display:none!important}'
    + '.sticky-cta.apply-bar .sc-apply{flex:1;display:flex;align-items:center;justify-content:center;min-height:52px;margin:0;'
    + 'max-width:none;width:auto;padding:0 12px;border:0;border-radius:6px;background:#234780;color:#fff;font-weight:700;'
    + 'font-size:1.02rem;text-decoration:none;box-shadow:0 4px 12px rgba(35,71,128,.25)}'
    + '.sticky-cta.apply-bar .sc-icon{flex:none;width:46px;height:46px;min-height:0;margin:0;padding:0;border-radius:50%;'
    + 'display:flex;align-items:center;justify-content:center;box-sizing:border-box;text-decoration:none;box-shadow:none}'
    + '.sticky-cta.apply-bar .sc-kakao{background:#FEE500;color:#191600;border:0}'
    + '.sticky-cta.apply-bar .sc-tel{background:#fff;border:1.5px solid #0E1B33;color:#0E1B33}'
    + '.sticky-cta.apply-bar svg{width:21px;height:21px;display:block}'
    + '@media (max-width:840px){html.has-apply-bar body{padding-bottom:calc(76px + env(safe-area-inset-bottom))}'
    + 'html.has-apply-bar{scroll-padding-bottom:84px}}'
    + '@media (min-width:841px){.sticky-cta.apply-bar{left:auto;right:24px;bottom:24px;width:300px;border:1px solid #E1DED6;'
    + 'border-radius:12px;padding:12px;box-shadow:0 12px 32px rgba(14,27,51,.18)}}'
    + '.mid-apply{margin:28px 0;text-align:center}'
    + '.mid-apply .mid-apply-btn{display:flex;align-items:center;justify-content:center;min-height:52px;border-radius:6px;'
    + 'background:#234780;color:#fff;font-weight:700;font-size:1.02rem;text-decoration:none}'
    + '.mid-apply p{margin:8px 0 0;font-size:.86rem;color:#526077}'
    + '.apply-sheet{position:fixed;inset:0;z-index:80}.apply-sheet[hidden]{display:none}'
    + '.apply-sheet-backdrop{position:absolute;inset:0;background:rgba(14,27,51,.45)}'
    + '.apply-sheet-panel{position:absolute;left:0;right:0;bottom:0;max-height:92svh;overflow:auto;background:var(--paper,#F7F5F0);'
    + 'border-radius:14px 14px 0 0;padding:14px 0 calc(8px + env(safe-area-inset-bottom));box-shadow:0 -10px 30px rgba(14,27,51,.2);'
    + 'overscroll-behavior:contain;box-sizing:border-box}'
    + '.apply-sheet-panel::before{content:"";display:block;width:40px;height:4px;border-radius:2px;background:#C9CED8;margin:0 auto 6px}'
    + '.apply-sheet-close{position:absolute;top:6px;right:8px;z-index:1;border:0;background:none;font:inherit;font-size:.92rem;'
    + 'font-weight:700;color:#263951;padding:10px 12px;cursor:pointer}'
    + '.apply-sheet-body .inline-diag,.apply-sheet-body .apply-section{margin:0;border-top:0;border-bottom:0;padding-top:12px}'
    + '@media (min-width:841px){.apply-sheet-panel{left:50%;right:auto;bottom:auto;top:50%;transform:translate(-50%,-50%);'
    + 'width:min(480px,92vw);max-height:88vh;border-radius:12px;padding-top:18px}.apply-sheet-panel::before{display:none}}'
    + 'html.apply-sheet-open,html.apply-sheet-open body{overflow:hidden}';
  const applyStyle = document.createElement('style');
  applyStyle.setAttribute('data-apply-everywhere', '');
  applyStyle.textContent = APPLY_CSS;
  document.head?.appendChild(applyStyle);

  let sticky = document.querySelector('.sticky-cta');
  if (!sticky && document.body) {
    sticky = document.createElement('div');
    sticky.className = 'sticky-cta';
    sticky.setAttribute('role', 'navigation');
    sticky.setAttribute('aria-label', '무료 진단 신청');
    sticky.hidden = true;
    document.body.appendChild(sticky);
  }
  if (sticky) {
    // 홈의 기존 바는 GA 에 'mobile_sticky' 로 쌓여 왔다 — 집계가 끊기지 않게 그 이름을 이어 쓴다. 나머지는 'sticky_bar'.
    const barWhere = sticky.querySelector('.sc-apply')?.dataset.ctaLocation || 'sticky_bar';
    sticky.classList.add('apply-bar');
    sticky.innerHTML = '<a class="sc-apply" href="#apply" data-cta-location="' + barWhere + '">무료 진단 신청</a>'
      + '<a class="sc-icon sc-kakao" href="https://pf.kakao.com/_GKuxfn/chat" target="_blank" rel="noopener" '
      + 'aria-label="카카오톡 상담" data-cta-location="sticky_bar">' + ICON_KAKAO + '</a>'
      + '<a class="sc-icon sc-tel" href="tel:1666-2425" aria-label="전화 상담 1666-2425" data-cta-location="sticky_bar">' + ICON_TEL + '</a>';
    document.documentElement.classList.add('has-apply-bar');
  }
  // 헤더 버튼은 히어로 CTA 가 보이는 동안 숨긴다 — 첫 화면 CTA 를 하나로 유지한다(규격 4절).
  // 모바일(≤840px)에서는 CSS 로 이미 감춰져 있고 펼침 메뉴의 .nav-book 이 그 자리를 대신한다.
  const headerCta = document.querySelector('.nav-cta-book');
  const heroCta = document.getElementById('heroCta');
  function inViewport(element) {
    if (!element || typeof element.getBoundingClientRect !== 'function') return false;
    const r = element.getBoundingClientRect();
    return r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < window.innerHeight;
  }
  // 키보드: 입력칸에 초점이 있거나(체크박스 제외), iOS 처럼 초점 없이 키보드가 남아 화면이 줄어든 경우.
  // 키보드 위로 바가 떠서 입력칸·제출 버튼을 가리지 않게 한다.
  function keyboardUp() {
    const a = document.activeElement;
    if (a && typeof a.matches === 'function'
      && a.matches('input:not([type=checkbox]):not([type=radio]):not([type=hidden]):not([type=submit]), textarea, select')) return true;
    const vv = window.visualViewport;
    return !!(vv && window.innerHeight && vv.height < window.innerHeight * 0.75);
  }
  let sheetIsOpen = false;
  function updateSticky() {
    const heroVisible = inViewport(heroCta);
    if (sticky) sticky.hidden = heroVisible || inViewport(form) || form.contains(document.activeElement) || sheetIsOpen || keyboardUp();
    if (headerCta) headerCta.hidden = heroVisible;
  }
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(updateSticky, { threshold: 0 });
    observer.observe(form);
    if (heroCta) observer.observe(heroCta);
  }
  if (typeof window.addEventListener === 'function') {
    for (const event of ['load', 'resize', 'pageshow', 'scroll']) {
      window.addEventListener(event, updateSticky, { passive: true });
    }
  }
  window.visualViewport?.addEventListener?.('resize', updateSticky);
  document.addEventListener('focusin', updateSticky);
  document.addEventListener('focusout', () => setTimeout(updateSticky, 0));
  updateSticky();

  // 그 자리 신청 창 — 폼은 페이지마다 하나라, 창을 열면 그 폼(#apply)을 창 안으로 옮기고 닫으면 제자리로 돌려놓는다.
  // 그래서 입력하던 값·완료 상태가 그대로 따라가고, 제출 코드(/api/lead·요청 ID·landing_url·generate_lead)는 그대로다.
  const applySection = document.getElementById('apply');
  const useSheet = !isHome && !!applySection && applySection.contains(form) && !!document.body;
  let sheet = null, sheetBody = null, sheetPanel = null, placeholder = null, opener = null, savedScroll = 0, pushedState = false;
  // 닫을 때 보낸 history.back() 의 popstate 가 아직 안 왔는데 다시 열면, 늦게 온 popstate 가 새 창을 닫아 버린다.
  // 그 신호가 올 때까지 다시 열기를 미뤘다가 이어서 연다(닫기를 잘못 누르고 곧바로 다시 누르는 경우).
  let backPending = false, reopen = null;
  function focusables() {
    return [...sheetPanel.querySelectorAll('button, [href], input:not([type=hidden]):not([tabindex="-1"]), select, textarea')]
      .filter(el => !el.disabled && el.getAttribute('aria-hidden') !== 'true' && el.offsetParent !== null);
  }
  // 키보드가 올라오면(iOS 는 화면 아래가 키보드에 덮인다) 창 아래끝을 키보드 바로 위로 올리고 높이를 그만큼 줄인다.
  function fitToViewport() {
    const vv = window.visualViewport;
    if (!sheetPanel || !vv) return;
    const covered = Math.max(0, Math.round(window.innerHeight - vv.height - (vv.offsetTop || 0)));
    const phone = window.innerWidth <= 840;
    sheetPanel.style.bottom = phone && covered > 40 ? covered + 'px' : '';
    sheetPanel.style.maxHeight = Math.max(240, Math.floor(vv.height - 12)) + 'px';
  }
  function openSheet(where, service) {
    if (!useSheet || sheetIsOpen) return;
    if (backPending) { reopen = [where, service]; return; }
    if (!sheet) {
      sheet = document.createElement('div');
      sheet.className = 'apply-sheet';
      sheet.hidden = true;
      sheet.innerHTML = '<div class="apply-sheet-backdrop" data-close></div>'
        + '<div class="apply-sheet-panel" role="dialog" aria-modal="true" aria-labelledby="inline-diag-title">'
        + '<button type="button" class="apply-sheet-close" data-close>닫기</button><div class="apply-sheet-body"></div></div>';
      document.body.appendChild(sheet);
      sheetPanel = sheet.querySelector('.apply-sheet-panel');
      sheetBody = sheet.querySelector('.apply-sheet-body');
      sheet.addEventListener('click', e => { if (e.target.closest('[data-close]')) closeSheet(false); });
      sheet.addEventListener('keydown', e => {
        if (e.key === 'Escape') { e.preventDefault(); closeSheet(false); return; }
        if (e.key !== 'Tab') return;
        const items = focusables();
        if (!items.length) return;
        const first = items[0], last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      });
      sheet.addEventListener('focusin', e => {
        // 키보드가 올라온 뒤 그 칸이 보이게. 그 사이 창이 닫혔으면(폼이 페이지 끝으로 돌아갔으면) 페이지를 끌고 가지 않는다.
        if (e.target.matches?.('input, textarea, select')) setTimeout(() => {
          if (sheetIsOpen && sheet.contains(e.target)) e.target.scrollIntoView?.({ block: 'center' });
        }, 250);
      });
    }
    if (service && serviceField && Object.hasOwn(serviceLabels, service)) {
      serviceField.value = service;
      updateEducationHelp();
    }
    opener = document.activeElement;
    savedScroll = window.scrollY || 0;
    placeholder = document.createElement('div');
    placeholder.className = 'apply-placeholder';
    applySection.parentNode.insertBefore(placeholder, applySection);
    sheetBody.appendChild(applySection);
    sheet.hidden = false;
    sheetIsOpen = true;
    document.documentElement.classList.add('apply-sheet-open');
    fitToViewport();
    ctaLocation = where;
    track('apply_sheet_open', { cta_location: where });
    // 휴대폰 뒤로가기로 페이지를 떠나지 않고 창만 닫히게 한다.
    try {
      // 창 때문에 생긴 기록을 되돌릴 때 브라우저가 스크롤 위치를 엉뚱하게 복원하지 않게 한다(닫은 뒤 직접 되돌린다).
      if ('scrollRestoration' in history) history.scrollRestoration = 'manual';
      history.pushState({ applySheet: true }, ''); pushedState = true;
    } catch (_) { pushedState = false; }
    updateSticky();
    setTimeout(() => { const items = focusables(); (items.find(el => el !== sheetPanel.querySelector('.apply-sheet-close')) || items[0])?.focus(); }, 0);
  }
  function closeSheet(fromHistory) {
    if (!sheetIsOpen) return;
    sheetIsOpen = false;
    placeholder.parentNode.insertBefore(applySection, placeholder);
    placeholder.remove();
    sheet.hidden = true;
    document.documentElement.classList.remove('apply-sheet-open');
    window.scrollTo(0, savedScroll);
    if (!fromHistory && pushedState) {
      pushedState = false;
      try {
        backPending = true;
        history.back();
        // popstate 가 끝내 안 오는 환경에서도 다시 열 수 있게
        setTimeout(() => { if (backPending) { backPending = false; const r = reopen; reopen = null; if (r) openSheet(...r); } }, 600);
      } catch (_) { backPending = false; /* 주소 기록을 못 되돌려도 창은 닫혔다 */ }
    }
    pushedState = false;
    updateSticky();
    try { opener?.focus?.({ preventScroll: true }); } catch (_) { /* 연 버튼이 없어졌으면 그대로 둔다 */ }
  }
  if (typeof window.addEventListener === 'function') {
    window.addEventListener('popstate', () => {
      if (backPending) {
        backPending = false;
        window.scrollTo(0, savedScroll);
        const r = reopen; reopen = null;
        if (r) openSheet(...r);
        return;
      }
      if (sheetIsOpen) { pushedState = false; closeSheet(true); }
    });
  }
  window.visualViewport?.addEventListener?.('resize', fitToViewport);
  // 신청 버튼은 다른 페이지로 보내지 않는다 — 바·중간 버튼·다른 페이지의 #apply 링크는 이 창을 연다.
  // 링크 href 는 그대로 둔다(자바스크립트가 없으면 예전처럼 홈 폼으로 간다). 같은 페이지 #apply 앵커는 지금처럼 스크롤.
  document.addEventListener('click', e => {
    if (!useSheet) return;
    const link = e.target instanceof Element ? e.target.closest('a') : null;
    if (!link || link.closest('.apply-sheet')) return;
    const href = link.getAttribute('href') || '';
    if (!href.endsWith('#apply')) return;
    let url;
    try { url = new URL(href, location.href); } catch (_) { return; }
    const norm = p => p.replace(/\.html$/, '').replace(/\/index$/, '/');
    const ours = link.closest('.sticky-cta, .mid-apply');
    if (!ours && norm(url.pathname) === norm(location.pathname)) return;
    e.preventDefault();
    openSheet(link.dataset.ctaLocation || (link.closest('header') ? 'header' : 'content'),
      url.searchParams.get('service') || link.dataset.consultationService || '');
  }, true);

  // 본문 중간 신청 버튼 — 폼 없던 페이지(페이지 끝 폼)가 휴대폰 5화면을 넘을 때만, 문서 40% 지점 h2 앞에 한 번.
  if (applySection?.hasAttribute('data-page-end') && document.documentElement.scrollHeight > window.innerHeight * 5) {
    const target = document.documentElement.scrollHeight * 0.4;
    const heads = [...document.querySelectorAll('h2')].filter(h => !h.closest('#apply, footer, header, details, table, .sticky-cta, .apply-sheet'));
    let best = null, gap = Infinity;
    for (const h of heads) {
      const d = Math.abs(h.getBoundingClientRect().top + window.scrollY - target);
      if (d < gap) { gap = d; best = h; }
    }
    if (best) best.insertAdjacentHTML('beforebegin', '<div class="mid-apply">'
      + '<a class="mid-apply-btn" href="#apply" data-cta-location="mid_content">무료 진단 신청</a>'
      + '<p>진단은 무료입니다.</p></div>');
  }
  function failure(uncertain, crashed) {
    if (!message) return;
    message.className = 'apply-msg err';
    message.textContent = crashed
      ? '전송에 실패했습니다. 1666-2425 또는 카카오톡으로 연락 주세요.'
      : uncertain
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
  // 제출 처리 전체를 감싼다. 2026-09-28 옛 캐시 JS 가 없는 칸(lf-biz)을 읽다 멈춰 전송도 안내도
  // 없이 조용히 실패했다 — 어떤 오류든 연락처 안내를 띄우고 form_error 로 숫자를 남긴다.
  form.addEventListener('submit', async e => {
    e.preventDefault();
    try {
      await submitLead();
    } catch (error) {
      busy = false; form.removeAttribute('aria-busy');
      if (button) { button.disabled = false; button.textContent = buttonLabel; }
      try { track('form_error', { error_message: String(error?.message || error).slice(0, 100) }); } catch (_) { /* 계측 실패가 안내를 막지 않게 */ }
      failure(false, true);
    }
  });
  async function submitLead() {
    if (busy || completed) return;
    // 성함·연락처는 없으면 보낼 수 없다 — 조용히 넘기지 말고 오류로 올려 안내·form_error 로 보낸다.
    if (!name || !phone) throw new Error('필수 칸 없음: ' + (name ? 'lf-phone' : 'lf-name'));
    name.setCustomValidity(name.value.trim() ? '' : '성함을 입력해 주세요.');
    const digits = phone.value.replace(/[\s()-]/g, '');
    phone.setCustomValidity(/^0\d{8,10}$/.test(digits) ? '' : '연락 가능한 전화번호를 확인해 주세요.');
    if (!form.reportValidity()) return;
    // 인라인 진단 폼(자금·재단 상세)에는 업종·문의 칸이 없다. 없는 칸은 빈 값으로 둔다.
    const fieldValue = id => document.getElementById(id)?.value.trim() || '';
    const industry = fieldValue('lf-biz');
    const memo = fieldValue('lf-memo');
    // 사업자 형태와 유입 페이지는 /api/lead 가 화이트리스트로 거르는 최상위 키로는 전달되지
    // 않는다(2026-09-28 메일 템플릿 렌더로 확인). 업종·통화시간과 같이 answers_text 와
    // diagnosis 에 실어야 알림 메일 본문에 찍힌다.
    const bizType = document.querySelector('#lf-biztype .biz-opt[aria-pressed="true"]')?.textContent.trim() || '';
    const leadPage = fieldValue('lf-page');
    const preferredTime = selectedTime || '아무 때나';
    // 최상위 source 키는 /api/lead 가 화이트리스트로 걸러 알림 메일에 안 실린다
    // (2026-09-28 메일 템플릿 렌더로 확인). 어느 폼에서 온 신청인지 남기려면 answers_text 로 보낸다.
    const source = leadPage ? 'bmaker.kr 자금·재단 인라인 진단 폼'
                            : 'bmaker.kr 홈페이지 간편신청';
    const serviceKey = selectedService();
    const serviceLabel = serviceLabels[serviceKey];
    const payload = {
      kind: 'consult', service: serviceKey === 'policy' ? 'pfm' : serviceKey, service_name: serviceLabel, delivery_required: true,
      consultation_service: serviceKey,
      name: name.value.trim(), phone: digits,
      preferred_time: preferredTime,
      answers_text: ['[문의 분야] ' + serviceLabel]
        .concat(bizType ? ['[사업자 형태] ' + bizType] : [])
        .concat(['[예약] 통화 희망: ' + preferredTime, '업종: ' + (industry || '미입력'), '문의: ' + (memo || '미입력')])
        .concat(leadPage ? ['[유입] ' + leadPage] : [])
        .concat(['[신청 경로] ' + source]).join(' · '),
      diagnosis: Object.assign({ '문의 분야': serviceLabel },
        bizType ? { '사업자 형태': bizType } : null,
        { '통화 희망 시간': preferredTime, industry, memo },
        leadPage ? { '유입 페이지': leadPage } : null),
      consent_privacy: document.getElementById('lf-consent')?.checked === true,
      consent_marketing: false, consent_version: 'v1.1-2026-09-07-service-selection',
      website: document.getElementById('lf-website')?.value || '',
      source: source,
      landing_url: landingUrl()
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
      message.textContent = '신청이 접수됐습니다. 평일 09:00~18:00 중 정하신 시간대에 전화드리겠습니다. 급한 문의는 1666-2425로 연락해 주세요.';
      form.reset(); selectedTime = '';
      [...timeButtons, ...bizButtons].forEach(b => b.setAttribute('aria-pressed', 'false'));
      track('generate_lead', { cta_location: ctaLocation, method: 'consultation_form', service_category: serviceKey });
      message.focus();
    } catch (error) {
      const reason = error.name === 'AbortError' ? 'timeout' : error.message === 'delivery_failed' ? 'delivery_failed' : 'network_or_response';
      track('consultation_error', { reason }); failure(reason !== 'delivery_failed');
    } finally {
      clearTimeout(timeout); busy = false; form.removeAttribute('aria-busy'); button.disabled = false;
      button.textContent = completed ? '신청 접수 완료' : buttonLabel;
    }
  }
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
