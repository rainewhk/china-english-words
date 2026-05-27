from english_words import get_english_words_set

web2lowerset = get_english_words_set(['web2'], lower=True)
gcidelowerset = get_english_words_set(['gcide'], lower=True)

print(type(web2lowerset))

def is_web2_word(word: str) -> bool:
    """Check if a word is an web2 word."""
    return word in web2lowerset

def is_gcide_word(word: str) -> bool:
    """Check if a word is an gcide word."""
    return word in gcidelowerset

if __name__ == '__main__':
    print(is_web2_word('fate'))
    print(is_gcide_word('fate'))
