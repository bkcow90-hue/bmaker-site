// blog.bmaker.kr → bmaker.kr 301 라우팅 (순수 함수 — Worker 와 node 테스트가 같이 쓴다).
// 맵 원본: redirects/blog-map.csv (wp_path,destination,action,reason). WordPress.com 폐쇄(A안, docs/wp-audit-2026-10.md).

export const FALLBACK = 'https://bmaker.kr/blog';
export const FEED = 'https://bmaker.kr/blog/feed.xml';

export function parseMap(csvText) {
  const map = new Map();
  const lines = csvText.replace(/\r/g, '').split('\n').filter(Boolean);
  const header = lines.shift();
  if (!header || !header.startsWith('wp_path,destination')) throw new Error('blog-map.csv 머리글이 다릅니다');
  for (const line of lines) {
    const [path, dest] = line.split(',');
    if (!path.startsWith('/') || !dest.startsWith('https://bmaker.kr/')) throw new Error(`맵 행 형식 오류: ${line}`);
    map.set(path, dest);
  }
  return map;
}

// WordPress 경로 정규화: 소문자·끝 슬래시·AMP 접미사·/feed 접미사 제거.
export function normalize(pathname) {
  let p;
  try { p = decodeURIComponent(pathname); } catch { p = pathname; }
  p = p.toLowerCase().replace(/\/{2,}/g, '/');
  if (!p.endsWith('/')) p += '/';
  p = p.replace(/\/(amp|embed)\/$/, '/');
  return p;
}

// 반환: { status, location } 또는 { status, body, type } (robots.txt)
export function route(urlString, map) {
  const url = new URL(urlString);
  const raw = url.pathname;
  if (raw === '/robots.txt') {
    // 옛 주소를 크롤러가 다시 방문해 301 을 확인할 수 있어야 하므로 전부 허용한다
    return { status: 200, type: 'text/plain; charset=utf-8', body: 'User-agent: *\nAllow: /\n\nSitemap: https://bmaker.kr/sitemap.xml\n' };
  }
  const p = normalize(raw);
  if (map.has(p)) return { status: 301, location: map.get(p) };
  if (/^\/(feed|comments\/feed|news-sitemap\.xml)\/$/.test(p)) return { status: 301, location: FEED };
  // 글 주소 뒤에 /feed/ /trackback/ 이 붙은 변형
  const base = p.replace(/(feed|comments\/feed|trackback)\/$/, '');
  if (base !== p && base !== '/' && map.has(base)) return { status: 301, location: map.get(base) };
  if (/^\/(sitemap[\w-]*\.xml|image-sitemap-\d+\.xml)\/$/.test(p)) return { status: 301, location: 'https://bmaker.kr/sitemap.xml' };
  if (p.startsWith('/category/news/') || p.startsWith('/category/policy-news/')) return { status: 301, location: 'https://bmaker.kr/blog/category/news' };
  // 그 밖(카테고리·태그·페이지 번호·검색·wp-* 등)은 블로그 목록으로
  return { status: 301, location: FALLBACK };
}
