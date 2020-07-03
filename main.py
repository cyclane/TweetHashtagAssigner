# Flask web app

from flask import Flask

app = Flask(__name__)

@app.route('/')
def main():
    return "Works!"

if __name__ == "__main__":
    # Only for debugging, this code will not run on server
    app.run(debug=True, port=80)