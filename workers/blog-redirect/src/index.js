// Cloudflare Worker: blog.bmaker.kr/* 를 받아 bmaker.kr 로 301. WordPress.com 원본으로는 보내지 않는다.
// 배포·DNS 전환은 대표 승인 후(PR 본문의 "승인 후 실행 순서" 참고).
import MAP_CSV from '../../../redirects/blog-map.csv';
import { parseMap, route } from './route.mjs';

const MAP = parseMap(MAP_CSV);

export default {
  async fetch(request) {
    const r = route(request.url, MAP);
    if (r.status === 301) {
      return new Response(null, {
        status: 301,
        headers: { Location: r.location, 'Cache-Control': 'public, max-age=86400', 'X-Redirect-By': 'blog-redirect' },
      });
    }
    return new Response(r.body, { status: r.status, headers: { 'Content-Type': r.type } });
  },
};
