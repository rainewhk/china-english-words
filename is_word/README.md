# `is_word` 使用说明文档

> 仓库路径：`is_word/`  
> 文档版本：基于仓库 `is_word/` 与 `middle_school/` 当前代码撰写。

```
https://github.com/dwyl/english-words
words.txt
read_english_dictionary.py

https://github.com/mwiens91/english-words-py
read_english_dictionary.py

https://www.gutenberg.org/files/3201/files/
https://pypi.org/project/moby-dict/
single.txt
```

## 一、模块概述

`is_word` 是一个**纯判定型（bool）英文词库**封装包，用来回答一个问题：

> 给定一个字符串，它是不是一个**合法的英文单词**？

它不依赖任何外部 NLP 服务，全部逻辑在本地通过 5 个相互独立的英文词集合/语料完成匹配判断，并通过大小写归一化与"非法字符"预过滤两条规则，将判定粒度统一到单词级别。

最终对外暴露的核心入口：

| 函数 | 来源文件 | 用途 |
| --- | --- | --- |
| `is_word(word)` | `is_word/__init__.py` | 宽松判定（5 个词典并集） |
| `is_word_strict(word)` | `is_word/__init__.py` | 严格判定（4 个词典并集，不含 wordfreq） |
| `is_web2_word(word)` | `get_english_words_set.py` | 是否在 Web2 词典中 |
| `is_gcide_word(word)` | `get_english_words_set.py` | 是否在 GCIDE 词典中 |
| `is_moby_dict_word(word)` | `moby_dict_word_list.py` | 是否在 Moby 词典中 |
| `is_english_word(word)` | `read_english_dictionary.py` | 是否在 `words.txt` 词典中 |
| `is_wordfreq_word(word)` | `wordfreq_words.py` | 是否在 wordfreq 'best' 词表中（频率 > 0） |

## 二、目录与文件一览

```
is_word/
├── __init__.py                # 对外入口，导出 is_word / is_word_strict
├── get_english_words_set.py   # 封装 english_words 包，提供 web2 / gcide
├── moby_dict_word_list.py     # 封装 Moby 词库
├── moby_corpus.py             # Moby 词库的下载、缓存、合并工具
├── read_english_dictionary.py # 本地 words.txt 词典封装
├── wordfreq_words.py          # 封装 wordfreq 的 best 词表
├── single.txt                 # Moby single.txt（解压出的纯词表，~3.5MB）
├── words.txt                  # dwyl/english-words 大词典（~4.6MB）
└── README                     # 数据来源说明
```

数据来源（详见 `is_word/README`）：

