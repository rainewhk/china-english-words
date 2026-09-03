# 词典 API

## 有道词典

<https://github.com/creatcode/api/blob/master/YoudaoDic.md>

- 联想
- 释义
- 翻译

### 联想

url：`http://dict.youdao.com/suggest`

拼接参数：

- `q`：查询关键词
- `le`：语言。英语:`eng`
- `num`：返回数量。
- `ver`：版本号。可为空
- `doctype`：返回类型。`json` 或 `xml`，为空默认 `xml`
- `keyform`：`mdict.` + 版本号 + `.手机平台`。可为空
- `model`：手机型号。可为空
- `mid`：平台版本。可为空
- `imei`：???。可为空
- `vendor`：应用下载平台。可为空
- `screen`：屏幕宽高。可为空
- `ssid`：用户名。可为空
- `abtest`：???。可为空

url 示例：<http://dict.youdao.com/suggest?q=a&le=eng&num=15&ver=2.0&doctype=json&keyfrom=mdict.7.2.0.android&model=honor&mid=5.6.1&imei=659135764921685&vendor=wandoujia&screen=1080x1800&ssid=superman&abtest=2> 或 <http://dict.youdao.com/suggest?q=a&le=eng&num=80&ver=&doctype=json&keyfrom=&model=&mid=&imei=&vendor=&screen=&ssid=&abtest=>

json 示例：

解析：

- `result`：返回结果信息
    - `code`：`200`为成功
    - `message`：成功时为 `success`，若错误，则是相应错误信息
- `data`：具体内容列表
    - `query`：联想字母
    - `entries`
        - `explain`：联想单词翻译
        - `entry`：联想单词
- `language`：`eng`

### 释义

url：`http://dict.youdao.com/jsonapi`

拼接参数：

- `jsonversion`：json 版本，目前已知取值`1`或`2`，返回结果大同小异。本文档采用`2`
- `client`：客户端类型，取值`mobile`
- `q`：查询单词
- `dicts`：需要查询哪些字典。目前已知 `{"count":99,"dicts":[["ec","ce","newcj","newjc","kc","ck","fc","cf","multle","jtj","pic_dict","tc","ct","typos","special","tcb","baike","lang","simple","wordform","exam_dict","ctc","web_search","auth_sents_part","ec21","phrs","input","wikipedia_digest","ee","collins","ugc","media_sents_part","syno","rel_word","longman","ce_new","le","newcj_sents","blng_sents_part","hh"],["ugc"],["longman"],["newjc"],["newcj"],["web_trans"],["fanyi"]]}`。可为空，为空则返回全部字段
- `keyfrom`：略，可见联想
- `model`：略，可见联想
- `mid`：略，可见联想
- `imei`：略，可见联想
- `vendor`：略，可见联想
- `screen`：略，可见联想
- `ssid`：略，可见联想
- `network`：网络状态，取值 `wifi`、`4G`、`5G` 等
- `abtest`：略，可见联想
- `xmlVersion`：

url 示例:<http://dict.youdao.com/jsonapi?jsonversion=2&client=mobile&q=account&dicts=%7B%22count%22%3A99%2C%22dicts%22%3A%5B%5B%22ec%22%2C%22ce%22%2C%22newcj%22%2C%22newjc%22%2C%22kc%22%2C%22ck%22%2C%22fc%22%2C%22cf%22%2C%22multle%22%2C%22jtj%22%2C%22pic_dict%22%2C%22tc%22%2C%22ct%22%2C%22typos%22%2C%22special%22%2C%22tcb%22%2C%22baike%22%2C%22lang%22%2C%22simple%22%2C%22wordform%22%2C%22exam_dict%22%2C%22ctc%22%2C%22web_search%22%2C%22auth_sents_part%22%2C%22ec21%22%2C%22phrs%22%2C%22input%22%2C%22wikipedia_digest%22%2C%22ee%22%2C%22collins%22%2C%22ugc%22%2C%22media_sents_part%22%2C%22syno%22%2C%22rel_word%22%2C%22longman%22%2C%22ce_new%22%2C%22le%22%2C%22newcj_sents%22%2C%22blng_sents_part%22%2C%22hh%22%5D%2C%5B%22ugc%22%5D%2C%5B%22longman%22%5D%2C%5B%22newjc%22%5D%2C%5B%22newcj%22%5D%2C%5B%22web_trans%22%5D%2C%5B%22fanyi%22%5D%5D%7D&keyfrom=mdict.7.2.0.android&model=honor&mid=5.6.1&imei=659135764921685&vendor=wandoujia&screen=1080x1800&ssid=superman&network=wifi&abtest=2&xmlVersion=5.1> 或 <http://dict.youdao.com/jsonapi?xmlVersion=5.1&client=&q=account&dicts=&keyfrom=&model=&mid=&imei=&vendor=&screen=&ssid=&network=5g&abtest=&jsonversion=2>

