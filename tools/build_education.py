"""Build the public education pages and retain navigation after ledger updates."""
from pathlib import Path
import html
import json
import re

ROOT = Path(__file__).resolve().parents[1]
FAQ = [
    ('어떤 기업이나 단체가 문의할 수 있나요?', '소상공인·개인사업자·상인회뿐 아니라 중소기업·법인사업자, 기업인협회, 산업단지, 창업보육기관 등 기업 교육을 준비하는 곳에서 문의할 수 있습니다. 기업 대표와 재무·회계·총무 담당자 교육도 대상이며 업종·업무·교육 목적에 맞춰 구성을 협의합니다.'),
    ('상인 교육과 법인 교육은 어떻게 다른가요?', '공식 공고를 읽는 기초는 공통이지만 실습과 결과물을 구분합니다. 소상공인 과정은 기본 준비 체크리스트, 중소기업·법인 과정은 운전·시설자금 계획, 담당자 워크숍은 재무자료·매출 근거·견적서와 준비 일정표를 중심으로 진행합니다.'),
    ('강의료와 진행 지역은 어떻게 정하나요?', '일정·장소·인원·시간·자료 범위를 확인한 뒤 출강 가능 여부와 견적을 안내합니다. 강사료·이동비·인쇄비 등의 포함 여부는 사전에 협의합니다.'),
    ('참여자의 신용정보나 대출 자료를 미리 보내야 하나요?', '아닙니다. 초기 교육 협의에는 단체 운영 정보만 필요합니다. 실습은 가상 사례나 본인 보관용 활동지를 활용하며 민감한 개인 자료의 단체 제출을 요구하지 않습니다.'),
    ('교육을 받으면 정책자금을 받을 수 있나요?', '교육은 제도 이해와 신청 준비를 돕는 과정입니다. 승인·한도를 보장하지 않으며, 지원 여부는 기관 심사로 결정됩니다. 공식 경로로 직접 신청할 수 있습니다.'),
    ('강의 뒤에 개별 상담도 가능한가요?', '주최 측과 별도 운영 시간·범위를 협의할 수 있습니다. 참여자의 자발적인 문의를 기준으로 진행하며 교육 참여를 컨설팅 계약과 연결해 강제하지 않습니다.'),
    ('강의와 자료를 녹화하거나 다시 배포해도 되나요?', '녹화·촬영·재배포 범위는 사전에 협의합니다. 공개된 프로그램 안내와 활동지는 단체 내부 검토와 참여자의 준비 목적으로 인쇄해 사용할 수 있습니다.')
]


def render_programs(programs, table=False):
    parts = []
    for course in programs:
        if sum(step[0] for step in course['steps']) != course['minutes']:
            raise ValueError(f"시간표 합계 불일치: {course['id']}")
        title, audience, takeaway = [html.escape(course[k]) for k in ('title', 'audience', 'takeaway')]
        if table:
            parts.append(f'<tr><td>{title}<br>{audience}</td><td>{course["minutes"]}분</td><td>{takeaway}</td></tr>')
        else:
            steps = ''.join(f'<li>{minutes}분 — {html.escape(text)}</li>' for minutes, text in course['steps'])
            parts.append(f'<article class="card" id="course-{html.escape(course["id"], quote=True)}"><span class="edu-tag">{course["minutes"]}분 · 기본 구성</span><h3>{title}</h3><p><b>대상</b> {audience}</p><ol>{steps}</ol><p><b>가져갈 것</b><br>{takeaway}</p><a href="/?service=education#apply" data-cta-location="education_{html.escape(course["id"], quote=True)}">이 과정 문의하기 →</a></article>')
    return ''.join(parts)


