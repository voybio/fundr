# utilities/grant_sumy.py

import os
import nltk

# --- 1) Instruct NLTK where to find local data (adjust as needed) ---
# This assumes your tokenizers are in "src/nltk_data/tokenizers/punkt/english/" etc.
nltk.data.path.append(os.path.join("src", "nltk_data"))

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

DEFAULT_LANGUAGE = "english"
DEFAULT_SENTENCES_COUNT = 10

def summarize_text(text, language=DEFAULT_LANGUAGE, sentence_count=DEFAULT_SENTENCES_COUNT):
    """
    Summarize a block of text using Sumy's LSA summarizer.

    :param text: The text to summarize (string)
    :param language: The language to use (default "english")
    :param sentence_count: How many sentences to include in the summary
    :return: A string containing the summarized sentences.
    """
    if not text or not text.strip():
        return "No description to summarize."

    # 2) Use Sumy’s PlaintextParser and Tokenizer with local nltk_data
    parser = PlaintextParser.from_string(text, Tokenizer(language))
    stemmer = Stemmer(language)
    summarizer = Summarizer(stemmer)
    summarizer.stop_words = get_stop_words(language)

    summary_sentences = summarizer(parser.document, sentence_count)
    summary = " ".join(str(s) for s in summary_sentences)
    return summary