解析：

- `simple`
    - `query`：查询单词
    - `word`
        - `usphone`：美式音标
        - `ukphone`：英式音标

- `ec`
    - `word`
        - `trs`：释义列表
            - `tr`
                - `l`
                    - `i`：释义
    - `exam_type`：考查范围

- `ugc`：用户贡献
    - `data`
        - `content`：具体贡献内容
        - `userName`：用户名
- `longman`：朗文当代高级英语辞典内容
    - `wordList`：释义列表
        - `HOMNUM`：
            - `Entry`
                - `Head`(固有字段)
                    - `FREQ`：频率，取值：`S1`为口语中最常用1000词，`W1`为书面英语中最常用的1000词等
                    - `VIDEOCAL`：英式发音
                    - `PronCodes`：音标
                        - `PRONKK`：英式音标
                        - `PRON`：美式音标
                    - `POS`：词性
                - `PhrVbEntry`(非固有字段)：短语动词
                    - `EXAMPLETRAN`：例句翻译
                        - `DEF`：详细英文释义
                        - `TRAN`：详细英文释义翻译
                        - `EXAMPLE`：例句
                        - `SYN`：同义词
                        - `Head`
                        - `POS`:词性
                - `Sense`
                    - `EXAMPLETRAN`：例句翻译
                    - `DEF`：详细英文释义
                    - `TRAN`：详细英文释义翻译
                    - `SIGNTRAN`：翻译
                    - `EXAMPLE`：例句
                    - `GramExa`：语法扩展
                        - `PROPFORMPREP`：与某词扩展
                        - `EXAMPLE`：例句
                        - `EXAMPLETRAN`：例句释义
                        - `COLLOTRAN`：短词释义
                        - ...
                - ......
- `web_trans`：网络释义
    - `web-translation`
        - `trans`：扩展词组翻译列表
            - `summary`
                - `line`：例句
            - `support`：基于多少个网页
            - `value`：翻译
        - `key-speech`：扩展词组拼接
        - `key`：扩展词组
- `pic_dict`：图片词典
    - `pic`：图片信息
        - `host`：
        - `img`：图片地址
        - `url`：链接
- `collins`：柯林斯英汉双解大辞典
    - `collins_entries`
        - `phonetic`：音标
        - `star`：星数
        - `pos_entry`：词性信息
            - `pos_tips`：词性翻译
            - `pos`：词性
        - `tran`：例句
- `ec21`：21世纪大英汉词典
    - `word`
        - `phrs`
            - `i`：短语列表
                - `des` 或 `tr`：描述
                    - `l`
                        - `i`：短语翻译
                - `phr`：
                    - `l`
                        - `i`：短语
        - `trs`：
            - `l`
                - `i`：释义
            - `pos`：词性
        - `phone`：音标
- `ee`：英英释义
    - `word`
        - `trs`：翻译列表
            - `tr`
                - `similar-words`：近义词列表
                    - `similar`：近义词
                - `l`
                    - `i`：例句
            - `pos`：词性
    - `phone`：音标
- `rel_word:`：同根词
    - `rels`：同根词列表
        - `rel`
            - `words`
                - `word`：词根
                - `tran`：词根翻译
            - `pos`：词性
- `phrs`：词组短语
    - `phrs`：词组短语列表
        - `phr`
            - `trs`
                - `tr`
                    - `l`
                        - `i`：词组短语翻译
            - `headword`
                - `l`
                    - `i`：词组短语
- `syno`：同近义词
    - `synos`：同近义词列表
        - `syno`
            - `tran`：同近义词翻译
            - `ws`：同近义词列表
                - `w`：同近义词
            - `pos`：词性
- `blng_sents_part`：双语例句
    - `sentence-pair`
        - `sentence-eng` 和 `sentence`：例句
        - `sentence-translation`：例句翻译
- `auth_sents_part`：权威例句
    - `sent`：
        - `foreign`：例句
        - `source`：来源
- `media_sents_part`：原声例句
    - `sent`
        - `eng`：例句
        - `snippets`
            - `snippet`
                - `source`：来源
                - `name`：来源文章名
                - `win8` 和 `streamUrl`：例句朗读地址
                - `duration`：例句朗读时长
        - `speech-size`：例句朗读 mp3 大小
