"""Confirmed startup service; rendered within the existing editorial build step."""
import html
import json
import re
from pathlib import Path
from inline_form import form_html, CSS as FORM_CSS

ROOT = Path(__file__).resolve().parents[1]
TITLE = '프랜차이즈 비교·창업비용·중장년 창업 상담 | 비즈니스 메이커'
DESCRIPTION = '희망 지역·예산·목표 매출에 맞는 프랜차이즈와 창업 후보를 함께 찾고 비교합니다. 총 창업비용, 상권과 운영 조건을 검토하는 비즈니스 메이커 창업컨설팅입니다.'
FAQ = [
    ('어떤 프랜차이즈가 맞는지 함께 찾아주나요?', '네. 희망 지역, 가용 예산, 목표 매출과 직접 운영할 수 있는 시간을 확인하고 창업 후보를 찾아 비교하는 서비스를 제공합니다. 후보별 자료를 확인한 뒤 검토 범위를 정합니다.'),
    ('중장년이나 퇴직 후 처음 창업하는 사람도 상담할 수 있나요?', '네. 사업자등록 전부터 상담할 수 있습니다. 이전 경력, 직접 일할 수 있는 시간, 생활비와 사업 예산을 나눠 보고 운영 가능한 업종과 후보를 비교합니다.'),
    ('목표 매출에 맞는 브랜드를 고르면 그만큼 벌 수 있나요?', '목표 매출은 후보를 검토하는 기준이며 실제 매출을 약속하는 수치가 아닙니다. 평균 매출과 개별 점포 매출은 다르고, 매출에서 비용을 제외한 금액도 따로 확인해야 합니다.'),
    ('창업 상담 수수료는 얼마인가요?', '수수료는 지역마다 다릅니다. 희망 지역과 요청 업무를 확인한 뒤 적용 비용과 제공 범위를 개별 안내합니다. 계약 전에 지급 조건과 추가 비용 여부를 확인하실 수 있습니다. 정책자금 상담의 보수 조건을 창업 서비스 전체에 적용하지 않습니다.'),
    ('상담할 때 무엇을 준비하면 되나요?', '희망 지역, 사용할 수 있는 자기자금, 목표 월매출 또는 필요한 월 생활비, 관심 업종과 하루 운영 가능 시간을 알려주세요. 관심 브랜드의 견적이나 매장 후보가 있으면 함께 검토합니다. 아직 정하지 못한 항목은 미정으로 알려주셔도 됩니다.'),
]


def render_page(page):
    body = (ROOT / 'tools/startup_body.html').read_text(encoding='utf-8')
    faq_html = ''.join(f'<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>' for q, a in FAQ)
    body = body.replace('<!-- startup-faq -->', faq_html)
    body = body.replace('<!-- startup-form -->', form_html('/startup', '창업 비교 상담', title='희망 지역과 예산부터 창업 상담', service='startup'))
    page = re.sub(r'<main>.*?</main>', lambda _: '<main>' + body + '</main>', page, count=1, flags=re.S)
    page = re.sub(r'<style data-startup-form>.*?</style>', '', page, flags=re.S)
    page = page.replace('</head>', '<style data-startup-form>' + FORM_CSS + '</style></head>')
    page = re.sub(r'<title>.*?</title>', lambda _: '<title>' + TITLE + '</title>', page, count=1)
    for attr, key, value in [('name', 'description', DESCRIPTION), ('property', 'og:title', TITLE), ('property', 'og:description', DESCRIPTION)]:
        page = re.sub(f'<meta {attr}="{key}" content="[^"]*">', lambda _, a=attr, k=key, v=value: f'<meta {a}="{k}" content="{html.escape(v, quote=True)}">', page)
    # Updated copy has not yet received a human content review.
    page = re.sub(r'<script type="application/ld\+json" data-reviewed>.*?</script>', '', page, flags=re.S)

    def schema(m):
        node = json.loads(m[1])
        if node.get('@type') == 'Service':
            node.update(name='프랜차이즈 비교·창업컨설팅', description=DESCRIPTION, serviceType='프랜차이즈 비교·창업비용 검토·중장년 창업 상담')
        elif node.get('@type') == 'FAQPage':
            node['mainEntity'] = [{'@type': 'Question', 'name': q, 'acceptedAnswer': {'@type': 'Answer', 'text': a}} for q, a in FAQ]
        return '<script type="application/ld+json">' + json.dumps(node, ensure_ascii=False) + '</script>'
    return re.sub(r'<script type="application/ld\+json">(.*?)</script>', schema, page, flags=re.S)


def build():
    path = ROOT / 'startup.html'
    path.write_text(render_page(path.read_text(encoding='utf-8')), encoding='utf-8')
