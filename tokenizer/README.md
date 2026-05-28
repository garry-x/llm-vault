# LLM Tokenizer 中英文对比示例

这是一个 tokenizer（subword 分词器）比较程序。它用同一篇原创微型小说的英文版与中文版，比较头部大模型家族在两种语言上的编码长度、压缩率和可获得的 token 切片。习惯上常称为 “BPE 测试”，但各家 tokenizer 的算法并不都严格等同于 BPE。

完整的版本核验、结果分析与可视化展示见 [TOKENIZER_ANALYSIS.html](TOKENIZER_ANALYSIS.html)。模型与公开资源核验日期为 **2026-05-27**。

## 最新模型入口

| Key | 厂商 / 当前代表 | 获取方式 | 可查看切片 |
| --- | --- | --- | --- |
| `openai` | OpenAI GPT-5.5 | 官方 `responses/input_tokens` API | 否 |
| `anthropic` | Anthropic Claude Opus 4.7 | 官方 `messages.count_tokens` API | 否 |
| `gemini` | Google Gemini 3.1 Pro Preview | 官方 `models.countTokens` API | 否 |
| `kimi` | Moonshot Kimi K2.6 | 官方 `tiktoken.model` | 是 |
| `deepseek` | DeepSeek V4 Pro | 官方 `tokenizer.json` | 是 |
| `qwen` | Alibaba Qwen3.6 27B | 官方 `tokenizer.json` | 是 |
| `llama` | Meta Llama 4 Maverick | 官方 `tokenizer.json`，需接受许可 | 是 |
| `mistral` | Mistral Medium 3.5 | 官方 `tokenizer.json` | 是 |
| `gemma` | Google Gemma 4 31B IT（非 Gemini） | 官方 `tokenizer.json` | 是 |
| `glm` | Z.ai GLM-5.1 | 官方 `tokenizer.json` | 是 |
| `ernie` | Baidu ERNIE 4.5 | 最新可获得的官方文本模型 tokenizer | 是 |
| `seed` | ByteDance Seed OSS | 最新可获得的官方通用模型 tokenizer | 是 |
| `hunyuan` | Tencent Hy3-preview | 最新可获得的官方通用对话模型 tokenizer | 是 |
| `minimax` | MiniMax M2.7 | 官方 `tokenizer.json` | 是 |
| `grok` | xAI Grok 4.3 | 官方 `/v1/tokenize-text` API | 是 |
| `cohere` | Cohere Command A+ 05-2026 | 官方 `tokenizer.json` | 是 |
| `nemotron` | NVIDIA Nemotron 3 Super | 官方 `tokenizer.json` | 是 |

另提供公开对照入口：`openai-o200k` 为 OpenAI `o200k_base` 本地编码，`grok-public` 为 xAI 已公开下载的 Grok-2 工件，`deepseek-v3.2` 为历史模型；`deepseek-v4-pro` 是 `deepseek` 的兼容别名。这些对照入口不冒充当前托管旗舰模型。

Anthropic、Gemini 与 OpenAI 最新模型的官方接口只返回计数，不能生成逐 token 彩色切片。它们的 API 请求口径也可能带消息结构开销，适合核算对应服务的输入消耗，不应用于冒充纯文本本地切片。xAI 最新接口会返回切片，但需要 `XAI_API_KEY`。

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 不需要 API key 的最新公开 tokenizer 集合与公开基线
bpe-demo --models openai-o200k,kimi,deepseek,qwen,gemma,mistral,glm,ernie,seed,hunyuan,minimax,grok-public,cohere,nemotron \
  --html reports/latest-verified.html --json reports/latest-verified.json

# 全部默认入口；没有 key 或访问许可的项会列为 skipped
bpe-demo --html reports/all.html --json reports/all.json
```

使用最新托管模型的官方 API：

```bash
export OPENAI_API_KEY="..."
export ANTHROPIC_API_KEY="..."
export GEMINI_API_KEY="..."
export XAI_API_KEY="..."
bpe-demo --models openai,anthropic,gemini,grok \
  --openai-model gpt-5.5 \
  --anthropic-model claude-opus-4-7 \
  --gemini-model gemini-3.1-pro-preview \
  --grok-model grok-4.3
```

也可以替换测试文本：

```bash
bpe-demo --models kimi,deepseek,qwen --english texts/story.en.txt --chinese texts/story.zh.txt
```

终端和 HTML 首先显示两份原文的字符数与 UTF-8 字节数，再为每个 tokenizer 显示 token 总数与压缩率。压缩率定义为 `原文字符数 / token 数`（`chars/token`），数值越高表示单位 token 覆盖字符越多。HTML 会将可获得的切片着色，JSON 输出包含 `compression_ratio_chars_per_token` 字段。

## 主要来源

- OpenAI GPT-5.5: https://developers.openai.com/api/docs/models/gpt-5.5/
- OpenAI input token counting: https://platform.openai.com/docs/api-reference/responses
- Anthropic models: https://platform.claude.com/docs/en/models-overview
- Gemini models / token counting: https://ai.google.dev/gemini-api/docs/models and https://ai.google.dev/gemini-api/docs/tokens
- xAI models / tokenize text: https://docs.x.ai/developers/models and https://docs.x.ai/developers/rest-api-reference/inference/other
- Kimi K2.6: https://huggingface.co/moonshotai/Kimi-K2.6
- DeepSeek V4 Pro: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro
- Qwen3.6 27B: https://huggingface.co/Qwen/Qwen3.6-27B
- Mistral Medium 3.5: https://huggingface.co/mistralai/Mistral-Medium-3.5-128B
- Gemma 4 31B IT: https://huggingface.co/google/gemma-4-31B-it
- GLM-5.1: https://huggingface.co/zai-org/GLM-5.1
- Hy3-preview: https://huggingface.co/tencent/Hy3-preview
- MiniMax M2.7: https://huggingface.co/MiniMaxAI/MiniMax-M2.7
- Nemotron 3 Super: https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16
