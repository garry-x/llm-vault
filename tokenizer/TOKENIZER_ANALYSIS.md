# 头部模型 Tokenizer 分析

本文分析示例程序覆盖的模型家族使用何种 tokenizer 资源、是否可以精确复现，以及同一篇中英双语短篇的编码表现。核验日期为 **2026-05-27**。

## 结论摘要

1. 默认模型入口已按可获取的官方信息升级：OpenAI `gpt-5.5`、Claude `claude-opus-4-7`、Gemini `gemini-3.1-pro-preview`、Kimi K2.6、DeepSeek V4 Pro、Qwen3.6、GLM-5.1、MiniMax M2.7、Mistral Medium 3.5、Gemma 4、Hy3-preview 和 Nemotron 3 Super 等。
2. “最新服务模型”不一定等于“可下载 tokenizer”。OpenAI GPT-5.5 使用官方计数 API；xAI Grok 4.3 使用官方切片 API。`o200k_base` 和 Grok-2 仅作为无需密钥的公开本地基线展示。
3. 本次实际验证的最新版公开 tokenizer 中，中文最紧凑的是 `Kimi K2.6`（233 tokens，`1.64 chars/token`），其次是 `MiniMax M2.7`（243，`1.57`）。
4. 英文结果仍较集中：公开验证集合为 224 至 245 tokens；中文从 233 至 376 tokens，分化明显更大。
5. `Qwen3.6 27B` 将本样本中文 token 数由此前 Qwen3 8B 的 268 降到 256；版本变动本身会改变成本估计，不能只记录厂商品牌。

## 比较口径

内置测试材料为同一篇原创微型小说《港口的钟》的英文版和中文版：

| 语言 | 原文字符数 | UTF-8 字节数 |
| --- | ---: | ---: |
| English | 1089 | 1089 |
| 中文 | 381 | 1123 |

```text
压缩率 = 原文字符数 / token 数，单位 chars/token
```

数值越高表示同等 token 预算覆盖更多该语言字符。中英文是语义对应的翻译，并非等长文本；结果适合在同一语言内横向比较 tokenizer。公开本地 tokenizer 编码纯文本，不附加 chat template 或 special tokens；官方 API 结果依照各接口口径展示。

## 最新版本核验

| 厂商 / 家族 | 当前选择 | 本程序精确路径 | 说明 |
| --- | --- | --- | --- |
| OpenAI | GPT-5.5 | `responses/input_tokens` API | 官方模型页称其为 newest frontier model；本地 `o200k_base` 仅另列基线 |
| Anthropic | Claude Opus 4.7 | `messages.count_tokens` API | 官方模型总览的最强通用可用模型 |
| Google Gemini | Gemini 3.1 Pro Preview | `models.countTokens` API | API 模型；与 Gemma 不共用本地结论 |
| Google Gemma | Gemma 4 31B IT | 官方 `tokenizer.json` | 可下载开放模型 tokenizer |
| Moonshot | Kimi K2.6 | 官方 `tiktoken.model` | 官方组织 2026-05-19 更新的最新 Kimi 文本模型仓库 |
| DeepSeek | DeepSeek V4 Pro | 官方 `tokenizer.json` | 官方组织当前最新 V4 Pro 仓库 |
| Alibaba | Qwen3.6 27B | 官方 `tokenizer.json` | 官方模型卡称为 Qwen3.6 首个 open-weight 变体 |
| Meta | Llama 4 Maverick | 官方 `tokenizer.json` | 当前 Llama 4 代表，仓库需许可；未计入本地表 |
| Mistral | Mistral Medium 3.5 128B | 官方 `tokenizer.json` | 官方组织最新通用文本模型仓库 |
| Z.ai / 智谱 | GLM-5.1 | 官方 `tokenizer.json` | 最新通用 GLM 文本仓库 |
| Baidu | ERNIE 4.5 | 官方 `tokenizer.json` | 可获取的最新 ERNIE 文本 tokenizer；更新的公开条目以视觉/OCR 为主 |
| ByteDance | Seed OSS | 官方 `tokenizer.json` | 可获取的官方通用文本 tokenizer |
| Tencent | Hy3-preview | 官方 `tokenizer.json` | 最新通用模型；更新的 Hy-MT2 为翻译专用，未作为通用代表 |
| MiniMax | MiniMax M2.7 | 官方 `tokenizer.json` | 官方组织当前最新通用文本仓库 |
| xAI | Grok 4.3 | `/v1/tokenize-text` API | 官方模型页 2026-05-15 推荐的通用模型；Grok-2 仅本地基线 |
| Cohere | Command A+ 05-2026 | 官方 `tokenizer.json` | 官方组织最新 Command A+ 发布 |
| NVIDIA | Nemotron 3 Super | 官方 `tokenizer.json` | 替代此前 Nano 入口 |

