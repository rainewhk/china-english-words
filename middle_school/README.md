# `middle_school` 目录说明文档

> 路径：`middle_school/`  
> 文档目标：**逐文件讲清楚每个脚本做了什么、技术细节、以及"想做类似事情去哪里找代码"**。

## 一、目录全貌

`middle_school/` 是一个**英语教材词库生产流水线**，把"中学英语教材 PDF"逐步变成"结构化的英文单词数据 / 词频分析 / Anki 卡片"。它由两条并行链路组成：

| 链路 | 输入 | 输出 | 关键脚本 |
| --- | --- | --- | --- |
| **教材抽取** | `books_junior/books_senior/*.pdf` | `*.txt` → `*.log / *.jsonl` | `extract_text.py`、`extract_words.py`、`main.py` |
| **第三方词库汇总** | `maimemo_senior/`、`youdao_ydschool_chugao/`、`top-rated/`、`维克多新高中英语词汇列表.txt` | `high_school.txt` | `extract.py` |
| **Anki 卡片生成** | `文言/120文言实词.CSV` | `文言/120文言实词_anki.csv` | `convert.py` |
| **词表汇总 / 去重** | `*.jsonl` | `words_set.txt`、`words_set_strict.txt` | `temp_generate_set.py`、`temp_generate_strict.py` |
| **词频数据库** | `books_junior + books_senior + ECDICT + wordfreq` | `top-rated/word_frequency.db` / `word_frequency.csv` | `top-rated/generate_db.py` |

子目录里还各有一个自己的小脚本（`maimemo_senior/count_words.py`、`youdao_ydschool_chugao/count_words.py`），详见后文。

## 二、文件清单与依赖概览

```
middle_school/
├── main.py                    # 入口调度：批量执行 extract_text + extract_words
├── extract_text.py            # PDF → TXT（含版面分析、合并、断字还原）
├── extract_words.py           # TXT → JSONL（含 Stanza 词形还原 + is_word 过滤）
├── extract.py                 # 多源词表汇总 → high_school.txt
├── temp_generate_set.py       # 把 books_*.jsonl 里的 lemma 合并到 words_set.txt
├── temp_generate_strict.py    # 同上，但用 is_word_strict 二次过滤
├── convert.py                 # 文言文 CSV → Anki 卡片 CSV（带 HTML/CSS 样式）
├── 维克多新高中英语词汇列表.txt  # 维克多词典的纯词表（被 extract.py 引用）
├── words_set.txt              # 所有教材 lemma 并集（含 [MANUAL]）
├── words_set_strict.txt       # 经 is_word_strict 过滤后的版本
├── books_junior/              # 初中教材 PDF/TXT/JSONL 落地目录
├── books_senior/              # 高中教材 PDF/TXT/JSONL 落地目录
├── maimemo_senior/            # 墨墨高中词库原始数据 + count_words.py
├── youdao_ydschool_chugao/    # 有道初中词库原始数据 + count_words.py
└── top-rated/                 # 词频分析（ECDICT + wordfreq + 教材） generate_db.py
```

依赖（来自各脚本 import）：

- **PDF 处理**：`pymupdf`（`import fitz`）
- **NLP**：`stanza`（`Pipeline('en', processors='tokenize,mwt,pos,lemma')`）
- **词典判定**：`is_word`（同级目录的 `../is_word/`）
- **词频**：`wordfreq`（`zipf_frequency`）
- **数据库**：`sqlite3`（标准库）
- **外部词频词典**：`ecdict/stardict.db`（路径写死在 `top-rated/generate_db.py`）
- **CLI/IO**：`csv`、`json`、`pathlib`、`re`、`collections.Counter`、`urllib.parse.unquote`

## 三、`extract_text.py` —— PDF → TXT（教材版）

> 入口函数：`extract_text(pdf_path, output_path)`

### 3.1 它做了什么

把"扫描/数字化教材"风格的 PDF（含双栏、脚注、词性标注、音标、页眉页脚）解析成**逐行干净文本**，输出 `.txt` 文件供 `extract_words.py` 进一步处理。

### 3.2 技术细节

整体流水线：

```
PDF → fitz.get_text("blocks") → sort_page_blocks → merge_blocks
    → clean_text_block → enhance_clean_line → should_skip_line → 写入 TXT
```

