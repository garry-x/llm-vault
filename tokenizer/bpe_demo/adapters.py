from __future__ import annotations

import json
import os
from urllib import request

from bpe_demo.core import TokenPiece, TokenizationResult


class AdapterUnavailable(RuntimeError):
    """Raised when an optional tokenizer cannot be used in this environment."""


def _byte_piece(value: bytes) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return "".join(chr(byte) if 32 <= byte < 127 else f"\\x{byte:02x}" for byte in value)


class OpenAILocalAdapter:
    name = "OpenAI o200k_base (公开本地基线)"
    source = "tiktoken:o200k_base"

    def __init__(self) -> None:
        try:
            import tiktoken
        except ImportError as exc:
            raise AdapterUnavailable("安装依赖后可加载 OpenAI tokenizer: pip install -e .") from exc
        self._encoding = tiktoken.get_encoding("o200k_base")

    def tokenize(self, text: str, language: str) -> TokenizationResult:
        ids = self._encoding.encode(text)
        pieces = [
            TokenPiece(token_id=token_id, text=_byte_piece(self._encoding.decode_single_token_bytes(token_id)))
            for token_id in ids
        ]
        return TokenizationResult(self.name, self.source, language, text, len(ids), pieces)


class OpenAIAPIAdapter:
    source = "api:responses.input_tokens"

    def __init__(self, model: str) -> None:
        self.model = model
        self.name = f"OpenAI ({model})"
        self._api_key = os.environ.get("OPENAI_API_KEY")
        if not self._api_key:
            raise AdapterUnavailable("设置 OPENAI_API_KEY 后可调用 OpenAI 官方 input_tokens 接口")

    def tokenize(self, text: str, language: str) -> TokenizationResult:
        body = json.dumps({"model": self.model, "input": text}).encode("utf-8")
        http_request = request.Request(
            "https://api.openai.com/v1/responses/input_tokens",
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=60) as response:
                count = json.load(response)["input_tokens"]
        except Exception as exc:
            raise AdapterUnavailable(f"OpenAI input_tokens 请求失败: {exc}") from exc
        note = "官方 API 仅返回该模型输入 token 总数，不公开逐 token 切片。"
        return TokenizationResult(self.name, self.source, language, text, count, None, note)


class AnthropicAdapter:
    source = "api:messages.count_tokens"

    def __init__(self, model: str) -> None:
        self.model = model
        self.name = f"Anthropic Claude ({model})"
        if not os.environ.get("ANTHROPIC_API_KEY"):
            raise AdapterUnavailable("设置 ANTHROPIC_API_KEY 后可调用 Claude 官方计数接口")
        try:
            from anthropic import Anthropic
        except ImportError as exc:
            raise AdapterUnavailable("安装依赖后可调用 Anthropic: pip install -e .") from exc
        self._client = Anthropic()

    def tokenize(self, text: str, language: str) -> TokenizationResult:
        response = self._client.messages.count_tokens(
            model=self.model,
            messages=[{"role": "user", "content": text}],
        )
        note = "官方 API 只返回消息输入 token 总数，包含消息封装开销，不公开逐 token 切片。"
        return TokenizationResult(self.name, self.source, language, text, response.input_tokens, None, note)


class GeminiAdapter:
    source = "api:models.countTokens"

    def __init__(self, model: str) -> None:
        self.model = model
        self.name = f"Google Gemini ({model})"
        api_key = os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise AdapterUnavailable("设置 GEMINI_API_KEY 后可调用 Gemini 官方计数接口")
        try:
            from google import genai
        except ImportError as exc:
            raise AdapterUnavailable("安装依赖后可调用 Gemini: pip install -e .") from exc
        self._client = genai.Client(api_key=api_key)

    def tokenize(self, text: str, language: str) -> TokenizationResult:
        response = self._client.models.count_tokens(model=self.model, contents=text)
        note = "官方 API 只返回 token 总数，不公开逐 token 切片。"
        return TokenizationResult(self.name, self.source, language, text, response.total_tokens, None, note)


