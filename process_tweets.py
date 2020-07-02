# Processes the tweets and their hashtags using nltk and wordnet then uses
# Bayes theorem with some laplace smoothing and word similarity and lemmatization

import nltk
from nltk.tokenize import TweetTokenizer
from nltk.stem import wordnet as wn

# Load data somewhere and get unique word count
unique_word_count = 1
# List of all possible hashtags and frequency
list_of_hashtags = {}
# Hashtags bag of words
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
    important_words = []
    for i, word_tag in enumerate(word_tags):
        if word_tag[1] not in {'CC', 'DT', 'EX', 'IN', 'LS', 'MD', 'PDT', 'POS', 'PRP', 'PRP$', 'RP', 'TO', 'UH', 'WDT', 'WP', 'WP$', 'WRB'}:
            important_words.append(simple_words[i])

    # Return array of lemmatized important words
    return important_words

# Returns list of hashtags with value for how probable they are for given tweet
def hashtag_assigner(tweet):
    hashtag_probabilities = {}
    for hashtag in list_of_hashtags:
        hashtag_probabilities[hashtag] = bayes_model(hashtag, tweet)
    return hashtag_probabilities

# Returns the proportional probability of the hashtag given the text and date
# of the tweet
def bayes_model(hashtag, tweet):
    # Find probability of the text given the hashtag
    probability_of_text = 1
    for word in process_text(tweet['text']):
        probability_of_text *= word_probability(word, hashtag)

    # Finds the probability of the hashtag given the timestamp
    probability_of_hashtag = hashtag_probability(hashtag, tweet['id'])

    return probability_of_text*probability_of_hashtag

# Finds the probability of a word given a hashtag with laplace smoothing
def word_probability(word, hashtag):
    probability = 1
    # Go through words in data and find their lemmatized similarity to word
    # Multiply similarity by the words count in the given hashtag category
    # Add to probability
    # Sum words in hashtag category
    # Get unique words in data set
    # Divide probability of sum of words in category plus unique word count
    return probability

# Finds probability of the hashtag by finding what percent of hashtags it made
# up in the given timeframe
def hashtag_probability(hashtag, id):
    probability = 1
    # Find timestamp of id
    # Get tweets in that timestamp
    # Add number of tweets with hashtag in time frame to probability
    # Divide probability by total hashtags in tweets in time frame
    return probability
