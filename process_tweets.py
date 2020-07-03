# Processes the tweets and their hashtags using nltk and wordnet then uses
# Bayes theorem with some laplace smoothing and word similarity and lemmatization

import nltk
from nltk.tokenize import TweetTokenizer
from nltk.stem import wordnet as wn

# NOTE: I don't know how we're loading this stuff
# Load data somewhere and get unique word count
unique_word_count = 1
# List of all possible hashtags and frequency
hashtag_frequency = {}
# Hashtags bag of words with pos tags
bags_of_words = {}
# Number of tweets in training data
tweet_num = 1

# Turns text into a list of lemmatized, important words
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
    # Also then change the pos tags to be compatible with wordnet
    important_words = []
    for word, tag in word_tags:
        if tag not in {'CC', 'DT', 'EX', 'IN', 'LS', 'MD', 'PDT', 'POS', 'PRP', 'PRP$', 'RP', 'TO', 'UH', 'WDT', 'WP', 'WP$', 'WRB'}:
            if tag[0] == 'N':
                important_words.append((word, wordnet.NOUN))
            elif tag[0] == 'V':
                important_words.append((word, wordnet.VERB))
            elif tag[0] == 'J':
                important_words.append((word, wordnet.ADJ))
            elif tag[0] == 'R':
                important_words.append((word, wordnet.ADV))
            else:
                important_words.append((word, ""))

    # Return array of lemmatized important words with pos tags
    return important_words

# Returns list of hashtags with value for how probable they are for given tweet
def hashtag_assigner(tweet):
    hashtag_probabilities = {}
    for hashtag in hashtag_frequency:
        hashtag_probabilities[hashtag] = bayes_model(hashtag, tweet)
    return hashtag_probabilities

# Returns the proportional probability of the hashtag given the text and date
# of the tweet
def bayes_model(hashtag, tweet):
    # Find probability of the text given the hashtag
    probability_of_text = 1
    for word, tag in process_text(tweet['text']):
        probability_of_text *= word_probability(word, tag, hashtag)

    # Finds the probability of the hashtag given the timestamp
    probability_of_hashtag = hashtag_probability(hashtag, tweet['id'])

    return probability_of_text*probability_of_hashtag

# Finds the probability of a word given a hashtag with laplace smoothing
def word_probability(word, tag, hashtag):
    probability = 1
    hashtag_words = bags_of_words[hashtag]
    wordcount = 0
    # Counts up how many of the word appear in the bag of words for the hashtag
    # Includes similar words as partial counts
    if tag != "":
        word_synset = wn.sysnsets(word, pos=tag)[0]
        for training_word, training_tag in hashtag_words:
            # NOTE: This could be made more thourough at the cost of some performance in the future
            training_synset = wn.synsets(training_word, pos=training_tag)[0]
            wordcount += wn.path_similarity(word_synset, training_synset)

    # Add to probability
    probability += wordcount

    # Divide probability of sum of words in category plus unique word count
    probability /= hashtag_frequency[hashtag] + unique_word_count

    return probability

# Finds probability of the hashtag by finding what percent of hashtags it made
# up in the given timeframe
# NOTE: currently does not include timeframe, will be added later
def hashtag_probability(hashtag, id):
    probability = 0
    # Find timestamp of id
    # Get tweets in that timestamp
    # Add number of tweets with hashtag in time frame to probability
    # Divide probability by total hashtags in tweets in time frame
    probability += hashtag_frequency[hashtag]
    probability /= len(hashtag_frequency)
    return probability
