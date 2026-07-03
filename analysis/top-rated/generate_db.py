#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成中学英语教材单词词频分析数据库
整合: ECDICT (BNC, FRQ), wordfreq (zipf), 中学教科书词频
"""

import json
import sqlite3
from pathlib import Path
from collections import Counter

from wordfreq import zipf_frequency

# 路径配置 - 在 top-rated 目录执行
# Path(__file__).parent = analysis/top-rated
# .parent.parent = 项目根目录
ROOT = Path(__file__).parent.parent.parent
ECDICT_DB_PATH = ROOT / "ecdict" / "stardict.db"
BOOKS_JUNIOR_PATH = ROOT / "books_junior"
BOOKS_SENIOR_PATH = ROOT / "books_senior"
OUTPUT_DB_PATH = ROOT / "analysis" / "top-rated" / "word_frequency.db"


def load_ecdict_data_for_words(words):
    """
    只为指定单词从 ECDICT 加载词频数据 (BNC, FRQ)"""
    ecdict_data = {}
    conn = sqlite3.connect(ECDICT_DB_PATH)
    cursor = conn.cursor()
    
    # 分批查询以避免 SQL 参数过多
    batch_size = 1000
    words_list = list(words)
    
    for i in range(0, len(words_list), batch_size):
        batch = words_list[i:i+batch_size]
        placeholders = ','.join('?' * len(batch))
        cursor.execute(f'SELECT word, bnc, frq FROM stardict WHERE word IN ({placeholders})', batch)
        
        for row in cursor.fetchall():
            word = row[0].lower().strip()
            try:
                bnc = int(row[1]) if row[1] else 0
            except:
                bnc = 0
            try:
                frq = int(row[2]) if row[2] else 0
            except:
                frq = 0
            ecdict_data[word] = {'bnc': bnc, 'frq': frq}
    
    conn.close()
    print(f"从 ECDICT 加载数据: {len(ecdict_data)} 条")
    return ecdict_data


def count_textbook_words():
    """统计中学教科书单词出现次数"""
    word_counts = Counter()
    total_lines = 0
    
    # 处理初中教材
    if BOOKS_JUNIOR_PATH.exists():
        for jsonl_file in BOOKS_JUNIOR_PATH.glob("*.jsonl"):
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        lemma = data.get('lemma', '').lower().strip()
                        if lemma and len(lemma) > 0:
                            word_counts[lemma] += 1
                            total_lines += 1
                    except json.JSONDecodeError:
                        continue
    
    # 处理高中教材
    if BOOKS_SENIOR_PATH.exists():
        for jsonl_file in BOOKS_SENIOR_PATH.glob("*.jsonl"):
            with open(jsonl_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        lemma = data.get('lemma', '').lower().strip()
                        if lemma and len(lemma) > 0:
                            word_counts[lemma] += 1
                            total_lines += 1
                    except json.JSONDecodeError:
                        continue
    
    # 融入 maimemo_senior 数据
    maimemo_csv = ROOT / "maimemo_senior" / "word_counts.csv"
    if maimemo_csv.exists():
        import csv
        with open(maimemo_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row['单词'].lower().strip()
                count = int(row['总次数'])
                if word:
                    word_counts[word] += count
                    total_lines += count
        print(f"融入 maimemo_senior 数据: {maimemo_csv}")
    
    # 融入 youdao_ydschool 数据
    youdao_csv = ROOT / "youdao_ydschool" / "word_counts.csv"
    if youdao_csv.exists():
        import csv
        with open(youdao_csv, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                word = row['单词'].lower().strip()
                count = int(row['总次数'])
                if word:
                    word_counts[word] += count
                    total_lines += count
        print(f"融入 youdao_ydschool 数据: {youdao_csv}")
    
    print(f"统计教科书词频: {len(word_counts)} 个不同单词, 总计 {total_lines} 次出现")
    return word_counts, total_lines


def get_zipf(word):
    """获取单词的 zipf frequency"""
    try:
        return zipf_frequency(word, 'en', wordlist='best')
    except:
        return 0.0


def create_database(word_counts, ecdict_data):
    """创建 SQLite 数据库"""
    # 确保输出目录存在
    OUTPUT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # 删除旧数据库
    if OUTPUT_DB_PATH.exists():
        OUTPUT_DB_PATH.unlink()
    
    conn = sqlite3.connect(OUTPUT_DB_PATH)
    cursor = conn.cursor()
    
    # 创建表
    cursor.execute('''
        CREATE TABLE word_frequency (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE NOT NULL,
            textbook_count INTEGER DEFAULT 0,
            bnc INTEGER DEFAULT 0,
            frq INTEGER DEFAULT 0,
            zipf REAL DEFAULT 0
        )
    ''')
    
    # 创建索引
    cursor.execute('CREATE INDEX idx_word ON word_frequency(word)')
    cursor.execute('CREATE INDEX idx_textbook_count ON word_frequency(textbook_count DESC)')
    cursor.execute('CREATE INDEX idx_bnc ON word_frequency(bnc)')
    cursor.execute('CREATE INDEX idx_frq ON word_frequency(frq)')
    cursor.execute('CREATE INDEX idx_zipf ON word_frequency(zipf DESC)')
    
    # 只处理教科书中的单词
    insert_data = []
    for word, count in word_counts.items():
        ecdict_info = ecdict_data.get(word, {})
        bnc = ecdict_info.get('bnc', 0)
        frq = ecdict_info.get('frq', 0)
        zipf = get_zipf(word)
        
        insert_data.append((word, count, bnc, frq, zipf))
    
    # 批量插入
    cursor.executemany('''
        INSERT INTO word_frequency (word, textbook_count, bnc, frq, zipf)
        VALUES (?, ?, ?, ?, ?)
    ''', insert_data)
    
    conn.commit()
    conn.close()
    
    print(f"创建数据库: {OUTPUT_DB_PATH}")
    print(f"  - 总计 {len(insert_data)} 个单词")
    print(f"  - 文件大小: {OUTPUT_DB_PATH.stat().st_size / 1024:.1f} KB")


def print_summary():
    """打印数据库摘要"""
    conn = sqlite3.connect(OUTPUT_DB_PATH)
    cursor = conn.cursor()
    
    # 总单词数
    cursor.execute('SELECT COUNT(*) FROM word_frequency')
    total = cursor.fetchone()[0]
    
    # 有 BNC 词频的单词
    cursor.execute('SELECT COUNT(*) FROM word_frequency WHERE bnc > 0')
    with_bnc = cursor.fetchone()[0]
    
    # 有 FRQ 词频的单词
    cursor.execute('SELECT COUNT(*) FROM word_frequency WHERE frq > 0')
    with_frq = cursor.fetchone()[0]
    
    # 有 ZIPF 词频的单词
    cursor.execute('SELECT COUNT(*) FROM word_frequency WHERE zipf > 0')
    with_zipf = cursor.fetchone()[0]
    
    # Top 20 高频教科书单词
    cursor.execute('''
        SELECT word, textbook_count, bnc, frq, zipf 
        FROM word_frequency 
        ORDER BY textbook_count DESC 
        LIMIT 20
    ''')
    top20 = cursor.fetchall()
    
    # 有 ECDICT 数据的单词
    cursor.execute('SELECT COUNT(*) FROM word_frequency WHERE bnc > 0 OR frq > 0')
    with_ecdict = cursor.fetchone()[0]
    
    conn.close()
    
    print("\n========== 数据库摘要 ==========")
    print(f"总单词数: {total}")
    print(f"有 BNC 词频: {with_bnc}")
    print(f"有 FRQ 词频: {with_frq}")
    print(f"有 ZIPF 词频: {with_zipf}")
    print(f"有 ECDICT 数据: {with_ecdict}")
    
    print("\n========== 教科书 Top 20 高频词 ==========")
    print(f"{'Rank':<6}{'Word':<20}{'Textbook':<12}{'BNC':<10}{'FRQ':<10}{'ZIPF':<8}")
    print("-" * 70)
    for i, (word, count, bnc, frq, zipf) in enumerate(top20, 1):
        bnc_str = str(bnc) if bnc else '-'
        frq_str = str(frq) if frq else '-'
        print(f"{i:<6}{word:<20}{count:<12}{bnc_str:<10}{frq_str:<10}{zipf:<8.2f}")


def main():
    print("开始生成中学英语教材单词词频分析数据库...\n")
    
    # 1. 统计教科书词频
    word_counts, total_lines = count_textbook_words()
    
    # 2. 只为教科书单词加载 ECDICT 数据
    ecdict_data = load_ecdict_data_for_words(word_counts.keys())
    
    # 3. 创建数据库
    create_database(word_counts, ecdict_data)
    
    # 4. 打印摘要
    print_summary()
    
    print(f"\n完成！数据库文件: {OUTPUT_DB_PATH}")


if __name__ == '__main__':
    main()
