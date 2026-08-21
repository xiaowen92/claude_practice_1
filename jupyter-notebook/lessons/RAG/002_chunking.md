# Lesson 2 — Text Chunking Strategies

课程位置:RAG and Agentic Search 章节,第 2 课(共 7 课)。上一课建立了"为什么需要
RAG"的直觉,这一课解决第一个具体问题:**怎么把文档切成 chunk**。

---

## Section 1 — High Level:chunking 是什么、为什么重要

### 一句话定义

Chunking(文本切块)是把一份文档切成若干个小段(chunk)的过程,这些 chunk 会被
存进 vector database,后续用户提问时,系统会去检索最相关的几个 chunk 塞进 prompt。

### 为什么 chunking 质量直接决定 RAG 质量(fact,课程原文明确强调)

**Fact**:chunking 是 RAG pipeline 里最关键的一步之一。切得不好,检索到的内容
就是不相关的,Claude 会基于错误的上下文给出完全错误的答案。

课程原文给的例子:一份文档里同时有 Medical Research 和 Software Engineering 两个
section。用户问"How many bugs did engineers fix this year?"(今年工程师修了多少
个 bug),如果切块方式把这两个 section 的内容混在一起,系统可能检索到 Medical
Research 那一段——因为医疗那段碰巧也出现了"bug"这个词(不同语境下的用法,比如
"a rare bug/pathogen"),但语义上跟软件工程的 bug 完全没关系。

这是一个**词面匹配和语义理解错位**的具体案例,也预告了后面 lesson 6(BM25,词面
匹配)和 lesson 3(embedding,语义匹配)要解决的核心矛盾。

### 三种主要 chunking 策略的取舍(fact,课程原文)

| 策略 | 优势 | 劣势 |
|---|---|---|
| **Size-based**(按固定字符数) | 实现最简单,适用于任何类型的文档(包括代码) | 会把单词、句子、标题硬生生切断,丢失上下文 |
| **Structure-based**(按文档结构,如 Markdown 标题) | 每个 chunk 就是一个完整 section,语义最干净 | 依赖文档本身有清晰的结构标记,plain text / PDF 往往没有 |
| **Semantic-based**(按语义相关性分组句子) | 效果最好,chunk 内容最相关 | 计算成本最高,实现最复杂,需要先理解每句话的语义 |

还有一种**Sentence-based**(按句子分组),课程原文把它当成 size-based 和
semantic-based 之间的**实用折中方案**:比 size-based 更不容易切断语义,又比
semantic-based 实现简单得多。

### 生产环境里的实际选择(fact,课程原文明确说)

> "Size-based chunking with overlap is often the go-to choice in production
> because it's simple, reliable, and works with any document type."

**Fact**:即使 size-based 有"切断单词"的明显缺陷,生产环境里它仍然是最常见的
默认选择——因为它足够可靠,不会因为文档格式的边界情况(edge case)把整个 pipeline
搞崩。

**Suggestion**(课程原文的判断标准):
- 如果你能保证文档格式(比如公司内部统一格式的报告)→ structure-based 效果最好
- 如果是通用文本文档 → sentence-based 是不错的中间选择
- 如果你要一个"万金油"、什么文档都能处理不出错的方案 → size-based(带 overlap)

**没有一种"最好"的策略**——课程原文最后明确这一点:选择取决于你的文档类型、
用例,以及你愿意在"实现复杂度"和"chunk 质量"之间做多大的取舍。

---

## Section 2 — 详细讲解:每种策略展开

### 2.1 Size-based chunking:overlap 解决的到底是什么问题

**问题**:如果没有 overlap,按固定字符数切,一个句子、一个专有名词很可能正好卡在
两个 chunk 的边界上,被硬切成两半。

**具体例子**(来自 `report.md` 的真实切割结果,chunk_size=150,overlap=20):

不加 overlap 时,chunk 3 结尾是:
```
"...traditional disciplinary boundaries. This year's review highlights significant progress in ten critical areas. Advances in **Medical Research** fo"
```
chunk 4 开头会是:
```
"cused on the rare XDR-471 syndrome..."
```
"**Medical Research** focused" 这个词组被硬生生切成 "fo" + "cused" 两半,分布在
两个不同的 chunk 里——如果检索只命中其中一个 chunk,模型看到的就是残缺的词。

