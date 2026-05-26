from extract_text import extract_text
from extract_words import extract_words

def exec_pdf(pdf_name):
    pdf_path = f'books/{pdf_name}.pdf'
    txt_path = f'books/{pdf_name}.txt'
    json_path = f'books/{pdf_name}'
    extract_text(pdf_path, txt_path)
    words_set = extract_words(txt_path, json_path)
    return words_set

if __name__ == '__main__':
    # 补充新的需要手动设置
    file_name_list = [
        "高中 沪外教版 必修第一册",
        "高中 沪外教版 必修第二册",
        "高中 沪外教版 必修第三册",
        "高中 沪外教版 选择性必修第一册",
        "高中 沪外教版 选择性必修第二册",
        "高中 沪外教版 选择性必修第三册",
        # "高中 沪教版 选择性必修第四册"
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
