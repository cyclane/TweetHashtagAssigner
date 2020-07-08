# Flask web app

from flask import Flask, request, abort
import json, mysql.connector, nltk
import lib

nltk.download("wordnet")
nltk.download("averaged_perceptron_tagger")

# Will change later so it's fine for it to be in repo
database = mysql.connector.connect(
    host="db",
    user="TweetHashtagAssigner",
    password="password",
    database="TweetHashtagAssigner"
)
app = Flask(__name__)
print("Loading model")
model = lib.Model.load(database, 5, 1)
print("Model loaded")

@app.route('/api/probability')
def main():
    global model
    text = request.args.get("text", default=None)
    if text:
        prob = model.text_probability(text)
        prob = lib.sort_probabilities(prob)
        hashtags = []
        for x in range(min(10,len(prob))):
            hashtags.append(model.get_hashtag_string(prob[x][0]))
        return json.dumps({
            "hashtags": hashtags
        })
    else:
        abort(404) 

if __name__ == "__main__":
    # Only for debugging, this code will not run on server
    app.run(debug=True, port=80)