# Lesson 1 — Introducing Retrieval Augmented Generation

课程位置:RAG and Agentic Search 章节,第 1 课(共 7 课)。这节是纯概念课,不涉及具体
算法,重点是建立"为什么需要 RAG"这个直觉,后面 6 课才会讲 chunking / embedding /
BM25 的具体实现。

---

## Section 1 — High Level:RAG 是什么、为什么需要它

### 一句话定义

RAG(Retrieval Augmented Generation,检索增强生成)是一种"先检索、再生成"的
方法:当文档太大塞不进一次 prompt 时,先把文档切成小块(chunk),再根据用户问题
只挑出最相关的几块塞进 prompt,而不是把整份文档都塞进去。

### 为什么需要它 —— 硬约束是什么

**Fact**(来自你贴的课程原文 + 官方 API 文档,我做了交叉验证):

Claude 的 context window(能塞进一次请求的 token 总量)不是无限的:
- Claude Sonnet 5 / Opus 5:1M tokens(约 55.5 万词)
- Claude Haiku 4.5:200K tokens(约 15 万词)

**这不是"太大就报错"这么简单**,课程原文提到的四个问题,我按 fact / suggestion 标注:

| 问题 | 类型 | 说明 |
|---|---|---|
| prompt 长度有硬上限 | fact | 超过 context window,API 直接报错,不会截断了事 |
| 超长 prompt 会降低 Claude 的有效性 | fact(课程原文) | 即使没超限,信息太多、太杂,模型也更难聚焦到真正相关的部分 |
| 更大的 prompt 更贵 | fact | Anthropic 按 token 计费,input token 越多花越多。这节 notebook 会用 `count_tokens`(免费接口)实测这个差异,不用真的调 `messages.create()` 烧 quota |
| 更大的 prompt 更慢 | fact | 输入 token 越多,处理时间越长 |

一个类比(硬件工程师视角):这跟你在跑 simulation 时不会把整个 chip 的全部
register map 都灌进 testbench 是一个道理 —— 你只关心跟当前 debug 目标相关的那一小块
address range。RAG 做的就是"先定位到相关的 address range,再深入看"。

### 两种方案的取舍

**方案 1:把整份文档塞进 prompt**(courses 原文管这个叫 "Include Everything")

```
Answer the user's question about the financial document.

<user_question>
{user_question}
</user_question>

<financial_document>
{financial_document}
</financial_document>
```

简单,但有上面表格里的四个硬伤。800 页财报塞不进去,或者塞进去了但贵、慢、模型
注意力被稀释。

**方案 2:RAG(先切块,再挑相关的塞进去)**

预处理阶段先把文档切成 chunk;用户提问时,搜索出最相关的几个 chunk,只把这几个
塞进 prompt。

**优势(fact,来自课程原文):**
- Claude 只聚焦在真正相关的内容上
- 能 scale 到非常大的文档,甚至多份文档一起检索
- prompt 更小 → 更便宜、更快

**代价(fact,来自课程原文,这点很重要,课程明确说 RAG 不是免费的午餐):**
- 需要一个额外的预处理步骤(切 chunk)
- 需要一套"搜索机制"去判断哪些 chunk 是"相关的"(这就是后面 embedding / BM25 两课要解决的)
- 被选中的 chunk 有可能不包含模型需要的全部上下文(retrieval 有可能"漏检")
- chunk 的切法有很多种(按固定长度切?按 section 标题切?),没有一种是万能的 —— 这是
  下一课(Text chunking strategies)要解决的问题

### 什么时候用 RAG(suggestion,来自课程原文的判断标准)

RAG 引入了额外的复杂度,不是所有场景都值得。课程给的判断标准:
- 文档非常大,单份塞不进 context window,或塞进去成本/延迟不可接受
- 需要跨多份文档检索
- 需要长期优化成本和响应速度(比如高频调用的生产系统)

