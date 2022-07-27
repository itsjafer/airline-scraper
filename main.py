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

@app.route('/delta', methods=['POST'])
def get_delta():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        deltaFlights = delta.get_flights(browser, origin, destination, date)

        return jsonify(deltaFlights)

@app.route('/united', methods=['POST'])
def get_united():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        unitedFlights = united.get_flights(browser, origin, destination, date)

        return jsonify(unitedFlights)

@app.route('/chase', methods=['POST'])
def get_chase():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        chaseFlights = skippedlagged.get_flights(browser, origin, destination, date)

        return jsonify(chaseFlights)

@app.route('/southwest', methods=['POST'])
def get_southwest():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=False
        )

        southwestFlights = southwest.get_flights(browser, origin, destination, date)

        return jsonify(southwestFlights)
        
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


