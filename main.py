import json
import requests
import os
import sys

import united, southwest, delta, skippedlagged, aeroplan, jetblue
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

    deltaFlights = delta.get_flights(origin, destination, date)

    return jsonify(deltaFlights)

@app.route('/united', methods=['POST'])
def get_united():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    unitedFlights = united.get_flights(origin, destination, date)

    return jsonify(unitedFlights)

@app.route('/aeroplan', methods=['POST'])
def get_aeroplan():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    aeroplanFlights = aeroplan.get_flights(origin, destination, date)

    return jsonify(aeroplanFlights)

@app.route('/chase', methods=['POST'])
def get_chase():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    chaseFlights = skippedlagged.get_flights(origin, destination, date)

    return jsonify(chaseFlights)

@app.route('/southwest', methods=['POST'])
def get_southwest():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    southwestFlights = southwest.get_flights(origin, destination, date)

    return jsonify(southwestFlights)

@app.route('/jetblue', methods=['POST'])
def get_jetblue():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    jetblueFlights = jetblue.get_flights(origin, destination, date)

    return jsonify(jetblueFlights)
        
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