关键模块：

1. **`is_chinese_char_or_punct(char)`**  
   判定 CJK / 全角标点（CJK 统一汉字 `U+4E00-U+9FFF`、CJK 符号 `U+3000-U+303F`、全角形式 `U+FF00-U+FFEF`）。用于判断"当前行是中英文混合"的边界。

2. **`enhance_clean_line(line)`** —— 行级清洗，6 个动作：
   - **Unicode → ASCII 标点**：`’‘“”–—…` 全部归一为 `'"'-...`。
   - **删除音标**：`re.sub(r'\s*/[^/]+/\s*', ' ', line)`（如 `/ˈæpəl/`）。
   - **截断到第一个中文**（含全角符号），丢弃中文释义/脚注。
   - **去尾部词性缩写**：`n|adj|adv|v|prep|conj|pron|num|art|int .?`。
   - **去尾部页码**：`re.sub(r'\s*\d+$', '', line)`。
   - **最终只保留 ASCII `[32, 126]`**（即"传统可打印 ASCII"），用于剔除所有残留的控制字符/特殊字符。

3. **`should_skip_line(line)`** —— 丢弃"页眉页脚 / 章节标题 / 空行"：
   - 纯数字（页码）→ 跳过。
   - 折叠空白后小写匹配：`unit / vocabulary / lookingforwards / namesandplaces / names / places` → 跳过。
   - 不含任何字母数字 → 跳过。

4. **`clean_text_block(text)`** —— 处理 PDF 块内**多行换行**：
   - 替换制表符与退格符。
   - **断字还原（word-wrap hyphen heuristic）**：上一行末尾的 `-` + 下一行首字符小写 → 合并为单词；首字母大写 → 保留连字符（认为是真正的复合词或专有名词）。
   - **中英文行间合并**：上一行末/下一行首是中文 → **不加空格**直接拼接；否则按英文 → **加空格**拼接。

5. **`sort_page_blocks(blocks, page_width)`** —— **版面阅读顺序**：
   - 把 block 切成两类：`full_width_blocks`（横跨页面中线且足够宽 → 横幅/标题）和 `other_blocks`（左右栏正文）。
   - 用 full_width_blocks 的纵向坐标把页面切成多个 `band`（带状区），每个带状区内按中线把块分到左右栏，**左右两栏各自按 y 排序**。这样保证双栏教材的阅读顺序是"上一段左栏全部 → 上一段右栏全部 → 横幅 → 下一段左栏…"。

6. **`merge_blocks(sorted_blocks)`** —— **段落/列表项合并**：
   - 维护一个 `current_block`，逐块判断是否应与上一个块合并。
   - **不该合并**（视为新条目）的模式：`** foo` / `* foo` / `UNIT 1` / `➊➋…` / `1.` 或 `1\t`。
   - **应该合并**的判定：同一列（中心 x 差 < 120）+ 垂直距离 < 40 + `is_continuation`，且不属于 bullet。
   - `is_continuation` 4 种情形：行末是 `-`、`,`/`,`/`;`/`;`、字母后跟小写、非句末中文后跟中文/小写。
   - 合并时同样按"中英文边界"决定加不加空格。

7. **`extract_text(pdf_path, output_path)`** —— 主入口：
   - 逐页 `fitz.open(pdf_path) → page.get_text("blocks")`。
   - 经过 `sort_page_blocks → merge_blocks → enhance_clean_line → should_skip_line` 后写入文件。
   - 每 10 页打印进度。

`__main__` 默认跑的是 `普通高中教科书·英语选择性必修 第四册.pdf`，**实际批量处理入口是 `main.py`**。

### 3.3 适用场景与"去哪找代码"

| 你想做的事 | 看哪里 |
| --- | --- |
| 把扫描版教材 PDF 转干净 TXT | `extract_text.py` 全文（特别是 `sort_page_blocks` 与 `merge_blocks`） |
| 处理 PDF 双栏/三栏版面 | `sort_page_blocks(blocks, page_width)` |
| 还原断字换行（word-wrap hyphen） | `clean_text_block()` 的 `match_prev`/`match_next` 分支 |
| 中英文混合文档的清洗 | `is_chinese_char_or_punct` + `clean_text_block` 的中英文空格策略 |
| 过滤页眉页脚/章节标题 | `should_skip_line` |

