# Processes the tweets and their hashtags using nltk and wordnet then uses
# Bayes theorem with some laplace smoothing and word similarity and lemmatization

import nltk

# Load data somewhere and get unique word count
unique_word_count = 1
# List of all possible hashtags
list_of_hashtags = []

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
    for word in tweet['text']:
        probability_of_text *= word_probability(word, hashtag)

    # Finds the probability of the hashtag given the timestamp
    probability_of_hashtag = hashtag_probability(hashtag, tweet['id'])

    return probability_of_text*probability_of_hashtag

# Finds the probability of a word given a hashtag with laplace smoothing
def word_probability(word, hashtag):
    probability = 1
    # Lemmatize word
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
