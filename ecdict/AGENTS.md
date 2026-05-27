# ECDICT 词库工具使用指南

本文档指导人工智能如何使用 `ecdict` 文件夹中的词库工具和数据库。

## 简介

ECDICT 是一个开源的英汉词典数据库，包含数十万条单词的英文/中文释义，并标注了各类考试大纲（四六级、托福、雅思、GRE等）和词频信息（BNC/当代语料库）。

## 现有文件说明

| 文件 | 类型 | 说明 |
|------|------|------|
| `stardict.db` | SQLite 数据库 | 核心词典数据库文件，包含完整词库数据 |
| `stardict.py` | Python 库 | 核心操作库，提供词典读写、查询、转换功能 |
| `dictutils.py` | Python 工具 | 高级工具集，用于生成各种格式的词典输出 |
| `linguist.py` | Python 工具 | 语言学处理工具（依赖外部 NLP 库）|
| `del_bfz.py` | 自定义脚本 | 清理 exchange 字段中的冗余标签（b:比较级/f:复数/z:最高级）|
| `README.md` | 文档 | 详细项目说明文档 |

## 核心数据库字段

词典中的每个词条包含以下字段：

| 字段 | 说明 |
|------|------|
| `word` | 单词名称 |
| `phonetic` | 音标（英式）|
| `definition` | 英文释义 |
| `translation` | 中文释义 |
| `pos` | 词性位置，如 `n:46/v:54` 表示46%作名词，54%作动词 |
| `collins` | 柯林斯星级（1-5星）|
| `oxford` | 是否属于牛津3000核心词汇 |
| `tag` | 考试标签：zk(中考)/gk(高考)/cet4/cet6/toefl/ielts/gre |
| `bnc` | 英国国家语料库词频顺序 |
| `frq` | 当代语料库词频顺序 |
| `exchange` | 时态变形，格式见下文 |
| `detail` | JSON 扩展信息（例句等）|
| `audio` | 读音音频 URL |

## 词形变换格式（exchange 字段）

格式：`类型1:变形词1/类型2:变形词2/...`

示例：`perceive` 的 exchange 为 `d:perceived/p:perceived/3:perceives/i:perceiving`

| 类型 | 说明 |
|------|------|
| `p` | 过去式（did）|
| `d` | 过去分词（done）|
| `i` | 现在分词（doing）|
| `3` | 第三人称单数（does）|
| `r` | 形容词比较级（-er）|
| `t` | 形容词最高级（-est）|
| `s` | 名词复数形式 |
| `0` | Lemma（原型），如 perceived 的 Lemma 是 perceive |
| `1` | Lemma 的变换形式类型标记 |

## 如何使用 stardict.py 核心库

### 1. 打开词典数据库

```python
import sys
sys.path.insert(0, 'ecdict')
import stardict

# 方式1：直接打开 SQLite 数据库文件
db = stardict.StarDict('ecdict/stardict.db')

# 方式2：使用 open_local 函数
db = stardict.open_local('ecdict/stardict.db')

# 方式3：打开 CSV 文件
csv_db = stardict.DictCsv('ecdict.csv')

# 方式4：连接 MySQL（需要 MySQLdb）
# mysql_db = stardict.DictMySQL('mysql://user:pass@host:port/dbname')
```

### 2. 查询单词

```python
# 按单词查询
result = db.query('hello')  # 返回字典或 None
# 或
data = db['hello']  # 使用 __getitem__ 语法

# 按 ID 查询
result = db.query(1234)

# 批量查询
results = db.query_batch(['hello', 'world', 'python'])

# 模糊匹配（返回相似单词列表）
matches = db.match('hel', limit=10, strip=False)  # 返回 [(id, word), ...]
# strip=True 时使用 sw 字段（去除非字母数字字符后匹配）
matches = db.match('hel', limit=10, strip=True)
```

返回的数据字典示例：
```python
{
    'id': 1234,
    'word': 'hello',
    'sw': 'hello',
    'phonetic': "hə'ləʊ",
    'definition': 'used as a greeting or to begin a telephone conversation',
    'translation': 'n. 表示问候；\nint. 喂；哈罗',
    'pos': 'n:23/u:77',
    'collins': 5,
    'oxford': 1,
    'tag': 'zk gk cet4 cet6 ky toefl',
    'bnc': 267,
    'frq': 335,
    'exchange': 's:hellos',
    'detail': None,
    'audio': None
}
```

### 3. 遍历词典

```python
# 遍历所有单词
for word_id, word in db:
    print(word_id, word)

# 获取总数
count = len(db)  # 或 db.count()

# 检查是否存在
if 'hello' in db:
    print('存在')

# 获取所有单词列表
all_words = db.dumps()
```

### 4. 修改词典数据

```python
# 注册新单词
db.register('newword', {
    'phonetic': 'nju:wɜ:d',
    'translation': '新词',
    'tag': 'cet4'
}, commit=True)

# 更新单词
db.update('hello', {
    'translation': '新的中文释义',
    'collins': 5
}, commit=True)

# 删除单词
db.remove('oldword', commit=True)

# 清空数据库
db.delete_all(reset_id=False)

# 手动提交（如果在上述操作中 commit=False）
db.commit()

# 关闭连接
db.close()
```

