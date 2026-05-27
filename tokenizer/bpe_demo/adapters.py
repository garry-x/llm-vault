from __future__ import annotations

import json
import os
from dataclasses import dataclass

from bpe_demo.core import TokenPiece, TokenizationResult


class AdapterUnavailable(RuntimeError):
    """Raised when an optional tokenizer cannot be used in this environment."""


def _byte_piece(value: bytes) -> str:
    try:
        return value.decode("utf-8")
    except UnicodeDecodeError:
        return "".join(chr(byte) if 32 <= byte < 127 else f"\\x{byte:02x}" for byte in value)


class OpenAIAdapter:
    name = "OpenAI GPT-4o"
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


@dataclass(frozen=True)
class HuggingFaceSpec:
    name: str
    repository: str
    requires_remote_code: bool = False
    fix_mistral_regex: bool = False


class HuggingFaceAdapter:
    def __init__(self, spec: HuggingFaceSpec, trust_remote_code: bool = False) -> None:
        self.name = spec.name
        self.source = f"huggingface:{spec.repository}"
        if spec.requires_remote_code and not trust_remote_code:
            raise AdapterUnavailable(
                f"{spec.name} 的官方 tokenizer 包含自定义代码；使用 --trust-remote-code 显式允许加载"
            )
        try:
            from transformers import AutoTokenizer
        except ImportError as exc:
            raise AdapterUnavailable("安装依赖后可加载 Hugging Face tokenizers: pip install -e .") from exc
        try:
            options = {"fix_mistral_regex": True} if spec.fix_mistral_regex else {}
            self._tokenizer = AutoTokenizer.from_pretrained(
                spec.repository,
                trust_remote_code=spec.requires_remote_code and trust_remote_code,
                **options,
            )
        except Exception as exc:
            raise AdapterUnavailable(f"无法加载 {spec.repository}: {exc}") from exc

    def tokenize(self, text: str, language: str) -> TokenizationResult:
        ids = self._tokenizer.encode(text, add_special_tokens=False)
        pieces = []
        for token_id in ids:
            decoded = self._tokenizer.decode(
                [token_id], skip_special_tokens=False, clean_up_tokenization_spaces=False
            )
            if "\ufffd" in decoded:
                decoded = self._tokenizer.convert_ids_to_tokens(token_id)
            pieces.append(TokenPiece(token_id=token_id, text=decoded))
        return TokenizationResult(self.name, self.source, language, text, len(ids), pieces)


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


class GrokAdapter:
    name = "xAI Grok-2"
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


HF_SPECS = {
    "kimi": HuggingFaceSpec("Kimi K2 Instruct", "moonshotai/Kimi-K2-Instruct", True),
    "qwen": HuggingFaceSpec("Qwen3 8B", "Qwen/Qwen3-8B"),
    "llama": HuggingFaceSpec("Meta Llama 3.3", "meta-llama/Llama-3.3-70B-Instruct"),
    "mistral": HuggingFaceSpec(
        "Mistral Small 3.1", "mistralai/Mistral-Small-3.1-24B-Instruct-2503", fix_mistral_regex=True
    ),
    "gemma": HuggingFaceSpec("Google Gemma 3", "google/gemma-3-12b-it"),
    "glm": HuggingFaceSpec("Z.ai GLM-4.5", "zai-org/GLM-4.5"),
    "ernie": HuggingFaceSpec("Baidu ERNIE 4.5", "baidu/ERNIE-4.5-21B-A3B-PT"),
    "seed": HuggingFaceSpec("ByteDance Seed OSS", "ByteDance-Seed/Seed-OSS-36B-Instruct"),
    "hunyuan": HuggingFaceSpec("Tencent Hunyuan A13B", "tencent/Hunyuan-A13B-Instruct", True),
    "minimax": HuggingFaceSpec("MiniMax M1", "MiniMaxAI/MiniMax-M1-80k-hf", True),
    "cohere": HuggingFaceSpec("Cohere Command A+", "CohereLabs/command-a-plus-05-2026-bf16"),
    "nemotron": HuggingFaceSpec(
        "NVIDIA Nemotron 3 Nano", "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16", True
    ),
}


def build_adapter(key: str, trust_remote_code: bool, anthropic_model: str, gemini_model: str):
    if key == "openai":
        return OpenAIAdapter()
    if key == "anthropic":
        return AnthropicAdapter(anthropic_model)
    if key == "gemini":
        return GeminiAdapter(gemini_model)
    if key == "deepseek":
        return TokenizersJsonAdapter("DeepSeek V3.2", "deepseek-ai/DeepSeek-V3.2")
    if key == "grok":
        return GrokAdapter()
    return HuggingFaceAdapter(HF_SPECS[key], trust_remote_code)