class TokenizersJsonAdapter:
    def __init__(self, name: str, repository: str, filename: str = "tokenizer.json") -> None:
        self.name = name
        self.source = f"huggingface:{repository}/{filename}"
        try:
            from huggingface_hub import hf_hub_download
            from tokenizers import Tokenizer
        except ImportError as exc:
            raise AdapterUnavailable("安装依赖后可加载 tokenizer.json 工件: pip install -e .") from exc
        try:
            path = hf_hub_download(repo_id=repository, filename=filename)
            self._tokenizer = Tokenizer.from_file(path)
        except Exception as exc:
            raise AdapterUnavailable(f"无法解析 {repository}/{filename}: {exc}") from exc

    def tokenize(self, text: str, language: str) -> TokenizationResult:
        encoding = self._tokenizer.encode(text, add_special_tokens=False)
        pieces = [
            TokenPiece(token_id=token_id, text=self._tokenizer.decode([token_id], skip_special_tokens=False))
            for token_id in encoding.ids
        ]
        return TokenizationResult(self.name, self.source, language, text, len(encoding.ids), pieces)


class KimiAdapter:
    name = "Moonshot Kimi K2.6"
    source = "huggingface:moonshotai/Kimi-K2.6/tiktoken.model"
    repository = "moonshotai/Kimi-K2.6"
    pattern = "|".join(
        [
            r"[\p{Han}]+",
            r"[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}&&[^\p{Han}]]*[\p{Ll}\p{Lm}\p{Lo}\p{M}&&[^\p{Han}]]+(?i:'s|'t|'re|'ve|'m|'ll|'d)?",
            r"[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}&&[^\p{Han}]]+[\p{Ll}\p{Lm}\p{Lo}\p{M}&&[^\p{Han}]]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?",
            r"\p{N}{1,3}",
            r" ?[^\s\p{L}\p{N}]+[\r\n]*",
            r"\s*[\r\n]+",
            r"\s+(?!\S)",
            r"\s+",
        ]
    )

    def __init__(self) -> None:
        try:
            from huggingface_hub import hf_hub_download
            import tiktoken
            from tiktoken.load import load_tiktoken_bpe
        except ImportError as exc:
            raise AdapterUnavailable("安装依赖后可加载 Kimi tiktoken 工件: pip install -e .") from exc
        try:
            model_path = hf_hub_download(repo_id=self.repository, filename="tiktoken.model")
            config_path = hf_hub_download(repo_id=self.repository, filename="tokenizer_config.json")
            with open(config_path, encoding="utf-8") as handle:
                decoder = json.load(handle).get("added_tokens_decoder", {})
            mergeable_ranks = load_tiktoken_bpe(model_path)
            base = len(mergeable_ranks)
            special_tokens = {
                decoder.get(str(token_id), {}).get("content", f"<|reserved_token_{token_id}|>"): token_id
                for token_id in range(base, base + 256)
            }
            self._encoding = tiktoken.Encoding(
                name="kimi-k2.6",
                pat_str=self.pattern,
                mergeable_ranks=mergeable_ranks,
                special_tokens=special_tokens,
            )
        except Exception as exc:
            raise AdapterUnavailable(f"无法解析 {self.repository}/tiktoken.model: {exc}") from exc

    def tokenize(self, text: str, language: str) -> TokenizationResult:
        ids = self._encoding.encode(text, allowed_special="all")
        pieces = [
            TokenPiece(token_id=token_id, text=_byte_piece(self._encoding.decode_single_token_bytes(token_id)))
            for token_id in ids
        ]
        return TokenizationResult(self.name, self.source, language, text, len(ids), pieces)


class GrokPublicAdapter:
    name = "xAI Grok-2 (最新公开 tokenizer 工件)"
    source = "huggingface:xai-org/grok-2/tokenizer.tok.json"

    def __init__(self) -> None:
        try:
            from huggingface_hub import hf_hub_download
            import tiktoken
        except ImportError as exc:
            raise AdapterUnavailable("安装依赖后可加载 Grok tokenizer 工件: pip install -e .") from exc
        try:
            path = hf_hub_download(repo_id="xai-org/grok-2", filename="tokenizer.tok.json")
            with open(path, encoding="utf-8") as handle:
                payload = json.load(handle)
            mergeable_ranks = {bytes(item["bytes"]): item["token"] for item in payload["regular_tokens"]}
            special_tokens = {bytes(item["bytes"]).decode(): item["token"] for item in payload["special_tokens"]}
            if payload["word_split"] != "V1":
                raise ValueError(f"unsupported word_split={payload['word_split']}")
            pattern = (
                r"(?i:'s|'t|'re|'ve|'m|'ll|'d)|[^\r\n\p{L}\p{N}]?\p{L}+|\p{N}|"
                r" ?[^\s\p{L}\p{N}]+[\r\n]*|\s*[\r\n]+|\s+(?!\S)|\s+"
            )
            self._encoding = tiktoken.Encoding(
                name="xai-grok-2",
                pat_str=payload.get("pat_str", pattern),
                mergeable_ranks=mergeable_ranks,
                special_tokens=special_tokens,
                explicit_n_vocab=payload.get("vocab_size"),
            )
        except Exception as exc:
            raise AdapterUnavailable(f"无法解析 xai-org/grok-2/tokenizer.tok.json: {exc}") from exc

    def tokenize(self, text: str, language: str) -> TokenizationResult:
        ids = self._encoding.encode(text, disallowed_special=())
        pieces = [
            TokenPiece(token_id=token_id, text=_byte_piece(self._encoding.decode_single_token_bytes(token_id)))
            for token_id in ids
        ]
        return TokenizationResult(self.name, self.source, language, text, len(ids), pieces)