### 5. 格式转换

```python
# CSV 转 SQLite
stardict.convert_dict('output.db', 'ecdict.csv')

# SQLite 转 CSV
stardict.convert_dict('output.csv', 'ecdict/stardict.db')

# CSV 之间的转换
stardict.convert_dict('output.csv', 'input.csv')
```

## 如何使用 LemmaDB 词干数据库

`LemmaDB` 用于处理单词变形与原型之间的转换（如 gave -> give）。

```python
import stardict

# 加载词干数据（注意：需要 lemma.en.txt 文件，当前目录可能缺失）
lemma = stardict.LemmaDB()
lemma.load('lemma.en.txt')  # 或 lemma-bnc.txt

# 查找单词的所有变形（由原型查变形）
forms = lemma.get('give')  # 返回 ['give', 'gives', 'giving', 'gave', 'given', ...]

# 反向查找原型（由变形查原型）
stems = lemma.get('gave', reverse=True)  # 返回 ['give']
# 或
stems = lemma.word_stem('gave')  # 同上

# 添加自定义词干关系
lemma.add('go', 'goes')
lemma.add('go', 'went')
lemma.add('go', 'gone')

# 保存修改
lemma.save('new-lemma.txt')

# 统计数据
print(len(lemma))  # 词根数量
print(lemma.stem_size())  # 同上
print(lemma.word_size())  # 衍生词数量
```

## 如何使用 dictutils.py 高级工具

```python
import sys
sys.path.insert(0, 'ecdict')
import stardict
import dictutils

# 打开数据库
db = stardict.open_local('ecdict/stardict.db')

# 使用 Generator 生成标签
gen = dictutils.Generator()

# 获取单词标签（考试类型+词频）
tag = gen.word_tag(db['hello'])  # 返回如 "中 高 四 六 研 托 雅 335/267"

# 获取单词级别
level = gen.word_level(db['hello'])  # 返回如 "K5"（柯林斯5星+牛津核心词）

# 获取词形变换文本
exchange_text = gen.word_exchange(db['perceive'], style=0)
# style=0: [时态] perceived, perceived, perceives, perceiving
# style=1: 时态: perceived, perceived, perceives, perceiving

# 获取词性分布
pos = gen.word_pos(db['fuse'])  # 返回如 "n(46%), v(54%)"
```

### 使用 Resemble 处理词语辨析

```python
# 加载辨析数据（需要 resemble.txt 文件，当前可能缺失）
res = dictutils.Resemble()
res.load('resemble.txt')

# 查询某个词的辨析
for wt in res['stimulate']:
    print(res.dump_text(wt))  # 文本格式
    print(res.dump_html(wt))  # HTML 格式
```

### 使用 Treasure 生成 Anki/MDX 数据

```python
# 生成 Anki 卡片数据
treasure = dictutils.Treasure()

# 获取正面（单词+音标）
front = treasure.generate_front(db['hello'])

# 获取背面（释义+时态+记忆技巧）
back = treasure.generate_back(db['hello'])

# 批量生成 MDX 文件
treasure.compile_mdx(db, 'anki-front.mdx', 'anki-back.mdx')
```

## 如何使用 stardict.tools 辅助工具

`stardict.tools` 是 `DictHelper` 类的实例，提供多种实用功能：

```python
import stardict

tools = stardict.tools

# 1. 导出字典差异（找出 words 中不在 dictionary 里的词）
words = ['apple', 'banana', 'xyz123']
count = tools.discrepancy_export(db, words, 'missing.csv', opts='')
# opts: 's'=跳过多空格词, 't'=跳过多词, 'p'=跳过带连字符的词

# 2. 导入差异数据
 tools.discrepancy_import(db, 'updated.csv', opts='')
# opts: 'n'=不更新已存在的词

# 3. 导出星际译王格式（.idx + .dict + .ifo）
wordmap = {'hello': '*[hə\'ləʊ]\n你好', 'world': '*[wɜ:ld]\n世界'}
tools.export_stardict(wordmap, 'output', 'My Dictionary')

# 4. 导出 MDX 源文件（.txt 格式）
tools.export_mdict(wordmap, 'output.txt')

# 5. 直接生成 .mdx 文件（需要 writemdict 库）
tools.export_mdx(wordmap, 'output.mdx', 'Dictionary Title')

# 6. 读取 .mdx 文件（需要 readmdict 库）
words = tools.read_mdx('input.mdx')

# 7. 导入 MDX 源文件
words = tools.import_mdict('source.txt')

# 8. 词形变换字符串解析/生成
exchg_obj = tools.exchange_loads('p:went/d:gone/i:going/3:goes')
# 返回 {'p': 'went', 'd': 'gone', 'i': 'going', '3': 'goes'}
exchg_str = tools.exchange_dumps(exchg_obj)

# 9. 词性字符串解析
pos_obj = tools.pos_loads('n:46/v:54')

# 10. 获取词性描述
pos_desc = tools.pos_detect('run', 'v')  # 返回 (u'动词', 'v.')

# 11. 解析 pos 字段获取详细分布
pos_list = tools.pos_extract(db['fuse'])
# 返回 [((u'动词', 'v.'), '54'), ((u'名词', 'n.'), '46')]

# 12. 设置/获取详细内容（detail 字段）
tools.set_detail(db, 'hello', 'syno', [[['n.', 'synonym'], ['word1', 'word2']]], create=True)
syno = tools.get_detail(db, 'hello', 'syno')

# 13. 加载文本文件（自动检测编码）
text = tools.load_text('file.txt')
```

