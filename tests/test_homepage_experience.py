from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class HomePageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.elements = []

    def handle_starttag(self, tag, attrs):
        element = {"tag": tag, "attrs": dict(attrs), "text": ""}
        self.stack.append(element)
        self.elements.append(element)

    def handle_startendtag(self, tag, attrs):
        self.elements.append({"tag": tag, "attrs": dict(attrs), "text": ""})

    def handle_data(self, data):
        for element in self.stack:
            element["text"] += data

    def handle_endtag(self, tag):
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index]["tag"] == tag:
                del self.stack[index:]
                break


class HeroHeadingParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._inside_heading = False
        self.lines = [""]

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "h1" and "serif" in attributes.get("class", "").split():
            self._inside_heading = True
        elif tag == "br" and self._inside_heading:
            self.lines.append("")

    def handle_data(self, data):
        if self._inside_heading:
            self.lines[-1] += data

    def handle_endtag(self, tag):
        if tag == "h1" and self._inside_heading:
            self._inside_heading = False
            self.lines = [" ".join(line.split()) for line in self.lines]


class HomepageExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        parser = HomePageParser()
        parser.feed(index)
        cls.elements = parser.elements
        heading_parser = HeroHeadingParser()
        heading_parser.feed(index)
        cls.hero_heading_lines = heading_parser.lines

    def test_hero_heading_has_three_lines_without_claiming_records_are_people(self):
        lines = self.hero_heading_lines
        self.assertEqual(len(lines), 3)
        self.assertTrue(all(lines))
        self.assertIn("정책자금", " ".join(lines))
        self.assertNotRegex(" ".join(lines), r"[\d,]+\s*분")

    def test_ledger_proof_is_linked_to_its_source_and_labeled_as_cases(self):
        proof_links = [
            element
            for element in self.elements
            if element["tag"] == "a"
            and "case-proof" in element["attrs"].get("class", "").split()
        ]
        self.assertEqual(len(proof_links), 1)
        self.assertEqual(proof_links[0]["attrs"]["href"], "/cases")
        self.assertRegex(proof_links[0]["text"], r"받은 사례 [\d,]+건")
        self.assertRegex(proof_links[0]["text"], r"20\d{2}\.\d{2}~20\d{2}\.\d{2}")

    def test_reservation_actions_are_visually_distinct_from_kakao_actions(self):
        reservation_actions = [
            element
            for element in self.elements
            if element["tag"] in {"a", "button"}
            # "무료 진단 신청" 통일(2026-09-28) 뒤로 홈 제출 버튼은 "진단 신청" 이다 — 빠뜨리면 검사에서 조용히 빠진다
            and any(w in " ".join(element["text"].split()) for w in ("상담 신청", "진단 신청"))
        ]

        self.assertGreaterEqual(len(reservation_actions), 3)
        for action in reservation_actions:
            classes = action["attrs"].get("class", "").split()
            with self.subTest(tag=action["tag"], classes=classes):
                self.assertNotIn("btn-kakao", classes)

    def test_case_results_are_announced_as_a_static_list(self):
        case_lists = [
            element
            for element in self.elements
            if "case-marquee" in element["attrs"].get("class", "").split()
        ]

        self.assertEqual(len(case_lists), 1)
        self.assertEqual(case_lists[0]["attrs"].get("aria-label"), "승인사례 목록")

    # ── 2026-11-02 홈 개편(규격 4-1) ─────────────────────────────────────
    def _section(self, section_id):
        return next(e for e in self.elements if e["tag"] == "section" and e["attrs"].get("id") == section_id)

    def _inside(self, section_id, tag):
        """section_id 구역 안의 tag 요소들 — 원본 순서로 구역 시작~다음 section 시작 사이."""
        start = self.elements.index(self._section(section_id))
        out = []
        for e in self.elements[start + 1:]:
            if e["tag"] == "section":
                break
            if e["tag"] == tag:
                out.append(e)
        return out

    def test_hero_heading_is_next_choice_copy_with_single_cta(self):
        self.assertEqual(" ".join(self.hero_heading_lines), "정책자금, 여기까지 만든 사업의 다음 선택지를 찾습니다.")
        hero = next(e for e in self.elements if e["tag"] == "section" and "hero" in e["attrs"].get("class", "").split())
        ctas = [e for e in self._inside_hero("a")]
        self.assertEqual([" ".join(a["text"].split()) for a in ctas], ["무료 진단 신청"])
        self.assertNotRegex(hero["text"], r"착수금|성공보수|진행비|받은 사례 [\d,]+건")
        self.assertIn("신청할 수 있는지부터 준비할 서류까지 함께 검토하고, 진행이 어렵다면 그 이유부터 말씀드립니다.", hero["text"])

    def _inside_hero(self, tag):
        hero = next(e for e in self.elements if e["tag"] == "section" and "hero" in e["attrs"].get("class", "").split())
        start = self.elements.index(hero)
        out = []
        for e in self.elements[start + 1:]:
            if e["tag"] == "section":
                break
            if e["tag"] == tag:
                out.append(e)
        return out

    def test_entry_cards_route_by_stage_without_numbers(self):
        h2 = self._inside("entry", "h2")
        self.assertEqual([" ".join(h["text"].split()) for h in h2], ["지금 어느 단계인지부터 고르세요."])
        cards = [e for e in self._inside("entry", "article") if "entry-card" in e["attrs"].get("class", "")]
        self.assertEqual(len(cards), 4)
        hrefs = [a["attrs"]["href"] for a in self._inside("entry", "a")]
        self.assertEqual(hrefs, ["/sosangin", "/jungsogieop", "/working-capital-facility", "/daehwan", "/startup"])
        for card in cards:
            with self.subTest(card=card["text"][:20]):
                self.assertNotRegex(card["text"], r"\d|금리|승인|가능성")
        self.assertFalse(any(e["attrs"].get("id") == "why-us" for e in self.elements))

    def test_principles_list_four_donts_and_three_doings(self):
        h2 = self._inside("principles", "h2")
        self.assertEqual(" ".join(h2[0]["text"].split()), "안 하는 일과, 하고 있는 일.")
        h3 = [" ".join(h["text"].split()) for h in self._inside("principles", "h3")]
        self.assertEqual(len(h3), 7)
        self.assertEqual(h3[4:], ["원장을 공개합니다", "이름을 걸고 합니다", "어려우면 먼저 말합니다"])
        stats = [e["attrs"].get("data-stat") for e in self._inside("principles", "span")]
        self.assertIn("total-n", stats)
        self.assertIn("ev-n", stats)
        hrefs = [a["attrs"]["href"] for a in self._inside("principles", "a")]
        for href in ("/cases", "#about", "/geojeol", "/jeosinyong"):
            self.assertIn(href, hrefs)

    def test_services_heading_keeps_next_choice_line(self):
        texts = [" ".join(p["text"].split()) for p in self._inside("services", "p")]
        self.assertIn("자금이 끝이 아니라 인증·연구소·지원금까지 순서로 봅니다.", texts)

    def test_form_lists_four_returns_then_guidebook_without_fee_copy(self):
        forms = [e for e in self.elements if e["tag"] == "form"]
        self.assertEqual(len(forms), 1)
        form = forms[0]
        returns = [" ".join(e["text"].split()) for e in self.elements
                   if e["tag"] == "li" and e in self._form_children(form)]
        self.assertEqual(returns, ["신청해 볼 기관·자금 후보", "지금 부족한 요건", "준비 순서와 서류", "진행이 어렵다면 그 이유"])
        text = " ".join(form["text"].split())
        self.assertLess(text.index("진단에서 돌려드리는 것"), text.index("가이드북"))
        self.assertNotRegex(text, r"착수금|성공보수|진행비|성과 보수")

    def _form_children(self, form):
        start = self.elements.index(form)
        out = []
        for e in self.elements[start + 1:]:
            if e["tag"] == "button" and e["attrs"].get("type") == "submit":
                break
            out.append(e)
        return out

    def test_bottom_sections_collapse_into_one_more_row(self):
        ids = {e["attrs"].get("id") for e in self.elements if e["tag"] == "section"}
        classes = " ".join(e["attrs"].get("class", "") for e in self.elements if e["tag"] == "section")
        for gone in ("event", "news"):
            self.assertNotIn(gone, ids)
        self.assertNotIn("edu-home", classes)
        for kept in ("about", "experts", "faq", "guides", "apply-section"):
            self.assertIn(kept, ids)
        links = self._inside("more", "a")
        self.assertEqual([a["attrs"]["href"] for a in links], ["/education", "#apply", "/blog"])
        self.assertEqual(links[1]["attrs"].get("data-cta-location"), "guidebook")
        self.assertIn("가이드북", links[1]["text"])


