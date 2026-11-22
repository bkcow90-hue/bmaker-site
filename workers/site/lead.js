// POST /api/lead
//
// Receives every lead submission from the six self-diagnosis pages and emails it
// to the operator via Resend. Replaces the n8n webhooks (lead-intake-pfm /
// consult-request-pfm), which stopped accepting traffic once the monthly
// execution quota ran out.
//
// The pages gate their success UI on `{ok:true}` in the response, so a visitor
// only sees their diagnosis report if this endpoint says ok. Mail delivery is
// therefore never allowed to fail the request: a send failure is retried once,
// logged, and the visitor still gets their report.

// Overridable so the switch to a verified bmaker.kr sender is a config change
// rather than a redeploy. Until the domain verifies, Resend's shared
// onboarding sender only delivers to the Resend account's own address, so
// LEAD_TO is set to that address in the meantime.
const DEFAULT_RECIPIENT = 'bmaker@bmaker.kr';
const DEFAULT_FROM = 'onboarding@resend.dev';
const RESEND_ENDPOINT = 'https://api.resend.com/emails';

// The diagnosis pages are same-origin with this function, so CORS does not
// apply to them. The marketing site at bmaker.kr posts here cross-origin and
// does need it.
//
// www is on this list purely as insurance. Cloudflare 301s www -> apex, so a
// real visitor's form always runs on the apex origin and the www entry is
// never used. It is here so that a broken or removed redirect degrades into
// "the form still works" instead of "leads vanish silently".
//
// DO NOT drop the 301 because this list exists. Serving www without a redirect
// creates duplicate-content pages for search engines; the redirect is still the
// correct fix for that, and this list does not replace it.
const ALLOWED_ORIGINS = ['https://bmaker.kr', 'https://www.bmaker.kr'];

// Echoes the caller's origin when it is on the list, so a browser's origin
// match succeeds for either host. Vary: Origin keeps a cache from handing the
// apex response to a www caller (or the reverse).
function corsHeaders(request) {
  const origin = request?.headers.get('origin') || '';
  return {
    'Access-Control-Allow-Origin': ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0],
    Vary: 'Origin',
  };
}

export async function onRequestPost({ request, env }) {
  let payload;
  try {
    // Content type varies by page: the five older diagnosis pages post
    // text/plain, /diagnosis/ posts application/json. Reading the body as text
    // and parsing it by hand accepts both, where request.json() would reject
    // the text/plain ones.
    payload = JSON.parse(await request.text());
  } catch {
    return json(request, { ok: false, error: 'invalid body' }, 400);
  }

  // Honeypot: a real visitor never sees the `website` field, so anything in it
  // is a bot. Answer ok so the bot learns nothing, but send no mail.
  if (str(payload.website)) {
    console.log('lead: honeypot tripped, dropped');
    return json(request, { ok: true });
  }

  const name = str(payload.name);
  const phone = str(payload.phone);
  if (!name || !phone) {
    return json(request, { ok: false, error: 'name and phone are required' }, 400);
  }

  const lead = normalize(payload, request);
  // Reservations require email-provider acceptance; legacy report clients remain compatible.
  const requireDelivery = payload.delivery_required === true;
  if (requireDelivery && (payload.consent_privacy !== true || !/^0\d{8,10}$/.test(phone.replace(/[\s()-]/g, '')))) {
    return json(request, { ok: false, error: 'invalid contact or consent' }, 400);
  }

  // CRM direct delivery goes first, so the mail can say whether it worked: when
  // it did not, the subject starts with '⚠️CRM 미등록' and the operator knows
  // from the inbox alone that this lead has to be entered by hand. It is capped
  // at CRM_BUDGET_MS so the visitor's request still fits the page's 22s timeout
  // alongside the mail (2 x 8s), and it can never fail the request.
  lead.crm = await sendToCrm(env, lead, payload).catch((err) => {
    console.error('lead: crm direct delivery threw', String(err));
    return { registered: false, reason: '전송 중 오류: ' + String(err).slice(0, 100) };
  });

  // str() trims: a secret uploaded through a shell pipe can carry a trailing
  // newline, which Resend rejects as an invalid key.
  if (!str(env.RESEND_API_KEY)) {
    console.error('lead: RESEND_API_KEY is not set - lead not delivered');
    return json(request, { ok: !requireDelivery, delivery: 'failed' }, requireDelivery ? 503 : 200);
  }

  // The guidebook mail to the visitor runs alongside the operator mail so the
  // request stays inside the page's 22s budget. Its failure never fails the
  // lead: the page just says the guidebook will be resent by phone.
  const [attempts, guidebook] = await Promise.all([
    sendWithRetry(env, lead),
    wantsGuidebook(payload, lead, env) ? sendGuidebook(env, lead) : Promise.resolve(undefined),
  ]);
  if (!attempts.some((a) => a.ok)) {
    // Last resort: the lead is at least in the log stream. Never fail the
    // visitor over it.
    console.error('lead: delivery failed after retry');
    return json(request, { ok: !requireDelivery, delivery: 'failed' }, requireDelivery ? 503 : 200);
  }

  // Acceptance by the provider does not guarantee inbox delivery.
  return json(request, { ok: true, delivery: 'accepted', ...(guidebook ? { guidebook } : {}) });
}