## 关于 linguist.py（WordHelper）

**注意：此工具需要安装外部 NLP 库（NLTK、NodeBox、pattern 等），当前环境可能未安装。**

```python
import sys
sys.path.insert(0, 'ecdict')
import linguist

tools = linguist.tools

# 获取 WordNet 定义（需要 nltk）
defs = tools.definition('run')

# 动词时态变化（需要 NodeBox）
tenses = tools.verb_tenses('go')
# 返回 {'i': 'going', 'p': 'went', 'd': 'gone', '3': 'goes'}

# 名词复数
plural = tools.noun_plural('child')

# 形容词比较级/最高级（需要 pattern）
comp = tools.adjective_comparative('good')  # better
sup = tools.adjective_superlative('good')   # best

# 词形还原（需要 nltk）
lemma = tools.lemmatize('gave', pos='v')  # give

# 获取所有动词/副词/形容词/名词列表（需要 NodeBox）
verbs = tools.all_verbs()
adverbs = tools.all_adverbs()
```

## 使用场景示例

### 场景1：查询单词并显示完整信息

```python
import stardict
import dictutils

db = stardict.open_local('ecdict/stardict.db')
gen = dictutils.Generator()

def show_word(word):
    data = db[word]
    if not data:
        print(f'未找到: {word}')
        return
    
    print(f"单词: {data['word']}")
    print(f"音标: {data['phonetic']}")
    print(f"中文: {data['translation']}")
    print(f"标签: {gen.word_tag(data)}")
    print(f"级别: {gen.word_level(data)}")
    print(f"时态: {gen.word_exchange(data, 0)}")
    
show_word('hello')
```

### 场景2：筛选特定考试词汇

```python
# 筛选所有 GRE 词汇
gre_words = []
for _, word in db:
    data = db[word]
    if data.get('tag') and 'gre' in data['tag']:
        gre_words.append(word)

print(f"GRE 词汇数量: {len(gre_words)}")
```

### 场景3：根据词频筛选高频词

```python
# 筛选 BNC 词频前 1000 的词
high_freq = []
for _, word in db:
    data = db[word]
    bnc = data.get('bnc')
    if bnc and bnc <= 1000:
        high_freq.append((word, bnc))

high_freq.sort(key=lambda x: x[1])
print(high_freq[:10])
```

### 场景4：处理文本中的单词原形

```python
# 将一段文本中的单词转换回原形
import re

def get_word_stem(word):
    """查询单词原形，先查词典，再尝试 LemmaDB"""
    # 先直接查询词典
    data = db.get(word.lower())
    if data and data.get('exchange'):
        ex = stardict.tools.exchange_loads(data['exchange'])
        if ex and '0' in ex:
            return ex['0']
    
    # 词典查不到，尝试 LemmaDB（如果可用）
    lemma = stardict.LemmaDB()
    # lemma.load('lemma.en.txt')  # 如果文件存在
    stems = lemma.word_stem(word.lower())
    if stems:
        return stems[0]
    
    return word

text = "The boys are running and played games"
words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
stems = [get_word_stem(w) for w in words]
print(stems)  # ['the', 'boy', 'be', 'run', 'and', 'play', 'game']
```

## 注意事项

1. **编码问题**：ECDICT 使用 UTF-8 编码，确保 Python 文件头部有 `# -*- coding: utf-8 -*-`

2. **缺失文件**：部分高级功能需要额外数据文件：
   - `lemma.en.txt` / `lemma-bnc.txt` → LemmaDB 词干数据
   - `resemble.txt` → 词语辨析数据
   - `treasure.db` / `ultimate.db` → 扩展词典数据
   - `bnc-words.csv` / `bnc-clear.csv` → BNC 语料数据

3. **外部依赖**：`linguist.py` 需要安装：
   - `nltk`（自然语言工具包）
   - `pattern`（文本处理库）
   - `NodeBox`（词形变化库）

4. **大小写不敏感**：词典查询对大小写不敏感，`db['Hello']` 等同于 `db['hello']`

5. **数据库连接**：使用完 `StarDict` 或 `DictMySQL` 后建议调用 `.close()` 关闭连接

6. **事务处理**：修改操作默认自动提交（`commit=True`），批量操作建议手动控制事务以提高性能

7. **模糊匹配**：使用 `strip=True` 可以匹配带连字符、空格等变体的单词，如 `long-time`、`longtime`、`long time` 都能匹配到

## 许可证

MIT License - 参见 `ecdict/LICENSE`

原始项目：https://github.com/skywind3000/ECDICT
