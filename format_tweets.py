# Turns downloaded tweets into text and hashtags for the model to use

import nltk
import json

def load_tweets(path):
    # Loads json file of tweets from the given path
    f = open(path)
    data = json.load(f)

    # Creates a list of tweets where each tweet is a dictionary of its text
    # hashtags and id
    tweets = []
    for index, tweet in enumerate(data['tweets']):
        tweets.append({})
        tweets[index]['text'] = tweet['extended_tweet']['full_text']
        tweets[index]['hashtags'] = [hashtag['text'] for hashtag in tweet['extended_tweet']['entities']['hashtags']]
        tweets[index]['id'] = int(tweet['id_str'])

    return tweets
