import json
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from common import StandardFlight, USER_AGENT, VIEWPORT, BLOCKED_RESOURCES
import math

def standardize_results(raw):
    results = list()
    for group in raw['data']['airBoundGroups']:

        flightLookups = list()
        for segment in group['boundDetails']['segments']:
            flightID = segment['flightId']
            flightLookup = raw['dictionaries']['flight'][flightID]
            flightLookups.append(flightLookup)

        result = StandardFlight(
            flightLookups[0]['departure']['dateTime'][0:19].replace("T", " "), 
            flightLookups[-1]['arrival']['dateTime'][0:19].replace("T", " "), 
            flightLookups[0]['departure']['locationCode'], 
            flightLookups[-1]['arrival']['locationCode'], 
            ", ".join([f'{segment["marketingAirlineCode"]} {segment["marketingFlightNumber"]}' for segment in flightLookups]), 
            sum([segment["duration"] // 60 for segment in flightLookups]), 
            []
        )

        for fare in group['airBounds']:
            try:
                cabin = { 
                    "eco": "economy", 
                    "ecoPremium": "economy", 
                    "business": "business", 
                    "first": "first",
                    }[fare['availabilityDetails'][0]['cabin']]
            except:
                continue

            bookingClass = fare['availabilityDetails'][0]
            miles = fare['prices']['milesConversion']['convertedMiles']['base']
            try:
                index, existingFare = next((i,v) for i,v in enumerate(result.fares) if v['cabin'] == cabin)
                
                if miles < existingFare['miles']:
                    result.fares[index] = {
                        "cabin": cabin,
                        "miles": miles,
                        "cash": math.ceil(fare['prices']['milesConversion']['convertedMiles']['totalTaxes'] // 100),
                        "currencyOfCash": fare['prices']['milesConversion']['remainingNonConverted']['currencyCode'],
                        "bookingClass": bookingClass,
                        "scraper": "aeroplan",
                    }
            except StopIteration as e:
                result.fares.append(
                    {
                        "cabin": cabin,
                        "miles": miles,
                        "cash": math.ceil(fare['prices']['milesConversion']['convertedMiles']['totalTaxes'] // 100),
                        "currencyOfCash": fare['prices']['milesConversion']['remainingNonConverted']['currencyCode'],
                        "bookingClass": bookingClass,
                        "scraper": "aeroplan",
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

        url = f'https://www.aircanada.com/aeroplan/redeem/availability/outbound?org0={origin}&dest0={destination}&departureDate0={date}&lang=en-CA&tripType=O&ADT=1&YTH=0&CHD=0&INF=0&INS=0&marketCode=DOM'

        flights = list()
        with page.expect_response("https://akamai-gw.dbaas.aircanada.com/loyalty/dapidynamic/1ASIUDALAC/v2/search/air-bounds", timeout=60000) as response_info:
            page.goto(url)
            rawResponse = response_info.value.json()
            if 'errors' in rawResponse:
                print(rawResponse['errors'])
                page.close()
                browser.close()
                return []
            if (rawResponse['data']['airBoundGroups'] and len(rawResponse['data']['airBoundGroups']) > 0):
                trips = rawResponse['data']['airBoundGroups']
                flights = standardize_results(rawResponse)
        page.close()
        browser.close()

        return flights