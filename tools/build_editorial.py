"""Publish approved guide copy after the ledger generators; safe to run repeatedly."""
from pathlib import Path
import html
import json
import re
import csv
from builddate import build_date

ROOT = Path(__file__).resolve().parents[1]
ITEMS = json.loads((ROOT / 'docs/editorial-content.json').read_text(encoding='utf-8'))
GROWTH = json.loads((ROOT / 'docs/funding-guides.json').read_text(encoding='utf-8'))
ITEMS += GROWTH
if len({x['slug'] for x in ITEMS}) != len(ITEMS):
    raise ValueError('Guide slugs must be unique')


def inline(text):
    text = html.escape(text)
    text = re.sub(r'\[([^]]+)\]\((https://[^\s)]+)\)', r'<a href="\2">\1</a>', text)
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)


def render(body, embedded=False):
    result = []
    for block in body.split('\n\n'):
        if block.startswith('# '):
            level = 2 if embedded else 1
            result.append(f'<h{level}>{inline(block[2:])}</h{level}>')
        elif block.startswith('## '):
            level = 3 if embedded else 2
            result.append(f'<h{level}>{inline(block[3:])}</h{level}>')
        else:
            result.append('<p>' + inline(block) + '</p>')
    return '\n'.join(result)


def replace_block(page, key, value):
    start, end = f'<!-- {key}:start -->', f'<!-- {key}:end -->'
    page = re.sub(re.escape(start) + r'.*?' + re.escape(end), '', page, flags=re.S)
    block = start + value + end
    # Keep the closing consultation section after the editorial content.
    marker = '<section class="block contact">'
    return page.replace(marker, block + marker, 1) if marker in page else page.replace('</main>', block + '</main>', 1)


def cards(items):
    return '<section class="editorial-links"><div class="wrap"><h2>함께 읽는 사업 준비 가이드</h2><div class="editorial-grid">' + ''.join(
        f'<a href="/{x["slug"]}{"" if x["new"] else "#preparation-guide"}">{html.escape(x["body"].splitlines()[0][2:])}<span>자세히 읽기 →</span></a>'
        for x in items) + '</div></div></section>'


def stylesheet(page):
    link = '<link rel="stylesheet" href="/assets/editorial.css">'
    return page if link in page else page.replace('</head>', link + '</head>')


def topic_links(links, heading='지금 단계에서 함께 확인할 자료'):
    cells = []
    for slug, label in links:
        if not re.fullmatch(r'[a-z0-9-]+', slug) or not (ROOT / (slug + '.html')).exists():
            raise ValueError(f'Unknown related page: {slug}')
        cells.append(f'<a href="/{slug}">{html.escape(label)}<span>자료 보기 →</span></a>')
    return '<section class="editorial-links"><div class="wrap"><h2>' + html.escape(heading) + '</h2><div class="editorial-grid">' + ''.join(cells) + '</div></div></section>'


def repayment_examples(rows):
    selected = sorted(rows, key=lambda r:(r['실행 연월'], r['사례ID']), reverse=True)[:8]
    cells = ''.join('<tr><td>' + html.escape(r['실행 연월']) + '</td><td>' + html.escape(r['자금명']) + '</td><td>' + f'{int(r["실행 금액(만원)"]):,}만원' + '</td><td>' + html.escape(r['상환 조건'] or '원장 미기재 — 약정 확인 필요') + '</td><td><a href="/cases#case-' + html.escape(r['사례ID'], quote=True) + '">사례 ' + html.escape(r['사례ID']) + '</a></td></tr>' for r in selected)
    return f'<h2>공개 원장의 실제 상환 조건 예시</h2><p>전체 공개 사례 {len(rows)}건 중 최근 최대 8건을 표시합니다. 원장에 적힌 문구를 그대로 보여주며 표본의 빈도를 전체 상품의 일반 조건으로 해석하지 않습니다. 금액·상환 조건은 당시 사례이며 현재 대출 조건이 아닙니다. <a href="/data/cases.csv">현재 공개 원장</a>과 각 사례 링크에서 근거를 확인하세요.</p><div class="tablewrap"><table><thead><tr><th>시점</th><th>상품</th><th>받은 금액</th><th>원장 상환 조건</th><th>근거</th></tr></thead><tbody>' + cells + '</tbody></table></div>'


