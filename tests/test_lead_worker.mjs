// bmaker.kr Worker 의 /api/lead (2026-11-16 codedaum 에서 옮김). fetch 는 가짜 — 아무것도 밖으로 나가지 않는다.
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import path from 'node:path';

const worker = (await import(pathToFileURL(path.resolve('workers/site/index.js')))).default;
let calls = [];
globalThis.fetch = async (url, opts = {}) => {
  url = String(url);
  calls.push({ url, opts });
  if (url.includes('api.resend.com')) return new Response('{}', { status: 200 });
  if (url.includes('/api/auto-intake')) return new Response(JSON.stringify({ ok: true, inserted: 1 }), { status: 200 });
  if (url.startsWith('https://codedaum.pages.dev/api/lead')) return new Response(JSON.stringify({ ok: true, delivery: 'accepted' }), { status: 200 });
  throw new Error('unexpected fetch ' + url);
};
const ctx = { waitUntil() {} };
const assets = { fetch: async (req) => new Response('asset:' + new URL(req.url).pathname) };
const lead = {
  kind: 'consult', service: 'general', service_name: '종합 상담', delivery_required: true,
  name: '홍길동', phone: '01012345678', consent_privacy: true, consent_marketing: false,
  request_id: '11111111-2222-3333-4444-555555555555', submitted_at: new Date().toISOString(),
  answers_text: '[문의 분야] 종합 상담', landing_url: 'https://bmaker.kr/',
};
const post = (env, extra = {}) => worker.fetch(new Request('https://bmaker.kr/api/lead', {
  method: 'POST', headers: { 'Content-Type': 'text/plain', origin: 'https://bmaker.kr' }, body: JSON.stringify({ ...lead, ...extra }),
}), { ASSETS: assets, ...env }, ctx);

// 1) 정적 파일은 Worker 를 거치지 않은 것처럼 그대로
let r = await worker.fetch(new Request('https://bmaker.kr/sinbo'), { ASSETS: assets }, ctx);
assert.equal(await r.text(), 'asset:/sinbo');

// 2) 비밀값이 아직 없으면 codedaum 으로 넘긴다 — 신청이 사라지지 않는다
calls = [];
r = await post({});
assert.equal(r.headers.get('X-Lead-Route'), 'legacy');
assert.equal((await r.json()).ok, true);
assert.equal(calls.length, 1); assert.match(calls[0].url, /codedaum\.pages\.dev\/api\/lead/);
assert.equal(JSON.parse(calls[0].opts.body).name, '홍길동');

// 3) 비밀값이 있으면 여기서 직접: 운영자 메일 + 가이드북 메일, codedaum 은 부르지 않는다
calls = [];
const env = { RESEND_API_KEY: 're_test', CRM_AUTO_INTAKE_TOKEN: 'crm', LEAD_FROM: 'lead@bmaker.kr', LEAD_TO: 'bmaker@bmaker.kr', GUIDEBOOK_URL: 'https://bmaker.kr/guide/test.pdf' };
r = await post(env, { email: 'ceo@example.com', guidebook_request: true });
const body = await r.json();
assert.equal(body.ok, true); assert.equal(body.guidebook, 'sent');
assert.ok(!calls.some((c) => c.url.includes('codedaum')), 'codedaum 호출 없음');
const mails = calls.filter((c) => c.url.includes('api.resend.com')).map((c) => JSON.parse(c.opts.body));
assert.equal(mails.length, 2);
const guide = mails.find((m) => m.subject.includes('가이드북'));
assert.deepEqual(guide.to, ['ceo@example.com']);
assert.ok(!/갚|보장/.test(guide.text), '금칙어');

// 4) GUIDEBOOK_URL 이 없으면 가이드북 메일은 안 나간다(운영자 메일만)
calls = [];
const { GUIDEBOOK_URL, ...noGuide } = env;
r = await post(noGuide, { email: 'ceo@example.com', guidebook_request: true });
assert.equal((await r.json()).guidebook, undefined);
assert.equal(calls.filter((c) => c.url.includes('api.resend.com')).length, 1);

// 4-1) 가이드북 요청은 CRM 에 '가이드북 요청=예' · '요청 가이드북'으로 간다(2026-11-23). 요청이 없으면 싣지 않는다.
//      GUIDEBOOK_URL 이 없어 메일을 못 보낸 경우에도 CRM 에는 요청이 남아야 직원이 따로 보낼 수 있다.
const crmFields = () => JSON.parse(calls.find((c) => c.url.includes('/api/auto-intake')).opts.body).items[0].fields;
assert.equal(crmFields()['가이드북 요청'], '예');
assert.equal(crmFields()['요청 가이드북'], '정책자금 자가진단 가이드북');
assert.equal(crmFields()['서비스'], '종합 상담 (general)');
calls = [];
r = await post(env, { request_id: '11111111-2222-3333-4444-666666666666' });
assert.equal((await r.json()).ok, true);
assert.ok(!('가이드북 요청' in crmFields()) && !('요청 가이드북' in crmFields()), '요청 없는 신청에는 가이드북 칸 없음');
calls = [];
r = await post(env, { request_id: '11111111-2222-3333-4444-777777777777', guidebook_request: 'true' });
assert.ok(!('가이드북 요청' in crmFields()), 'true(불리언)만 요청으로 본다');

// 5) GET 은 거절, OPTIONS 는 204
r = await worker.fetch(new Request('https://bmaker.kr/api/lead'), { ASSETS: assets }, ctx);
assert.equal(r.status, 405);
r = await worker.fetch(new Request('https://bmaker.kr/api/lead', { method: 'OPTIONS', headers: { origin: 'https://bmaker.kr' } }), { ASSETS: assets }, ctx);
assert.equal(r.status, 204);

console.log('RESULT: lead worker checks passed');
