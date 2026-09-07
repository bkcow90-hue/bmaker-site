import json
import re
import subprocess
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = ['funding', 'marketing', 'startup', 'work', 'business-guide']

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'a' and attrs.get('href', '').startswith('/'):
            self.links.append(attrs['href'])

def test_new_service_pages_have_working_routes_and_contact_intent():
    for slug in PAGES:
        source = (ROOT / f'{slug}.html').read_text(encoding='utf-8')
        assert source.count('<h1>') == 1
        assert source.count('src="/assets/conversion.js"') == 1
        for raw in re.findall(r'<script type="application/ld\+json">(.*?)</script>', source, re.S):
            data = json.loads(raw)
            if data.get('@type') == 'FAQPage':
                for item in data['mainEntity']:
                    assert item['name'] in source
                    assert item['acceptedAnswer']['text'] in source
        parser = Links(); parser.feed(source)
        for href in parser.links:
            path = urlsplit(href).path
            target = ROOT / (path.strip('/') + '.html' if path != '/' else 'index.html')
            assert target.exists(), (slug, href)
        for match in re.findall(r'href="(/\?service=[^"]+)"', source):
            assert match.endswith('#apply')

def test_company_home_offers_all_service_choices_and_scope():
    source = (ROOT / 'index.html').read_text(encoding='utf-8')
    for key in ['general', 'policy', 'marketing', 'startup', 'certification']:
        assert f'<option value="{key}">' in source
    assert '광고·마케팅, 창업컨설팅, 기업인증은 업무 범위에 따른 견적' in source
    assert '광고·마케팅' in (ROOT / 'privacy.html').read_text(encoding='utf-8')

def test_ga_initialization_with_service_routing():
    subprocess.run(['node', 'tests/test_analytics.mjs'], cwd=ROOT, check=True, capture_output=True, text=True)
