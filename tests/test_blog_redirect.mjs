// blog.bmaker.kr 301 Worker 라우팅 검사 — redirects/blog-map.csv 40행과 WordPress.com 백업(index.csv) 대조.
// 실행: node tests/test_blog_redirect.mjs   (pr-check node 단계)
import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { parseMap, route, FALLBACK, FEED } from '../workers/blog-redirect/src/route.mjs';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const csv = readFileSync(join(ROOT, 'redirects/blog-map.csv'), 'utf8');
const map = parseMap(csv);
let fail = 0;
const ok = (cond, msg) => { if (!cond) { fail++; console.error('FAIL', msg); } };

// 1) 맵 40행, 백업의 URL 40개가 전부 맵에 있다
ok(map.size === 40, `맵 행 수 ${map.size} ≠ 40`);
const idx = readFileSync(join(ROOT, 'docs/wp-export-2026-10/index.csv'), 'utf8').replace(/^﻿/, '').split(/\r?\n/).slice(1).filter(Boolean);
ok(idx.length === 40, `백업 index.csv ${idx.length}행`);
for (const line of idx) {
  const url = line.split(',')[3];
  const r = route(url, map);
  ok(r.status === 301 && r.location !== FALLBACK || new URL(url).pathname === '/', `${url} 가 맵에 없어 목록으로 떨어짐`);
}

// 2) 목적지는 저장소에 실제 페이지가 있어야 한다(404 금지)
for (const [path, dest] of map) {
  const rel = dest.replace('https://bmaker.kr', '').replace(/^\//, '');
  const file = rel === '' ? 'index.html' : `${rel}.html`;
  ok(existsSync(join(ROOT, file)), `${path} → ${dest}: ${file} 없음`);
}

// 3) 루트와 변형 주소
const R = (u) => route(u, map);
ok(R('https://blog.bmaker.kr/').location === 'https://bmaker.kr/blog', '루트 → /blog');
ok(R('https://www.blog.bmaker.kr/').location === 'https://bmaker.kr/blog', 'www 루트 → /blog');
ok(R('https://www.blog.bmaker.kr/restart-special-funding/').location === 'https://bmaker.kr/jaedojeon', 'www 글 주소');
ok(R('https://blog.bmaker.kr/restart-special-funding').location === 'https://bmaker.kr/jaedojeon', '끝 슬래시 없음');
ok(R('https://blog.bmaker.kr/Restart-Special-Funding/?utm_source=x').location === 'https://bmaker.kr/jaedojeon', '대문자·쿼리');
ok(R('https://blog.bmaker.kr/cash-flow-13-weeks/amp/').location === 'https://bmaker.kr/blog/cash-flow-13-weeks', 'AMP');
ok(R('https://blog.bmaker.kr/cash-flow-13-weeks/feed/').location === 'https://bmaker.kr/blog/cash-flow-13-weeks', '글 feed');
ok(R('https://blog.bmaker.kr/feed/').location === FEED, '사이트 feed');
ok(R('https://blog.bmaker.kr/sitemap.xml').location === 'https://bmaker.kr/sitemap.xml', 'sitemap');
ok(R('https://blog.bmaker.kr/category/funding/').location === FALLBACK, '알 수 없는 경로 → 목록');
ok(R('https://blog.bmaker.kr/%EC%A0%95%EC%B1%85/').location === FALLBACK, '한글 경로');
const robots = R('https://blog.bmaker.kr/robots.txt');
ok(robots.status === 200 && robots.body.includes('Allow: /'), 'robots.txt 는 200·전체 허용(옛 주소 재방문 → 301 확인)');

// 4) 목적지가 다시 리다이렉트 체인을 만들지 않는다(blog.bmaker.kr 로 돌아가지 않음)
for (const dest of map.values()) ok(!dest.includes('blog.bmaker.kr'), `체인: ${dest}`);

if (fail) { console.error(`blog-redirect: ${fail}건 실패`); process.exit(1); }
console.log(`blog-redirect OK — 맵 ${map.size}행 · 백업 ${idx.length} URL · 변형 12건`);
