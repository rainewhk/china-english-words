from extract_text import extract_text
from extract_words import extract_words

root_name = 'books_junior'

def exec_pdf(pdf_name):
    pdf_path = f'{root_name}/{pdf_name}.pdf'
    txt_path = f'{root_name}/{pdf_name}.txt'
    json_path = f'{root_name}/{pdf_name}'
    extract_text(pdf_path, txt_path)
    words_set = extract_words(txt_path, json_path)
    return words_set

if __name__ == '__main__':
    # 补充新的需要手动设置
    file_name_list = [
        # 人教版
        "初中 人教版 七年级上册",
        "初中 人教版 七年级下册",
        "初中 人教版 八年级上册",
        "初中 人教版 八年级下册",
        "初中 人教版 九年级全一册",
        # 译林版
        "初中 译林版 七年级上册",
        "初中 译林版 七年级下册",
        "初中 译林版 八年级上册",
        "初中 译林版 八年级下册",
        "初中 译林版 九年级上册",
        "初中 译林版 九年级下册",
        # 外研社版
        "初中 外研社版 七年级上册",
        "初中 外研社版 七年级下册",
        "初中 外研社版 八年级上册",
        "初中 外研社版 八年级下册",
        "初中 外研社版 九年级上册",
        "初中 外研社版 九年级下册",
        # 冀教版
        "初中 冀教版 七年级上册",
        "初中 冀教版 七年级下册",
        "初中 冀教版 八年级上册",
        "初中 冀教版 八年级下册",
        "初中 冀教版 九年级全一册",
        # 沪教版
        "初中 沪教版 七年级上册",
        "初中 沪教版 七年级下册",
        "初中 沪教版 八年级上册",
        "初中 沪教版 八年级下册",
        "初中 沪教版 九年级上册",
        "初中 沪教版 九年级下册",
        # 沪外教版
        "初中 沪外教版 七年级上册",
        "初中 沪外教版 七年级下册",
        "初中 沪外教版 八年级上册",
        "初中 沪外教版 八年级下册",
        "初中 沪外教版 九年级上册",
        "初中 沪外教版 九年级下册",
        # 科普版
        "初中 科普版 七年级上册",
        "初中 科普版 七年级下册",
        "初中 科普版 八年级上册",
        "初中 科普版 八年级下册",
        "初中 科普版 九年级上册",
        "初中 科普版 九年级下册",
        # 鲁教版（五四学制）
        "初中 鲁教版 六年级上册",
        "初中 鲁教版 六年级下册",
        "初中 鲁教版 七年级上册",
        "初中 鲁教版 七年级下册",
        "初中 鲁教版 八年级上册",
        "初中 鲁教版 八年级下册",
        "初中 鲁教版 九年级全一册",
        # 教科版（五四学制）
        "初中 教科版 六年级上册",
        "初中 教科版 六年级下册",
        "初中 教科版 七年级上册",
        "初中 教科版 七年级下册",
        "初中 教科版 八年级上册",
        "初中 教科版 八年级下册",
        "初中 教科版 九年级上册",
        "初中 教科版 九年级下册",
    ]

    # 从 words_set.txt 恢复状态

    for file_name in file_name_list:
        words_set = set()
        with open('words_set.txt', 'r', encoding='utf-8') as f:
            for line in f:
                words_set.add(line.strip())
        words_set.update(exec_pdf(file_name))
        unique_list = sorted(list(words_set))
        with open('words_set.txt', 'w', encoding='utf-8') as f:
            for word in unique_list:
                f.write(word + '\n')