## 四、`extract_words.py` —— TXT → JSONL（每词结构化）

> 入口函数：`extract_words(txt_path, output_name)`

### 4.1 它做了什么

对 `extract_text.py` 输出的纯文本逐行做 **Stanza 英文流水线**，得到每个 token 的 `text / lemma / upos / xpos / feats`，再用 `is_word` 过滤掉非英文词，最后写两份文件：

- `<output_name>.log` —— 去重排序后的 lemma 列表（一行一词）
- `<output_name>.jsonl` —— 每个 token 的完整结构（每行一个 JSON）

### 4.2 技术细节

1. **Stanza 流水线**：`nlp = stanza.Pipeline('en', processors='tokenize,mwt,pos,lemma', verbose=True)`  
   - `mwt`（multi-word token）会把 `don't`、`I'm` 等拆开；所以下游需要跳过带 `_` 的 `text`。
   - `pos` 提供 UPOS/XPOS/feats；`lemma` 提供词形还原。

2. **预处理**：`line.replace('(', ' ( ').replace(')', ' ) ')` —— 在括号两侧加空格，避免 Stanza 把 `word(w)` 错识别成单 token。

3. **批量送入**：`in_docs = [stanza.Document([], text=d) for d in documents]` → `nlp(in_docs)`（批量模式比一行一调快很多）。

4. **三道过滤**（详见 `docs/is_word.md`）：
   - `exclude_filters['upos']`：`PUNCT / X / NUM / SYM`
   - `exclude_filters['xpos']`：`ADD`
   - `word.lemma.isnumeric()` → 跳过
   - `'_' in word.text` → 跳过（被 mwt 拆开的组合词，如 `do n't`）
   - **`is_word(word.lemma)` 命中** → 写入小写 lemma
   - **否则 `is_word(word.text)` 命中** → 用 `text` 小写代替 lemma，并附 `[MANUAL]` 后缀
   - **都不命中** → `continue` 跳过整个 token

5. **输出字段**：`text / lemma / upos / xpos / feats`（5 个字段），其中 `feats` 是字符串形式的形态特征（如 `Mood=Ind|Number=Sing|Person=1|Tense=Pres|VerbForm=Fin`）。

6. **`unique_set = set(i['lemma'] for i in result)`**：用于后续累计（虽然 `main.py` 已注释掉对全局 `words_set.txt` 的更新，但函数仍 `return unique_set`）。

### 4.3 适用场景与"去哪找代码"

| 你想做的事 | 看哪里 |
| --- | --- |
| 对英语文本做批量词形还原 + 词性标注 | `extract_words.py` 的 stanza 初始化 + `extract_words` 主循环 |
| 区分"标准词形还原"与"未还原但仍是英文单词" | `[MANUAL]` 后缀逻辑（第 48-49 行） |
| 跳过标点/数字/未知词 | `exclude_filters` + `_in word.text` 检查 |

## 五、`main.py` —— 流水线编排入口

### 5.1 它做了什么

`main.py` 是一个**调度脚本**，不写新逻辑，只把 `extract_text.extract_text` 与 `extract_words.extract_words` 串起来，对 `file_name_list` 中列出的每本教材 PDF 跑一次：

```
PDF  → TXT  → JSONL/LOG
```

### 5.2 技术细节

- `root_name = 'books_junior'`：输入输出都在 `books_junior/`（**当前**没有切换到 `books_senior/`，要换目录得改这里）。
- `exec_pdf(pdf_name)`：把 `books_junior/<pdf_name>.pdf` 转成 `.txt`，再调用 `extract_words` 输出 `.log`/`.jsonl`。
- `file_name_list`：列出了**所有要处理的初中教材**，已注释掉"人教版 / 译林版 / 外研社版"三套，只保留"冀教版 / 沪教版 / 沪外教版 / 科普版 / 鲁教版 / 教科版"。注释里写的是"补充新的需要手动设置"，所以**新版本只需替换/打开注释**即可。
- `__main__` 的 `for` 循环目前**只调 `extract_words`**，跳过了 `extract_text`（注释掉了）—— 意味着 `*.txt` 是**预先准备好的**，跑这个脚本不会重新解析 PDF。
- 文件末尾被注释的代码展示了**累加到全局 `words_set.txt` 的旧方案**（现在被 `temp_generate_set.py` 取代）。

