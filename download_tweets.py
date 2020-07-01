# Downloads tweets and puts them in format to go to process_tweets.py

import sys, argparse, json, random, urllib.parse, time
try:
    import requests
    from requests.auth import AuthBase
except:
    print("This script requires the \"requests\" package!")

try:
    import nltk
except:
    print("This script requires the \"nltk\" package!")

def drawProgressBar(percent, bar_length=20):
    sys.stdout.write("\r")
    sys.stdout.write("[{:<{}}] {:.0f}%".format("=" * int(bar_length * percent), bar_length, percent * 100))
    sys.stdout.flush()

# (Copied from Twitter)
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

def search_request(bearer_token, query):
    url = f"https://api.twitter.com/1.1/search/tweets.json?q={urllib.parse.quote(query)}&count=100"
    headers = {"Accept-Encoding": "gzip"}
    response = requests.get(url, auth=bearer_token, headers=headers)
    if response.status_code != 200:
        return []
    return json.loads(response.text)["statuses"]

def get_random_query():
    return random.choice(nltk.corpus.words.words())

def remove_repeated_tweets(tweets):
    exists = []
    non_repeated_tweets = []
    for tweet in tweets:
        if not tweet["id_str"] in exists:
            exists.append(tweet["id_str"])
            non_repeated_tweets.append(tweet)

    return non_repeated_tweets


parser = argparse.ArgumentParser()
parser.add_argument("--output","-o",help="Name of output file (JSON)",default="tweets.json")
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

    tweets = []

    try:
        while True:
            tweets += search_request(bearer_token, get_random_query())
            time.sleep(2) # Stay within the rate limit of 1 request every 2 seconds
    except KeyboardInterrupt:
        print(f"Script interupted! Saving tweets to \"{args.output}\"")
    except Exception as e:
        print(f"Script errored! Saving tweets to \"{args.output}\"\n\n{e}")

    # Filter repeated tweets
    tweets = remove_repeated_tweets(tweets)

    # Save tweets
    with open(args.output, "w") as output:
        json.dump(tweets, output)