如果你的文档本来就小,能一次塞进 prompt,**不需要 RAG** —— 这是课程原文明确强调的
"trade-off":RAG 用更多的工程复杂度换取 scalability 和效率,复杂度不是白拿的。

---

## Section 2 — 详细讲解:每个概念展开

### 2.1 "Context window" 到底限制的是什么

Context window 限制的是**一次 API 调用里,input + output 加起来的 token 总量**
(不同模型上限不同,见上面表格)。这里有个容易搞混的点:

**Fact**:超过 context window 不是"模型帮你自动截断",而是 API 直接返回 error。
你的课程笔记里 Tip 1 写过"即使你设了 max_tokens,LLM 也不会照着这个数生成,只是被
这个数截断"—— 那个是 `max_tokens`(限制**输出**长度)的行为,跟 context window
(限制**input+output 总和**)是两个不同的概念,别混。

### 2.2 为什么"塞全部内容"在工程上是个坏主意,即使技术上塞得进去

假设你的文档只有 50K tokens,Sonnet 5 的 1M context window 完全装得下,那是不是
就不需要 RAG 了?

**Fact + suggestion 混合判断**:技术上装得下,但如果你的 应用是"每次用户提问都要
重新把这 50K tokens 发一遍",那么:
- 每次提问都要为这 50K tokens 付费(除非用 prompt caching,那是后面 Features of
  Claude 章节的内容,这里先不展开)
- 大部分内容跟当前问题根本无关,模型要在无关信息里"捞针"

这就是课程原文说的"Claude becomes less effective with very long prompts"——
不是模型看不懂,是信噪比变差了。

### 2.3 "Relevant"(相关)这个词背后藏着一整个技术问题

课程原文这句话是这节课真正的重点:

> "you'd search through your chunks, find the 'Risk Factors' section, and
> include just that relevant chunk"

"搜索出相关 chunk"这一步,说起来一句话,做起来需要解决:
1. 怎么切 chunk(下一课)
2. 怎么表示"相关性"—— 用词面匹配(BM25,第 6 课)还是语义匹配(embedding,第 3 课)
3. 怎么把两种检索方式结合起来(第 7 课 Multi-Index)

这节课不解决这些问题,只是让你先建立"这里有个需要解决的问题"的认知。这也是为什么
课程接下来 6 课分别对应:chunking → embedding → RAG flow 概览 → RAG flow 实现 →
BM25 → 多索引组合。

### 2.4 一个具体例子(用来贯穿整个 RAG 章节)

我在 `sample_docs/financial_report.txt` 准备了一份虚构的财报,结构故意模仿真实
文档(Business Overview / Risk Factors / Financial Highlights / Legal
Proceedings 四个 section)。后面每一课都会用这份文档做检索练习,比如:

- 问 "What risk factors does this company have?" → 正确答案应该命中 SECTION 2
- 问 "What was the gross margin?" → 正确答案应该命中 SECTION 3

这节课我们还没有"检索"能力,所以先做一件更基础的事:**用实测数据验证"文档太大"
这个问题本身**——用 `count_tokens`(免费、不烧 quota)量出"把整份文档塞进
prompt"要花多少 token,直观感受一下"方案 1"的代价。

---

## Section 3 — Code 实操

对应 notebook:`001_intro_rag.ipynb`

### 3.1 为什么这节的 code 这么"轻"

这节课程原文本身没有给代码,是纯概念讲解。所以这节的 code 目的不是"实现 RAG",
而是让你**用真实数字验证 Section 1 表格里的 fact**——即"prompt 越大,占用的
token 越多"。用的是 `client.messages.count_tokens()` 这个接口,官方文档写明它
**免费、且和 message creation 有独立的 rate limit**,所以不会占用你现在紧张的
quota。

### 3.2 Cell 1 — 复用 helpers,不重写 client

```python
from helpers import client, model
```