// Preflight. Only reached once a page posts application/json cross-origin;
// same-origin posts and text/plain posts never trigger it.
export async function onRequestOptions({ request }) {
  return new Response(null, {
    status: 204,
    headers: {
      ...corsHeaders(request),
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
      'Access-Control-Max-Age': '86400',
    },
  });
}

function normalize(payload, request) {
  const kind = str(payload.kind) === 'consult' ? 'consult'
    : payload.email_request ? 'email'
      : 'lead';

  return {
    kind,
    requestId: /^[a-f0-9-]{36}$/.test(str(payload.request_id)) ? str(payload.request_id) : '',
    service: str(payload.service),
    serviceName: str(payload.service_name) || str(payload.service) || '미상',
    name: str(payload.name),
    phone: str(payload.phone),
    email: str(payload.email),
    answersText: str(payload.answers_text),
    answers: isObject(payload.diagnosis) ? payload.diagnosis : {},
    result: str(payload.diagnosis_result),
    consentPrivacy: payload.consent_privacy === true,
    consentMarketing: payload.consent_marketing === true,
    consentVersion: str(payload.consent_version),
    submittedAt: payload.delivery_required === true && /^\d{4}-\d{2}-\d{2}T/.test(str(payload.submitted_at)) && Number.isFinite(Date.parse(payload.submitted_at)) ? nowKst(new Date(payload.submitted_at)) : nowKst(),
    referer: request.headers.get('referer') || '',
    // The page the visitor landed on, query string included. bmaker.kr sends it
    // in the body because its Referrer-Policy (strict-origin-when-cross-origin)
    // strips the path and query from the cross-origin Referer header - so the
    // header alone never carries utm_source / fbclid, and the CRM cannot tell a
    // Meta ad lead from a homepage lead. Only bmaker.kr / codedaum URLs are kept.
    landingUrl: landingUrlOf(payload.landing_url),
    source: str(payload.source),
    ip: request.headers.get('cf-connecting-ip') || '',
    userAgent: request.headers.get('user-agent') || '',
  };
}