- `wikipedia_digest`：百科
    - `source`
        - `url`：链接
    - `summarys`
        - `summary`：百科内容
        - `key`：关键词

### 翻译

url：<http://fanyi.youdao.com/translate>

请求方式：`POST`

请求体：i

请求格式：`x-www-form-urlencoded`

拼接参数：

- `doctype`：`json` 或 `xml`
- `jsonversion`：如果 `doctype` 值是 `xml`，则去除该值，若 `doctype` 值是 `json`，该值为空即可
- `xmlVersion`：如果 `doctype` 值是 `json`，则去除该值，若 `doctype` 值是 `xml`，该值为空即可
- `type`：语言自动检测时为 `null`，为 `null` 时可为空。`英译中`为 `EN2ZH_CN`，`中译英`为 `ZH_CN2EN`，`日译中`为 `JA2ZH_CN`，`中译日`为 `ZH_CN2JA`，`韩译中`为 `KR2ZH_CN`，`中译韩`为 `ZH_CN2KR`，`中译法`为 `ZH_CN2FR`，`法译中`为 `FR2ZH_CN`
- `keyform`：略，同联想
- `model`：略，同联想
- `mid`：略，同联想
- `imei`：略，同联想
- `vendor`：略，同联想
- `screen`：略，同联想
- `ssid`：略，同联想
- `network`：略，同释义
- `abtest`：略，同联想

url 示例：<http://fanyi.youdao.com/translate?doctype=json&jsonversion=&type=&keyfrom=&model=&mid=&imei=&vendor=&screen=&ssid=&network=&abtest=>

解析：

- `type`：翻译类型。`2`之前的表示原文类型，`2`之后表示译文类型。ps：`2` 表示 `to`
- `errorCode`：`0`表示成功
- `translateResult`：疑问结果
    - `src`：原文
    - `tgt`：译文

## 必应词典

<https://github.com/creatcode/api/blob/master/BingDic.md>

- 词典
- 翻译

ps：必应词典在本地存有数据库，所以它的联想功能是直接在数据库中查找 —— <https://github.com/jokermonn/-Api/blob/master/mircrosoft_bing_dic.db> 或 <https://github.com/jokermonn/-Api/blob/master/mircrosoft_bing_dic..xlsx>。**本地数据库中包含单词的基础默认翻译**

### 词典

url：<https://dict.bing.com.cn/api/http/v2/4154AA7A1FC54ad7A84A0236AA4DCAF3/en-us/zh-cn/>

拼接参数：

- `q`：关键词
- `format`：返回格式。`application/json` 或 `application/xml`

url 示例：<https://dict.bing.com.cn/api/http/v2/4154AA7A1FC54ad7A84A0236AA4DCAF3/en-us/zh-cn/?q=address&format=application/json>

解析：

- `LEX`
    - `C_DEF`：英-汉
        - `POS`：词性。PS：若该值为 `web`，则是必应词典中的`互联网释义`的内容
        - `SEN`：
            - `D`：释义
            - `R`：???
            - `STS`
                - `S`
                    - `D`：例句
                - `T`
                    - `D`：例句翻译
            - `URL`：参考链接
    - `H_DEF`：英-英
        - `POS`：词性。PS：若该值为 `web`，则是必应词典中的`互联网释义`的内容
        - `SEN`：
            - `D`：例句
            - `URL`：参考链接
    - `THES`：同义词和反义词
        - `A`：反义词列表
        - `POS`：词性
        - `S`：同义词列表
    - `PRON`：音标
        - `L`：地区，取 `US` 或 `UK`
        - `V`：音标
    - `PHRASE`：词组列表
        - `DEF`：词组翻译
        - `SIG`：???
        - `V`：词组
    - `INF`：其他形式
        - `IE`：形式
        - `T`：什么式，取 `pl`(复数)、`pp`(过去分词)、`prp`(现在分词)、`3pps`(第三人称单数)、`s`(原型)、`prt`(现在式)、`pt`(过去式)
- `SENT`：例句
    - `COUNT`：数量
    - `OFFSET`：分页
    - `ST`
        - `S`：例句翻译信息
            - `AD`：拼音
            - `D`：例句翻译
        - `T`：例句信息
            - `D`：例句

### 翻译

url：<https://dict.bing.com.cn/api/http/v2/4154AA7A1FC54ad7A84A0236AA4DCAF3/en-us/zh-cn/>

拼接参数：

- `q`：查询内容，使用 `+` 将多个单词连接起来
- `format`：返回内容格式。`application/xml` 或 `application/json`

url 示例：<https://dict.bing.com.cn/api/http/v2/4154AA7A1FC54ad7A84A0236AA4DCAF3/en-us/zh-cn/?q=merry+me&format=application/json>