def main():
    shell = (ROOT / 'marketing.html').read_text(encoding='utf-8')
    programs = json.loads((ROOT / 'docs/education-programs.json').read_text(encoding='utf-8'))
    for slug, title, description in [
        ('education', '소상공인·중소기업 정책자금 교육·출강 | 비즈니스 메이커', '소상공인·중소기업·법인 대표와 재무·회계·총무 담당자를 위한 정책자금 준비 교육. 60분 입문, 90분 기업 자금계획, 120분 실무 워크숍과 기업·단체 맞춤 출강을 안내합니다.'),
        ('education-program', '정책자금 교육 프로그램·준비 활동지 | 비즈니스 메이커', '단체 담당자용 정책자금 교육 프로그램과 참여자용 준비 활동지. 강의 구성과 운영 준비 항목을 확인하고 인쇄하거나 PDF로 저장하세요.')]:
        page = re.sub(r'<script type="application/ld\+json"[^>]*>.*?</script>', '', shell, flags=re.S)
        page = re.sub(r'<title>.*?</title>', f'<title>{html.escape(title)}</title>', page)
        url = 'https://bmaker.kr/' + slug
        for attr, key, value in [('name','description',description),('property','og:title',title),('property','og:description',description),('property','og:url',url)]:
            page = re.sub(f'<meta {attr}="{key}" content="[^"]*">', f'<meta {attr}="{key}" content="{html.escape(value,quote=True)}">', page)
        page = re.sub(r'<link rel="canonical" href="[^"]*">', f'<link rel="canonical" href="{url}">', page)
        page = page.replace('data-service="marketing"','data-service="education"').replace('/?service=marketing#apply','/?service=education#apply')
        body = (ROOT / f'docs/{slug}-body.html').read_text(encoding='utf-8')
        body = body.replace('{{PROGRAMS}}', render_programs(programs)).replace('{{PROGRAM_ROWS}}', render_programs(programs, table=True))
        body = body.replace('{{FAQ}}', ''.join(f'<details><summary>{html.escape(q)}</summary><p>{html.escape(a)}</p></details>' for q,a in FAQ))
        page = re.sub(r'<main>.*?</main>', '<main>' + body + '</main>', page, flags=re.S)
        if slug == 'education':
            from build_editorial import topic_links, replace_block, stylesheet
            mapping = json.loads((ROOT / 'docs/topic-links.json').read_text(encoding='utf-8'))
            page = stylesheet(replace_block(page, 'topic-links', topic_links(mapping[slug])))
        schemas = [{'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'홈','item':'https://bmaker.kr/'},{'@type':'ListItem','position':2,'name':title.split(' | ')[0],'item':url}]}]
        if slug == 'education':
            schemas += [{'@context':'https://schema.org','@type':'Service','name':'소상공인·중소기업·법인 정책자금 준비 교육·출강','description':description,'url':url,'provider':{'@id':'https://bmaker.kr/#org','@type':'Organization','name':'비즈니스 메이커'}}, {'@context':'https://schema.org','@type':'FAQPage','mainEntity':[{'@type':'Question','name':q,'acceptedAnswer':{'@type':'Answer','text':a}} for q,a in FAQ]}]
        assets = '<link rel="stylesheet" href="/assets/education.css"><script src="/assets/education.js" defer></script>'
        page = page.replace('</head>',assets+''.join('<script type="application/ld+json">'+json.dumps(x,ensure_ascii=False)+'</script>' for x in schemas)+'</head>')
        (ROOT / (slug+'.html')).write_text(page,encoding='utf-8')
    for path in ROOT.glob('*.html'):
        page = path.read_text(encoding='utf-8')
        def nav(match):
            s = match[0]
            if 'href="/education"' not in s and 'href="/business-guide"' in s:
                s=s.replace('<a href="/business-guide"','<a href="/education">교육·출강</a><a href="/business-guide"',1)
            return s
        page=re.sub(r'<nav\b[^>]*>.*?</nav>',nav,page,flags=re.S)
        if path.name=='index.html':
            block='<section class="edu-home"><div class="wrap"><div><p>기업 대표·실무 담당자·단체 교육 안내</p><h2>소상공인부터 중소기업·법인까지,<br>정책자금 준비를 실무 교육으로.</h2><p>60분 입문 · 90분 기업 자금계획 · 120분 준비자료 워크숍.<br>기업·상인회·협회 맞춤 출강과 인쇄용 활동지를 확인하세요.</p></div><a href="/education">교육·출강 프로그램 보기 →</a></div></section>'
            if '<section class="edu-home">' in page:
                page = re.sub(r'<section class="edu-home">.*?</section>', lambda _: block, page, count=1, flags=re.S)
            else:page=page.replace('<section class="services"',block+'\n<section class="services"',1)
            css='<link rel="stylesheet" href="/assets/education.css">'
            if css not in page:page=page.replace('</head>',css+'</head>')
        path.write_text(page,encoding='utf-8')
    path=ROOT/'sitemap.xml';s=path.read_text(encoding='utf-8')
    for slug in ['education','education-program']:
        loc=f'<loc>https://bmaker.kr/{slug}</loc>'
        if loc not in s:s=s.replace('</urlset>',f'<url>{loc}</url>\n</urlset>')
    path.write_text(s,encoding='utf-8')
    summary = '- [교육·출강](https://bmaker.kr/education): 소상공인·중소기업·법인 대표와 재무·회계·총무 담당자 대상. 60분 입문·90분 기업 자금계획·120분 준비자료 워크숍 및 기업·단체 맞춤 출강. 김상표 대표 진행. 일정·지역·인원·출강료는 별도 협의하며 승인이나 교육 실적을 뜻하지 않음.'
    for name in ('llms.txt', 'llms-full.txt'):
        path = ROOT / name
        text = path.read_text(encoding='utf-8')
        if '- [교육·출강]' in text:
            text = re.sub(r'- \[교육·출강\][^\n]*', lambda _: summary, text)
        else:
            text += '\n\n## 기업·단체 교육\n' + summary + '\n- 프로그램·활동지: https://bmaker.kr/education-program\n'
        path.write_text(text, encoding='utf-8')


if __name__=='__main__':main()
