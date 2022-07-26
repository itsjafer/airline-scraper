import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync
import time
from common import StandardFlight, USER_AGENT, VIEWPORT, BLOCKED_RESOURCES

def standardize_results(trip):
    results = list()
    for flight in trip['Flights']:
        result = StandardFlight(
            f'{flight["DepartDateTime"]}:00', 
            f'{flight["DestinationDateTime"]}:00', 
            flight['Origin'], 
            flight['Destination'], 
            f'{flight["MarketingCarrier"]} {flight["FlightNumber"]}', 
            flight['TravelMinutes'], 
            []
        )

        if flight['Origin'] != trip['RequestedOrigin'] and flight['Origin'] != trip['Origin']:
            continue
        
        if flight['Destination'] != trip['RequestedDestination'] and flight['Destination'] != trip['Destination']:
            # Connecting flight
            if len(flight['Connections']) <= 0:
                continue
            result.arrivalDateTime = flight['Connections'][-1]["DestinationDateTime"]
            result.flightNo += ", " + (', ').join([f'{v["MarketingCarrier"]} {v["FlightNumber"]}' for v in flight['Connections']])

            result.duration += sum([v['TravelMinutes'] for v in flight['Connections']])

            result.destination = flight['Connections'][-1]['Destination']

        for product in flight['Products']:
            if len(product['Prices']) <= 0:
                continue
            miles = product['Prices'][0]['Amount']
            cash =  product['Prices'][1]['Amount'] if len(product['Prices']) >= 2 else 0
            currencyOfCash = (product['Prices'][1]['Currency'] or "") if len(product['Prices']) >= 2 else 0
            bookingClass = product['BookingCode']

            try:
                cabin = { 
                    "United First": "business", 
                    "United Economy": "economy", 
                    "United Business": "business", 
                    "Economy": "economy", 
                    "Business": "business", 
                    "First": "first", 
                    "United Polaris business": "business", 
                    "United Premium Plus": "economy" 
                    }[product['Description']]
            except:
                continue
            
            try:
                index, existingFare = next((i,v) for i,v in enumerate(result.fares) if v['cabin'] == cabin)
                
                if miles < existingFare['miles']:
                    result.fares[index] = {
                        "cabin": cabin,
                        "miles": miles,
                        "cash": cash,
                        "currencyOfCash": currencyOfCash,
                        "bookingClass": bookingClass,
                        "scraper": "United",
                    }
            except StopIteration as e:
                result.fares.append(
                    {
                        "cabin": cabin,
                        "miles": miles,
                        "cash": cash,
                        "currencyOfCash": currencyOfCash,
                        "bookingClass": bookingClass,
                        "scraper": "United",
                    }
                )

        results.append(result)
    return results

def get_flights(origin, destination, date):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
                headless=True,
                args = [
                    '--use-gl=egl'
                ]
            )
        page = browser.new_page(
            user_agent=USER_AGENT,
            viewport=VIEWPORT
        )
        client = page.context.new_cdp_session(page)
        client.send("Network.setBlockedURLs", { "urls": BLOCKED_RESOURCES })
        url = f'https://www.united.com/en/us/fsr/choose-flights?f={origin}&t={destination}&d={date}&tt=1&at=1&sc=7&px=1&taxng=1&newHP=True&clm=7&st=bestmatches&fareWheel=False'

        flights = list()
        tries = 0
        while True:
            if tries == 2:
                raise Exception("Unable to get flights for United")
            try:
                with page.expect_response("https://www.united.com/api/flight/FetchFlights", timeout=20000) as response_info:
                    page.goto(url)
                    rawResponse = response_info.value.json()
                    if (rawResponse['data']['Trips'] and len(rawResponse['data']['Trips']) > 0):
                        trips = rawResponse['data']['Trips']
                        flights = standardize_results(trips[0])
                        break
            except PlaywrightTimeoutError:
                tries += 1
                time.sleep(5)

        page.close()
        browser.close()

        return flights
            