对应 Section 2.1:这里的 `client` / `model` 就是你在
`001_tools_multi-turn_conversation.ipynb` 里已经搭好的那个(内网 gateway +
`claude-sonnet-4-5`),搬进了 `helpers.py`,以后每一课都这样引用,不用重新粘贴
client 构造代码。

### 3.3 Cell 2 — 读入 sample_docs,模拟"方案 1"

```python
from pathlib import Path

doc_path = Path("sample_docs/financial_report.txt")
financial_document = doc_path.read_text(encoding="utf-8")

user_question = "What risk factors does this company have?"

# 对应 Section 1 "方案 1" 的 prompt 模板
stuffed_prompt = f"""Answer the user's question about the financial document.

<user_question>
{user_question}
</user_question>

<financial_document>
{financial_document}
</financial_document>"""
```

这里直接照抄课程原文给的 prompt 模板(方案 1),`{financial_document}` 换成我们
自己的示例财报。

### 3.4 Cell 3 — 用 count_tokens 量化"塞全部内容"的代价

```python
full_count = client.messages.count_tokens(
    model=model,
    messages=[{"role": "user", "content": stuffed_prompt}],
)
print(f"Full document prompt: {full_count.input_tokens} tokens")
```

**输入**:整份文档 + 问题拼成的一条 user message。
**输出**:一个 token 数(int)。
**为什么这么写**:`count_tokens` 的参数形状和 `messages.create()` 完全一样
(同样是 `model` + `messages`),这是官方文档明确保证的 —— 所以你以后测真实场景
的 prompt 大小,不用改写法,直接把 `create` 换成 `count_tokens` 就行。

### 3.5 Cell 4 — 对比:只塞"相关 chunk"要花多少 token

```python
# 手动模拟"已经检索到相关 chunk"之后的 prompt(下一课开始才会讲怎么自动做这一步)
risk_factors_chunk = """SECTION 2: RISK FACTORS

Supply chain concentration. Acme Semiconductor sources over 70 percent of its
wafer fabrication capacity from a single foundry partner located in Taiwan.
...
"""

chunked_prompt = f"""Answer the user's question about the financial document.

<user_question>
{user_question}
</user_question>

<financial_document>
{risk_factors_chunk}
</financial_document>"""

chunk_count = client.messages.count_tokens(
    model=model,
    messages=[{"role": "user", "content": chunked_prompt}],
)
print(f"Chunked prompt: {chunk_count.input_tokens} tokens")
print(f"Reduction: {(1 - chunk_count.input_tokens / full_count.input_tokens):.0%}")
```

**输入**:同样的问题,但 `<financial_document>` 换成只有 Risk Factors 那一段。
**输出**:更小的 token 数 + 一个百分比,直观看到"只塞相关 chunk"省了多少。
**这一步故意手动写死 chunk**:因为这节课还没学怎么自动切 chunk、自动挑出相关的
chunk —— 那是第 2 课(chunking)和第 3/6/7 课(检索)要解决的。这里先用手动挑选
的方式,让你亲眼看到"如果我能自动做到这一步,能省多少 token"。

### Notebook 里不会做的事(留给后面课程)

- 自动切 chunk → Lesson 2
- 自动判断"哪个 chunk 相关" → Lesson 3(embedding)、Lesson 6(BM25)
- 完整串起来的 pipeline → Lesson 4、5、7

---

## 自测问题

1. Context window 限制的是 input 还是 output,还是两者加起来?它和 `max_tokens`
   参数限制的是不是同一件事?
2. 课程原文列出的 RAG 的 4 个 challenges 里,哪一个是"即使你把 chunking 和检索都
   做对了,依然可能发生"的风险?(提示:检索这件事本身有没有 100% 准确的保证)
3. 如果你的文档只有 2000 tokens,Sonnet 5 的 context window 是 1M tokens,你还
   需要上 RAG 吗?为什么?
4. 为什么这节验证 token 数用的是 `count_tokens` 而不是 `messages.create()`?
   两者在计费和 rate limit 上有什么区别?
