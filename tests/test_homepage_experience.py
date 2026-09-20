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
            and "hero-proof" in element["attrs"].get("class", "").split()
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
            and "상담 신청" in " ".join(element["text"].split())
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

    def test_news_hides_instagram_while_guidebook_event_remains_visible(self):
        instagram_grid = next(
            element
            for element in self.elements
            if element["attrs"].get("id") == "instaGrid"
        )
        instagram_more = next(
            element
            for element in self.elements
            if "media-more" in element["attrs"].get("class", "").split()
        )
        guidebook_event = next(
            element
            for element in self.elements
            if "event-banner" in element["attrs"].get("class", "").split()
        )

        self.assertIn("hidden", instagram_grid["attrs"])
        self.assertIn("hidden", instagram_more["attrs"])
        self.assertNotIn("hidden", guidebook_event["attrs"])


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
