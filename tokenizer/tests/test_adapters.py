import io
import json
import os
import unittest
from unittest.mock import patch

from bpe_demo.adapters import GrokAPIAdapter, OpenAIAPIAdapter


class _Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class ApiAdapterTests(unittest.TestCase):
    def test_openai_latest_api_count_response(self):
        payload = _Response(json.dumps({"input_tokens": 7}).encode("utf-8"))
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test"}, clear=True):
            with patch("bpe_demo.adapters.request.urlopen", return_value=payload):
                result = OpenAIAPIAdapter("gpt-5.5").tokenize("sample", "English")
        self.assertEqual(result.count, 7)
        self.assertIsNone(result.pieces)

    def test_grok_latest_api_returns_visible_pieces(self):
        payload = _Response(
            json.dumps(
                {"token_ids": [{"token_id": 10, "string_token": "你"}, {"token_id": 11, "string_token": "好"}]}
            ).encode("utf-8")
        )
        with patch.dict(os.environ, {"XAI_API_KEY": "test"}, clear=True):
            with patch("bpe_demo.adapters.request.urlopen", return_value=payload):
                result = GrokAPIAdapter("grok-4.3").tokenize("你好", "中文")
        self.assertEqual(result.count, 2)
        self.assertEqual([piece.text for piece in result.pieces], ["你", "好"])


if __name__ == "__main__":
    unittest.main()