解析：同词典解析

## 金山词霸

<https://github.com/creatcode/api/blob/master/KingsoftDic.md>

- 连续
- 释义
- 翻译

### 联想

url：<http://dict-mobile.iciba.com/interface/index.php>

拼接参数：

- `c`：固定值 `word`
- `m`：固定值 `getsuggest`
- `nums`：返回数量
- `client`：固定值 `6`
- `is_need_mean`：固定值 `1`
- `word`：搜索词

示例 url：<http://dict-mobile.iciba.com/interface/index.php?c=word&m=getsuggest&nums=10&client=6&is_need_mean=1&word=h>

解析：

- `status`：请求成功时为 `1`
- `message`：具体联想单词信息列表
    - `key`：联想单词
    - `value`：???
    - `means`：释义列表
        - `part`：词性
        - `means`：释义列表

### 释义

url：<http://www.iciba.com/index.php>

拼接参数：

- `a`：固定值 `getWordMean`
- `c`：固定值 `search`
- `list`：以 `1,3,4,5,8,9,10,12,13,14,18,21,3003,3005` 为字符串进行组合
    - `1`：对应 json 中 `baesInfo` 字段，基础释义
    - `3`：对应 json 中 `collins` 字段，柯林斯高阶英汉双解学习词典
    - `4`：对应 json 中 `ee_mean` 字段，英英词典
    - `5`：对应 json 中 `trade_means` 字段，行业词典
    - `8`：对应 json 中 `sentence` 字段，双语例句
    - `9`：对应 json 中 `netmean` 字段，网络释义
    - `10`：对应 json 中 `auth_sentence` 字段，权威例句
    - `12`：对应 json 中 `synonym` 字段，同义词
    - `13`：对应 json 中 `antonym` 字段，反义词
    - `14`：对应 json 中 `phrase` 字段，词组搭配
    - `18`：对应 json 中 `encyclopedia` 字段，百科全书
    - `21`：对应 json 中 `cetFour` 字段，四级真题
    - `3003`：对应 json 中 `bidec` 字段，英汉双向大词典
    - `3005`：对应 json 中 `jushi` 字段，例句
- `word`：释义单词

url 示例：<http://www.iciba.com/index.php?a=getWordMean&c=search&list=1%2C2%2C3%2C4%2C5%2C8%2C9%2C10%2C12%2C13%2C14%2C18%2C21%2C22%2C3003%2C3005&word=hello>

解析：

- `errno`：请求成功时返回 `0`
- `errmsg`：请求失败时返回错误信息，否则返回 `success`
- `baseInfo`：基础信息
    - `word_name`：
    - `exchange`：其他形式
        - `word_pl`：复数形式
        - `word_third`：第三人称单数
        - `word_past`：过去分词
        - `word_done`：现在分词
        - `word_ing`：正在进行时
        - `word_er`：比较式
        - `word_est`：最高级
        - `word_prep`：介词形式
        - `word_adv`：副词形式
        - `word_verb`：动词形式
        - `word_noun`：名词形式
        - `word_adj`：形容词形式
        - `word_conn`：连词形式
    - `symbols`：发音信息
        - `ph_en`：美式英标
        - `ph_am`：英式音标
        - `ph_en_mp3`：英式发音
        - `ph_am_mp3`：
        - `parts`：词性信息，同连续
- `sameAnalysis`：简单分析
    - `part_name`：解释
    - `means`：释义列表
        - `word_list`：相近含义单词
        - `means`：相近含义单词释义
- ... // 后续太长，笔者此处不做扩展，详情可对照网页和 json 自行解析

<h2 id="translation">翻译</h2>

url：<http://fy.iciba.com/ajax.php>

拼接参数：

- `a`：固定值 `fy`
- `f`：原文内容类型，日语取 `ja`，中文取 `zh`，英语取 `en`，韩语取 `ko`，德语取 `de`，西班牙语取 `es`，法语取 `fr`，自动则取 `auto`
- `t`：译文内容类型，日语取 `ja`，中文取 `zh`，英语取 `en`，韩语取 `ko`，德语取 `de`，西班牙语取 `es`，法语取 `fr`，自动则取 `auto`
- `w`：查询内容

url 示例：<http://fy.iciba.com/ajax.php?a=fy&f=auto&t=auto&w=hello%20world>

解析：

- `status`：请求成功时则取 `1`
- `content`：内容信息
    - `from`：原文内容类型
    - `to`：译文内容类型
    - `vendor`：来源平台
    - `out`：译文内容
    - `err_no`：请求成功时取 `0`
