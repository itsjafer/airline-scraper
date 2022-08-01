import fetch from "node-fetch"
function StandardFlight(departTime, arrivalTime, origin, destination, flightNo, duration, fares) {
  return {
    departureDateTime: departTime,
    arrivalDateTime: arrivalTime,
    origin: origin,
    destination: destination,
    flightNo: flightNo,
    duration: duration,
    fares: fares
  }
}

const standardizeResults = (slices) => {
    let results = []
    for (let slice of slices) {
      let result = StandardFlight(
          slice["segments"][0]["departureDateTime"].replace(" ", "").replace("T", " ").substring(0,16), 
          slice["segments"].slice(-1)[0]["arrivalDateTime"].replace(" ", "").replace("T", " ").substring(0,16), 
          slice["segments"][0]["origin"]["code"], 
          slice["segments"].slice(-1)[0]["destination"]["code"], 
          slice['segments'].map(c => `${c["flight"]['carrierCode']} ${c["flight"]['flightNumber']}`).join(", "),
          slice['durationInMinutes'], 
          [])
      for (let product of slice['pricingDetail']) {
        if (!product['productAvailable'])
          continue

        let cabin = { "COACH": "economy", "PREMIUM_ECONOMY": "economy", "FIRST": "business", "BUSINESS": "business" }[product['productType']]
        let fare = {
          "cash": product['perPassengerTaxesAndFees']['amount'],
          "currencyOfCash": product['perPassengerTaxesAndFees']['currency'],
          "miles": product['perPassengerAwardPoints'],
          "cabin": cabin,
          "scraper": "American Airlines",
          "bookingClass": "?"
        }

        if (cabin === undefined)
          continue

        let existingFare = result.fares.find((fare) => fare.cabin === cabin)
        if (existingFare !== undefined) {
          if (product['perPassengerAwardPoints'] < existingFare.miles)
            existingFare = fare
        } else {
          result.fares.push(fare)
        }
      results.push(result)
    }
    }
    return results
}

export const aaFunc = async (origin, destination, date) => {
  
    const raw = await fetch("https://www.aa.com/booking/api/search/itinerary", {
        method: "POST",
        headers: {
        "content-type": "application/json",
        "accept": "application/json, text/plain, */*",
        "accept-language": "en-US,en;q=0.9"
        },
        body: JSON.stringify({
        "metadata": { "selectedProducts": [], "tripType": "OneWay", "udo": {} },
        "passengers": [{ "type": "adult", "count": 1 }],
        "queryParams": { "sliceIndex": 0, "sessionId": "", "solutionId": "", "solutionSet": "" },
        "requestHeader": { "clientId": "AAcom" },
        "slices": [{
            "allCarriers": true,
            "cabin": "",
            "connectionCity": null,
            "departureDate": date,
            "destination": destination,
            "includeNearbyAirports": false,
            "maxStops": null,
            "origin": origin,
            "departureTime": "040001"
        }],
        "tripOptions": { "locale": "en_US", "searchType": "Award" },
        "loyaltyInfo": null
        })
    })
    const resp = await raw.text()
    const json = JSON.parse(resp)

    if (json.error && json.error !== "309")
        throw new Error(json.error)

    const flightsWithFares = []
    if (json.slices && json.slices.length > 0) {
        const flights = standardizeResults(json.slices)
        flightsWithFares.push(...flights)
    }
    return JSON.stringify(flightsWithFares)
};