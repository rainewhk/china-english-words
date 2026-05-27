from is_word.moby_corpus import words

# 第一次调用会自动下载并缓存，之后直接读缓存
all_words = words()

def is_moby_dict_word(word: str) -> bool:
    """Check if a word is an English word."""
    return word in all_words

if __name__ == '__main__':
    print(is_english_word('fate'))
