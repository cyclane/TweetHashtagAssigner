import nltk
from nltk.tokenize import TweetTokenizer
from nltk.corpus import wordnet as wn
from nltk.stem.wordnet import WordNetLemmatizer

# Turns text into a list of lemmatized, important words
def process_text(text):
    # Tokenize tweet into words
    # NOTE: I'm not sure TweetTokenizer is actually useful here, might just change it to word tokenizer later
    tokenizer = TweetTokenizer(preserve_case=False)
    tokens = tokenizer.tokenize(text)

    # Lemmatize the words
    lemmatizer = WordNetLemmatizer()
    simple_words = [lemmatizer.lemmatize(token) for token in tokens]

    # Tag simplified words with part of speech
    word_tags = nltk.pos_tag(simple_words)

    # Remove conjunctions, determiners, etc.
    # Full list of what the tags mean at https://medium.com/@muddaprince456/categorizing-and-pos-tagging-with-nltk-python-28f2bc9312c3
    # Also then change the pos tags to be compatible with wordnet
    important_words = []
    for word, tag in word_tags:
        if tag not in {'CC', 'DT', 'EX', 'IN', 'LS', 'MD', 'PDT', 'POS', 'PRP', 'PRP$', 'RP', 'TO', 'UH', 'WDT', 'WP', 'WP$', 'WRB'}:
            if tag[0] == 'N':
                important_words.append((word, wn.NOUN))
            elif tag[0] == 'V':
                important_words.append((word, wn.VERB))
            elif tag[0] == 'J':
                important_words.append((word, wn.ADJ))
            elif tag[0] == 'R':
                important_words.append((word, wn.ADV))
            else:
                important_words.append((word, ""))

    # Return array of lemmatized important words with pos tags
    return important_words
