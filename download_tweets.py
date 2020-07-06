# Downloads tweets and puts them in format to go to process_tweets.py

import sys, argparse, json, random, urllib.parse, time, copy, threading, time
try:
    import tweepy
except:
    print("This script requires the \"tweepy\" package!")
    exit()
try:
    import mysql.connector
except:
    print("This script requires the \"mysql-connector-python\" package!")
    exit()

tweet_count = 0

def save(cursor, tweet_id, tweet_text, tweet_hashtags):
    cursor.execute(
        "INSERT INTO tweets (id, content, hashtags) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE id=%s",
        (tweet_id, tweet_text, ",".join(tweet_hashtags), tweet_id)
    )

class Counter:
    def __init__(self):
        self.value = 0
    def add(self, value):
        self.value += value

class StreamListener(tweepy.StreamListener):
    def __init__(self, cursor, logging):
        super().__init__()
        self.count = 0
        self.cursor = cursor
        self.logging = logging

    def on_status(self, status):
        text = status.text
        entities = status.entities

        if status.truncated:
            text = status.extended_tweet["full_text"]
            entities = status.extended_tweet["entities"]
        
        if len(entities["hashtags"]) > 0:
            self.count += 1
            save(
                self.cursor,
                status.id,
                text,
                [
                    hashtag["text"]
                    for hashtag in entities["hashtags"]
                ]
            )
            if self.logging:
                sys.stdout.write("\r")
                sys.stdout.write(f"{self.count} Tweets saved")
                sys.stdout.flush()

    def on_error(self, status_code):
        print(f"! Encountered streaming error ({status_code})")

parser = argparse.ArgumentParser()
parser.add_argument("--address","-a",help="Hostname of output database",default="db")
parser.add_argument("--database","-d",help="Name of database to use",default="TweetHashtagAssigner")
parser.add_argument("--user","-u",help="Database user to login with",default="TweetHashtagAssigner")
parser.add_argument("--password","-p",help="Database password for user",required=True)
parser.add_argument("--key","-k",help="Consumer API Key",required=True)
parser.add_argument("--secret","-s",help="Consumer API Secret",required=True)
parser.add_argument("--token","-t",help="User API token",required=True)
parser.add_argument("--token_secret","-ts",help="User API token secret",required=True)
parser.add_argument("--logging","-l",help="Log actions",action="store_true")
args = parser.parse_args()



if __name__ == "__main__":
    auth = tweepy.OAuthHandler(args.key, args.secret)
    auth.set_access_token(args.token, args.token_secret)
    api = tweepy.API(auth)

    if args.logging:
        print("Press ctrl + c to end the script, otherwise it well keep downloading at an interval of 1 request every 2 seconds (rate limit)")

    database = mysql.connector.connect(
        host=args.address,
        user=args.user,
        password=args.password,
        database=args.database
    )

    counter = Counter()
    streamListener = StreamListener(database.cursor(),logging=args.logging)
    start = time.time()

    try:
        stream = tweepy.Stream(auth=api.auth, listener=streamListener,tweet_mode="extended")
        stream.filter(
            track=["the","of","to","and","a","in","is","it","you","that","he","was","for","on","are","with","as","I","his","they","be","at","one","have","this","from","or"],
            languages=["en"]
        )
    except KeyboardInterrupt:
        if args.logging: print(f"\nScript interupted!")
    except Exception as e:
        if args.logging: print(f"\nScript errored!\n\n{e}")
    end = time.time()
    database.commit()

    if args.logging:
        print("Total time (s):",end-start)
        print("Valid tweets per second:",streamListener.count/(end-start))