async function sendWithRetry(env, lead) {
  const to = str(env.LEAD_TO) || DEFAULT_RECIPIENT;
  const from = str(env.LEAD_FROM) || DEFAULT_FROM;

  const attempts = [];
  for (let attempt = 1; attempt <= 2; attempt++) {
    try {
      const res = await fetch(RESEND_ENDPOINT, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${str(env.RESEND_API_KEY)}`,
          'Content-Type': 'application/json',
          ...(lead.requestId ? { 'Idempotency-Key': `bmaker-${lead.requestId}` } : {}),
        },
        signal: AbortSignal.timeout(8000),
        body: JSON.stringify({
          from,
          to: [to],
          reply_to: lead.email || undefined,
          subject: subjectOf(lead),
          text: textBody(lead),
        }),
      });
      const text = await res.text();
      attempts.push({ attempt, ok: res.ok, status: res.status, body: text.slice(0, 500) });
      if (res.ok) return attempts;
      console.error(`lead: resend attempt ${attempt} returned ${res.status}`, text);
    } catch (err) {
      attempts.push({ attempt, ok: false, status: 0, body: String(err).slice(0, 500) });
      console.error(`lead: resend attempt ${attempt} threw`, String(err));
    }
  }
  return attempts;
}

// ── Guidebook mail to the visitor ───────────────────────────────────────────
//
// bmaker.kr's home form has an optional e-mail field (2026-11-13): when it is
// filled, the visitor gets a link to the self-check guidebook PDF (env
// GUIDEBOOK_URL, a bmaker.kr address; unset = feature off). One attempt,
// short timeout, idempotent per request id so a retried submit does not send a
// second copy. The mail is informational (what they asked for), no offers.
// CRM 의 '요청 가이드북' 칸에 들어가는 이름. 가이드북이 늘면 폼이 고른 이름을 여기로 넘긴다.
const GUIDEBOOK_NAME = '정책자금 자가진단 가이드북';
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function wantsGuidebook(payload, lead, env) {
  // No GUIDEBOOK_URL configured = the PDF is not uploaded yet: send nothing,
  // and the page tells the visitor it will be sent after the call.
  return /^https:\/\/bmaker\.kr\//.test(str(env.GUIDEBOOK_URL)) && payload.guidebook_request === true && lead.consentPrivacy && EMAIL_RE.test(lead.email) && lead.email.length <= 120;
}

async function sendGuidebook(env, lead) {
  const from = str(env.GUIDE_FROM) || str(env.LEAD_FROM) || DEFAULT_FROM;
  try {
    const res = await fetch(RESEND_ENDPOINT, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${str(env.RESEND_API_KEY)}`,
        'Content-Type': 'application/json',
        ...(lead.requestId ? { 'Idempotency-Key': `bmaker-guide-${lead.requestId}` } : {}),
      },
      signal: AbortSignal.timeout(7000),
      body: JSON.stringify({
        from,
        to: [lead.email],
        reply_to: str(env.LEAD_TO) || DEFAULT_RECIPIENT,
        subject: '[비즈니스 메이커] 요청하신 정책자금 자가진단 가이드북',
        text: guidebookText(lead, str(env.GUIDEBOOK_URL)),
      }),
    });
    if (res.ok) return 'sent';
    console.error('lead: guidebook mail returned', res.status, (await res.text()).slice(0, 300));
  } catch (err) {
    console.error('lead: guidebook mail threw', String(err));
  }
  return 'failed';
}

function guidebookText(lead, url) {
  return [
    `${lead.name}님, 비즈니스 메이커입니다.`,
    '',
    '상담 신청과 함께 요청하신 「정책자금 자가진단 가이드북」을 보내드립니다.',
    `PDF 받기: ${url}`,
    '',
    '상담 전화를 드리기 전에 한 번 훑어보시면, 통화 때 어떤 이야기가 오갈지 미리 감을 잡으실 수 있습니다.',
    '체크가 안 되는 항목이 있어도 괜찮습니다. 그 부분은 통화에서 같이 보겠습니다.',
    '',
    '비즈니스 메이커 · 1666-2425 · https://bmaker.kr',
    '이 메일은 상담 신청 폼에서 가이드북 발송을 요청하신 분께만 한 번 보내는 안내 메일입니다.',
  ].join('\n');
}

// ── CRM direct delivery ─────────────────────────────────────────────────────
//
// POST the lead straight to the CRM's /api/auto-intake, as the 'mail-homepage'
// source, with the same field labels the CRM's mail parser reads out of the
// notification mail. Same source kind + same labels means the CRM applies the
// exact same mapping and source rule (utm / fbclid -> 7.메타, else 6.홈페이지)
// whichever path a lead arrives by.
//
// Dedupe: with a request id both paths use 'lead:<id>', which the CRM claims
// once - the second arrival is recorded as a duplicate and does nothing (no
// second lead, no second inbox badge). Without one (older diagnosis pages) the
// keys differ, and the CRM's 24h same-phone cooldown makes the second arrival a
// duplicate instead.
//
// The token lives only in the Pages secret CRM_AUTO_INTAKE_TOKEN. Nothing here
// is ever sent to the browser.
const DEFAULT_CRM_BASE = 'https://policy-fund-crm.vercel.app';
// Whole budget for the CRM call, retry included. The CRM answers in ~1s; the
// rest of the 22s page timeout belongs to the mail (2 x 8s).
const CRM_BUDGET_MS = 5000;

