from __future__ import annotations

import html
import json
from pathlib import Path

from bpe_demo.core import TokenPiece, TokenizationResult


def _visible(text: str) -> str:
    return text.replace(" ", "␠").replace("\n", "↵\n").replace("\t", "⇥")


def source_text_table(results: list[TokenizationResult]) -> str:
    source_results: dict[str, TokenizationResult] = {}
    for result in results:
        source_results.setdefault(result.language, result)
    headers = ["原文", "字符数", "UTF-8 字节数"]
    rows = [
        [language, str(result.char_count), str(result.byte_count)]
        for language, result in source_results.items()
    ]
    widths = [max(len(row[index]) for row in [headers, *rows]) for index in range(len(headers))]
    render = lambda row: " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
    return "\n".join([render(headers), "-+-".join("-" * width for width in widths), *(render(row) for row in rows)])


def summary_table(results: list[TokenizationResult]) -> str:
    by_model: dict[str, dict[str, TokenizationResult]] = {}
    for result in results:
        by_model.setdefault(result.model, {})[result.language] = result
    headers = ["Tokenizer", "英文 tokens", "英文压缩率 chars/token", "中文 tokens", "中文压缩率 chars/token", "ZH/EN tokens"]
    rows: list[list[str]] = []
    for model, language_results in by_model.items():
        en = language_results.get("English")
        zh = language_results.get("中文")
        rows.append(
            [
                model,
                str(en.count) if en else "-",
                f"{en.chars_per_token:.2f}" if en else "-",
                str(zh.count) if zh else "-",
                f"{zh.chars_per_token:.2f}" if zh else "-",
                f"{zh.count / en.count:.2f}" if en and zh and en.count else "-",
            ]
        )
    widths = [max(len(row[index]) for row in [headers, *rows]) for index in range(len(headers))]
    render = lambda row: " | ".join(cell.ljust(widths[index]) for index, cell in enumerate(row))
    return "\n".join([render(headers), "-+-".join("-" * width for width in widths), *(render(row) for row in rows)])


def token_preview(result: TokenizationResult, limit: int) -> str:
    if result.pieces is None:
        return f"{result.model} / {result.language}: {result.note}"
    values = [f"{piece.token_id}:{_visible(piece.text)!r}" for piece in result.pieces[:limit]]
    suffix = f" ... (+{result.count - limit})" if result.count > limit else ""
    return f"{result.model} / {result.language}: " + " | ".join(values) + suffix


def write_json(path: Path, results: list[TokenizationResult], skipped: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"results": [result.as_dict() for result in results], "skipped": skipped}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _token_spans(pieces: list[TokenPiece] | None) -> str:
    if pieces is None:
        return '<p class="muted">该接口不提供 token 切片。</p>'
    spans = []
    for index, piece in enumerate(pieces):
        value = html.escape(_visible(piece.text))
        spans.append(f'<span class="t t{index % 6}" title="id={piece.token_id}">{value}</span>')
    return "".join(spans)


def write_html(path: Path, results: list[TokenizationResult], skipped: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text_metrics: dict[str, TokenizationResult] = {}
    for result in results:
        text_metrics.setdefault(result.language, result)
    metrics = "".join(
        f"<tr><td>{html.escape(language)}</td><td>{result.char_count}</td><td>{result.byte_count}</td></tr>"
        for language, result in text_metrics.items()
    )
    cards = []
    for result in results:
        cards.append(
            f"""<section class="card">
<h2>{html.escape(result.model)} <small>{html.escape(result.language)}</small></h2>
<p><strong>{result.count}</strong> tokens · 压缩率 <strong>{result.compression_ratio:.2f}</strong> chars/token
<br><code>{html.escape(result.source)}</code></p>
<div class="tokens">{_token_spans(result.pieces)}</div>
<p class="muted">{html.escape(result.note)}</p>
</section>"""
        )
    skip_items = "".join(f"<li><strong>{html.escape(key)}</strong>: {html.escape(reason)}</li>" for key, reason in skipped.items())
    document = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>LLM Tokenizer 中英文对比</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 1100px; margin: 32px auto; padding: 0 20px; color: #18212b; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fit,minmax(460px,1fr)); gap: 18px; }}
.card {{ border: 1px solid #d9e0e8; border-radius: 12px; padding: 16px; }}
h1 {{ margin-bottom: 6px; }} h2 {{ margin: 0 0 10px; font-size: 18px; }} small {{ color: #617184; font-weight: normal; }}
.tokens {{ line-height: 2.25; white-space: pre-wrap; overflow-wrap: anywhere; }}
.t {{ padding: 4px 3px; border-radius: 4px; margin-right: 1px; }}
.t0 {{ background:#e1f1ff }} .t1 {{ background:#e5f7eb }} .t2 {{ background:#fff0d9 }}
.t3 {{ background:#f5e8ff }} .t4 {{ background:#ffe7ec }} .t5 {{ background:#e8f3f1 }}
.muted {{ color: #617184; font-size: 13px; }} code {{ font-size: 12px; }}
table {{ border-collapse: collapse; margin: 16px 0 24px; }} td, th {{ border: 1px solid #d9e0e8; padding: 7px 12px; text-align: left; }}
</style></head><body>
<h1>LLM Tokenizer 中英文对比</h1>
<p class="muted">压缩率 = 原文字符数 / token 数（chars/token），越高表示单位 token 覆盖字符越多。悬停彩色片段可查看 token id；空格显示为 ␠，换行显示为 ↵。</p>
<h2>测试原文大小</h2><table><thead><tr><th>原文</th><th>字符数</th><th>UTF-8 字节数</th></tr></thead><tbody>{metrics}</tbody></table>
{"<h2>跳过的 tokenizer</h2><ul>" + skip_items + "</ul>" if skipped else ""}
<div class="cards">{''.join(cards)}</div>
</body></html>"""
    path.write_text(document, encoding="utf-8")
