import json
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from common import StandardFlight, USER_AGENT, VIEWPORT

def standardize_results(rawResponse, pointsFactor):
    results = list()
    for id in rawResponse["flights"]:
        flight = rawResponse["flights"][id]
        
        result = StandardFlight(
            flight["segments"][0]["departure"]["time"].replace("T", " ")[0:16], 
            flight["segments"][0]["arrival"]["time"].replace("T", " ")[0:16], 
            flight["segments"][0]["departure"]["airport"], 
            flight["segments"][-1]["arrival"]["airport"], 
            ", ".join([f'{segment["airline"]} {segment["flight_number"]}' for segment in flight["segments"]]), 
            sum([segment["duration"] // 60 for segment in flight["segments"]]), 
            [])

        rawFares = list(filter(lambda x: (x["flight"] == id), rawResponse["itineraries"]["outbound"]))

        standardFares = list()
        for rawFare in rawFares:
            fare = {
                        "cabin": "economy",
                        "miles": rawFare['one_way_price'] / pointsFactor,
                        "cash": 0,
                        "currencyOfCash": "USD",
                        "bookingClass": None,
                    }
            standardFares.append(fare)
        lowestFare = None
        for fare in standardFares:
            if (not lowestFare) or fare["cash"] < lowestFare["cash"]:
                lowestFare = fare
        result.fares.append(lowestFare)
        results.append(result)
    return results


def get_flights(browser, origin, destination, date, pointsFactor=1.25):
    context = browser.new_context()
    page = context.new_page(
        user_agent=USER_AGENT,
        viewport=VIEWPORT
    )

    stealth_sync(page)

    page.goto(f'https://skiplagged.com/flights/{origin}/{destination}/{date}#', wait_until="domcontentloaded")

    flights = list()
    with page.expect_response(lambda response: "search.php" in response.url) as response_info:
        rawResponse = response_info.value.json()
        flights = standardize_results(rawResponse, pointsFactor)
    
    return flights
       