## 已验证公开 Tokenizer

下表数据来自本工作区实际下载并运行的官方公开 tokenizer 资源。OpenAI 与 xAI 的本地行被清楚标记为公开基线，而不是最新托管模型 API 的结果；最新 API 项需相应密钥才会加入输出。

| 模型 / 基线 | 加载机制 | 词表规模 | 英文 tokens | 英文压缩率 | 中文 tokens | 中文压缩率 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| OpenAI `o200k_base`（公开基线） | `tiktoken` | 200,019 | 226 | 4.82 | 324 | 1.18 |
| Moonshot Kimi K2.6 | `tiktoken.model` | 163,840 | 227 | 4.80 | 233 | 1.64 |
| DeepSeek V4 Pro | `tokenizer.json` | 129,280 | 226 | 4.82 | 256 | 1.49 |
| Alibaba Qwen3.6 27B | `tokenizer.json` | 248,070 | 230 | 4.73 | 256 | 1.49 |
| Google Gemma 4 31B IT | `tokenizer.json` | 262,144 | 231 | 4.71 | 294 | 1.30 |
| Mistral Medium 3.5 | `tokenizer.json` | 131,072 | 229 | 4.76 | 376 | 1.01 |
| Z.ai GLM-5.1 | `tokenizer.json` | 154,856 | 226 | 4.82 | 263 | 1.45 |
| Baidu ERNIE 4.5 | `tokenizer.json` | 101,304 | 245 | 4.44 | 273 | 1.40 |
| ByteDance Seed OSS | `tokenizer.json` | 155,121 | 231 | 4.71 | 260 | 1.47 |
| Tencent Hy3-preview | `tokenizer.json` | 120,818 | 232 | 4.69 | 257 | 1.48 |
| MiniMax M2.7 | `tokenizer.json` | 200,054 | 225 | 4.84 | 243 | 1.57 |
| xAI Grok-2（公开基线） | `tokenizer.tok.json` | 131,072 | 224 | 4.86 | 291 | 1.31 |
| Cohere Command A+ | `tokenizer.json` | 255,032 | 224 | 4.86 | 282 | 1.35 |
| NVIDIA Nemotron 3 Super | `tokenizer.json` | 131,072 | 229 | 4.76 | 376 | 1.01 |

### 中文表现

| 排名 | 模型 / 基线 | 中文 tokens | 中文压缩率 |
| ---: | --- | ---: | ---: |
| 1 | Moonshot Kimi K2.6 | 233 | 1.64 |
| 2 | MiniMax M2.7 | 243 | 1.57 |
| 3 | DeepSeek V4 Pro | 256 | 1.49 |
| 3 | Alibaba Qwen3.6 27B | 256 | 1.49 |
| 5 | Tencent Hy3-preview | 257 | 1.48 |
| 6 | ByteDance Seed OSS | 260 | 1.47 |
| 7 | Z.ai GLM-5.1 | 263 | 1.45 |
| 8 | Baidu ERNIE 4.5 | 273 | 1.40 |
| 9 | Cohere Command A+ | 282 | 1.35 |
| 10 | xAI Grok-2（公开基线） | 291 | 1.31 |
| 11 | Google Gemma 4 31B IT | 294 | 1.30 |
| 12 | OpenAI `o200k_base`（公开基线） | 324 | 1.18 |
| 13 | Mistral Medium 3.5 | 376 | 1.01 |
| 13 | NVIDIA Nemotron 3 Super | 376 | 1.01 |