- `words.txt` — [dwyl/english-words](https://github.com/dwyl/english-words)
- `single.txt`（Moby 词库） — [Project Gutenberg 3201](https://www.gutenberg.org/files/3201/files/)，通过 [moby-dict](https://pypi.org/project/moby-dict/) 下载
- Web2 / GCIDE — [english-words](https://pypi.org/project/english-words/) Python 包

## 三、内部词典说明

### 3.1 Web2 / GCIDE（`get_english_words_set.py`）

基于 [`english_words`](https://pypi.org/project/english-words/) 包，模块**导入时**就预先构造两个全小写集合：

```python
web2lowerset  = get_english_words_set(['web2'],  lower=True)
gcidelowerset = get_english_words_set(['gcide'], lower=True)
```

判定函数：

```python
def is_web2_word(word: str) -> bool:
    return word in web2lowerset

def is_gcide_word(word: str) -> bool:
    return word in gcidelowerset
```

要点：

- 集合**预加载**于模块导入阶段（一次性开销），后续每次查询都是 O(1)。
- 全部已**小写化**，因此调用方传入的 `word` 必须是小写形式（`is_word` 主入口负责大小写归一）。

### 3.2 Moby 词库（`moby_corpus.py` + `moby_dict_word_list.py`）

`moby_corpus.py` 负责从 Project Gutenberg 下载并合并所有 Moby 词表文件：

- 目录列表 URL：`_LISTING_URL = "https://www.gutenberg.org/files/3201/files/"`
- 默认缓存目录：`~/.cache/moby_corpus/`
- 文件列表缓存：`file_list.txt`
- 单文件下载支持 **3 次重试** + 指数退避（`time.sleep(2 ** attempt)`）
- 写入使用 **临时文件 + `os.replace`** 的原子替换，避免半成品文件被并发读取
- `words()` 函数把所有 `.txt` 词表合并为一个 `set[str]`（用 `latin-1` 解码容错）
- 首次调用需要联网；之后**完全离线**

`moby_dict_word_list.py` 在模块导入时执行一次 `words()`，结果缓存为模块级 `all_words`：

```python
from is_word.moby_corpus import words
all_words = words()  # 首次会下载并缓存

def is_moby_dict_word(word: str) -> bool:
    return word in all_words
```

仓库中已附带 `single.txt`，实际查询时通常使用本地这份精简版（见后文 `is_word_strict` 与 `is_word` 的区别）。

### 3.3 本地词典（`read_english_dictionary.py`）

直接读取同目录下的 `words.txt`（约 37 万词，dwyl/english-words 仓库快照）：

```python
with open(f'{current_dir}/words.txt') as word_file:
    valid_words = set(word_file.read().split())

def is_english_word(word: str) -> bool:
    return word in valid_words
```

特点：

- 大小写敏感（与原文件一致，调用前需自行归一化）
- 包含大量**专有名词、地名、人名、品牌**等（如 "Beijing"、"Google"）
- 不区分词性、不区分词频

### 3.4 wordfreq 词频词表（`wordfreq_words.py`）

封装 [`wordfreq`](https://pypi.org/project/wordfreq/) 的 `'best'` 词表（高频词子集，~70k 词）：

```python
def is_wordfreq_word(word: str) -> bool:
    return word_frequency(word, 'en', wordlist='best') > 0.0

def is_wordfreq_zipf_word(word: str) -> bool:
    return zipf_frequency(word, 'en', wordlist='best') >= 1.0
```

要点：

- `word_frequency` 是**实数运算**（不是 O(1) 查询），且依赖下载数据
- 只用 `> 0.0` 的阈值（包含出现频次极低的词），所以匹配率很高
- 提供了一个更严格的变体 `is_wordfreq_zipf_word`，要求 zipf 频率 ≥ 1.0（更高频），但默认并不对外暴露使用

## 四、`__init__.py` 主入口详解

### 4.1 `has_impossible_english_chars` —— 非法字符预过滤

```python
def has_impossible_english_chars(text: str) -> bool:
    if text.startswith('-') or text.startswith('\'') or text.startswith('.'):
        return True

    allowed_chars = set(string.ascii_letters + string.digits + "'-.")

    for char in text:
        if ord(char) < 128:                       # 只检查 ASCII 字符
            if char not in allowed_chars:
                return True                       # 出现空格、!、@、#、,、;、? 等
    return False
```

判定规则：

- **首字符**为 `-`、`'`、`.` → 直接视为非法（英语单词一般不以这些符号开头）
- 字符串中（仅看 ASCII 区段）出现除**字母、数字、`'`、`-`、`.`** 之外的字符 → 视为非法
- 非 ASCII（Unicode）字符**忽略**（不影响后续词典匹配，由词典自然过滤）

### 4.2 `_is_word_ori` / `_is_word_ori_strict` —— 词典并集

```python
def _is_word_ori(word: str) -> bool:
    # 宽松：5 个词典并集
    return (is_web2_word(word) or is_gcide_word(word)
            or is_moby_dict_word(word) or is_english_word(word)
            or is_wordfreq_word(word))

def _is_word_ori_strict(word: str) -> bool:
    # 严格：去掉 wordfreq 的 4 个词典并集
    return (is_web2_word(word) or is_gcide_word(word)
            or is_moby_dict_word(word) or is_english_word(word))
```

区别只在是否包含 `is_wordfreq_word`：

- 严格版不含 wordfreq → 不依赖 wordfreq 包与联网，**完全离线**且无 `single.txt` 之外的大文件依赖
- 宽松版多了 wordfreq → 对**网络新词**（如 `covid`、`metaverse` 等）识别率更高

### 4.3 `is_word` / `is_word_strict` —— 公开 API

```python
def is_word(word: str) -> bool:
    if has_impossible_english_chars(word):
        return False
    return (_is_word_ori(word.lower())    or
            _is_word_ori(word.capitalize()) or
            _is_word_ori(word.upper())    or
            _is_word_ori(word.title()))

def is_word_strict(word: str) -> bool:
    if has_impossible_english_chars(word):
        return False
    return (_is_word_ori_strict(word.lower())    or
            _is_word_ori_strict(word.capitalize()) or
            _is_word_ori_strict(word.upper())    or
            _is_word_ori_strict(word.title()))
```

算法步骤：

1. **非法字符预过滤**：命中即返回 `False`。
2. **大小写归一化**：把输入分别转成四种形式 `lower / capitalize / upper / title`，任一形式在词典中找到即视为合法。

四种形式示例（输入 `"iPhone"`）：

| 形式 | 结果 |
| --- | --- |
| `lower`      | `"iphone"`     |
| `capitalize` | `"Iphone"`     |
| `upper`      | `"IPHONE"`     |
| `title`      | `"Iphone"`     |

> 由于 `words.txt` / `web2` / `gcide` / `moby` 的预加载集合都是小写（或与原文一致），所以**对小写形式命中概率最高**。其余三种形式用于补救"以全大写 / 标题大写形式收录"的少量词条。

## 五、在 `middle_school` 中的使用

### 5.1 `extract_words.py` —— 词性标注 + 单词过滤

`middle_school/extract_words.py:3` 导入：

```python
from is_word import is_word
```

使用位置（`extract_words.py:46-51`）：

```python
if is_word(word.lemma):
    word.lemma = word.lemma.lower()
elif is_word(word.text):
    word.lemma = word.text.lower() + '[MANUAL]'
else:
    continue
```

业务逻辑：

1. 使用 **Stanza** 对每行文本做 `tokenize + mwt + pos + lemma` 流水线，得到每个词的 `text`（原形）与 `lemma`（词元）。
2. 排除 `PUNCT / X / NUM / SYM` 等无用 UPOS 与 `ADD` 等 XPOS。
3. 排除纯数字词、含 `_` 的组合词（如 `don't` 被 mwt 拆开的情况）。
4. **首选**用 `is_word(word.lemma)` 判定是否为合法英文单词：
   - 命中 → 将 `lemma` 转小写后写入。
5. **回退**到 `is_word(word.text)`：
   - 命中 → 用 `text` 小写代替 `lemma`，并在末尾追加 **`[MANUAL]`** 标记，表示该词**未被词形还原**，可能是专有名词、新词、或 Stanza 词元不在词典内但原文属于合法英文单词。
6. 两者都未命中 → 直接 `continue` 跳过该 token。
7. 最终输出 `<name>.log`（去重排序后的 lemma 列表）与 `<name>.jsonl`（每个 token 的结构化信息：`text / lemma / upos / xpos / feats`）。

> 关键设计：把"是单词但不是常用词元"的情况用 `[MANUAL]` 标记出来，便于后续人工 review 与补录到词表。

### 5.2 `temp_generate_strict.py` —— 用严格词典汇总词表

`middle_school/temp_generate_strict.py:6` 导入：

```python
from is_word import is_word_strict
```

使用位置（`temp_generate_strict.py:36-41`）：

```python
if is_word_strict(lemma):
    words_set.add(lemma)
    count += 1
elif is_word_strict(text):
    words_set.add(text)
    count += 1
```

业务逻辑：

- 遍历 `books_junior/` 与 `books_senior/` 下所有 `*.jsonl`（由 `extract_words.py` 生成）。
- 对每条记录的 `lemma` 优先用 **`is_word_strict`**（不含 wordfreq）判定；不命中再退到 `text`。
- 把所有通过判定的词写入 `words_set_strict.txt`（排序后去重）。

与 `temp_generate_set.py`（无过滤直接收集 `lemma`）的对比：

| 脚本 | 是否过滤 | 输出文件 | 适用场景 |
| --- | --- | --- | --- |
| `temp_generate_set.py` | ❌（不过滤） | `words_set.txt` | 全量词表（含 `[MANUAL]`、专有名词、新词） |
| `temp_generate_strict.py` | ✅（`is_word_strict`） | `words_set_strict.txt` | 仅保留**严格词典认可的词** |

### 5.3 调用约定总结

| 场景 | 用哪个函数 | 为什么 |
| --- | --- | --- |
| **抽取课本单词时希望尽量收词**（含新词、网络词、专有名词） | `is_word` | 包含 wordfreq，召回率高 |
| **生成"严格"词表、排除生造词** | `is_word_strict` | 不依赖 wordfreq，完全离线，结果更保守 |
| **只想查询单一词典**（如只想知道是不是 Moby 词） | `is_moby_dict_word` 等 | 细粒度控制 |

## 六、安装与运行前置依赖

```toml
# pyproject.toml / uv 管理依赖
[project]
dependencies = [
    "english_words",   # 提供 web2 / gcide
    "wordfreq",         # 提供 'best' 词表
    "requests",         # moby_corpus 下载依赖
    "stanza",           # middle_school 业务依赖
]
```

`is_word` 本体**无任何运行时网络请求**（除首次使用 `is_moby_dict_word` / `is_word` 触发 Moby 下载外）；`is_word_strict` 路径**完全离线**。

## 七、注意事项与已知边界

1. **大小写匹配**：5 个子集合中 `web2 / gcide / moby` 都是**小写预加载**；`words.txt` / `wordfreq` 内部也是小写化判定。`__init__.py` 的入口函数已自动做四种大小写尝试，调用方无需再处理大小写。
2. **首字符限制**：以 `-` / `'` / `.` 开头的字符串一律返回 `False`，因此像 `.com` 这种顶级域会被直接拒绝。
3. **`_is_word` 顺序短路**：`_is_word_ori` 中 `is_word` 各子判定按顺序执行，命中即返回，理论上 `is_web2_word / is_gcide_word` 的 O(1) 集合查询最快，会优先命中。
4. **`wordfreq` 性能开销**：`is_wordfreq_word` 每次都会进行实数运算（`word_frequency > 0.0`），相对其他 4 个 O(1) 集合查询较慢；如果只关心是否在词频表中，可以直接用 `is_wordfreq_word` 或自己缓存 `word_frequency` 结果。
5. **`[MANUAL]` 标记**：`extract_words.py` 会把"原文是合法单词但词元不是"的情况用 `[MANUAL]` 后缀写入 `lemma`，下游消费 `words_set*.txt` 时需要注意这种字符串后缀。
6. **`is_word_strict` 不等于"更严格"的英文语义**：它只是去掉了 wordfreq 这一来源，所以**对低频/新词识别反而更差**；所谓"严格"指的是"只信任离线词典"。

## 八、最小使用示例

```python
from is_word import is_word, is_word_strict

# 基础判定
print(is_word('fate'))          # True
print(is_word_strict('fate'))   # True

# 大小写无关
print(is_word('Fate'))          # True
print(is_word('FATE'))          # True

# 非法字符
print(is_word('hello world'))   # False（空格）
print(is_word('hello!'))        # False（感叹号）

# 新词 / 网络词（依赖 wordfreq）
print(is_word('metaverse'))     # True （is_word）/ False （is_word_strict）

# 词元 vs 原文
print(is_word('singaporean'))   # True（人名/形容词）
print(is_word('woodfired'))     # True（组合形容词）
```
