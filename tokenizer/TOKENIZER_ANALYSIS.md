# 头部模型 Tokenizer 分析

本文分析本示例覆盖的模型家族使用何种 tokenizer 资源、能否精确复现，以及它们在同一篇中英双语短篇上的编码表现。核验日期为 **2026-05-27**。

## 结论摘要

1. `tokenizer` 是模型接口契约的一部分，不应只凭厂商品牌推断。应固定到具体模型版本和官方发布的 tokenizer 文件或计数 API。
2. 对可下载 tokenizer 的模型，本示例可以显示逐 token 切片；对 Anthropic Claude 与 Google Gemini，只能通过官方 API 获得计数，无法绘制真实切片。
3. 在本次中文样本上，已实际验证模型中 `DeepSeek V3.2` 与 `DeepSeek V4 Pro` 并列使用最少 token（256，`1.49 chars/token`），其次是 `Seed OSS`（260）和 `GLM-4.5`（263）。
4. 英文差异明显小于中文差异：最少为 `Grok-2` 与 `Cohere Command A+` 的 224 tokens，最多为 `ERNIE 4.5` 的 245 tokens。
5. 词表规模不是压缩率的充分条件。`Cohere Command A+` 的公开 tokenizer 词表约 255k，中文结果仍弱于词表约 128k 的 `DeepSeek V3.2`；训练语料、合并规则和中日韩字符覆盖方式更关键。

## 比较口径

内置测试材料为同一篇原创微型小说《港口的钟》的英文版本和中文版本：

| 语言 | 原文字符数 | UTF-8 字节数 |
| --- | ---: | ---: |
| English | 1089 | 1089 |
| 中文 | 381 | 1123 |

压缩率定义为：

```text
压缩率 = 原文字符数 / token 数，单位 chars/token
```

数值越高，表示同等 token 预算可覆盖更多该语言字符。由于中文和英文文本是语义对应的翻译，而不是逐字符等长文本，适合在**同一语言内横向比较 tokenizer**；不应仅凭中英文两列的绝对比值判断语言能力。

本程序对本地 tokenizer 编码的是纯文本，不附加 chat template 或 special tokens。Anthropic API 的计数输入使用 `messages` 结构，可能包含消息封装开销，因此其结果属于线上计费/上下文核算口径，而不是逐片段纯文本对齐口径。

## 资源类型

| 模型家族 | 本示例代表版本 | 官方/公开资源路径 | 复现类型 | 逐 token 展示 |
| --- | --- | --- | --- | --- |
| OpenAI | GPT-4o / `o200k_base` | 官方开源 `tiktoken` | 本地精确编码 | 是 |
| Anthropic | Claude，model id 可配置 | 官方 `messages.count_tokens` | API 精确计数 | 否 |
| Google Gemini | `gemini-2.5-flash`，可配置 | 官方 `models.countTokens` | API 精确计数 | 否 |
| Google Gemma | Gemma 3 12B IT | 官方 Hugging Face tokenizer | 本地编码，仓库可能需许可 | 是 |
| Moonshot | Kimi K2 Instruct | 官方 Hugging Face 仓库 | 本地编码，需显式信任自定义代码 | 是 |
| DeepSeek | DeepSeek V3.2 | 官方 `tokenizer.json` | 本地精确编码 | 是 |
| DeepSeek | DeepSeek V4 Pro | 官方 `tokenizer.json` | 本地精确编码 | 是 |
| Alibaba | Qwen3 8B | 官方 Hugging Face tokenizer | 本地精确编码 | 是 |
| Meta | Llama 3.3 Instruct | 官方 Hugging Face tokenizer | 本地编码，可能需接受许可 | 是 |
| Mistral | Mistral Small 3.1 | 官方 Hugging Face tokenizer；官方另开源 `mistral-common` | 本地精确编码 | 是 |
| Z.ai / 智谱 | GLM-4.5 | 官方 Hugging Face tokenizer | 本地精确编码 | 是 |
| Baidu | ERNIE 4.5 | 官方 Hugging Face tokenizer | 本地精确编码 | 是 |
| ByteDance | Seed OSS | 官方 Hugging Face tokenizer | 本地精确编码 | 是 |
| Tencent | Hunyuan A13B | 官方 Hugging Face tokenizer | 本地编码，需显式信任自定义代码 | 是 |
| MiniMax | MiniMax M1 | 官方 Hugging Face tokenizer | 本地编码，需显式信任自定义代码 | 是 |
| xAI | Grok-2 | 官方 `tokenizer.tok.json`，模型卡指向 SGLang 读取实现 | 本地精确编码 | 是 |
| Cohere | Command A+ | 官方 Hugging Face tokenizer | 本地精确编码 | 是 |
| NVIDIA | Nemotron 3 Nano | 官方 Hugging Face tokenizer | 本地编码，需显式信任自定义代码 | 是 |

