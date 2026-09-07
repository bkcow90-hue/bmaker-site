"""Publish approved guide copy after the ledger generators; safe to run repeatedly."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
ITEMS = json.loads((ROOT / 'docs/editorial-content.json').read_text(encoding='utf-8'))


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


def main():
    shell = (ROOT / 'marketing.html').read_text(encoding='utf-8').replace('<link rel="stylesheet" href="/assets/editorial.css">', '')
    for item in ITEMS:
        path = ROOT / (item['slug'] + '.html')
        url = 'https://bmaker.kr/' + item['slug']
        if item['new']:
            page = re.sub(r'<script type="application/ld\+json">.*?</script>', '', shell, flags=re.S)
            page = re.sub(r'<title>.*?</title>', '<title>' + html.escape(item['title']) + '</title>', page)
            for attr, key, value in [('name', 'description', item['description']), ('property', 'og:title', item['title']), ('property', 'og:description', item['description']), ('property', 'og:url', url), ('property', 'og:type', 'article')]:
                page = re.sub(f'<meta {attr}="{key}" content="[^"]*">', f'<meta {attr}="{key}" content="{html.escape(value, quote=True)}">', page)
            page = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', page)
            page = page.replace('data-service="marketing"', f'data-service="{item["service"]}"')
            page = page.replace('/?service=marketing#apply', f'/?service={item["service"]}#apply')
            title = item['body'].splitlines()[0][2:]
            crumb = '<div class="wrap crumb"><a href="/">홈</a> / <a href="/business-guide">사업 가이드</a></div>'
            article = '<article class="editorial-copy editorial-standalone">' + render(item['body']) + '</article>'
            related = cards([x for x in ITEMS if x['service'] == item['service'] and x != item])
            page = re.sub(r'<main>.*?</main>', '<main>' + crumb + article + related + '</main>', page, flags=re.S)
            faq = []
            for q, a in re.findall(r'^\*\*(.+?)\*\* (.+)$', item['body'], flags=re.M):
                faq.append({'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': re.sub(r'\[([^]]+)\]\([^)]+\)', r'\1', a)}})
            schemas = [{'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': '홈', 'item': 'https://bmaker.kr/'},
                {'@type': 'ListItem', 'position': 2, 'name': '사업 가이드', 'item': 'https://bmaker.kr/business-guide'},
                {'@type': 'ListItem', 'position': 3, 'name': title, 'item': url}]},
                {'@context': 'https://schema.org', '@type': 'FAQPage', 'mainEntity': faq}]
            page = page.replace('</head>', ''.join('<script type="application/ld+json">' + json.dumps(x, ensure_ascii=False) + '</script>' for x in schemas) + '</head>')
        else:
            page = path.read_text(encoding='utf-8')
            content = '<section id="preparation-guide" class="editorial-copy editorial-embedded" aria-label="신청과 상담 준비 가이드">' + render(item['body'], embedded=True) + '</section>'
            page = replace_block(page, 'editorial-copy', content)
        path.write_text(stylesheet(page), encoding='utf-8')

    for slug, selection in [('business-guide', ITEMS), ('marketing', [x for x in ITEMS if x['service'] == 'marketing']), ('startup', [x for x in ITEMS if x['service'] == 'startup' and x['new']]), ('funding', ITEMS[:5])]:
        path = ROOT / (slug + '.html')
        page = replace_block(path.read_text(encoding='utf-8'), 'editorial-links', cards(selection))
        path.write_text(stylesheet(page), encoding='utf-8')

    path = ROOT / 'sitemap.xml'
    sitemap = path.read_text(encoding='utf-8')
    for item in ITEMS:
        url = 'https://bmaker.kr/' + item['slug']
        if '<loc>' + url + '</loc>' not in sitemap:
            sitemap = sitemap.replace('</urlset>', f'<url><loc>{url}</loc></url>\n</urlset>')
    path.write_text(sitemap, encoding='utf-8')


if __name__ == '__main__':
    main()
