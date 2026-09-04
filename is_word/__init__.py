from is_word.get_english_words_set import is_web2_word, is_gcide_word
from is_word.moby_dict_word_list import is_moby_dict_word
from is_word.read_english_dictionary import is_english_word
from is_word.wordfreq_words import is_wordfreq_word

import string


def has_impossible_english_chars(text: str) -> bool:
    """
    判断字符串中是否包含英文单词/文本中绝对不可能出现的字符（忽略 Unicode 字符）。

    允许的 ASCII 字符包括：字母、连字符'-'、单引号"'"、点号'.' 以及数字。
    """
    # string.ascii_letters 包含 a-z, A-Z
    # string.digits 包含 0-9
    # 额外加上 "'"、"-" 和 "."
    if text.startswith("-") or text.startswith("'") or text.startswith("."):
        return True

    allowed_chars = set(string.ascii_letters + string.digits + "'-.")

    for char in text:
        # 仅检查 ASCII 字符（排查 Unicode）
        if ord(char) < 128:
            if char not in allowed_chars:
                return True  # 发现了绝对不允许的字符（如空格、!, @, # 等）

    return False


def _is_word_ori(word: str) -> bool:
    return (
        is_web2_word(word)
        or is_gcide_word(word)
        or is_moby_dict_word(word)
        or is_english_word(word)
        or is_wordfreq_word(word)
    )


def _is_word_ori_strict(word: str) -> bool:
    return (
        is_web2_word(word)
        or is_gcide_word(word)
        or is_moby_dict_word(word)
        or is_english_word(word)
    )


def is_word(word: str) -> bool:
    """Check if a word is an English word."""
    if has_impossible_english_chars(word):
        return False
    return (
        _is_word_ori(word.lower())
        or _is_word_ori(word.capitalize())
        or _is_word_ori(word.upper())
        or _is_word_ori(word.title())
    )


def is_word_strict(word: str) -> bool:
    """Check if a word is an English word."""
    if has_impossible_english_chars(word):
        return False
    return (
        _is_word_ori_strict(word.lower())
        or _is_word_ori_strict(word.capitalize())
        or _is_word_ori_strict(word.upper())
        or _is_word_ori_strict(word.title())
    )


if __name__ == "__main__":
    print(is_word("woodfired"))
    print(is_word("singaporean"))
