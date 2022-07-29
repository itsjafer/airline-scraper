import playwright from 'playwright-aws-lambda'

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

const standardizeResults = (trip) => {
  let results = []
  for (let flight of trip.Flights) {
    let result = StandardFlight(
      `${flight["DepartDateTime"]}:00`, 
      `${flight["DestinationDateTime"]}:00`, 
      flight['Origin'], 
      flight['Destination'], 
      `${flight["MarketingCarrier"]} ${flight["FlightNumber"]}`, 
      flight['TravelMinutes'], 
      []
    )

    if (flight['Origin'] !== trip['RequestedOrigin'] && flight['Origin'] !== trip['Origin'])
      continue
        
    if (flight['Destination'] !== trip['RequestedDestination'] && flight['Destination'] !== trip['Destination']) {
      // Connecting flight
      if (flight['Connections'].length <= 0)
        continue
      result.arrivalDateTime = flight['Connections'].slice(-1)[0]["DestinationDateTime"]

      result.flightNo += ", " + flight['Connections'].map(c => `${c["MarketingCarrier"]} ${c["FlightNumber"]}`).join(", ")
      
      result.duration += flight['Connections'].reduce((accumulator, object) => {
        return accumulator + object['TravelMinutes']
      }, 0)
      
      result.destination = flight['Connections'].slice(-1)[0]['Destination']
    }

    for (let product of flight['Products']) {
      if (product['Prices'].length <= 0)
        continue
      
        const miles = product.Prices[0].Amount
        const cash = product.Prices.length >= 2 ? product.Prices[1].Amount : 0
        const currencyOfCash = product.Prices.length >= 2 ? (product.Prices[1].Currency ?? "") : ""
        const bookingClass = product.BookingCode
        const cabin = { "United First": "business", "United Economy": "economy", "United Business": "business", Economy: "economy", Business: "business", First: "first", "United Polaris business": "business", "United Premium Plus": "economy" }[product.Description]

        if (cabin === undefined)
          continue

        let existingFare = result.fares.find((fare) => fare.cabin === cabin)
        if (existingFare !== undefined) {
          if (miles < existingFare.miles)
            existingFare = { ...{ cabin, miles, cash, currencyOfCash, bookingClass, scraper: "United" } }
        } else {
          result.fares.push({ cabin, miles, cash, currencyOfCash, bookingClass, scraper: "United" })
        }
    }

    results.push(result)
      
    }

  return results
}

export const united = async (req, res) => {
  let browser = null;
  let flights = []
  try {
    browser = await playwright.launchChromium({headless:true});
    const context = await browser.newContext({
        userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
        viewport: { 'width': 1920, 'height': 1080 }
    });

    const page = await context.newPage();
    let origin = "ORD"
    let destination = "LGA"
    let date = "2022-09-02"

    let tries = 0
    while (true) {
      if (tries == 2)
        throw new Error("Unable to get flights for United")
      try {
        page.goto(`https://www.united.com/en/us/fsr/choose-flights?f=${origin}&t=${destination}&d=${date}&tt=1&at=1&sc=7&px=1&taxng=1&newHP=True&clm=7&st=bestmatches&fareWheel=False`);
        const response = await page.waitForResponse("https://www.united.com/api/flight/FetchFlights")

        const raw = await response.json()

        if (raw.data.Trips && raw.data.Trips.length > 0) {
          flights = standardizeResults(raw.data.Trips[0])
        }
        break;
      } catch (error) {
        tries += 1
      }
    }
    

  } catch (error) {
    throw error;
  } finally {
    if (browser) {
      await browser.close();
    }
  }
  res.status(200).send(flights);
  return JSON.stringify(flights)
};