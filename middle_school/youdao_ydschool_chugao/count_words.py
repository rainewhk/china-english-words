import csv
import json
import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DICT_DIR = os.path.join(BASE_DIR, 'dict')
OUTPUT_PATH = os.path.join(BASE_DIR, 'word_counts.csv')


def main():
    counter = Counter()

    jsonl_files = sorted(
        f for f in os.listdir(DICT_DIR)
        if f.endswith('.jsonl')
    )
    print(f"Found {len(jsonl_files)} jsonl files.")

    for filename in jsonl_files:
        filepath = os.path.join(DICT_DIR, filename)
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    head_word = data.get('headWord')
                    if head_word:
                        counter[head_word] += 1
                except json.JSONDecodeError:
                    continue
        print(f"Processed: {filename}")

    with open(OUTPUT_PATH, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['单词', '总次数'])
        for word, count in counter.most_common():
            writer.writerow([word, count])

    print(f"Done. Total unique words: {len(counter)}")
    print(f"Output: {OUTPUT_PATH}")


if __name__ == '__main__':
    main()