**加了 overlap=20 之后**,chunk 4 实际会从"往回退 20 个字符"的位置开始:
```
"edical Research** focused on the rare XDR-471 syndrome, yielding new diagnostic insights..."
```
虽然词开头(“M”)仍然缺了,但因为有重叠区,只要相关的那句话完整落在**某一个**
chunk 里,检索就能命中完整语义。这就是 overlap 的作用:不是"消除"切断问题,而是
"提高至少有一个 chunk 包含完整上下文的概率"。

**硬件工程师类比**:这跟你在做 timing closure 时给 setup/hold margin 留 guard
band 是一个道理——你没法保证每个 corner 都完美,但留出重叠余量能覆盖大部分实际
出问题的边界情况。

### 2.2 Structure-based chunking:能拿到"完整 section"是有代价的

`chunk_by_section` 按 Markdown 的 `"\n## "` 标记切分,报告里的每个二级标题
(`## Section 1: Medical Research...`)就是一个天然的切分点。

**验证结果**(对 `report.md` 实际跑出来的):切出 15 个 chunk,每个 chunk 恰好
对应一个 section(Executive Summary / Table of Contents / Methodology / Section
1-10 / Future Directions),不会出现两个不同主题混在一个 chunk 里的情况——这正好
解决了 Section 1 里提到的"bug 词面匹配错误检索"问题的根源(前提是切得对)。

**代价**(fact,容易被忽略的坑):`re.split(r"\n## ", document_text)` 切分之后,
分隔符本身(`"\n## "`)被消耗掉了,每个 chunk **不包含它自己的二级标题文字**——
比如 chunk 1 的内容是 `"Executive Summary\n\n..."` 而不是
`"## Executive Summary\n\n..."`。标题文字虽然还留着(因为标题后面还有换行),但
"## "这个 Markdown 语法标记被吃掉了。如果你后续需要保留完整 Markdown 格式,要在
正则里用 capture group 把标题保留,这里的实现选择了最简单的写法,牺牲了这一点。

**这个策略的硬性前提**:必须提前知道文档有稳定的结构标记。如果输入是没有标题的
plain text,或者是 PDF 转出来的乱格式文本,`chunk_by_section` 会直接失效(可能
只切出 1 个 chunk,或者切分点完全不对)。

### 2.3 Sentence-based chunking:为什么是"折中"

`chunk_by_sentence` 先用正则 `(?<=[.!?])\s+` 把整段文本切成句子列表,再按
`max_sentences_per_chunk` 个句子分一组,组间留 `overlap_sentences` 句重叠。

**为什么这个正则不会切断单词**:`(?<=[.!?])` 是 lookbehind,只在"句末标点
(. ! ?)后面紧跟空白"的位置切分——标点符号本身留在前一句末尾,不会像
size-based 那样在任意字符位置硬切。

**验证结果**:`report.md`(18305 字符)用默认参数(`max_sentences_per_chunk=5,
overlap_sentences=1`)切出 33 个句子级 chunk,比 size-based 的 141 个 chunk 少
很多——因为每个 chunk 装的是"5 句完整的话",天然比固定 150 字符能装下更多完整
语义单元。

**局限**:句子本身如果很长(比如财报里那种一句话塞进好几个数据引用的长句),
单句就可能超过合理长度;而且句子级别的切分仍然可能把"讨论同一个话题的连续 5 句
话"和"下一个话题的第 1 句"分到一起,不像 structure-based 那样有明确的语义边界。

### 2.4 三种策略的共同坑:都不保证"检索到的 chunk 一定相关"

**重要提醒**(呼应上一课的自测题):即使 chunking 做对了,这三种策略解决的都是
"怎么把文档切成合理的单元",不解决"用户提问时怎么判断哪个 chunk 相关"——那是
lesson 3(embedding)和 lesson 6(BM25)要解决的问题。chunking 只是让后续检索
有一个"质量及格"的候选池,candidate pool 本身的质量上限就是这一课的主题。

---

## Section 3 — Code 实操

对应 notebook:`002_chunking.ipynb`(直接沿用课程提供的原始 notebook,我在每个
cell 上加了注释,没有新建或改动原始逻辑)。

### 3.1 为什么这节直接用课程给的 notebook,不重新生成

