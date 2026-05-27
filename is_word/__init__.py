from is_word.get_english_words_set import is_web2_word, is_gcide_word
from is_word.moby_dict_word_list import is_moby_dict_word
from is_word.read_english_dictionary import is_english_word
from is_word.wordfreq_words import is_wordfreq_zipf_word

def is_word(word: str) -> bool:
    """Check if a word is an English word."""
    return is_web2_word(word) or is_gcide_word(word) or is_moby_dict_word(word) or is_english_word(word) or is_wordfreq_zipf_word(word)


if __name__ == '__main__':
    print(is_word('woodfired'))
    print(is_word('singaporean'))
