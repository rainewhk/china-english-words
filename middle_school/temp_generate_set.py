import json
from pathlib import Path

root_name_list = ['books_junior', 'books_senior']


def main():
    words_set = set()
    total_files_sum = 0
    
    for root_name in root_name_list:
        books_dir = Path(root_name)
        if not books_dir.exists():
            print(f"目录不存在: {books_dir}")
            continue

        jsonl_files = list(books_dir.glob('*.jsonl'))
        if not jsonl_files:
            print(f"在 {books_dir} 下未找到 .jsonl 文件")
            continue

        total_files = len(jsonl_files)

        for i, filepath in enumerate(jsonl_files, 1):
            count = 0
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        item = json.loads(line)
                        lemma = item.get('lemma', '')
                        if lemma:
                            words_set.add(lemma)
                            count += 1
                    except json.JSONDecodeError:
                        continue
            print(f"[{i}/{total_files}] {filepath.name}: 提取 {count} 个 lemma")
            total_files_sum += total_files

    # 排序并写入文件
    sorted_words = sorted(words_set)
    output_path = Path('words_set.txt')
    with open(output_path, 'w', encoding='utf-8') as f:
        for word in sorted_words:
            f.write(word + '\n')

    print(f"\n总计: 从 {total_files_sum} 个文件提取 {len(words_set)} 个唯一单词")
    print(f"已排序写入: {output_path}")


if __name__ == '__main__':
    main()