## 已验证本地 Tokenizer

下表中的模型已在本工作区实际下载公开 tokenizer 文件并运行双语样本。`词表规模` 来自本地加载后的 tokenizer 元数据；added/special token 的计法可能导致少量额外条目，因此用约数表达。

| 模型 | 加载机制 | 词表规模（约） | 英文 tokens | 英文压缩率 | 中文 tokens | 中文压缩率 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| OpenAI GPT-4o | `tiktoken` `o200k_base` | 200,019 | 226 | 4.82 | 324 | 1.18 |
| Qwen3 8B | HF Fast tokenizer / BPE | 151,669 | 226 | 4.82 | 268 | 1.42 |
| xAI Grok-2 | tiktoken 格式公开工件 | 131,072 | 224 | 4.86 | 291 | 1.31 |
| DeepSeek V3.2 | `tokenizer.json` / BPE | 128,815 | 226 | 4.82 | 256 | 1.49 |
| DeepSeek V4 Pro | `tokenizer.json` / BPE | 129,280 | 226 | 4.82 | 256 | 1.49 |
| Z.ai GLM-4.5 | HF Fast tokenizer / BPE | 151,365 | 226 | 4.82 | 263 | 1.45 |
| ByteDance Seed OSS | HF Fast tokenizer / BPE | 155,121 | 231 | 4.71 | 260 | 1.47 |
| Mistral Small 3.1 | HF Fast tokenizer / BPE，启用官方提示的 regex fix | 131,072 | 229 | 4.76 | 376 | 1.01 |
| Baidu ERNIE 4.5 | HF tokenizer / BPE | 101,304 | 245 | 4.44 | 273 | 1.40 |
| Cohere Command A+ | HF Fast tokenizer / BPE | 255,032 | 224 | 4.86 | 282 | 1.35 |

### 中文表现

按本次中文样本 token 数从少到多排序：

| 排名 | 模型 | 中文 tokens | 中文压缩率 |
| ---: | --- | ---: | ---: |
| 1 | DeepSeek V3.2 | 256 | 1.49 |
| 1 | DeepSeek V4 Pro | 256 | 1.49 |
| 3 | ByteDance Seed OSS | 260 | 1.47 |
| 4 | Z.ai GLM-4.5 | 263 | 1.45 |
| 5 | Qwen3 8B | 268 | 1.42 |
| 6 | Baidu ERNIE 4.5 | 273 | 1.40 |
| 7 | Cohere Command A+ | 282 | 1.35 |
| 8 | xAI Grok-2 | 291 | 1.31 |
| 9 | OpenAI GPT-4o | 324 | 1.18 |
| 10 | Mistral Small 3.1 | 376 | 1.01 |

`DeepSeek V3.2` 与 `DeepSeek V4 Pro` 相比 `Mistral Small 3.1` 在该中文文本上少使用 120 tokens，减少约 31.9%。V4 Pro 与 V3.2 在两份样本上的完整 token id 序列一致，但 V4 Pro 的词表规模多 465 个条目，因此不能推断两者对任意文本均完全相同。这说明对中文长上下文、中文 RAG 文档或中文提示词成本评估时，不能直接复用英文场景下的 tokenizer 印象。

### 英文表现

英文结果集中在 224 到 245 tokens 之间：

| 排名 | 模型 | 英文 tokens | 英文压缩率 |
| ---: | --- | ---: | ---: |
| 1 | xAI Grok-2 | 224 | 4.86 |
| 1 | Cohere Command A+ | 224 | 4.86 |
| 3 | OpenAI GPT-4o | 226 | 4.82 |
| 3 | Qwen3 8B | 226 | 4.82 |
| 3 | DeepSeek V3.2 | 226 | 4.82 |
| 3 | DeepSeek V4 Pro | 226 | 4.82 |
| 3 | Z.ai GLM-4.5 | 226 | 4.82 |
| 8 | Mistral Small 3.1 | 229 | 4.76 |
| 9 | ByteDance Seed OSS | 231 | 4.71 |
| 10 | Baidu ERNIE 4.5 | 245 | 4.44 |

这组模型在普通英文叙事文本上差距较小。英文成本估算仍需使用目标模型自己的 tokenizer，但 tokenizer 通常不会像中文一样造成大幅排名分化。

## 模型家族解读

### OpenAI

OpenAI 的 `tiktoken` 是开源实现。示例为 GPT-4o 使用的 `o200k_base`，可以本地获得 token id 与字节片段。其大词表对多语言覆盖较 `cl100k_base` 更友好，但本样本的中文压缩率仍低于多款国内开源模型。

### Anthropic Claude

