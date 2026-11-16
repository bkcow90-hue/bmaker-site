// bmaker.kr Worker — 정적 파일은 그대로 내보내고 /api/lead 만 여기서 받는다 (2026-11-16 대표 "codedaum 은 다른 용도로, bmaker 만 쓰고 싶다").
//
// lead.js 는 codedaum functions/api/lead.js(가이드북 메일 포함, codedaum PR #2)를 옮겨 온 것이다.
// 전환기 안전장치: 이 Worker 에 RESEND_API_KEY 가 아직 없으면 신청을 codedaum 으로 그대로 넘긴다.
// 비밀값을 넣는 순간부터 codedaum 없이 돈다 — 그 전에 머지해도 신청이 사라지지 않는다.
import { onRequestPost, onRequestOptions } from './lead.js';

const LEGACY = 'https://codedaum.pages.dev/api/lead';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    if (url.pathname !== '/api/lead') return env.ASSETS.fetch(request);
    if (request.method === 'OPTIONS') return onRequestOptions({ request, env });
    if (request.method !== 'POST') return new Response('Method Not Allowed', { status: 405, headers: { Allow: 'POST, OPTIONS' } });
    if (!String(env.RESEND_API_KEY || '').trim()) {
      const headers = new Headers(request.headers);
      headers.set('origin', 'https://bmaker.kr');
      const res = await fetch(LEGACY, { method: 'POST', headers, body: await request.text() });
      return new Response(res.body, { status: res.status, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store', 'X-Lead-Route': 'legacy' } });
    }
    return onRequestPost({ request, env, waitUntil: (p) => ctx.waitUntil(p) });
  },
};
