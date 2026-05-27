from is_word.get_english_words_set import is_web2_word, is_gcide_word
from is_word.moby_dict_word_list import is_moby_dict_word
from is_word.read_english_dictionary import is_english_word
from is_word.wordfreq_words import is_wordfreq_word

def _is_word_ori(word: str) -> bool:
    return is_web2_word(word) or is_gcide_word(word) or is_moby_dict_word(word) or is_english_word(word) or is_wordfreq_word(word)

def is_word(word: str) -> bool:
    """Check if a word is an English word."""
    return _is_word_ori(word.lower()) or _is_word_ori(word.capitalize()) or _is_word_ori(word.upper())  or _is_word_ori(word.title())

if __name__ == '__main__':
    print(is_word('woodfired'))
    print(is_word('singaporean'))
