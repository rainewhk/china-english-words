from get_english_words_set import is_web2_word, is_gcide_word
from moby_dict_word_list import is_moby_dict_word
from read_english_dictionary import is_english_word


def is_word(word: str) -> bool:
    """Check if a word is an English word."""
    return is_web2_word(word) or is_gcide_word(word) or is_moby_dict_word(word) or is_english_word(word)


if __name__ == '__main__':
    print(is_word('fate'))
    print(is_web2_word('fate'))
    print(is_gcide_word('fate'))
    print(is_moby_dict_word('fate'))
    print(is_english_word('fate'))
    
    print(is_word('facetious'))
    print(is_web2_word('facetious'))
    print(is_gcide_word('facetious'))
    print(is_moby_dict_word('facetious'))
    print(is_english_word('facetious'))
