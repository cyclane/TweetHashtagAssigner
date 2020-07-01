# Turns downloaded tweets into text and hashtags for the model to use

import nltk
import json

def load_tweets(path):
    # Loads json file of tweets from the given path
    f = open(path)
    data = json.load(f)

    # Creates a list of tweets where each tweet is a dictionary of its text
    # hashtags id and lemmatized important words
    tweets = []
    for index, tweet in enumerate(data['tweets']):
        tweets.append({})
        tweets[index]['text'] = tweet['extended_tweet']['full_text']
        tweets[index]['hashtags'] = [hashtag['text'] for hashtag in tweet['extended_tweet']['entities']['hashtags']]
        tweets[index]['id'] = int(tweet['id_str'])
        tweets[index]['words'] = process_text(tweets[index]['text'])
    return tweets

def process_text(text):
    # Tokenize the text into words with nltk
    # Remove unimportant words like 'the'
    # Lemmatize the words
    # Return array of lemmatized important words
    pass