### 5.3 适用场景与"去哪找代码"

| 你想做的事 | 看哪里 |
| --- | --- |
| 批量跑一套教材 | `main.py` 整体结构 + `file_name_list` |
| 切换输入目录到 `books_senior` | 改 `root_name` 并取消对应 PDF 的注释 |
| 恢复"重新跑 PDF"的能力 | 取消第 89 行 `extract_text` 的注释，并修改 `file_name_list` 中要重跑的条目 |

## 六、`temp_generate_set.py` —— 全量词表汇总

### 6.1 它做了什么

遍历 `books_junior/`、`books_senior/` 下所有 `*.jsonl`，把每条记录的 `lemma` 直接收集到 `words_set.txt`（**不过滤**）。

### 6.2 技术细节

- 用 `pathlib.Path.glob('*.jsonl')` 找文件，逐行 `json.loads`，跳过 `json.JSONDecodeError`。
- **不调 `is_word`**：保留所有 lemma，包括 `[MANUAL]` 标记、专有名词、被 Stanza 错误还原但原文是单词的项。
- 最终用 `sorted(words_set)` 排序后写入 `words_set.txt`。

### 6.3 与 `temp_generate_strict.py` 的对比

| 维度 | `temp_generate_set.py` | `temp_generate_strict.py` |
| --- | --- | --- |
| 过滤 | ❌ | ✅ `is_word_strict` |
| 取值优先级 | 仅 `lemma` | `lemma` → 失败回退 `text` |
| 输出 | `words_set.txt` | `words_set_strict.txt` |
| 适合 | 全量盘点、人工 review | 输出"可信词表" |

## 七、`temp_generate_strict.py` —— 严格词表汇总

### 7.1 它做了什么

与 `temp_generate_set.py` 同结构，但**多了一层 `is_word_strict` 校验**：先校验 `lemma`，失败再校验 `text`。通过的才加入集合。

### 7.2 技术细节

- 同样遍历 `books_junior/` 与 `books_senior/` 的 `*.jsonl`。
- `is_word_strict` 来自 `../is_word/`，不含 wordfreq，**完全离线**且不会因为新词/网络词误命中。
- 输出 `words_set_strict.txt`。
- 打印每个文件贡献的词数与总数，便于排查某本书为什么词数异常少。

## 八、`extract.py` —— 第三方词库汇总到 `high_school.txt`

### 8.1 它做了什么

把 4 个**已统计好的 CSV / TXT 词表**合并去重，输出到仓库根目录的 `high_school.txt`：

1. `middle_school/maimemo_senior/word_counts.csv`（墨墨高中词库）
2. `middle_school/youdao_ydschool_chugao/word_counts.csv`（有道初中词库）
3. `middle_school/top-rated/word_frequency.csv`（教材高频）
4. `middle_school/维克多新高中英语词汇列表.txt`（维克多高中词汇）

### 8.2 技术细节

- 每个 CSV 都是 `单词, 次数`（含表头），`extract.py` 用 `next(reader)` 跳过表头，然后只读第一列 `row[0].strip().lower()`，**忽略次数**。
- TXT 直接逐行 `lower()` 入集合。
- `sorted(words)` → `high_school.txt`（每行一个词）。

### 8.3 适用场景

| 你想做的事 | 看哪里 |
| --- | --- |
| 把多个词库 CSV/TXT 合并成一个纯词表 | `extract.py` 整体结构（极简模板） |
| 只取第一列、忽略统计列 | `next(reader)` + `row[0].strip().lower()` |

## 九、`convert.py` —— 文言文 CSV → Anki 卡片 CSV

### 9.1 它做了什么

把 `文言/120文言实词.CSV`（每行：单词 + 多行释义）转换成 Anki 可导入的 HTML 表格形式，写到 `文言/120文言实词_anki.csv`。

> 注意：当前仓库中 `文言/` 目录不存在（被 git 忽略或在另一台机器上），所以直接 `python convert.py` 会因找不到输入文件而 `return`。脚本设计上是**自包含**的，路径通过 `os.path.join("文言", ...)` 拼接。

