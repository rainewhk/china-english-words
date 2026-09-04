from wordfreq import word_frequency, zipf_frequency


def is_wordfreq_word(word: str) -> bool:
    """Check if a word is an English word."""
    return word_frequency(word, "en", wordlist="best") > 0.0


def is_wordfreq_zipf_word(word: str) -> bool:
    """Check if a word is an English word."""
    return zipf_frequency(word, "en", wordlist="best") >= 1.0


if __name__ == "__main__":
    print(word_frequency("petrichor", "en", wordlist="best"))
    print(zipf_frequency("petrichor", "en", wordlist="best"))
