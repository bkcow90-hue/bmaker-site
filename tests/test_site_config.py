from html.parser import HTMLParser
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.anchors = []
        self._current = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._current = {"attrs": dict(attrs), "text": ""}

    def handle_data(self, data):
        if self._current is not None:
            self._current["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self._current is not None:
            self._current["text"] = " ".join(self._current["text"].split())
            self.anchors.append(self._current)
            self._current = None


def parse_robots_groups(text):
    groups = {}
    current_agents = []
    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        field, value = (part.strip() for part in line.split(":", 1))
        field = field.lower()
        if field == "user-agent":
            current_agents = [value]
            groups.setdefault(value, [])
        elif current_agents:
            for agent in current_agents:
                groups.setdefault(agent, []).append((field, value))
    return groups


class SiteConfigurationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.robots = (ROOT / "robots.txt").read_text(encoding="utf-8")
        cls.parser = AnchorParser()
        cls.parser.feed(cls.index)

    def test_header_cta_is_the_diagnosis_booking_button(self):
        """헤더는 첫 화면에 늘 떠 있다 — 규격상 그 자리의 버튼은 진단 예약 하나다(카톡은 문의 섹션·플로팅바로)."""
        header = self.index[self.index.index("<header>"):self.index.index("</header>")]
        self.assertNotIn("pf.kakao.com", header)
        booking = [a for a in self.parser.anchors
                   if a["attrs"].get("data-cta-location") == "header"]
        self.assertEqual(len(booking), 1, booking)
        self.assertEqual(booking[0]["text"], "무료 진단 예약")
        self.assertEqual(booking[0]["attrs"]["href"], "/#apply")

    def test_kakao_ctas_use_https_and_expose_their_source(self):
        expected = {
            "전문가 연계 상담하기": "experts",
            "카카오톡 무료 상담하기": "contact",
        }
        for label, source in expected.items():
            matches = [a for a in self.parser.anchors if a['text'] == label and a['attrs'].get('data-cta-location') == source]
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0]['attrs']['href'], 'https://pf.kakao.com/_GKuxfn/chat')

    def test_shared_conversion_script_is_loaded(self):
        self.assertEqual(self.index.count('src="/assets/conversion.js"'), 1)
        script = (ROOT / 'assets/conversion.js').read_text(encoding='utf-8')
        self.assertIn("'https://pf.kakao.com/_GKuxfn/chat'", script)
        self.assertIn("a.dataset.ctaLocation = 'form_error'", script)
        self.assertIn("track('kakao_click', { cta_location: where })", script)

    def test_ai_search_agent_and_training_usage_are_explicitly_allowed(self):
        groups = parse_robots_groups(self.robots)
        self.assertIn(
            ("content-signal", "search=yes, ai-input=yes, ai-train=yes"),
            groups["*"],
        )

        for agent in (
            "GPTBot",
            "OAI-SearchBot",
            "ChatGPT-User",
            "ClaudeBot",
            "Claude-SearchBot",
            "Claude-User",
            "PerplexityBot",
            "Google-Extended",
            "Yeti",
        ):
            with self.subTest(agent=agent):
                access_rules = [
                    rule for rule in groups.get(agent, []) if rule[0] in {"allow", "disallow"}
                ]
                self.assertEqual(access_rules, [("allow", "/")])


if __name__ == "__main__":
    unittest.main()
