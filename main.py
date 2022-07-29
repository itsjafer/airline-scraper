import json
import requests
import os
import sys

import united, southwest, delta, skippedlagged, aeroplan, jetblue, virgin, aa, alaska
from playwright.sync_api import sync_playwright
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_caching import Cache

cache = Cache(config={'CACHE_TYPE': 'SimpleCache'})
app = Flask(__name__)
CORS(app)
cache.init_app(app)

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

@app.route('/virgin', methods=['POST'])
def get_virgin():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    virginFlights = virgin.get_flights(origin, destination, date)

    return jsonify(virginFlights)

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

@app.route('/aa', methods=['POST'])
def get_aa():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    aaFlights = aa.get_flights(origin, destination, date)

    return jsonify(aaFlights)

@app.route('/alaska', methods=['POST'])
def get_alaska():
    origin = request.form['origin'].upper()
    destination = request.form['destination'].upper()
    date = request.form['date']

    alaskaFlights = alaska.get_flights(origin, destination, date)

    return jsonify(alaskaFlights)
        
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))


