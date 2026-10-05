import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import build_blog as B


def test_asset_paths_are_local_and_root_relative():
    assert B.asset_path('assets/og.png') == '/assets/og.png'
    for path in ['https://example.com/x.png', '/assets/../x.png', '/missing.png', '/assets/no-such-image.png']:
        with pytest.raises(SystemExit):
            B.asset_path(path)


def test_image_block_escapes_alt_and_renders_real_dimensions():
    markup = B.render(B.blocks('![사장님 <확인> "안내"](/assets/og.png)'))
    assert '<img ' in markup and '&lt;확인&gt;' in markup and '&quot;안내&quot;' in markup
    assert 'width=' in markup and 'height=' in markup and 'loading="lazy"' in markup
    assert '<a ' not in markup


def test_carousel_pages_match_images_og_faq_and_cta():
    posts = [B.read_post(p) for p in (ROOT / 'posts').glob('*.md')]
    cards = [p for p in posts if p.get('carousel')]
    assert len(cards) >= 3
    for p in cards:
        page = (ROOT / 'blog' / (p['slug'] + '.html')).read_text(encoding='utf-8')
        assert len(re.findall(r'<figure class="post-card">', page)) == 5
        assert f'property="og:image" content="{B.SITE}{p["image"]}"' in page
        data = [json.loads(x) for x in re.findall(r'<script type="application/ld\+json"[^>]*>(.*?)</script>', page, re.S)]
        post = next(x for x in data if x['@type'] == 'BlogPosting')
        assert post['image'] == B.SITE + p['image']
        assert post['author']['name'] == '김상표'
        faq = next(x for x in data if x['@type'] == 'FAQPage')
        assert len(faq['mainEntity']) == 3
        assert page.count('>무료 진단 예약하기</a>') == 1
        assert 'https://www.instagram.com/bmaker_kr/' in page
        assert all(re.sub('<[^>]+>', '', h).endswith('?') for h in re.findall(r'<h2[^>]*>(.*?)</h2>', page, re.S))
