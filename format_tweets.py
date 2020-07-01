# Turns downloaded tweets into text and hashtags for the model to use

import nltk
import json

def load_tweets(path):
    f = open(path)
    data = json.load(f)
    # Maybe we should make an object for this
    tweets_text = []
    tweets_hashtags = []
    tweets_date = []
    for tweet in data['tweets']:
        tweets_text.append(tweet['extended_tweet']['full_text'])
        tweets_hashtags.append([hashtag['text'] for hashtag in tweet['extended_tweet']['entities']['hashtags']])
        tweets_date.append(tweet['created_at'])
    # Yeah we might wanna make an object for this
    return tweets_text, tweets_hashtags, tweets_date
