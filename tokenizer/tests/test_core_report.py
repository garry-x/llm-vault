import json
import tempfile
import unittest
from pathlib import Path

from bpe_demo.core import TokenPiece, TokenizationResult, read_sample
from bpe_demo.report import source_text_table, summary_table, token_preview, write_html, write_json


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.results = [
            TokenizationResult(
                "Demo",
                "test",
                "English",
                "Hello world",
                2,
                [TokenPiece(1, "Hello"), TokenPiece(2, " world")],
            ),
            TokenizationResult(
                "Demo",
                "test",
                "中文",
                "你好世界",
                2,
                [TokenPiece(3, "你好"), TokenPiece(4, "世界")],
            ),
        ]

    def test_samples_are_bilingual_story_versions(self):
        self.assertIn("harbor", read_sample("English").lower())
        self.assertIn("港口", read_sample("中文"))

    def test_summary_contains_language_metrics(self):
        summary = summary_table(self.results)
        self.assertIn("英文 tokens", summary)
        self.assertIn("中文压缩率", summary)
        self.assertIn("Demo", summary)

    def test_source_text_table_contains_original_character_count(self):
        table = source_text_table(self.results)
        self.assertIn("字符数", table)
        self.assertIn("English", table)
        self.assertIn("11", table)

    def test_preview_marks_spaces(self):
        preview = token_preview(self.results[0], 2)
        self.assertIn("␠world", preview)

    def test_reports_include_results_and_token_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            json_path = Path(directory) / "result.json"
            html_path = Path(directory) / "result.html"
            write_json(json_path, self.results, {"api": "missing key"})
            write_html(html_path, self.results, {})
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            html_report = html_path.read_text(encoding="utf-8")
        self.assertEqual(payload["results"][0]["count"], 2)
        self.assertEqual(payload["results"][0]["compression_ratio_chars_per_token"], 5.5)
        self.assertEqual(payload["skipped"]["api"], "missing key")
        self.assertIn("id=1", html_report)
        self.assertIn("LLM Tokenizer", html_report)
        self.assertIn("压缩率", html_report)


if __name__ == "__main__":
    unittest.main()