Anthropic 为当前 Claude 提供官方 token counting API，而未发布可作为当前线上模型精确替代的本地逐 token 编码器。因而本示例只在设置 `ANTHROPIC_API_KEY` 时调用官方计数接口，不使用第三方近似 tokenizer 冒充 Claude 的真实切分。

### Google Gemini 与 Gemma

Gemini 的精确入口是官方 `countTokens` API，属于闭源线上模型计数。Gemma 是 Google 发布的开放权重模型家族，拥有可下载 tokenizer；Gemma 的 tokenizer 结果不能视为 Gemini 的分词结果。

### DeepSeek、Qwen、GLM、ERNIE、Seed

这些模型都发布了可下载的 tokenizer 资源，适合离线测算中文文档、提示词与上下文成本。本样本中五者的中文压缩率均明显优于 OpenAI GPT-4o 与 Mistral Small 3.1，说明其词表/合并规则为中文常见字符序列提供了更密集的表示。

DeepSeek V3.2 在当前 `transformers` 环境下通过完整 `AutoTokenizer` 初始化会触碰无关的模型配置兼容问题；示例直接读取官方 `tokenizer.json`，只保留本任务所需的精确纯文本分词行为。DeepSeek V4 Pro 同样提供官方 `tokenizer.json`，本示例新增 `deepseek-v4-pro` 入口并验证了其双语样本结果。

### Mistral

Mistral 官方维护 `mistral-common` tokenizer 库。对于所选 Hugging Face 仓库，`transformers` 明确提示应启用 `fix_mistral_regex=True`；本示例已启用该修正。Mistral 在本中文样本上的压缩率较低，不代表模型生成质量结论，只反映该 tokenizer 对该中文文本的 token 使用量。

### xAI Grok

Grok-2 官方仓库发布的 `tokenizer.tok.json` 不是通用 Hugging Face `tokenizer.json`，而是 tiktoken 格式工件。其模型卡指向 SGLang 的开源加载支持；本示例按该公开解析路径构造 `tiktoken.Encoding`，因此可以本地展示 token id 和片段。

### 需要额外信任或授权的模型

Kimi、Hunyuan、MiniMax 与 Nemotron 的加载路径涉及仓库中的自定义 tokenizer 代码，本程序默认不执行，必须显式传入 `--trust-remote-code`。Llama 和 Gemma 的仓库可能要求 Hugging Face 登录并接受模型许可。这些限制属于获取/执行边界，并不表示对应模型没有 tokenizer。

## 使用建议

| 场景 | 建议 |
| --- | --- |
| 估算线上账单或上下文限制 | 使用实际 API 模型对应的官方计数接口或官方 tokenizer，并固定模型 id |
| 比较中文 RAG 文档占用 | 用同一批真实中文业务文档运行本示例，不只依赖短篇样本 |
| 评估双语应用 | 分别统计中文、英文和混合文本；避免从纯英文 benchmark 推断中文 token 成本 |
| 检查 token 切片 | 使用 HTML 报告定位专有名词、数字、标点、代码片段和罕见汉字的分裂方式 |
| 执行远程代码 tokenizer | 仅对可信官方仓库显式启用，并固定仓库版本以便复现 |

## 复现命令

```bash
# 公开并已实际验证的一组本地 tokenizer
bpe-demo --models openai,qwen,grok,deepseek,deepseek-v4-pro,glm,seed,mistral,ernie,cohere \
  --html reports/verified.html --json reports/verified.json

# 官方 API 计数，需要密钥
bpe-demo --models anthropic,gemini
```

可视化报告会列出原文字符数、UTF-8 字节数、每个模型中英文 token 总数和压缩率，并在本地 tokenizer 可用时展示彩色逐 token 片段。

## 主要来源

- OpenAI `tiktoken`: https://github.com/openai/tiktoken
- OpenAI token counting cookbook: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
- Anthropic token counting: https://docs.anthropic.com/en/docs/build-with-claude/token-counting
- Google Gemini token counting: https://ai.google.dev/gemini-api/docs/tokens
- Mistral `mistral-common`: https://github.com/mistralai/mistral-common
- xAI Grok-2: https://huggingface.co/xai-org/grok-2
- SGLang Grok tokenizer loader: https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/tokenizer/tiktoken_tokenizer.py
- DeepSeek V3.2: https://huggingface.co/deepseek-ai/DeepSeek-V3.2
- DeepSeek V4 Pro: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro
- Qwen3 8B: https://huggingface.co/Qwen/Qwen3-8B
- GLM-4.5: https://huggingface.co/zai-org/GLM-4.5
- ERNIE 4.5: https://huggingface.co/baidu/ERNIE-4.5-21B-A3B-PT
- Seed OSS: https://huggingface.co/ByteDance-Seed/Seed-OSS-36B-Instruct
- Cohere Command A+: https://huggingface.co/CohereLabs/command-a-plus-05-2026-bf16