class GrokAPIAdapter:
    source = "api:/v1/tokenize-text"

    def __init__(self, model: str) -> None:
        self.model = model
        self.name = f"xAI Grok ({model})"
        self._api_key = os.environ.get("XAI_API_KEY")
        if not self._api_key:
            raise AdapterUnavailable("设置 XAI_API_KEY 后可调用 xAI 官方 tokenize-text 接口")

    def tokenize(self, text: str, language: str) -> TokenizationResult:
        body = json.dumps({"model": self.model, "text": text}).encode("utf-8")
        http_request = request.Request(
            "https://api.x.ai/v1/tokenize-text",
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with request.urlopen(http_request, timeout=60) as response:
                tokens = json.load(response)["token_ids"]
        except Exception as exc:
            raise AdapterUnavailable(f"xAI tokenize-text 请求失败: {exc}") from exc
        pieces = [TokenPiece(token_id=token["token_id"], text=token["string_token"]) for token in tokens]
        return TokenizationResult(self.name, self.source, language, text, len(pieces), pieces)


JSON_SPECS = {
    "qwen": ("Alibaba Qwen3.6 27B", "Qwen/Qwen3.6-27B"),
    "llama": ("Meta Llama 4 Maverick", "meta-llama/Llama-4-Maverick-17B-128E-Instruct"),
    "mistral": ("Mistral Medium 3.5", "mistralai/Mistral-Medium-3.5-128B"),
    "gemma": ("Google Gemma 4 31B IT", "google/gemma-4-31B-it"),
    "glm": ("Z.ai GLM-5.1", "zai-org/GLM-5.1"),
    "ernie": ("Baidu ERNIE 4.5", "baidu/ERNIE-4.5-21B-A3B-PT"),
    "seed": ("ByteDance Seed OSS", "ByteDance-Seed/Seed-OSS-36B-Instruct"),
    "hunyuan": ("Tencent Hy3-preview", "tencent/Hy3-preview"),
    "minimax": ("MiniMax M2.7", "MiniMaxAI/MiniMax-M2.7"),
    "cohere": ("Cohere Command A+", "CohereLabs/command-a-plus-05-2026-bf16"),
    "nemotron": ("NVIDIA Nemotron 3 Super", "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16"),
}


def build_adapter(
    key: str,
    trust_remote_code: bool,
    openai_model: str,
    anthropic_model: str,
    gemini_model: str,
    grok_model: str,
):
    if key == "openai":
        return OpenAIAPIAdapter(openai_model)
    if key == "openai-o200k":
        return OpenAILocalAdapter()
    if key == "anthropic":
        return AnthropicAdapter(anthropic_model)
    if key == "gemini":
        return GeminiAdapter(gemini_model)
    if key in {"deepseek", "deepseek-v4-pro"}:
        return TokenizersJsonAdapter("DeepSeek V4 Pro", "deepseek-ai/DeepSeek-V4-Pro")
    if key == "deepseek-v3.2":
        return TokenizersJsonAdapter("DeepSeek V3.2 (历史对照)", "deepseek-ai/DeepSeek-V3.2")
    if key == "kimi":
        return KimiAdapter()
    if key == "grok":
        return GrokAPIAdapter(grok_model)
    if key == "grok-public":
        return GrokPublicAdapter()
    name, repository = JSON_SPECS[key]
    return TokenizersJsonAdapter(name, repository)