### 9.2 技术细节

1. **`parse_line(line)`**：把每行释义切成 `(key, val)`：
   - 不含 `。` → 直接视为注释/音标/提示 → `("", line)`。
   - 含 `。` → 按首个 `。` 切分。
   - 用正则 `^[\(\（\s]*\d+[\)\）\s\.]|^[①-⑩]|^[A-Za-z]\s*\.` 判定是否为"编号义项"（如 `1. xxx` / `① xxx` / `A. xxx`）。
   - 否则按 key 长度兜底：`<=15` 字符视为"义项标题"，否则视为"长注释"。

2. **`generate_html_table(explanation)`**：
   - 把每行 `parse_line` 后组装成 `<tr><td class="anki-key">…</td><td class="anki-val">…</td></tr>`。
   - `key` 为空时：
     - 如果 `val` **只包含字母 + 拼音声调（āáǎà…）** → 用 `<span class="anki-pron">` 标紫。
     - 否则视为普通注释 → 用 `<span class="anki-note">` 标绿（带左侧绿条）。

3. **`ANKI_CSS`**：完整的 `<style>...</style>` 块，包含：
   - 表格布局、字号、padding。
   - 暗色模式 `@media (prefers-color-scheme: dark)` 适配。
   - 只在**第一条记录**（`idx == 0`）注入；Anki 会把这个 `<style>` 应用到整个 session，所以只需一次。

4. **`main()`**：读取 → 逐行构造 HTML → 写回 CSV（`newline=""` 防止 Windows 写入双倍行尾）。

### 9.3 适用场景与"去哪找代码"

| 你想做的事 | 看哪里 |
| --- | --- |
| 把"释义 + 音标 + 注释"的纯文本转成 Anki HTML 卡片 | `convert.py` 整体 |
| 用正则区分"编号义项 / 长注释 / 音标" | `parse_line()` + `generate_html_table()` 的 `is_pron` 判断 |
| 给 Anki 卡片注入暗色 CSS | `ANKI_CSS` 与 `idx == 0` 的注入策略 |

## 十、`maimemo_senior/count_words.py` —— 墨墨高中词库计数

### 10.1 它做了什么

从 `词库 高中.md`（一个 Markdown 表格，每行 `| 词库名 | [链接](file.txt) | 描述 |`）解析出要统计的 txt 文件名列表，遍历 `exported/word/*.txt`，对每个文件用 `split()` 切词，`collections.Counter` 累加，最后写出 `word_counts.csv`（两列：单词 / 总次数，按频次降序）。

### 10.2 技术细节

- **Markdown 解析**：手动 `line.split('|')`，跳过含 `选修` 的行（高中选修教材不在统计范围），跳过表头/分隔线行，用正则 `r'\]\(([^)]+)\)'` 抽出第二列的链接文本。
- **URL 解码**：`unquote(os.path.basename(href))`，因为文件名可能含 `%E4%B8%AD` 这类编码。
- **写入 CSV**：用 `encoding='utf-8-sig'`（BOM 头），便于 Excel 正确识别中文。
- **频次排序**：`counter.most_common()` 自然给出降序。

### 10.3 适用场景

| 你想做的事 | 看哪里 |
| --- | --- |
| 从 Markdown 表格批量解析文件名清单 | `extract_txt_filenames(md_path)` |
| `Counter.update(tokens)` 的典型用法 | `main()` 第 50-55 行 |
| 给 CSV 加 BOM 头（Excel 友好） | `open(..., encoding='utf-8-sig')` |

## 十一、`youdao_ydschool_chugao/count_words.py` —— 有道初中词库计数

### 11.1 它做了什么

读取 `dict/*.jsonl`（每行一个词头 JSON，含 `headWord` 字段），累加 `headWord` 计数，输出 `word_counts.csv`。

### 11.2 技术细节

- 用 `os.listdir` + 排序找到所有 `.jsonl`，比 `glob` 更直观。
- `data.get('headWord')` 累加；无 `headWord` 的记录静默忽略。
- 同样是 `utf-8-sig` 编码 + `most_common()` 降序输出。

### 11.3 适用场景

