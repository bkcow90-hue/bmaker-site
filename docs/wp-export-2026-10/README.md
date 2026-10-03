# blog.bmaker.kr 백업 (2026-10-04)

WordPress.com 폐쇄(A안, docs/wp-audit-2026-10.md) 전 원본 보관. 출처는 WP REST API(`/wp-json/wp/v2/*`).

| 파일 | 내용 |
|---|---|
| `posts.json` | 글 31개 전체 응답(제목·본문 HTML·발행일·수정일·슬러그·카테고리) |
| `pages.json` | 페이지 9개 전체 응답 |
| `categories.json`·`tags.json`·`media.json` | 분류·미디어 목록 |
| `sitemap-1.xml` | WordPress.com 사이트맵(40 URL) |
| `index.csv` | 40개 요약(종류·ID·슬러그·URL·제목·발행일·수정일·카테고리·본문 바이트·SHA1 앞 12자리) |
| `images/` | `blog.bmaker.kr/wp-content/uploads` 자체 업로드 4개(아이콘·og). 본문 이미지는 bmaker.kr 자산의 CDN 사본(i0.wp.com)과 소진공 외부 배너뿐이라 받지 않음(`images.txt` 에 목록) |

docs/ 는 .assetsignore 대상이라 사이트에 공개되지 않는다.
