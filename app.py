from flask import Flask, jsonify, request

app = Flask(__name__)

@app.route("/")

def home():
    return "first Flask app"