| 你想做的事 | 看哪里 |
| --- | --- |
| 批量汇总多个 JSONL 文件的某个字段 | `youdao_ydschool_chugao/count_words.py` 全文（与 `maimemo_senior/count_words.py` 互为对照） |

## 十二、`top-rated/generate_db.py` —— 中学教材词频 SQLite 数据库

### 12.1 它做了什么

把"教材语料 + 第三方词典"三路数据汇成一张 SQLite 表 `word_frequency`，便于按 `textbook_count / bnc / frq / zipf` 排序和检索；同时输出 `word_frequency.csv`（Excel 友好）。

### 12.2 技术细节

#### 路径与配置（文件首部）

```python
ROOT = Path(__file__).parent.parent.parent      # 项目根目录
ECDICT_DB_PATH    = ROOT / "ecdict" / "stardict.db"
BOOKS_JUNIOR_PATH = ROOT / "books_junior"
BOOKS_SENIOR_PATH = ROOT / "books_senior"
OUTPUT_DB_PATH    = ROOT / "analysis" / "top-rated" / "word_frequency.db"
```

> ⚠️ 这里的路径假设 `top-rated/` 在 `analysis/` 子目录下（`ROOT.parent.parent`），但实际仓库中 `top-rated/` 在 `middle_school/` 下。**直接跑会找不到 `ecdict/stardict.db` 与 `books_*`**，需要修正路径或软链。

#### `count_textbook_words()`

- 遍历 `books_junior/*.jsonl` 和 `books_senior/*.jsonl`，按 `lemma` 累加：
  - 读 `data['lemma']` → `lower().strip()` → 去掉 `? ! ,` → 过滤含 `# = [ ]` 的"病态 lemma" → 计数。
  - **初中教材**还会过滤 `? ! = # [ ]`；高中教材只过滤空值（逻辑差异见代码注释）。
- 追加两个 CSV 来源：`maimemo_senior/word_counts.csv`、`youdao_ydschool/word_counts.csv`（注：路径写的是 `youdao_ydschool`，与目录名 `youdao_ydschool_chugao` 略有不一致）。
- 返回 `(word_counts: Counter, total_lines: int)`。

#### `load_ecdict_data_for_words(words)`

- 连接 `ecdict/stardict.db`（**SQLite ECDICT 词典库**）。
- **分批查询**（`batch_size = 1000`），避免 `IN (?, ?, …)` 参数过多超过 SQL 限制。
- 只查 `word, bnc, frq` 三列；缺失值兜底为 0。
- 返回 `{word: {'bnc': int, 'frq': int}}`。

#### `create_database(word_counts, ecdict_data)`

- 删除旧库，重新创建。
- 表结构：`word_frequency(id, word UNIQUE, textbook_count, bnc, frq, zipf)`。
- 索引：单列索引 + 排序索引（`textbook_count DESC / zipf DESC`）。
- 数据准备：每条记录用 `get_zipf(word)` 现算 `zipf_frequency(word, 'en', wordlist='best')`。
- 按 `textbook_count DESC` 排序后批量插入。
- **`get_zipf` 用 try/except 兜底为 0.0**，避免 wordfreq 抛异常中断。

#### `write_csv(word_counts, ecdict_data)`

- 同样的数据写一份 `word_frequency.csv`（`utf-8` + Excel 友好排序）。

#### `print_summary()`

- 控制台打印：总词数、有 BNC / FRQ / ZIPF 的词数、教科书 Top 20。

### 12.3 适用场景与"去哪找代码"

| 你想做的事 | 看哪里 |
| --- | --- |
| 把多个 JSONL/CSV 的词频合并到 SQLite | `count_textbook_words()` + `create_database()` |
| 用 SQL 批量查询 ECDICT（避免一次塞过多参数） | `load_ecdict_data_for_words()` 的 `batch_size=1000` 模式 |
| 多列降序索引 + 默认排序 | `create_database()` 第 165-170 行的 `CREATE INDEX ... DESC` |
| 给数据加 `zipf` 等外部计算列 | `get_zipf()` 兜底 + `cursor.executemany(...)` 批量插入 |

## 十三、`books_junior/` 与 `books_senior/`

