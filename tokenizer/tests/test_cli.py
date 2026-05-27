import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from bpe_demo.cli import _model_keys, main
from bpe_demo.core import TokenPiece, TokenizationResult


class DummyAdapter:
    name = "Dummy"
    source = "test"

    def tokenize(self, text, language):
        return TokenizationResult(self.name, self.source, language, text, 1, [TokenPiece(1, text)])


class CliTests(unittest.TestCase):
    def test_all_declared_models_are_accepted(self):
        keys = _model_keys("openai,gemini,deepseek-v4-pro,glm,ernie,seed,hunyuan,minimax,grok,cohere,nemotron")
        self.assertEqual(keys[-1], "nemotron")

    def test_cli_writes_reports(self):
        with tempfile.TemporaryDirectory() as directory:
            html_path = Path(directory) / "output.html"
            json_path = Path(directory) / "output.json"
            stdout = io.StringIO()
            with patch("bpe_demo.cli.build_adapter", return_value=DummyAdapter()):
                with redirect_stdout(stdout):
                    status = main(
                        ["--models", "openai", "--preview", "0", "--html", str(html_path), "--json", str(json_path)]
                    )
            self.assertEqual(status, 0)
            self.assertTrue(html_path.exists())
            self.assertTrue(json_path.exists())
            self.assertIn("测试原文大小", stdout.getvalue())
            self.assertIn("英文压缩率", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