// Returns { registered, reason }. registered = the CRM holds this lead now
// (newly registered, a returning customer, or one it already had). Anything
// else - no token, refused, 5xx, timeout, or accepted but failed (bad phone,
// missing source) - is not registered and gets the warning subject.
async function sendToCrm(env, lead, payload) {
  const token = str(env.CRM_AUTO_INTAKE_TOKEN);
  if (!token) {
    console.error('lead: CRM_AUTO_INTAKE_TOKEN is not set - crm direct delivery skipped');
    return { registered: false, reason: 'CRM 토큰이 설정되지 않아 보내지 않았습니다' };
  }
  const base = (str(env.CRM_BASE_URL) || DEFAULT_CRM_BASE).replace(/\/+$/, '');
  const body = JSON.stringify({ sourceKind: 'mail-homepage', mode: 'normal', items: [crmItem(lead, payload)] });
  const deadline = Date.now() + CRM_BUDGET_MS;

  let reason = '';
  for (let attempt = 1; attempt <= 2; attempt++) {
    const left = deadline - Date.now();
    if (left < 500) break;
    try {
      const res = await fetch(`${base}/api/auto-intake`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(left),
        body,
      });
      const text = await res.text();
      if (res.ok) return crmOutcome(text);
      console.error(`lead: crm attempt ${attempt} returned ${res.status}`, text.slice(0, 300));
      reason = `CRM 이 거절했습니다(HTTP ${res.status})`;
      // 4xx will not get better on a retry (bad token, bad shape).
      if (res.status < 500) break;
    } catch (err) {
      console.error(`lead: crm attempt ${attempt} threw`, String(err));
      reason = err?.name === 'TimeoutError' || err?.name === 'AbortError'
        // The CRM may still have finished it - say so, so nobody enters it twice.
        ? `CRM 응답이 ${CRM_BUDGET_MS / 1000}초 안에 오지 않았습니다(등록됐을 수도 있으니 CRM 에서 전화번호로 먼저 검색)`
        : 'CRM 에 연결하지 못했습니다';
    }
  }
  return { registered: false, reason: reason || 'CRM 에 연결하지 못했습니다' };
}

function crmOutcome(text) {
  let b = {};
  try { b = JSON.parse(text); } catch { /* fall through: not registered */ }
  const n = (k) => Number(b?.[k]) || 0;
  if (b?.ok === true && n('inserted') + n('reinflow') + n('duplicate') > 0) {
    const what = n('inserted') ? '신규 등록' : n('reinflow') ? '재유입' : '이미 있는 고객(중복)';
    return { registered: true, reason: what };
  }
  console.error('lead: crm accepted but did not register', text.slice(0, 300));
  return { registered: false, reason: 'CRM 이 받았지만 등록하지 못했습니다(CRM 설정 → 자동 입력 기록에서 사유 확인)' };
}

function crmItem(lead, payload) {
  const fields = {};
  const put = (label, value) => { if (str(value)) fields[label] = str(value); };

  put('구분', { consult: '상담 신청', email: '리포트 메일 요청', lead: '진단 제출' }[lead.kind]);
  put('서비스', lead.service ? `${lead.serviceName} (${lead.service})` : lead.serviceName);
  put('이름', lead.name);
  put('전화', formatPhone(lead.phone));
  put('이메일', lead.email);
  // The structured answers, under the labels the mail's detail lines carry.
  for (const [key, value] of Object.entries(lead.answers)) {
    if (key === 'diagnosis_result') continue;
    put(key === '유입 페이지' ? '유입' : key, value);
  }
  put('진단 결과', lead.result);
  // 가이드북 요청(홈 폼의 가이드북 이메일 칸) — CRM 이 고객 항목 '가이드북 요청'(예) · '요청 가이드북'(이름)에 넣어
  // 가이드북을 보내야 할 고객만 거를 수 있게 한다(2026-11-23). 요청하지 않은 신청에는 싣지 않는다(CRM 이 '아니오'로 적는다).
  if (payload?.guidebook_request === true) {
    put('가이드북 요청', '예');
    put('요청 가이드북', GUIDEBOOK_NAME);
  }
  put('신청 경로', lead.source);
  // Korean 12h form with '(KST)': the CRM's parser pins it to +09:00.
  put('제출 시각', lead.submittedAt);
  put('유입 페이지', lead.landingUrl || lead.referer);
  put('개인정보 동의', lead.consentPrivacy ? `동의 (${lead.consentVersion || '버전 미상'})` : '미동의');
  put('광고성 수신 동의', lead.consentMarketing ? '동의' : '미동의');

  return {
    dedupeKey: lead.requestId
      ? `lead:${lead.requestId}`
      : `direct:${lead.phone.replace(/\D/g, '')}:${lead.submittedAt}`,
    fields,
    timeZone: null,
    clientIp: lead.ip,
    userAgent: lead.userAgent,
    raw: {
      via: 'codedaum /api/lead (direct)',
      requestId: lead.requestId,
      referer: lead.referer,
      landingUrl: lead.landingUrl,
      answersText: lead.answersText,
      answers: lead.answers,
      payloadKeys: Object.keys(payload || {}),
    },
  };
}