- **作用**：教材数据的**落地目录**，每个教材一个 PDF / TXT / LOG / JSONL 三件套。
- **`*.txt`**：由 `extract_text.py` 生成。
- **`*.log`**：由 `extract_words.py` 生成，每行一个唯一 lemma（可能含 `[MANUAL]`）。
- **`*.jsonl`**：由 `extract_words.py` 生成，每行一个 token 的 5 字段结构化记录。

> 这两个目录是其他下游脚本（`temp_generate_*`、`top-rated/generate_db.py`、`extract.py`）的**唯一数据源**，命名需保持稳定。

## 十四、典型工作流对照表

| 目标 | 跑哪些脚本 | 关键参数 |
| --- | --- | --- |
| **从 PDF 重新抽取全部教材** | ① `extract_text.py`（逐书 PDF） ② `extract_words.py`（逐书 TXT） | 批量可参考 `main.py`，但需把 `extract_text` 注释打开 |
| **从已有 TXT 重跑 `*.log/*.jsonl`** | `main.py`（当前默认状态） | 改 `root_name` / `file_name_list` |
| **汇总教材词表（不过滤）** | `temp_generate_set.py` | 产出 `words_set.txt` |
| **汇总教材词表（严格词典过滤）** | `temp_generate_strict.py` | 产出 `words_set_strict.txt` |
| **合并第三方词库** | `extract.py` | 产出根目录 `high_school.txt` |
| **生成词频数据库** | `top-rated/generate_db.py` | 需先修路径 + 准备 `ecdict/stardict.db` |
| **文言文 → Anki 卡片** | `convert.py` | 需先有 `文言/120文言实词.CSV` |

## 十五、注意事项与已知坑

1. **路径硬编码**：`top-rated/generate_db.py` 的 `ROOT.parent.parent` 假设目录结构和实际不完全一致，跑前需调整。
2. **`main.py` 默认跳过 `extract_text`**：跑它不会重新解析 PDF；新加教材必须先用 `extract_text.py` 生成 `.txt`。
3. **`[MANUAL]` 后缀**：`extract_words.py` 写入的 lemma 可能带这个标记，下游消费词表时需注意。
4. **`should_skip_line` 的硬编码英文关键词**：`unit / vocabulary / lookingforwards / namesandplaces`，中文教材 PDF 的章节标题如果是中文，不会被匹配跳过 —— 这是设计选择。
5. **`fitz.get_text("blocks")` 依赖 PDF 内嵌文本**：扫描型 PDF（图片扫描）需要先 OCR，否则 `blocks` 为空。
6. **`is_word` 模块导入**：所有用到 `is_word` 的脚本都以 `from is_word import ...` 形式导入，依赖同级目录的 `../is_word/`（不是 `from is_word.is_word import ...`）。请保证运行目录在仓库根。
7. **`Stanza` 模型下载**：`stanza.Pipeline('en', ...)` 首次会下载英文模型到 `~/stanza_resources/`，需要联网。

---

## 附录：脚本依赖矩阵

| 脚本 | 直接依赖 | 数据来源 | 产出 |
| --- | --- | --- | --- |
| `extract_text.py` | `fitz` | `books_*/*.pdf` | `books_*/*.txt` |
| `extract_words.py` | `stanza`, `is_word` | `books_*/*.txt` | `books_*/*.log`, `*.jsonl` |
| `main.py` | `extract_text`, `extract_words` | `books_*/*.pdf` + `*.txt` | 同上（调度） |
| `temp_generate_set.py` | stdlib | `books_*/*.jsonl` | `words_set.txt` |
| `temp_generate_strict.py` | `is_word_strict` | `books_*/*.jsonl` | `words_set_strict.txt` |
| `extract.py` | stdlib | 多个 CSV/TXT | 根目录 `high_school.txt` |
| `convert.py` | stdlib | `文言/*.CSV` | `文言/*_anki.csv` |
| `maimemo_senior/count_words.py` | stdlib | `词库 高中.md` + `exported/word/*.txt` | `word_counts.csv` |
| `youdao_ydschool_chugao/count_words.py` | stdlib | `dict/*.jsonl` | `word_counts.csv` |
| `top-rated/generate_db.py` | `sqlite3`, `wordfreq`, `csv` | `books_*/*.jsonl` + `ecdict/stardict.db` + 两个 CSV | `word_frequency.db` + `.csv` |