class ScrollRevealTests(unittest.TestCase):
    """스크롤 리빌은 conversion.js 가 CSS 까지 주입해 정적 페이지도 덮는다.
    홈의 기존 .reveal/.on 구현과 섞이면 이중 적용이 되므로 네임스페이스를 분리한다."""

    def test_scroll_reveal_is_injected_scoped_and_excludes_interactive_surfaces(self):
        js = (ROOT / "assets/conversion.js").read_text(encoding="utf-8")
        home = (ROOT / "index.html").read_text(encoding="utf-8")

        # CSS 단일 출처: 스크립트가 주입하고 페이지 <style> 에는 없다
        self.assertIn(".rv{opacity:0", js)
        self.assertIn(".rv-in{opacity:1", js)
        self.assertIn("data-rv", js)
        self.assertNotIn(".rv{opacity:0", home)

        # 모션 저감 설정 존중
        self.assertIn("(prefers-reduced-motion: reduce)", js)
        self.assertIn("@media(prefers-reduced-motion:reduce){.rv{", js)

        # 제외 대상 — 히어로·폼·CTA·고정바, 그리고 홈의 기존 .reveal
        exclude = js.split("var EXCLUDE")[1].split(";")[0]
        for selector in (".hero", "#leadForm", ".cta-inline", ".sticky-cta", ".reveal"):
            with self.subTest(selector=selector):
                self.assertIn(selector, exclude)

        # 큰 표는 행 단위가 아니라 컨테이너 단위로 등장
        self.assertIn("rows.length <= 20", js)

        # 홈의 기존 구현은 그대로 남아 있어야 한다 (이중 적용 방지의 반대편 확인)
        self.assertIn(".reveal{opacity:0", home)
        self.assertIn("classList.add('on')", home)

if __name__ == "__main__":
    unittest.main()