Kimi K2.6 相比 Mistral Medium 3.5 / Nemotron 3 Super 在该中文文本上减少 143 tokens，减少约 38.0%。这只描述 tokenizer 对该语料的上下文占用，不是模型生成质量排名。

### 英文表现

英文最少的是 Grok-2 公开基线和 Cohere Command A+（224 tokens，`4.86 chars/token`）；MiniMax M2.7 为 225；最多为 ERNIE 4.5（245）。最新版公开模型在普通英文叙事文本上的跨度仅 21 tokens，显著小于中文跨度。

## 实现边界

- OpenAI：`openai` 入口调用 GPT-5.5 官方 input token API；`openai-o200k` 只表示可本地可视化的 `o200k_base`，不推断为 GPT-5.5 的公开映射。
- Claude 与 Gemini：仅使用官方计数 API，不用第三方 tokenizer 模拟真实线上切分。
- xAI：`grok` 通过官方 `/v1/tokenize-text` 测 Grok 4.3 并可返回切片；`grok-public` 复现官方公开的 Grok-2 下载工件。
- Kimi：K2.6 发布 `tiktoken.model` 与官方加载代码。本示例按其公开 pattern 和 special token 配置构造 `tiktoken.Encoding`，无需执行远程 Python 代码。
- 标准公开仓库：DeepSeek、Qwen、Gemma、Mistral、GLM、ERNIE、Seed、Hy3、MiniMax、Cohere 与 Nemotron 均直接读取官方 `tokenizer.json`。
- Meta：Llama 4 Maverick 仓库需要接受许可；程序保留入口，但未经授权时会报告 skipped。

## 复现命令

```bash
# 无密钥、已实际验证的最新公开 tokenizer 与必要的公开基线
bpe-demo --models openai-o200k,kimi,deepseek,qwen,gemma,mistral,glm,ernie,seed,hunyuan,minimax,grok-public,cohere,nemotron \
  --html reports/latest-verified.html --json reports/latest-verified.json

# 最新线上模型 API，需要相应密钥
bpe-demo --models openai,anthropic,gemini,grok

# 历史 DeepSeek 对照（不属于默认最新集合）
bpe-demo --models deepseek-v3.2,deepseek
```

## 主要来源

- OpenAI GPT-5.5: https://developers.openai.com/api/docs/models/gpt-5.5/
- OpenAI Responses input tokens: https://platform.openai.com/docs/api-reference/responses
- Anthropic models overview: https://platform.claude.com/docs/en/models-overview
- Google Gemini models: https://ai.google.dev/gemini-api/docs/models
- xAI models: https://docs.x.ai/developers/models
- xAI tokenize text: https://docs.x.ai/developers/rest-api-reference/inference/other
- Kimi K2.6: https://huggingface.co/moonshotai/Kimi-K2.6
- DeepSeek V4 Pro: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro
- Qwen3.6 27B: https://huggingface.co/Qwen/Qwen3.6-27B
- Gemma 4 31B IT: https://huggingface.co/google/gemma-4-31B-it
- Mistral Medium 3.5: https://huggingface.co/mistralai/Mistral-Medium-3.5-128B
- GLM-5.1: https://huggingface.co/zai-org/GLM-5.1
- ERNIE 4.5: https://huggingface.co/baidu/ERNIE-4.5-21B-A3B-PT
- Seed OSS: https://huggingface.co/ByteDance-Seed/Seed-OSS-36B-Instruct
- Hy3-preview: https://huggingface.co/tencent/Hy3-preview
- MiniMax M2.7: https://huggingface.co/MiniMaxAI/MiniMax-M2.7
- Cohere Command A+: https://huggingface.co/CohereLabs/command-a-plus-05-2026-bf16
- Nemotron 3 Super: https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16
