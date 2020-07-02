# Turns text of a tweet into the important words that are tokenized and lemmatized

import nltk
from nltk.tokenize import TweetTokenizer
from nltk.stem import wordnet as wn

def process_text(text):
    # Tokenize tweet into words
    # NOTE: I'm not sure TweetTokenizer is actually useful here, might just change it to word tokenizer later
    tokenizer = TweetTokenizer(preserve_case=False)
    tokens = tokenizer.tokenize(text)

    # Lemmatize the words
    lemmatizer = wn.WordNetLemmatizer()
    simple_words = [lemmatizer.lemmatize(token) for token in tokens]

    # Tag simplified words with part of speech
    word_tags = nltk.pos_tag(simple_words)

    # Remove conjunctions, determiners, etc.
    # Full list of what the tags mean at https://medium.com/@muddaprince456/categorizing-and-pos-tagging-with-nltk-python-28f2bc9312c3
    important_words = []
    for i, word_tag in enumerate(word_tags):
        if word_tag[1] not in {'CC', 'DT', 'EX', 'IN', 'LS', 'MD', 'PDT', 'POS', 'PRP', 'PRP$', 'RP', 'TO', 'UH', 'WDT', 'WP', 'WP$', 'WRB'}:
            important_words.append(simple_words[i])

    # Return array of lemmatized important words
    return important_words
