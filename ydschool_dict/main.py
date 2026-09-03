#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
有道背单词词库下载与纯净单词 TXT 提取脚本。

功能：
1. 从有道官方接口获取所有词书清单（81本）及离线包下载链接。
2. 自动下载缺失的 ZIP 离线包（支持断点检测与本地已有文件复用）。
3. 解压并解析 ZIP 内的 JSONL 文件，逐行提取 headWord。
4. 替换法语等特殊字母为标准英文字母（如 café -> cafe）。
5. 按照教材系列（小学/初中/高中多册）与版本（正序版/乱序版/图片记忆）进行合并。
6. 去重并按字母正序排列，输出最纯净的 txt 文件（一行一个单词）至 ydschool_dict/book/。
"""

import argparse
import glob
import json
import os
import re
import sys
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

# 配置编码
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
BOOK_OUT_DIR = BASE_DIR / "book"
CACHE_DIR = BASE_DIR / "raw_zips"
LEGACY_BOOK_DIR = BASE_DIR / "dict" / "book"

# 接口常量
API_PARAM_URL = "http://reciteword.youdao.com/reciteword/v1/param?key=normalBooks"
API_BOOKS_INFO_URL = "http://reciteword.youdao.com/reciteword/v1/getBooksInfo"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# 法语/特殊重音字母转换表
FR_EN_MAP = [
    ("é", "e"), ("ê", "e"), ("è", "e"), ("ë", "e"),
    ("à", "a"), ("â", "a"), ("ç", "c"),
    ("î", "i"), ("ï", "i"),
    ("ô", "o"),
    ("ù", "u"), ("û", "u"), ("ü", "u"),
    ("ÿ", "y"),
    ("É", "E"), ("Ê", "E"), ("È", "E"), ("Ë", "E"),
    ("À", "A"), ("Â", "A"), ("Ç", "C"),
    ("Î", "I"), ("Ï", "I"),
    ("Ô", "O"),
    ("Ù", "U"), ("Û", "U"), ("Ü", "U"),
    ("Ÿ", "Y"),
]


def clean_word(word: str) -> str:
    """清理单词首尾空格及特殊重音字母。"""
    word = word.strip()
    for fr, en in FR_EN_MAP:
        if fr in word:
            word = word.replace(fr, en)
    return word


def fetch_book_list() -> list[dict]:
    """从有道背单词接口获取全部词书的完整信息。"""
    print("[1/4] 正在从有道 API 获取词书列表...")
    req = urllib.request.Request(API_PARAM_URL, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    book_list = data["data"]["normalBooks"]["bookList"]
    book_ids = [b["id"] for b in book_list]
    print(f"      获取到 {len(book_ids)} 本词书 ID")

    print("[2/4] 正在获取词书详情与离线下载链接...")
    post_params = {
        "screen": "720x1280",
        "imei": "CQlhZDQ5NDllNmU0M2Y2ZTUxCWQ2NmRlNGIxN2Q1Mw==",
        "mid": "6.0.1",
        "keyfrom": "reciteword.1.5.3.android",
        "vendor": "index",
        "version": "1.5.3",
        "model": "Redmi_4A",
        "bookIds": str(book_ids),
        "reciteType": "normal",
    }
    encoded_data = urllib.parse.urlencode(post_params).encode("utf-8")
    req_info = urllib.request.Request(
        API_BOOKS_INFO_URL, data=encoded_data, headers=DEFAULT_HEADERS
    )
    with urllib.request.urlopen(req_info, timeout=20) as resp:
        info_data = json.loads(resp.read().decode("utf-8"))
    
    books_info = info_data["data"]["normalBooksInfo"]
    print(f"      成功获取 {len(books_info)} 本词书的元数据与下载地址")
    return books_info


def find_or_download_zip(book: dict, force_download: bool = False) -> Path:
    """寻找本地已有 ZIP 文件或下载最新 ZIP。"""
    url = book["offlinedata"]
    filename = os.path.basename(url)
    expected_size = int(book.get("size", 0))

    # 优先检查本地 raw_zips/
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target_path = CACHE_DIR / filename
    if not force_download and target_path.exists() and target_path.stat().st_size > 0:
        return target_path

    # 检查 dict/book/ 历史目录
    legacy_path = LEGACY_BOOK_DIR / filename
    if not force_download and legacy_path.exists() and legacy_path.stat().st_size > 0:
        return legacy_path

    # 本地不存在则从网络下载
    print(f"      正在下载: {book['title']} ({filename}) ...")
    req = urllib.request.Request(url, headers=DEFAULT_HEADERS)
    with urllib.request.urlopen(req, timeout=30) as resp, open(target_path, "wb") as out_f:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            out_f.write(chunk)
    
    return target_path


def parse_words_from_zip(zip_path: Path) -> list[str]:
    """从词书 ZIP 内的 json/jsonl 文件中解析出所有 headWord。"""
    words = []
    with zipfile.ZipFile(zip_path) as zf:
        for member in zf.namelist():
            if member.endswith(".json") or member.endswith(".jsonl"):
                with zf.open(member) as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            obj = json.loads(line.decode("utf-8"))
                            hw = obj.get("headWord")
                            if hw:
                                cleaned = clean_word(hw)
                                if cleaned:
                                    words.append(cleaned)
                        except Exception:
                            continue
    return words


def get_merged_title(book: dict) -> str:
    """根据词书的标题和 ID 获取合并后的目标词表标题。"""
    title = book["title"]
    bid = book["id"]

    # 1. 中小学教材分册系列合并
    if "人教版小学英语" in title:
        return "人教版小学英语"
    if "人教版初中英语" in title:
        return "人教版初中英语"
    if "外研社版初中英语" in title:
        return "外研社版初中英语"
    if "人教版高中英语" in title:
        return "人教版高中英语"
    if "北师大版高中" in title:
        return "北师大版高中"

    # 2. 正序版 / 乱序版 / 倒序版 / 图片记忆合并
    title_clean = re.sub(r"（(?:正序版|图片记忆|乱序版|倒序版)）", "", title).strip()

    # 3. 中考 / 高考必备词汇对应关系
    if bid == "ChuZhongluan_2":
        return "初中英语词汇"
    if bid == "GaoZhongluan_2":
        return "高中英语词汇"

    return title_clean


def main():
    parser = argparse.ArgumentParser(description="有道背单词词库纯净单词导出工具")
    parser.add_argument(
        "--force-download", action="store_true", help="强制从网络重新下载全部 ZIP 离线包"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(BOOK_OUT_DIR),
        help="TXT 导出目录，默认 ydschool_dict/book",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1 & 2: 获取词书列表与详情
    books_info = fetch_book_list()

    # 3: 下载与解析各词书
    print("[3/4] 正在下载词书离线包并提取 headWord ...")
    book_words_map = {}
    for idx, book in enumerate(books_info, 1):
        bid = book["id"]
        zip_path = find_or_download_zip(book, force_download=args.force_download)
        words = parse_words_from_zip(zip_path)
        book_words_map[bid] = {
            "info": book,
            "words": words,
            "zip": zip_path,
        }
        if idx % 10 == 0 or idx == len(books_info):
            print(f"      已处理: {idx}/{len(books_info)} 本词书")

    # 4: 分组归并、去重与正序排序
    print("[4/4] 正在进行系列合并、去重与正序排序...")
    groups = {}
    for bid, item in book_words_map.items():
        book = item["info"]
        merged_title = get_merged_title(book)
        groups.setdefault(merged_title, []).append(item)

    print(f"      共整理归并为 {len(groups)} 个词表文件")

    # 写入 TXT 文件并统计
    summary_records = []
    for merged_title, items in sorted(groups.items()):
        # 汇总所有版本的单词
        all_words = []
        source_bids = []
        for it in items:
            all_words.extend(it["words"])
            source_bids.append(it["info"]["id"])

        # 去重
        unique_words = list(set(all_words))

        # 严格正序排序：不区分大小写排序，相同字母则大写优先
        unique_words.sort(key=lambda s: (s.casefold(), s))

        # 写入 TXT 文件（最纯净：一行一个单词）
        txt_filename = f"{merged_title}.txt"
        txt_path = out_dir / txt_filename
        with open(txt_path, "w", encoding="utf-8", newline="\n") as f:
            for w in unique_words:
                f.write(f"{w}\n")

        summary_records.append({
            "filename": txt_filename,
            "merged_title": merged_title,
            "book_count": len(items),
            "source_ids": ", ".join(source_bids),
            "word_count": len(unique_words),
            "file_size": txt_path.stat().st_size,
        })

    # 输出统计表格
    print("\n" + "=" * 80)
    print(f"{'序号':<4} | {'词表文件名':<22} | {'词数':>6} | {'包含书数':>4} | {'原始 ID 列表'}")
    print("-" * 80)
    for idx, rec in enumerate(summary_records, 1):
        print(
            f"{idx:<4} | {rec['filename']:<22} | {rec['word_count']:>6} | "
            f"{rec['book_count']:>4} | {rec['source_ids']}"
        )
    print("=" * 80)
    total_words = sum(r["word_count"] for r in summary_records)
    print(f"全部处理完成！共生成 {len(summary_records)} 个纯净词表，总计包含 {total_words} 词次（各表内去重）。")
    print(f"导出路径: {out_dir.resolve()}\n")


if __name__ == "__main__":
    main()
