# Gets all data needed for process_tweets.py to run and saves it

import nltk
import pickle
import mysql.connector
from process_tweets import process_text

# Load tweet database
tweet_db = mysql.connector.connect(
    host='localhost',
    user='root',
    password='{/x%\#fY#95<hFks',
    database='tweethashtagassigner'
)

cursor = tweet_db.cursor()

cursor.execute("SELECT * FROM tweets")

tweets = [{
    "id": tweet[0],
    "content": tweet[1],
    "hashtags": tweet[2].split(",")
} for tweet in cursor.fetchall() ]

for i, tweet in enumerate(tweets):
    tweets[i]['words'] = process_text(tweet['content'])

data = {}

def build(tweets):
    data['tweet_num'] = len(tweets)
    data['unique_word_count'] = 0
    data['bags_of_words'] = {}
    data['hashtag_frequency'] = {}
    word_list = []
    for tweet in tweets:
        for hashtag in tweet['hashtags']:
            data['bags_of_words'][hashtag] = {}
            if hashtag not in data['hashtag_frequency']:
                data['hashtag_frequency'][hashtag] = 1
            else:
                data['hashtag_frequency'][hashtag] += 1

            for word in tweet['words']:
                if word not in word_list:
                    word_list.append(word)
                    data['unique_word_count'] += 1

                if word not in data['bags_of_words'][hashtag]:
                    data['bags_of_words'][hashtag][word] = 1
                else:
                    data['bags_of_words'][hashtag][word] += 1

build(tweets)
print(data)
pickle.dump(data, open('model.pickle', 'wb'))
