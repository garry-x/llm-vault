# LLM Tokenizer 中英文对比示例

这是一个 tokenizer（subword 分词器）比较程序。它用同一篇原创微型小说的英文版与中文版，比较主流大模型家族的编码长度和 token 切片。习惯上常称为 “BPE 测试”，但各家 tokenizer 的具体算法并不都严格等同于 BPE。

更完整的模型 tokenizer 机制、公开程度与本样本结果分析见 [TOKENIZER_ANALYSIS.md](TOKENIZER_ANALYSIS.md)，可视化展示页见 [TOKENIZER_ANALYSIS.html](TOKENIZER_ANALYSIS.html)。

## 覆盖模型

| Key | 厂商 / 模型代表 | 获取方式 | 可查看切片 |
| --- | --- | --- | --- |
| `openai` | OpenAI GPT-4o (`o200k_base`) | 官方 `tiktoken` | 是 |
| `anthropic` | Anthropic Claude | 官方 `messages.count_tokens` API | 否 |
| `gemini` | Google Gemini | 官方 `models.countTokens` API | 否 |
| `kimi` | Moonshot Kimi K2 Instruct | 官方 Hugging Face tokenizer，自定义代码 | 是 |
| `deepseek` | DeepSeek V3.2 | 官方 Hugging Face `tokenizer.json` | 是 |
| `deepseek-v4-pro` | DeepSeek V4 Pro | 官方 Hugging Face `tokenizer.json` | 是 |
| `qwen` | Alibaba Qwen3 | 官方 Hugging Face tokenizer | 是 |
| `llama` | Meta Llama 3.3 | 官方 Hugging Face tokenizer，可能需 HF 授权 | 是 |
| `mistral` | Mistral Small 3.1 | 官方 Hugging Face tokenizer | 是 |
| `gemma` | Google Gemma 3（并非 Gemini） | 官方 Hugging Face tokenizer，可能需 HF 授权 | 是 |
| `glm` | Z.ai / 智谱 GLM-4.5 | 官方 Hugging Face tokenizer | 是 |
| `ernie` | Baidu ERNIE 4.5 | 官方 Hugging Face tokenizer | 是 |
| `seed` | ByteDance Seed OSS | 官方 Hugging Face tokenizer | 是 |
| `hunyuan` | Tencent Hunyuan A13B | 官方 Hugging Face tokenizer，自定义代码 | 是 |
| `minimax` | MiniMax M1 | 官方 Hugging Face tokenizer，自定义代码 | 是 |
| `grok` | xAI Grok-2 | 官方公开的 tiktoken 格式工件 | 是 |
| `cohere` | Cohere Command A+ | 官方 Hugging Face tokenizer | 是 |
| `nemotron` | NVIDIA Nemotron 3 Nano | 官方 Hugging Face tokenizer，自定义代码 | 是 |

程序只下载 tokenizer 文件，不下载模型权重。产品服务的 tokenizer 可能随具体 API 模型版本变化；本示例以表中的明确模型版本为准，不以品牌名推断未公开的线上实现。

Anthropic 和 Gemini 的官方接口仅返回计数，不能生成彩色逐 token 切片。它们的 API 计数还可能包含消息结构开销，适合核算该服务的输入消耗，不应当与纯文本本地编码逐 token 对齐比较。

## 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .

# 不需要 API key 的公开、本地可切片示例
bpe-demo --models openai,deepseek,deepseek-v4-pro,qwen,glm,ernie,seed \
  --html reports/tokenizers.html --json reports/tokenizers.json

# 全部入口；不可访问或未配置的项会列为 skipped
bpe-demo --html reports/all.html --json reports/all.json
```

Kimi、Hunyuan、MiniMax 和 Nemotron 的相应仓库示例声明或使用自定义 tokenizer 代码。仅在信任相应官方仓库代码时执行：

```bash
bpe-demo --models kimi,hunyuan,minimax,nemotron --trust-remote-code --html reports/remote-code.html
```

需要 API key 的官方计数方式：

```bash
export ANTHROPIC_API_KEY="..."
export GEMINI_API_KEY="..."
bpe-demo --models anthropic,gemini \
  --anthropic-model claude-sonnet-4-5-20250929 \
  --gemini-model gemini-2.5-flash
