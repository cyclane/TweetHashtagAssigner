# Downloads tweets and puts them in format to go to process_tweets.py

import sys, argparse, json, random, urllib.parse, time, copy, threading, string
try:
    import requests
    from requests.auth import AuthBase
except:
    print("This script requires the \"requests\" package!")
try:
    import nltk
except:
    print("This script requires the \"nltk\" package!")
try:
    import mysql.connector
except:
    print("This script requires the \"mysql-connector-python\" package!")

# (Copied from Twitter docs)
# Generates a bearer token with consumer key and secret via https://api.twitter.com/oauth2/token.
class BearerTokenAuth(AuthBase):
    def __init__(self, consumer_key, consumer_secret):
        self.bearer_token_url = "https://api.twitter.com/oauth2/token"
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.bearer_token = self.get_bearer_token()

    def get_bearer_token(self):
        response = requests.post(
            self.bearer_token_url,
            auth=(self.consumer_key, self.consumer_secret),
            data={'grant_type': 'client_credentials'},
            headers={'User-Agent': 'LabsRecentSearchQuickStartPython'})

        if response.status_code is not 200:
            raise Exception("Cannot get a Bearer token (HTTP %d): %s" % (response.status_code, response.text))

        body = response.json()
        return body['access_token']

    def __call__(self, r):
        r.headers['Authorization'] = f"Bearer %s" % self.bearer_token
        r.headers['User-Agent'] = 'LabsResearchSearchQuickStartPython'
        return r

class Counter:
    def __init__(self):
        self.value = 0
    def add(self, value):
        self.value += value

def tweets_search_request(bearer_token, query):
    url = f"https://api.twitter.com/1.1/search/tweets.json?q={urllib.parse.quote(query)}&count=100&tweet_mode=extended&lang=en"
    headers = {"Accept-Encoding": "gzip"}
    response = requests.get(url, auth=bearer_token, headers=headers)
    if response.status_code != 200:
        print(response.text)
        return []
    return json.loads(response.text)["statuses"]

def get_random_query():
    """
    query_words = []
    while len(query_words)+8*(len(query_words)-1) < 300:
        word = ""
        while word in query_words or word == "":
            word = random.choice(nltk.corpus.words.words()).lower()
        query_words.append(word)
    query_words.pop(-1)
    return " OR ".join(query_words)
    """
    return "\"{}\"".format(random.choice(list(string.ascii_lowercase)))

def remove_repeated_tweets(tweets):
    exists = []
    non_repeated_tweets = []
    for tweet in tweets:
        if not tweet["id_str"] in exists:
            exists.append(tweet["id_str"])
            non_repeated_tweets.append(tweet)
    return non_repeated_tweets

def save(database, tweets, counter=None):
    cursor = database.cursor()
    count = 0
    for tweet in tweets:
        if len(tweet["entities"]["hashtags"]) > 0:
            count += 1
            cursor.execute(
                "INSERT INTO tweets (id, content, hashtags) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE id=%s",
                (int(tweet["id_str"]), tweet["full_text"], ",".join([ hashtag["text"] for hashtag in tweet["entities"]["hashtags"] ]), int(tweet["id_str"]))
            )
    database.commit()
    print(f"{count} tweets saved to database")
    if counter:
        counter.add(count)

parser = argparse.ArgumentParser()
parser.add_argument("--address","-a",help="Hostname of output database",default="db")
parser.add_argument("--database","-d",help="Name of database to use",default="TweetHashtagAssigner")
parser.add_argument("--user","-u",help="Database user to login with",default="TweetHashtagAssigner")
parser.add_argument("--password","-p",help="Database password for user",required=True)
parser.add_argument("--key","-k",help="Consumer API Key",required=True)
parser.add_argument("--secret","-s",help="Consumer API Secret",required=True)
args = parser.parse_args()

if __name__ == "__main__":
    nltk.download("words")

    try:
        bearer_token = BearerTokenAuth(args.key, args.secret)
        print("Twitter successfully authorised!")
    except Exception as error:
        print(error)
    print("Press ctrl + c to end the script, otherwise it well keep downloading at an interval of 1 request every 2 seconds (rate limit)")

    database = mysql.connector.connect(
        host=args.address,
        user=args.user,
        password=args.password,
        database=args.database
    )

    counter = Counter()
    iterations = 0

    try:
        while True:
            tweets = tweets_search_request(bearer_token, get_random_query())
            save_thread = threading.Thread(target=save,args=(database, tweets, counter))
            save_thread.start()
            iterations += 1
            time.sleep(2) # Stay within the rate limit of 1 request every 2 seconds
    except KeyboardInterrupt:
        print(f"Script interupted!")
    except Exception as e:
        print(f"Script errored!\n\n{e}")
    print("Total tweets saved to database (there may be some error due to duplicate tweets):",counter.value)
    print("Total requests:",iterations)
    print("Tweets per request average:",counter.value/iterations)
