from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from bpe_demo.adapters import AdapterUnavailable, build_adapter
from bpe_demo.core import read_sample
from bpe_demo.report import source_text_table, summary_table, token_preview, write_html, write_json

SUPPORTED_MODELS = (
    "openai",
    "openai-o200k",
    "anthropic",
    "gemini",
    "kimi",
    "deepseek",
    "deepseek-v3.2",
    "deepseek-v4-pro",
    "qwen",
    "llama",
    "mistral",
    "gemma",
    "glm",
    "ernie",
    "seed",
    "hunyuan",
    "minimax",
    "grok",
    "grok-public",
    "cohere",
    "nemotron",
)

DEFAULT_MODELS = (
    "openai",
    "openai-o200k",
    "anthropic",
    "gemini",
    "kimi",
    "deepseek",
    "qwen",
    "llama",
    "mistral",
    "gemma",
    "glm",
    "ernie",
    "seed",
    "hunyuan",
    "minimax",
    "grok",
    "grok-public",
    "cohere",
    "nemotron",
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="比较头部 LLM tokenizer 对英文和中文短篇的编码效果。")
    parser.add_argument(
        "--models",
        default=",".join(DEFAULT_MODELS),
        help="逗号分隔的 tokenizer: " + ",".join(SUPPORTED_MODELS),
    )
    parser.add_argument("--english", type=Path, help="替换内置英文测试文本的 UTF-8 文件")
    parser.add_argument("--chinese", type=Path, help="替换内置中文测试文本的 UTF-8 文件")
    parser.add_argument("--preview", type=int, default=20, help="终端展示每种文本的前 N 个 token")
    parser.add_argument("--json", type=Path, help="输出完整 JSON 结果")
    parser.add_argument("--html", type=Path, help="输出彩色 token 切片 HTML 报告")
    parser.add_argument(
        "--trust-remote-code",
        action="store_true",
        help="兼容保留参数；当前默认适配器不执行 Hugging Face 远程代码",
    )
    parser.add_argument(
        "--openai-model",
        default=os.environ.get("OPENAI_MODEL", "gpt-5.5"),
        help="OpenAI responses/input_tokens 使用的 model id",
    )
    parser.add_argument(
        "--anthropic-model",
        default=os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-7"),
        help="Anthropic count_tokens 使用的 model id",
    )
    parser.add_argument(
        "--gemini-model",
        default=os.environ.get("GEMINI_MODEL", "gemini-3.1-pro-preview"),
        help="Google countTokens 使用的 model id",
    )
    parser.add_argument(
        "--grok-model",
        default=os.environ.get("GROK_MODEL", "grok-4.3"),
        help="xAI tokenize-text 使用的 model id",
    )
    return parser.parse_args(argv)


def _model_keys(value: str) -> list[str]:
    keys = [key.strip().lower() for key in value.split(",") if key.strip()]
    invalid = [key for key in keys if key not in SUPPORTED_MODELS]
    if invalid:
        raise ValueError(f"不支持的 model: {', '.join(invalid)}")
    return list(dict.fromkeys(keys))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        models = _model_keys(args.models)
        texts = {"English": read_sample("English", args.english), "中文": read_sample("中文", args.chinese)}
    except (ValueError, OSError) as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 2

    results = []
    skipped: dict[str, str] = {}
    for key in models:
        try:
            adapter = build_adapter(
                key,
                args.trust_remote_code,
                args.openai_model,
                args.anthropic_model,
                args.gemini_model,
                args.grok_model,
            )
            results.extend(adapter.tokenize(text, language) for language, text in texts.items())
        except AdapterUnavailable as exc:
            skipped[key] = str(exc)
        except Exception as exc:
            skipped[key] = f"编码失败: {exc}"

    if skipped:
        print("跳过:")
        for key, reason in skipped.items():
            print(f"  {key}: {reason}")
        print()
    if not results:
        print("没有可用的 tokenizer 结果。", file=sys.stderr)
        return 1

    print("测试原文大小:")
    print(source_text_table(results))
    print("\n压缩率 = 原文字符数 / token 数 (chars/token)，数值越高表示编码更紧凑。\n")
    print(summary_table(results))
    if args.preview > 0:
        print("\nToken preview:")
        for result in results:
            print(token_preview(result, args.preview))
    if args.json:
        write_json(args.json, results, skipped)
        print(f"\nJSON report: {args.json}")
    if args.html:
        write_html(args.html, results, skipped)
        print(f"HTML report: {args.html}")
    return 0
