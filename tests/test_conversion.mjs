// Run the production handler in a small DOM fixture; fetch cannot reach a network.
import vm from 'node:vm';
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { webcrypto } from 'node:crypto';
const script = fs.readFileSync('assets/conversion.js', 'utf8');
class Element {
  constructor() { this.value = ''; this.listeners = {}; this.dataset = {}; this.attributes = {}; this.children = []; this.textContent = ''; }
  addEventListener(type, fn) { this.listeners[type] = fn; }
  setAttribute(k, v) { this.attributes[k] = v; }
  getAttribute(k) { return this.attributes[k]; }
  removeAttribute(k) { delete this.attributes[k]; }
  setCustomValidity(v) { this.invalid = v; }
  appendChild(x) { this.children.push(x); }
  focus() {} contains() { return false; }
}
function fixture(mode, service = "general", env = {}) {
  const els = Object.fromEntries(['leadForm','applyMsg','lf-phone','lf-name','lf-biz','lf-memo','lf-consent','lf-website','lf-service'].map(id => [id,new Element()]));
  const button = new Element(), f = els.leadForm;
  f.querySelector = () => button;
  f.reportValidity = () => !els['lf-phone'].invalid && !els['lf-name'].invalid && els['lf-consent'].checked;
  f.reset = () => { for (const x of Object.values(els)) x.value = ''; };
  els['lf-name'].value = '테스트'; els['lf-phone'].value = '010-0000-0000'; els['lf-consent'].checked = true;
  const events = [], bodies = []; let abort;
  const window = { dataLayer: { push: e => events.push(e) }, sessionStorage: env.storage };
  const document = { getElementById: id => els[id], querySelectorAll: () => [], querySelector: () => null, addEventListener() {}, createElement: () => new Element() };
  const fetch = async (_, opts) => {
    bodies.push(JSON.parse(opts.body));
    if (mode === 'timeout') { abort(); throw Object.assign(new Error(), { name:'AbortError' }); }
    if (mode === 'network') throw new Error('mock');
    if (mode === 'bad_json') return { ok:true, json: async () => { throw new SyntaxError(); } };
    return { ok: mode !== 'http_error', json: async () => mode === 'success' ? { ok:true, delivery:'accepted' } : mode === 'legacy' ? { ok:true } : { ok:false, delivery:'failed' } };
  };
  vm.runInNewContext(script, { window, document, location: env.location || { pathname:'/', search:'?service='+service }, URL, URLSearchParams, Element, fetch, crypto:webcrypto, AbortController, setTimeout:fn => {abort=fn; return 1;}, clearTimeout() {} });
  return { els, button, events, bodies, submit: () => f.listeners.submit({ preventDefault() {} }) };
}
for (const mode of ['success','legacy','http_error','network','bad_json','timeout']) {
  const f = fixture(mode); await f.submit();
  assert.equal(f.button.disabled, false);
  assert.equal(f.bodies[0].delivery_required, true);
  assert.equal(f.events.filter(e => e.event === 'generate_lead').length, mode === 'success' ? 1 : 0);
  if (mode === 'success') { await f.submit(); assert.equal(f.bodies.length,1,'double submit after completion ignored'); }
  else {
    assert.equal(f.els['lf-name'].value, '테스트'); assert.equal(f.els.applyMsg.children[0].children.length, 2);
    await f.submit(); assert.equal(f.bodies[0].request_id, f.bodies[1].request_id); assert.equal(f.bodies[0].submitted_at, f.bodies[1].submitted_at);
  }
  assert.ok(!JSON.stringify(f.events).includes('01000000000'), 'analytics exclude contact data');
}
const invalid = fixture('success'); invalid.els['lf-phone'].value = 'invalid'; await invalid.submit(); assert.equal(invalid.bodies.length, 0);
const pending = fixture('network'); await Promise.all([pending.submit(),pending.submit()]); assert.equal(pending.bodies.length,1);
console.log('Conversion handler: delivery contract, duplicate guard, retries, validation, errors and privacy passed.');

