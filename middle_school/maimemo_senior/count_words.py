import csv
import os
import re
from collections import Counter
from urllib.parse import unquote

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(BASE_DIR, "词库 高中.md")
WORD_DIR = os.path.join(BASE_DIR, "exported", "word")
OUTPUT_PATH = os.path.join(BASE_DIR, "word_counts.csv")


def extract_txt_filenames(md_path):
    """从 markdown 表格第二列提取 txt 文件名"""
    filenames = []
    with open(md_path, "r", encoding="utf-8") as f:
        for line in f:
            if "选修" in line:
                continue
            line = line.strip()
            if not line or line.startswith("| 词库名") or line.startswith("|---"):
                continue
            # 匹配 markdown 表格行
            cells = line.split("|")
            if len(cells) < 3:
                continue
            # 第二列（索引1，因为 split 后第一个元素是空的）
            second_col = cells[2].strip()
            # 提取链接中的 href
            match = re.search(r"\]\(([^)]+)\)", second_col)
            if match:
                href = match.group(1)
                # URL 解码文件名
                filename = unquote(os.path.basename(href))
                if filename.endswith(".txt"):
                    filenames.append(filename)
    return filenames


def main():
    filenames = extract_txt_filenames(MD_PATH)
    print(f"Found {len(filenames)} txt files in markdown table.")

    counter = Counter()

    for filename in filenames:
        filepath = os.path.join(WORD_DIR, filename)
        if not os.path.exists(filepath):
            print(f"Warning: File not found: {filepath}")
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            # split on any whitespace (newlines, spaces, tabs, etc.)
            tokens = content.split()
            counter.update(tokens)
        print(f"Processed: {filename}")

    # Write csv
    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["单词", "总次数"])
        for word, count in counter.most_common():
            writer.writerow([word, count])

    print(f"Done. Total unique words: {len(counter)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
