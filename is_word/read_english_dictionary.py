import os
current_dir = os.path.dirname(os.path.abspath(__file__))

with open(f'{current_dir}/words.txt') as word_file:
    valid_words = set(word_file.read().split())


def is_english_word(word: str) -> bool:
    """Check if a word is an English word."""
    return word in valid_words


if __name__ == '__main__':
    print(is_english_word('fate'))