课程官方 notebook 已经包含了 3 个 chunking 函数 + 1 个跑 size-based chunking
的示例 cell,逻辑完整、可直接运行。按你的要求,后续课程不再新建 `.ipynb`,只在
原 notebook 基础上加注释——所以这节直接把 `001_chunking.ipynb` 复制过来重命名
为 `002_chunking.ipynb`(保持这个 RAG 文件夹里"编号跟课程顺序对应"的命名习惯),
再逐 cell 补充中文注释。

### 3.2 定义 `chunk_by_char` 的 cell —— Section 2.1 对应的代码

```python
def chunk_by_char(text, chunk_size=150, chunk_overlap=20):
    ...
```

**输入**:一段字符串 `text`,以及 `chunk_size`(每个 chunk 的字符数)和
`chunk_overlap`(相邻 chunk 重叠的字符数)。
**输出**:一个字符串列表,每个元素是一个 chunk。
**关键行**:`start_idx = end_idx - chunk_overlap if end_idx < len(text) else
len(text)` —— 只有当这不是最后一个 chunk 时才往回退 overlap,否则直接跳到文本
末尾结束循环。这行代码就是 2.1 节里"overlap 提高完整语义落在同一 chunk 里的
概率"这个机制的具体实现。

### 3.3 定义 `chunk_by_sentence` 的 cell —— Section 2.3 对应的代码

```python
sentences = re.split(r"(?<=[.!?])\s+", text)
```

**为什么这么写**:用 lookbehind 保证标点留在句子末尾,这是 2.3 节解释的"不会
切断单词"的核心原因。之后按 `max_sentences_per_chunk - overlap_sentences` 步长
滑动窗口取句子分组,跟 `chunk_by_char` 的 overlap 逻辑是同一个思路,只是单位从
"字符"换成了"句子"。

### 3.4 定义 `chunk_by_section` 的 cell —— Section 2.2 对应的代码

```python
def chunk_by_section(document_text):
    pattern = r"\n## "
    return re.split(pattern, document_text)
```

**输入**:整份 Markdown 文本。**输出**:按二级标题切开的字符串列表。这是三种
策略里代码最短的一个,但代价就是 2.2 节说的"标题标记被吃掉"和"依赖文档结构"
两个限制。

### 3.5 实际跑 chunking 的 cell —— 用 `report.md` 验证 Section 2.1 的坑

```python
with open("./report.md", "r") as f:
    text = f.read()

chunks = chunk_by_char(text)

[print(chunk + "\n----\n") for chunk in chunks]
```

**输入**:`report.md`(课程提供,18305 字符,故意设计成 10 个互不相关领域拼接
起来的文档,专门用来暴露"切错了混入不相关内容"的问题)。
**输出**:141 个 chunk,逐个打印,用 `----` 分隔。
**验证到的真实结果**(实际跑这份 notebook 得到的,不是估算):
- chunk 3 结尾是 `"...Advances in **Medical Research** fo"`,chunk 4 开头是
  `"cused on the rare XDR-471 syndrome..."`——正是 2.1 节讲的单词被硬切成两半
- 多个 chunk(如 chunk 39/40、chunk 49)横跨两个不同 section 的边界,比如
  同时包含"Section 1 Medical Research 的结尾句"和"Section 2 Software
  Engineering 的开头句"——这就是这节课开头举的"bug"混淆案例的根源:如果这样
  的 chunk 被检索命中,模型看到的上下文里同时有医疗和软件工程的内容
- **这个 cell 完全不调用 Claude API**,纯本地字符串处理,不产生任何 token 消耗,
  不受你目前 rate limit 的影响

---

## 自测问题

1. `chunk_by_char` 加了 `chunk_overlap` 之后,是"保证"还是"提高概率"让完整语义
   落在同一个 chunk 里?两者的区别是什么?
2. 如果你的文档是没有 Markdown 标题、纯文本贴出来的日志文件,三种策略里哪个会
   直接失效,哪个仍然可用?
3. `chunk_by_section` 用 `re.split(r"\n## ", document_text)` 切分之后,每个
   chunk 里还包不包含 `"## "` 这个标记本身?这会不会影响后续展示或检索?
4. 这节课的 `chunk_by_char` cell 完全没有调用 Claude API,为什么在 RAG pipeline
   里 chunking 这一步通常也不需要调用大模型?
