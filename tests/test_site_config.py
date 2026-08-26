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

    def test_kakao_ctas_use_https_and_expose_their_source(self):
        expected = {
            "카톡 상담": "header",
            "전문가 연계 상담하기": "experts",
            "카카오톡 무료 상담하기": "contact",
        }
        anchors = {anchor["text"]: anchor["attrs"] for anchor in self.parser.anchors}

        for label, source in expected.items():
            with self.subTest(label=label):
                self.assertEqual(
                    anchors[label].get("href"),
                    "https://pf.kakao.com/_GKuxfn/chat",
                )
                self.assertEqual(anchors[label].get("data-cta-location"), source)

    def test_form_error_kakao_link_is_https_and_source_tagged(self):
        self.assertIn("kakao.href = 'https://pf.kakao.com/_GKuxfn/chat';", self.index)
        self.assertIn("kakao.dataset.ctaLocation = 'form_error';", self.index)

    def test_kakao_clicks_are_queued_with_the_cta_location(self):
        self.assertIn("event: 'kakao_click'", self.index)
        self.assertIn("cta_location: link.dataset.ctaLocation", self.index)

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
