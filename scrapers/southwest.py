import json
from playwright.sync_api import sync_playwright
from common import StandardFlight, USER_AGENT, VIEWPORT

def standardize_results(results):
    flights = list()
    for result in results:
        flight = StandardFlight(
            result["departureDateTime"][:19].replace("T", " "), 
            result["arrivalDateTime"][:19].replace("T", " "), 
            result["originationAirportCode"], 
            result["destinationAirportCode"], 
            ", ".join([f'{segment["operatingCarrierCode"]} {segment["flightNumber"]}' for segment in result["segments"]]), 
            result["totalDuration"], 
            []
            )

        types = result["fareProducts"]["ADULT"]
        lowestFare = None
        for productType in types:
            product = result["fareProducts"]["ADULT"][productType]
            if product["availabilityStatus"] != "AVAILABLE":
                continue
            fare = {
                        "cabin": "economy",
                        "miles": int(float(product["fare"]["totalFare"]["value"])),
                        "cash": int(float(product["fare"]["totalTaxesAndFees"]["value"])),
                        "currencyOfCash": product["fare"]["totalTaxesAndFees"]["currencyCode"],
                        "bookingClass": product["productId"].split(",")[1],
                    }
            if (not lowestFare) or fare["miles"] < lowestFare["miles"]:
                lowestFare = fare
        flight.fares.append(lowestFare)
        flights.append(flight)
    return flights   

def get_flights(origin, destination, date):
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True
        )
        page = browser.new_page(
            user_agent=USER_AGENT,
            viewport=VIEWPORT
        )

        page.goto('https://www.southwest.com/air/booking/', wait_until="networkidle")

        # Fill in values
        page.locator("input[value='oneway']").check()
        page.locator("input[value='POINTS']").check()
        page.locator("input#originationAirportCode").fill(origin)
        page.locator("input#destinationAirportCode").fill(destination)
        page.locator("input#departureDate").fill(f'{date[5:7]}/{date[8:10]}')
        page.locator("#form-mixin--submit-button").click()

        flights = list()
        tries = 0
        rawResponse = None
        while True:
            if tries == 5:
                print("I give up")
                exit()
            tries += 1
            with page.expect_response("https://www.southwest.com/api/air-booking/v1/air-booking/page/air/booking/shopping") as response_info:
                rawResponse = response_info.value.json()
                if rawResponse['success']:
                    break
            page.locator("#form-mixin--submit-button").click()
        browser.close()

        results = rawResponse["data"]["searchResults"]["airProducts"][0]["details"]
        flights = standardize_results(results)

        return flights

print(get_flights("MDW", "LGA", "2022-09-23"))