```

也可以替换测试文本：

```bash
bpe-demo --models openai,qwen --english texts/story.en.txt --chinese texts/story.zh.txt
```

终端和 HTML 首先显示两份原文的字符数与 UTF-8 字节数，再为每个 tokenizer 显示 token 总数与压缩率。压缩率定义为 `原文字符数 / token 数`（`chars/token`），数值越高表示单位 token 覆盖字符越多。HTML 报告还会将本地可获得的切片着色，悬停可查看 token id；JSON 输出包含 `compression_ratio_chars_per_token` 字段。

## 来源

- OpenAI `tiktoken`: https://cookbook.openai.com/examples/how_to_count_tokens_with_tiktoken
- Anthropic token counting: https://docs.anthropic.com/en/docs/build-with-claude/token-counting
- Gemini token counting: https://ai.google.dev/gemini-api/docs/tokens
- Moonshot Kimi: https://huggingface.co/moonshotai/Kimi-K2-Instruct
- DeepSeek: https://huggingface.co/deepseek-ai/DeepSeek-V3.2
- DeepSeek V4 Pro: https://huggingface.co/deepseek-ai/DeepSeek-V4-Pro
- Qwen: https://huggingface.co/Qwen/Qwen3-8B
- Meta Llama: https://huggingface.co/meta-llama/Llama-3.3-70B-Instruct
- Mistral: https://huggingface.co/mistralai/Mistral-Small-3.1-24B-Instruct-2503
- Google Gemma: https://huggingface.co/google/gemma-3-12b-it
- GLM: https://huggingface.co/zai-org/GLM-4.5
- ERNIE: https://huggingface.co/baidu/ERNIE-4.5-21B-A3B-PT
- Seed: https://huggingface.co/ByteDance-Seed/Seed-OSS-36B-Instruct
- Hunyuan: https://huggingface.co/tencent/Hunyuan-A13B-Instruct
- MiniMax: https://huggingface.co/MiniMaxAI/MiniMax-M1-80k-hf
- Grok: https://huggingface.co/xai-org/grok-2
- Grok tokenizer 读取实现（SGLang）: https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/tokenizer/tiktoken_tokenizer.py
- Cohere Command A+: https://huggingface.co/CohereLabs/command-a-plus-05-2026-bf16
- NVIDIA Nemotron: https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16

## 开源实现核验

本程序优先复用厂商发布的 tokenizer 文件或官方/官方指向的开源实现，而不是近似估算：

| 厂商 | 已找到的公开实现或资源 |
| --- | --- |
| OpenAI | 官方开源 `openai/tiktoken`，可本地精确编码 |
| Anthropic | 当前 Claude 官方只公开 `count_tokens` API；旧的/第三方 tokenizer 不作为当前 Claude 精确依据 |
| Google | Gemini 使用官方 `countTokens` API；Gemma 则公开 Hugging Face tokenizer，两者不是同一模型 |
| Mistral | 官方开源 `mistralai/mistral-common`，含版本化 tokenizer；本示例对纯文本加载同仓库 tokenizer 文件 |
| Meta | 官方 Llama 仓库提供 tokenizer 下载流程，但需要接受 Meta 许可 |
| xAI | Grok-2 发布 `tokenizer.tok.json`，模型卡指向 SGLang 开源的 tiktoken 解析实现；本示例复现该读取方式 |
| 国内开源模型 | Kimi、DeepSeek、Qwen、GLM、ERNIE、Seed、Hunyuan、MiniMax 均发布了模型仓库中的 tokenizer 资源；DeepSeek V3.2 与 V4 Pro 在本例中直接读取各自官方 `tokenizer.json`，避免加载无关模型配置 |
