#!/usr/bin/env python3
"""Encode and decode text with tokenizer vocab files in ../vocab.

Examples:
  python examples/tokenize_text.py
  python examples/tokenize_text.py --tokenizer vocab/deepseek-v4-pro.tokenizer.json --text "你好，tokenizer"
  python examples/tokenize_text.py --tokenizer vocab/openai-o200k_base.tiktoken --text-file res/original_novel_en.txt
  python examples/tokenize_text.py --tokenizer vocab/kimi-k2.6.tiktoken.model --config vocab/kimi-k2.6.tokenizer_config.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable


# tiktoken's o200k pattern. It is used here for local .tiktoken files because
# those files contain merge ranks but not the regex pre-tokenizer definition.
O200K_PAT_STR = (
    r"""[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]*"""
    r"""\p{Ll}[\p{L}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?"""
    r"""|[^\r\n\p{L}\p{N}]?[\p{Lu}\p{Lt}\p{Lm}\p{Lo}\p{M}]+"""
    r"""[\p{Ll}\p{Lm}\p{Lo}\p{M}]*(?i:'s|'t|'re|'ve|'m|'ll|'d)?"""
    r"""|\p{N}{1,3}"""
    r"""| ?[^\s\p{L}\p{N}]+[\r\n/]*"""
    r"""|\s*[\r\n]+"""
    r"""|\s+(?!\S)"""
    r"""|\s+"""
)


DEFAULT_TEXT = "雾港灯塔准时亮起。The lighthouse turned on at exactly midnight."
DECODED_PREVIEW_CHARS = 20


def die_missing(package: str) -> None:
    print(
        f"Missing dependency: {package}\n"
        "Install dependencies with:\n"
        "  python -m pip install -r requirements.txt",
        file=sys.stderr,
    )
    raise SystemExit(2)


def load_text(args: argparse.Namespace) -> str:
    if args.text is not None:
        return args.text
    if args.text_file is not None:
        return Path(args.text_file).read_text(encoding="utf-8")
    return DEFAULT_TEXT


def load_special_tokens(config_path: str | None) -> dict[str, int]:
    if not config_path:
        return {}

    config = json.loads(Path(config_path).read_text(encoding="utf-8"))
    decoder = config.get("added_tokens_decoder", {})
    special_tokens: dict[str, int] = {}

    for token_id, item in decoder.items():
        if item.get("special"):
            special_tokens[item["content"]] = int(token_id)

    return special_tokens


def encode_with_tokenizers(tokenizer_path: Path, text: str) -> tuple[list[int], str, list[str]]:
    try:
        from tokenizers import Tokenizer
    except ImportError:
        die_missing("tokenizers")

    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    encoded = tokenizer.encode(text)
    ids = encoded.ids
    decoded = tokenizer.decode(ids, skip_special_tokens=False)
    return ids, decoded, encoded.tokens


def encode_with_tiktoken(
    tokenizer_path: Path,
    text: str,
    config_path: str | None,
    allowed_special: set[str],
) -> tuple[list[int], str, list[str]]:
    try:
        import tiktoken
        from tiktoken.load import load_tiktoken_bpe
    except ImportError:
        die_missing("tiktoken")

    mergeable_ranks = load_tiktoken_bpe(str(tokenizer_path))
    special_tokens = load_special_tokens(config_path)
    encoding = tiktoken.Encoding(
        name=tokenizer_path.stem,
        pat_str=O200K_PAT_STR,
        mergeable_ranks=mergeable_ranks,
        special_tokens=special_tokens,
    )

    ids = encoding.encode(text, allowed_special=allowed_special)
    decoded = encoding.decode(ids)
    pieces = [encoding.decode_single_token_bytes(token_id).decode("utf-8", errors="replace") for token_id in ids]
    return ids, decoded, pieces


def format_ids(ids: Iterable[int], limit: int) -> str:
    values = list(ids)
    shown = values[:limit]
    suffix = "" if len(values) <= limit else f" ... (+{len(values) - limit} more)"
    return ", ".join(str(item) for item in shown) + suffix


def preview_text(text: str, limit: int = DECODED_PREVIEW_CHARS) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + "..."


def main() -> int:
    parser = argparse.ArgumentParser(description="Encode and decode text with a local tokenizer vocab file.")
    parser.add_argument(
        "--tokenizer",
        default="vocab/qwen3.6-27b.tokenizer.json",
        help="Path to a vocab file. Supports *.tokenizer.json, *.tiktoken, and *.tiktoken.model.",
    )
    parser.add_argument("--config", help="Optional tokenizer_config.json, useful for tiktoken special tokens.")
    parser.add_argument("--text", help="Text to encode. Defaults to a short bilingual sample.")
    parser.add_argument("--text-file", help="Read text from a UTF-8 file instead of --text.")
    parser.add_argument("--show", type=int, default=80, help="Maximum number of token ids/pieces to print.")
    parser.add_argument(
        "--allow-special",
        action="append",
        default=[],
        help="Allow a special token during tiktoken encoding. Can be repeated, or use 'all'.",
    )
    args = parser.parse_args()

    tokenizer_path = Path(args.tokenizer)
    if not tokenizer_path.exists():
        print(f"Tokenizer file not found: {tokenizer_path}", file=sys.stderr)
        return 1

    text = load_text(args)
    allowed_special = set(args.allow_special)
    if "all" in allowed_special:
        allowed_special = "all"  # type: ignore[assignment]

    if tokenizer_path.suffix == ".json":
        ids, decoded, pieces = encode_with_tokenizers(tokenizer_path, text)
        backend = "tokenizers"
    elif tokenizer_path.suffix == ".tiktoken" or tokenizer_path.name.endswith(".tiktoken.model"):
        ids, decoded, pieces = encode_with_tiktoken(tokenizer_path, text, args.config, allowed_special)
        backend = "tiktoken"
    else:
        print(f"Unsupported tokenizer format: {tokenizer_path}", file=sys.stderr)
        return 1

    print(f"Tokenizer: {tokenizer_path}")
    print(f"Backend:   {backend}")
    print(f"Chars:     {len(text)}")
    print(f"Tokens:    {len(ids)}")
    print(f"Roundtrip: {decoded == text}")
    print()
    print("Token ids:")
    print(format_ids(ids, args.show))
    print()
    print("Token pieces:")
    print(repr(pieces[: args.show]) + ("" if len(pieces) <= args.show else f" ... (+{len(pieces) - args.show} more)"))
    print()
    print("Decoded text:")
    print(preview_text(decoded))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
