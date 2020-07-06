# Flask web app

from flask import Flask, request, abort
import json

app = Flask(__name__)

@app.route('/api/probability')
def main():
    text = request.args.get("text", default=None)
    if text:
        # This is only for testing
        return json.dumps({
            "hashtags": [text, "a", "b", "c", "d", "e", "f", "g", "h", "i"]
        })
    else:
        abort(404) 

if __name__ == "__main__":
    # Only for debugging, this code will not run on server
    app.run(debug=True, port=80)