// Keep only an absolute http(s) URL on our own sites. Anything else is dropped
// rather than trusted - it decides which ad gets credit for the lead.
function landingUrlOf(value) {
  const raw = str(value);
  if (!raw || raw.length > 2000) return '';
  try {
    const u = new URL(raw);
    if (!/^https?:$/.test(u.protocol)) return '';
    if (!/(^|\.)bmaker\.kr$|(^|\.)codedaum\.pages\.dev$/.test(u.hostname)) return '';
    return u.toString();
  } catch {
    return '';
  }
}

function subjectOf(lead) {
  const tag = lead.kind === 'consult' ? '상담신청' : '리드';
  // Only a lead the CRM confirmed is left unmarked. lead.crm is absent only in
  // code paths that never tried (none today) - treat that as unconfirmed too.
  const warn = lead.crm?.registered ? '' : '⚠️CRM 미등록 ';
  return `${warn}[${tag}] ${lead.serviceName} - ${lead.name} ${formatPhone(lead.phone)}`;
}

function textBody(lead) {
  const lines = [];
  const add = (label, value) => { if (value) lines.push(`${label}: ${value}`); };

  if (lead.crm && !lead.crm.registered) {
    lines.push('⚠️ CRM 에 자동 등록되지 않았습니다 — 손으로 넣어 주세요.');
    lines.push(`   이유: ${lead.crm.reason}`);
    lines.push('');
  }
  add('구분', { consult: '상담 신청', email: '리포트 메일 요청', lead: '진단 제출' }[lead.kind]);
  add('서비스', lead.service ? `${lead.serviceName} (${lead.service})` : lead.serviceName);
  add('CRM 등록', lead.crm?.registered ? `됨 (${lead.crm.reason})` : '안 됨');
  lines.push('');

  add('이름', lead.name);
  add('전화', formatPhone(lead.phone));
  add('이메일', lead.email);
  lines.push('');

  if (lead.answersText) {
    lines.push('[진단 답변]');
    lines.push(lead.answersText);
    lines.push('');
  }

  // The inline forms put their page path under '유입 페이지' in the answers.
  // Printed under that label it shadowed the real landing URL in the CRM mail
  // parser (first label wins), so it is printed as '유입' - the same label the
  // summary line already uses for it.
  const detail = Object.entries(lead.answers)
    .filter(([key, value]) => key !== 'diagnosis_result' && str(value))
    .map(([key, value]) => `  - ${key === '유입 페이지' ? '유입' : key}: ${value}`);
  if (detail.length) {
    lines.push('[진단 답변 상세]');
    lines.push(...detail);
    lines.push('');
  }

  add('진단 결과', lead.result);
  if (lead.result) lines.push('');

  lines.push('[제출 정보]');
  add('  제출 시각', lead.submittedAt);
  add('  유입 페이지', lead.landingUrl || lead.referer);
  // Lets the CRM recognise the mail copy of a lead it already got directly:
  // both paths key the lead as 'lead:<요청 ID>', so it is registered once.
  add('  요청 ID', lead.requestId);
  add('  개인정보 동의', lead.consentPrivacy ? `동의 (${lead.consentVersion || '버전 미상'})` : '미동의');
  add('  광고성 수신 동의', lead.consentMarketing ? '동의' : '미동의');
  add('  IP', lead.ip);
  add('  User-Agent', lead.userAgent);

  return lines.join('\n');
}

function formatPhone(digits) {
  const d = digits.replace(/\D/g, '');
  if (d.length === 11) return `${d.slice(0, 3)}-${d.slice(3, 7)}-${d.slice(7)}`;
  if (d.length === 10) return `${d.slice(0, 3)}-${d.slice(3, 6)}-${d.slice(6)}`;
  return digits;
}

function nowKst(date = new Date()) {
  return new Intl.DateTimeFormat('ko-KR', {
    timeZone: 'Asia/Seoul',
    dateStyle: 'medium',
    timeStyle: 'medium',
  }).format(date) + ' (KST)';
}

function summary(lead) {
  return `${lead.serviceName} / ${lead.name} / ${lead.phone}`;
}

function str(value) {
  return typeof value === 'string' ? value.trim() : value == null ? '' : String(value).trim();
}

function isObject(value) {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function json(request, body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
      ...corsHeaders(request),
    },
  });
}