for (const service of ['policy', 'marketing', 'startup', 'certification', 'education', 'general']) {
  const f = fixture('success', service);
  assert.equal(f.els['lf-service'].value, service, 'landing choice preselected');
  await f.submit();
  assert.equal(f.bodies[0].consultation_service, service);
  assert.equal(f.bodies[0].service, service === 'policy' ? 'pfm' : service);
  assert.ok(f.bodies[0].answers_text.includes(f.bodies[0].service_name));
  // /api/lead 는 최상위 키를 화이트리스트로 거른다 — 통화 희망 시간과 신청 경로가
  // answers_text 에 없으면 운영자 알림 메일에서 사라진다(2026-09-28 메일 템플릿 렌더로 확인).
  assert.ok(f.bodies[0].answers_text.includes(f.bodies[0].preferred_time), 'preferred_time reaches the mail body');
  assert.ok(f.bodies[0].answers_text.includes(f.bodies[0].source), 'source reaches the mail body');
  assert.equal(f.events.find(e => e.event === 'generate_lead').service_category, service, 'category survives form reset');
}
const unknown = fixture('success', '__proto__');
assert.equal(unknown.els['lf-service'].value, 'general');
const changed = fixture('network', 'marketing'); await changed.submit();
changed.els['lf-service'].value = 'startup'; await changed.submit();
assert.notEqual(changed.bodies[0].request_id, changed.bodies[1].request_id, 'changed inquiry gets new id');
assert.equal(changed.bodies[1].consultation_service, 'startup');
console.log('Service preselection, lead routing, category tracking and changed-service retries passed.');

// 유입 경로(landing_url) — CRM 이 출처·근거(파워링크/자연 유입)를 가리는 입력. 우리 Referrer-Policy 때문에
// codedaum 이 받는 Referer 헤더에는 경로·쿼리가 없다. 그래서 본문으로 보낸다(2026-10-04).
const memory = () => { const m = new Map(); return { getItem: k => m.has(k) ? m.get(k) : null, setItem: (k, v) => m.set(k, String(v)) }; };
const at = (path, search = '') => ({ origin: 'https://bmaker.kr', pathname: path, search });

// 1) 파워링크 광고로 착지 → 그 페이지에서 신청: 광고 파라미터만 남고 나머지 쿼리는 버린다
let store = memory();
let f = fixture('success', 'policy', { storage: store, location: at('/jungjingong', '?n_media=27758&n_query=정책자금&n_ad_group=grp-a&service=policy&email=a@b.com') });
await f.submit();
let landing = new URL(f.bodies[0].landing_url);
assert.equal(landing.origin + landing.pathname, 'https://bmaker.kr/jungjingong');
assert.equal(landing.searchParams.get('n_media'), '27758');
assert.equal(landing.searchParams.get('n_query'), '정책자금');
assert.equal(landing.searchParams.get('n_ad_group'), 'grp-a');
assert.equal(landing.searchParams.has('service'), false, 'non-ad query dropped');
assert.equal(landing.searchParams.has('email'), false, 'non-ad query dropped');

// 2) 같은 탭에서 광고 없는 홈으로 옮겨 신청해도 첫 광고 착지가 근거로 남는다
f = fixture('success', 'general', { storage: store, location: at('/', '') });
await f.submit();
assert.equal(new URL(f.bodies[0].landing_url).searchParams.get('n_media'), '27758', 'ad landing survives navigation');

// 3) 같은 탭에서 다른 광고(utm)를 다시 누르면 그 광고가 근거
f = fixture('success', 'general', { storage: store, location: at('/', '?utm_source=powerlink&utm_campaign=b') });
await f.submit();
landing = new URL(f.bodies[0].landing_url);
assert.equal(landing.searchParams.get('utm_source'), 'powerlink');
assert.equal(landing.searchParams.has('n_media'), false, 'latest ad landing wins');

// 4) 자연 유입: 광고 파라미터 없이 착지 → 첫 착지 페이지(쿼리 없음)
store = memory();
fixture('success', 'general', { storage: store, location: at('/sojingong', '?ref=blog') });
f = fixture('success', 'general', { storage: store, location: at('/', '') });
await f.submit();
assert.equal(f.bodies[0].landing_url, 'https://bmaker.kr/sojingong', 'organic keeps first landing, no query');

// 5) 저장소를 못 쓰면(사생활 모드) 신청 시점 주소로 — 신청은 그대로 된다
const broken = { getItem() { throw new Error('denied'); }, setItem() { throw new Error('denied'); } };
f = fixture('success', 'general', { storage: broken, location: at('/', '?n_media=1') });
await f.submit();
assert.equal(f.bodies.length, 1);
assert.equal(new URL(f.bodies[0].landing_url).searchParams.get('n_media'), '1');

// 6) 연락처가 유입 경로에 섞이지 않는다
assert.ok(!f.bodies[0].landing_url.includes('0000'), 'no contact data in landing_url');
console.log('Landing URL: ad params kept, other query dropped, survives navigation, latest ad wins, organic, storage failure passed.');
