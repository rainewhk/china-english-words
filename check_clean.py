import json
import os
from pathlib import Path
from is_word import is_word


def clean_jsonl_file(filepath: Path) -> tuple[int, int]:
    """
    清理单个 JSONL 文件，仅保留 lemma 是有效单词的行。

    Returns:
        (原始行数, 保留行数)
    """
    kept_lines = []
    total_count = 0

    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            total_count += 1
            try:
                item = json.loads(line)
                text = item.get('text', ' ')
                lemma = item.get('lemma', '')
                if is_word(lemma) or is_word(lemma.lower()):
                    kept_lines.append(line)
                elif is_word(text) or is_word(text.lower()):
                    item['lemma'] = text
                    kept_lines.append(json.dumps(item, ensure_ascii=False))
            except json.JSONDecodeError:
                # 解析错误的行也保留，避免数据丢失
                kept_lines.append(line)

    # 原位覆盖写入
    with open(filepath, 'w', encoding='utf-8') as f:
        for line in kept_lines:
            f.write(line + '\n')

    return total_count, len(kept_lines)


def main():
    books_dir = Path('books')
    if not books_dir.exists():
        print(f"目录不存在: {books_dir}")
        return

    jsonl_files = list(books_dir.glob('*.jsonl'))
    if not jsonl_files:
        print(f"在 {books_dir} 下未找到 .jsonl 文件")
        return

    total_files = len(jsonl_files)
    total_original = 0
    total_kept = 0

    for i, filepath in enumerate(jsonl_files, 1):
        original, kept = clean_jsonl_file(filepath)
        removed = original - kept
        total_original += original
        total_kept += kept
        print(f"[{i}/{total_files}] {filepath.name}: {original} -> {kept} (删除 {removed})")

    print(f"\n总计: {total_original} -> {total_kept} (删除 {total_original - total_kept})")


if __name__ == '__main__':
    main()
