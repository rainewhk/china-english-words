import csv

words = set()

for path in [
    r"middle_school\maimemo_senior\word_counts.csv",
    r"middle_school\youdao_ydschool_chugao\word_counts.csv",
    r"middle_school\top-rated\word_frequency.csv",
]:
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if row and row[0].strip():
                words.add(row[0].strip().lower())

with open(r"middle_school\维克多新高中英语词汇列表.txt", "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if line:
            words.add(line.lower())

with open(r"high_school.txt", "w", encoding="utf-8") as f:
    for w in sorted(words):
        f.write(w + "\n")

print(f"total: {len(words)}")