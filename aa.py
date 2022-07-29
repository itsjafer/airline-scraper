import json
import requests
from common import StandardFlight


def standardize_results(slices):
    results = []
    for slice in slices:
      result = StandardFlight(
          slice["segments"][0]["departureDateTime"].replace(" ", "").replace("T", " ")[0:16], 
          slice["segments"][-1]["arrivalDateTime"].replace(" ", "").replace("T", " ")[0:16], 
          slice["segments"][0]["origin"]["code"], 
          slice["segments"][-1]["destination"]["code"], 
          ", ".join([f'{segment["flight"]["carrierCode"]} {segment["flight"]["flightNumber"]}' for segment in slice["segments"]]), 
          slice['durationInMinutes'], 
          [])
      for product in slice['pricingDetail']:
        if not product['productAvailable']:
          continue

        cabin = { "COACH": "economy", "PREMIUM_ECONOMY": "economy", "FIRST": "business", "BUSINESS": "business" }[product['productType']]
        fare = {
          "cash": product['perPassengerTaxesAndFees']['amount'],
          "currencyOfCash": product['perPassengerTaxesAndFees']['currency'],
          "miles": product['perPassengerAwardPoints'],
          "cabin": cabin,
          "scraper": "American Airlines",
          "bookingClass": "?"
        }

        try:
          index, existingFare = next((i,v) for i,v in enumerate(result.fares) if v['cabin'] == cabin)
          
          if product['perPassengerAwardPoints'] < existingFare['miles']:
              result.fares[index] = fare
        except StopIteration as e:
          result.fares.append(fare)
      results.append(result)

    return results

def get_flights(origin, destination, date):
    url = 'https://www.aa.com/booking/api/search/itinerary'
    body = {
      "metadata": { 
        "selectedProducts": [], 
        "tripType": "OneWay", 
        "udo": {} 
      },
      "passengers": [{ "type": "adult", "count": 1 }],
      "queryParams": { "sliceIndex": 0, "sessionId": "", "solutionId": "", "solutionSet": "" },
      "requestHeader": { "clientId": "AAcom" },
      "slices": [{
        "allCarriers": True,
        "cabin": "",
        "connectionCity": None,
        "departureDate": date,
        "destination": destination,
        "includeNearbyAirports": False,
        "maxStops": None,
        "origin": origin,
        "departureTime": "040001"
      }],
      "tripOptions": { "locale": "en_US", "searchType": "Award" },
      "loyaltyInfo": None
    }

    header = {
      "content-type": "application/json",
      "accept": "application/json, text/plain, */*",
      "accept-language": "en-US,en;q=0.9"
    }

    x = requests.post(url, headers=header, json=body)

    if not x.ok:
        raise Exception("Failed to get OK response from American Airlines")
    flights = []
    rawResponse = x.json()
    if 'slices' in rawResponse and len(rawResponse['slices']) > 0:
        flights = standardize_results(rawResponse['slices'])

    return flights