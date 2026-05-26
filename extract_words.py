import stanza
import json

nlp = stanza.Pipeline('en', processors='tokenize,mwt,pos,lemma', verbose=True)

exclude_filters = {
    "upos": [
        'PUNCT',
        'X',
        'NUM',
        'SYM'
    ],
    "xpos": [
        'ADD'
    ]
}

def extract_words(txt_path, output_name):
    documents = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            documents.append(line.strip().replace('(', ' ( ').replace(')', ' ) '))
    in_docs = [stanza.Document([], text=d) for d in documents]
    doc = nlp(in_docs)
    # print(doc)

    result = []

    for line in doc:
        for sentence in line.sentences:
            # dict_out = sentence.to_dict()
            # print(type(sentence))
            # print(sentence.constituency)
            # print(sentence.dependencies)
            for word in sentence.words:
                # 删除 id start_char end_char misc（如果存在）
                if word.upos in exclude_filters['upos']:
                    continue
                if word.xpos in exclude_filters['xpos']:
                    continue
                if word.lemma.isnumeric():
                    continue
                if len(word.lemma) < 2:
                    continue
                if '_' in word.text:
                    continue
                word_out = {
                    "text": word.text,
                    "lemma": word.lemma.lower(), # 此处额外做小写处理，避免一些特殊单词重复出现
                    "upos": word.upos,
                    "xpos": word.xpos,
                    "feats": word.feats
                }
                result.append(word_out)

    data = [i['lemma'] for i in result]
    
    unique_set = set(data)
    unique_sorted_list = sorted(list(unique_set))

    with open(f'{output_name}.log', 'w', encoding='utf-8') as f:
        for item in unique_sorted_list:
            f.write(item + '\n')

    with open(f'{output_name}.jsonl', 'w', encoding='utf-8') as f:
        for item in result:
            json_str = json.dumps(item, ensure_ascii=False)
            f.write(json_str + '\n')

    return unique_set
