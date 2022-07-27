import json
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync
import time
from common import StandardFlight, USER_AGENT, VIEWPORT

def standardize_results(rawResponse):
    results = list()
    for itinerary in rawResponse['itinerary']:
        result = StandardFlight(
            itinerary['depart'][0:19].replace("T", " "), 
            itinerary['arrive'][0:19].replace("T", " "), 
            itinerary['from'], 
            itinerary['to'], 
            ", ".join([f'{segment["marketingAirlineCode"]} {segment["flightno"]}' for segment in itinerary["segments"]]), 
            0, 
            []
        )

        id = itinerary['id']
        for checkFare in rawResponse['fareGroup']:
            for bundle in checkFare['bundleList']:
                if bundle['itineraryID'] != id:
                    continue
                if bundle['points'] == "N/A":
                    continue

                cabin = {
                    "Y": "economy",
                    "J": "business",
                    "C": "business" 
                    }[bundle['cabinclass']]
                miles = int(float(bundle['points']))
                cash =  float(bundle['fareTax'])
                currencyOfCash = rawResponse['currency']
                bookingClass = itinerary['segments'][0]['bookingclass']
            
                try:
                    index, existingFare = next((i,v) for i,v in enumerate(result.fares) if v['cabin'] == cabin)
                    
                    if miles < existingFare['miles']:
                        result.fares[index] = {
                            "cabin": cabin,
                            "miles": miles,
                            "cash": cash,
                            "currencyOfCash": currencyOfCash,
                            "bookingClass": bookingClass,
                            "scraper": "JetBlue",
                        }
                except StopIteration as e:
                    result.fares.append(
                        {
                            "cabin": cabin,
                            "miles": miles,
                            "cash": cash,
                            "currencyOfCash": currencyOfCash,
                            "bookingClass": bookingClass,
                            "scraper": "JetBlue",
                        }
                    )

                results.append(result)
    return results

def get_flights(origin, destination, date):
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(
                headless=True
            )
        page = browser.new_page(
            user_agent=USER_AGENT,
            viewport=VIEWPORT
        )

        stealth_sync(page)

        url = f'https://www.jetblue.com/booking/flights?from={origin}&to={destination}&depart={date}&noOfRoute=1&isMultiCity=false&lang=en&adults=1&children=0&infants=0&sharedMarket=false&roundTripFaresFlag=false&usePoints=true'

        flights = list()
        tries = 0
        while True:
            if tries == 2:
                return []
                
            try:
                with page.expect_response(lambda x: "outboundLFS" in x.url and x.request.method == "POST", timeout=20000) as response_info:
                    page.goto(url)
                    if response_info.value.status_text == "JB_INVALID_REQUEST":
                        
                        page.close()
                        browser.close()
                        return []

                    rawResponse = response_info.value.json()
                    if (rawResponse['itinerary'] and len(rawResponse['itinerary']) > 0):
                        flights = standardize_results(rawResponse)
                        break
            except PlaywrightTimeoutError:
                tries += 1
                time.sleep(5)

        page.close()
        browser.close()

        return flights
