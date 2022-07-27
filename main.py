import json
import requests
import os
import sys

import united, southwest, delta, skippedlagged
from playwright.sync_api import sync_playwright
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/")
def hello_world():
    name = os.environ.get("NAME", "World")
    return "Hello {}!".format(name)

@app.route('/get_flights', methods=['POST'])
def get_flights():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
        )

        deltaFlights = delta.get_flights(browser, origin, destination, date)
        unitedFlights = united.get_flights(browser, origin, destination, date)
        chaseFlights = skippedlagged.get_flights(browser, origin, destination, date)
        southwestFlights = southwest.get_flights(browser, origin, destination, date)
        print(deltaFlights)

        return jsonify(deltaFlights + chaseFlights + unitedFlights + southwestFlights)
        
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


