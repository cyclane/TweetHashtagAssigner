# Flask web app

from flask import Flask

app = Flask(__name__)

@app.route('/')
def main():
    return "Works!"