def main():
    # Legacy repayment sample labels referenced IDs that had since been reassigned.
    # Render current examples from the same public ledger as /cases instead.
    path = ROOT / 'sanghwan.html'
    page = path.read_text(encoding='utf-8')
    with (ROOT / 'data/cases.csv').open(encoding='utf-8-sig', newline='') as f:
        repayment_rows = list(csv.DictReader(f))
    evidence = '<!-- repayment-evidence:start -->' + repayment_examples(repayment_rows) + '<!-- repayment-evidence:end -->'
    if '<!-- repayment-evidence:start -->' in page:
        page = re.sub(r'<!-- repayment-evidence:start -->.*?<!-- repayment-evidence:end -->', lambda _: evidence, page, flags=re.S)
    else:
        page = re.sub(r'<p><b>짧은 답:</b>.*?(?=\s*<h2>용어부터 정확히)', lambda _: '<p><b>짧은 답:</b> 거치기간의 이자, 분할상환이 시작되는 시점, 만기의 원금 부담을 나눠 확인해야 합니다. 실제 납입 방식은 상품명만으로 판단하지 말고 약정의 기간·금리·상환 방식을 확인하세요.</p>' + evidence, page, count=1, flags=re.S)
    page = re.sub(r'<p>추측 대신 실행 24건의 약정을.*?</p>', '<p>거치기간의 이자부터 분할상환·만기의 원금 부담까지, 실제 약정에서 확인할 항목을 정리합니다.</p>', page)
    title = '정책자금 상환 방식 — 거치·분할·만기와 상환계획서 | 비즈니스 메이커'
    description = '정책자금 대출의 거치·원금균등분할·만기 상환 구조와 납입액 계산 예시. 공개 원장의 실제 상환 조건과 자금계획 준비 방법을 확인하세요.'
    page = re.sub(r'<title>.*?</title>', '<title>' + title + '</title>', page)
    for attr, key, value in [('name', 'description', description), ('property', 'og:title', title), ('property', 'og:description', description)]:
        page = re.sub(f'<meta {attr}="{key}" content="[^"]*">', f'<meta {attr}="{key}" content="{value}">', page)
    page = page.replace(' 저희 실행 기록에서도 보증서 대출 3건이 이 구조였습니다.', ' 보증서 대출도 상품과 약정에 따라 분할상환 등 다른 방식일 수 있으며 연장은 자동으로 확정되지 않습니다.')
    def repayment_schema(match):
        data = json.loads(match[1])
        if data.get('@type') == 'Article':
            data['headline'] = title.split(' | ')[0]
        return '<script type="application/ld+json">' + json.dumps(data, ensure_ascii=False) + '</script>'
    page = re.sub(r'<script type="application/ld\+json">(.*?)</script>', repayment_schema, page, flags=re.S)
    path.write_text(page, encoding='utf-8')
    shell = (ROOT / 'marketing.html').read_text(encoding='utf-8').replace('<link rel="stylesheet" href="/assets/editorial.css">', '')
    for item in ITEMS:
        path = ROOT / (item['slug'] + '.html')
        url = 'https://bmaker.kr/' + item['slug']
        if item['new']:
            page = re.sub(r'<script type="application/ld\+json"[^>]*>.*?</script>', '', shell, flags=re.S)
            page = re.sub(r'<title>.*?</title>', '<title>' + html.escape(item['title']) + '</title>', page)
            for attr, key, value in [('name', 'description', item['description']), ('property', 'og:title', item['title']), ('property', 'og:description', item['description']), ('property', 'og:url', url), ('property', 'og:type', 'article')]:
                page = re.sub(f'<meta {attr}="{key}" content="[^"]*">', f'<meta {attr}="{key}" content="{html.escape(value, quote=True)}">', page)
            page = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', page)
            page = page.replace('data-service="marketing"', f'data-service="{item["service"]}"')
            page = page.replace('/?service=marketing#apply', f'/?service={item["service"]}#apply')
            title = item['body'].splitlines()[0][2:]
            crumb = '<div class="wrap crumb"><a href="/">홈</a> / <a href="/business-guide">사업 가이드</a></div>'
            article = '<article class="editorial-copy editorial-standalone">' + render(item['body']) + '</article>'
            related = '' if item in GROWTH else cards([x for x in ITEMS if x['service'] == item['service'] and x != item][:4])
            page = re.sub(r'<main>.*?</main>', '<main>' + crumb + article + related + '</main>', page, flags=re.S)
            faq = []
            for q, a in re.findall(r'^\*\*(.+?)\*\* (.+)$', item['body'], flags=re.M):
                faq.append({'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', a)}})
            schemas = [{'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': '홈', 'item': 'https://bmaker.kr/'},
                {'@type': 'ListItem', 'position': 2, 'name': '사업 가이드', 'item': 'https://bmaker.kr/business-guide'},
                {'@type': 'ListItem', 'position': 3, 'name': title, 'item': url}]},
                {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': faq}]
            if item in GROWTH:
                schemas.append({'@context': 'https://schema.org', '@type': 'Article',
                                'headline': title, 'inLanguage': 'ko', 'mainEntityOfPage': url,
                                'dateModified': str(build_date()),
                                'author': {'@type': 'Organization', 'name': '비즈니스 메이커', '@id': 'https://bmaker.kr/#org'},
                                'publisher': {'@type': 'Organization', 'name': '비즈니스 메이커', '@id': 'https://bmaker.kr/#org'}})
            page = page.replace('</head>', ''.join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False) + '</script>' for x in schemas) + '</head>')
        else:
            page = path.read_text(encoding='utf-8')
            content = '<section id="preparation-guide" class="editorial-copy editorial-embedded" aria-label="신청과 상담 준비 가이드">' + render(item['body'], embedded=True) + '</section>'
            page = replace_block(page, 'editorial-copy', content)
        if item in GROWTH:
            # Search snippets must describe the content actually present on this page.
            page = re.sub(r'<title>.*?</title>', '<title>' + html.escape(item['title']) + '</title>', page)
            for attr, key, value in [('name', 'description', item['description']), ('property', 'og:title', item['title']), ('property', 'og:description', item['description'])]:
                page = re.sub(f'<meta {attr}="{key}" content="[^"]*">', f'<meta {attr}="{key}" content="{html.escape(value, quote=True)}">', page)
        if item.get('official_contact'):
            # Informational referrals must not funnel official-loan enquiries
            # through the company's inherited mobile consultation buttons.
            contact = html.escape(item['official_contact'], quote=True)
            bar = f'<div class="sticky" aria-label="공식 기관 안내"><a class="btn" style="grid-column:1/-1" href="{contact}">공식 기관에서 확인하기</a></div>'
            page = re.sub(r'<div class="sticky".*?</div>', lambda _: bar, page, flags=re.S)
        path.write_text(stylesheet(page), encoding='utf-8')

    for slug, selection in [('business-guide', ITEMS), ('marketing', [x for x in ITEMS if x['service'] == 'marketing']), ('startup', [x for x in ITEMS if x['service'] == 'startup' and x['new']]), ('funding', ITEMS[:5])]:
        path = ROOT / (slug + '.html')
        page = replace_block(path.read_text(encoding='utf-8'), 'editorial-links', cards(selection))
        path.write_text(stylesheet(page), encoding='utf-8')

    mapping = json.loads((ROOT / 'docs/topic-links.json').read_text(encoding='utf-8'))
    for slug, links in mapping.items():
        # Education is rendered later, so its builder owns the same contextual links.
        if slug == 'education':
            continue
        path = ROOT / (slug + '.html')
        page = replace_block(path.read_text(encoding='utf-8'), 'topic-links', topic_links(links))
        path.write_text(stylesheet(page), encoding='utf-8')
    # Two useful directories, not a site-wide block of unrelated keyword links.
    for source, slug, id_key, label_key, heading in [
        ('funds', 'sojingong', '자금ID', '자금명', '소상공인 자금별 준비 안내'),
        ('jaedan', 'gaein', '재단ID', '재단명', '사업장 소재지의 신용보증재단 찾기')]:
        with (ROOT / f'data/{source}.source.csv').open(encoding='utf-8-sig', newline='') as f:
            rows = [r for r in csv.DictReader(f) if r.get('사이트 공개', '').upper() == 'Y']
        links = [(r[id_key], r[label_key]) for r in rows]
        path = ROOT / (slug + '.html')
        page = replace_block(path.read_text(encoding='utf-8'), 'topic-directory', topic_links(links, heading))
        path.write_text(stylesheet(page), encoding='utf-8')

    path = ROOT / 'sitemap.xml'
    sitemap = path.read_text(encoding='utf-8')
    for item in ITEMS:
        url = 'https://bmaker.kr/' + item['slug']
        if '<loc>' + url + '</loc>' not in sitemap:
            sitemap = sitemap.replace('</urlset>', f'<url><loc>{url}</loc></url>\n</urlset>')
    path.write_text(sitemap, encoding='utf-8')
    for name in ['llms.txt', 'llms-full.txt']:
        path = ROOT / name
        summary = path.read_text(encoding='utf-8')
        summary = re.sub(r'^- \[정책자금 상환, 실제 구조\][^\n]*', '- [정책자금 상환, 실제 구조](https://bmaker.kr/sanghwan) — 거치·분할·만기의 차이, 납입액 가상 계산, 현재 공개 원장에서 연결한 실제 상환 조건 예시. 과거 사례는 현재 약정 조건이 아니며 개별 약정을 확인해야 함.', summary, flags=re.M)
        start, end = '<!-- preparation-guides:start -->', '<!-- preparation-guides:end -->'
        summary = re.sub(re.escape(start) + r'.*?' + re.escape(end) + r'\n?', '', summary, flags=re.S)
        lines = '\n'.join(f'- [{x["title"].split(" | ")[0]}](https://bmaker.kr/{x["slug"]}): {x["description"]}' for x in GROWTH if x['new'])
        summary = summary.rstrip() + '\n\n' + start + '\n## 기업 자금 준비 자료\n' + lines + '\n' + end + '\n'
        path.write_text(summary, encoding='utf-8')


if __name__ == '__main__':
    main()
