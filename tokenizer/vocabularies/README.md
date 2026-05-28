# Tokenizer 词表工件

本目录保存 `TOKENIZER_ANALYSIS.html` 中已公开可复现项目的官方 tokenizer 工件，核验与复制日期为 **2026-05-27**。文件名中包含模型标识，避免不同仓库均名为 `tokenizer.json` 时发生混淆。

这些文件保留官方原始格式：

- `*.tokenizer.json` 包含词表及复现编码所需的 tokenizer 结构信息，例如 merge / pre-tokenizer 配置。
- `*.tiktoken` 或 `*.tiktoken.model` 为 tiktoken mergeable-rank 词表工件。
- `*.tokenizer.tok.json` 为 xAI Grok-2 发布的 tiktoken 格式工件。

## 当前公开工件

| 文件 | 对应模型 / 用途 | 官方来源 |
| --- | --- | --- |
| `kimi-k2.6.tiktoken.model` | Moonshot Kimi K2.6 | https://huggingface.co/moonshotai/Kimi-K2.6 |
| `kimi-k2.6.tokenizer_config.json` | Kimi K2.6 special token 配置 | https://huggingface.co/moonshotai/Kimi-K2.6 |
| `deepseek-v4-pro.tokenizer.json` | DeepSeek V4 Pro | https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro |
| `qwen3.6-27b.tokenizer.json` | Alibaba Qwen3.6 27B | https://huggingface.co/Qwen/Qwen3.6-27B |
| `gemma-4-31b-it.tokenizer.json` | Google Gemma 4 31B IT | https://huggingface.co/google/gemma-4-31B-it |
| `mistral-medium-3.5.tokenizer.json` | Mistral Medium 3.5 | https://huggingface.co/mistralai/Mistral-Medium-3.5-128B |
| `glm-5.1.tokenizer.json` | Z.ai GLM-5.1 | https://huggingface.co/zai-org/GLM-5.1 |
| `ernie-4.5.tokenizer.json` | Baidu ERNIE 4.5 | https://huggingface.co/baidu/ERNIE-4.5-21B-A3B-PT |
| `seed-oss.tokenizer.json` | ByteDance Seed OSS | https://huggingface.co/ByteDance-Seed/Seed-OSS-36B-Instruct |
| `tencent-hy3-preview.tokenizer.json` | Tencent Hy3-preview | https://huggingface.co/tencent/Hy3-preview |
| `minimax-m2.7.tokenizer.json` | MiniMax M2.7 | https://huggingface.co/MiniMaxAI/MiniMax-M2.7 |
| `cohere-command-a-plus-05-2026.tokenizer.json` | Cohere Command A+ 05-2026 | https://huggingface.co/CohereLabs/command-a-plus-05-2026-bf16 |
| `nvidia-nemotron-3-super.tokenizer.json` | NVIDIA Nemotron 3 Super | https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16 |

## 公开基线与历史对照

| 文件 | 对应入口 | 说明 / 来源 |
| --- | --- | --- |
| `openai-o200k_base.tiktoken` | `openai-o200k` | 官方 `tiktoken` 资源；这是本地公开基线，不标称为 GPT-5.5 词表。来源：https://openaipublic.blob.core.windows.net/encodings/o200k_base.tiktoken |
| `xai-grok-2-public.tokenizer.tok.json` | `grok-public` | Grok-2 官方公开下载工件，不标称为 Grok 4.3。来源：https://huggingface.co/xai-org/grok-2 |
| `deepseek-v3.2-history.tokenizer.json` | `deepseek-v3.2` | DeepSeek 历史对照。来源：https://huggingface.co/deepseek-ai/DeepSeek-V3.2 |

## 未包含本地词表的入口

| 当前模型 | 原因 |
| --- | --- |
| OpenAI GPT-5.5 | 本示例通过官方 `responses/input_tokens` API 精确计数；未发现可明确映射到该模型的独立公开下载词表。 |
| Anthropic Claude Opus 4.7 | 官方提供 `messages.count_tokens` API，不发布可作为当前线上模型依据的本地词表。 |
| Google Gemini 3.1 Pro Preview | 官方提供 `models.countTokens` API；Gemma 工件不能替代 Gemini。 |
| xAI Grok 4.3 | 本示例通过官方 `/v1/tokenize-text` API 使用当前模型；下载目录只提供 Grok-2 公开基线。 |
| Meta Llama 4 Maverick | 官方 Hugging Face 仓库要求接受模型许可；当前环境未取得工件。 |

文件完整性可通过同目录的 `SHA256SUMS` 校验。
