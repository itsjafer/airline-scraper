import json
import time
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
                        "scraper": "Southwest",
                    }
            if (not lowestFare) or fare["miles"] < lowestFare["miles"]:
                lowestFare = fare
        flight.fares.append(lowestFare)
        flights.append(flight)
    return flights   

def get_flights(origin, destination, date):
    with sync_playwright() as playwright:
        browser = playwright.firefox.launch(
                headless=False,
            )
        page = browser.new_page(
            user_agent=USER_AGENT,
            viewport=VIEWPORT
        )

        page.goto('https://www.southwest.com/air/booking/', wait_until="domcontentloaded", timeout=60000)
        time.sleep(5)

        # Fill in values
        page.locator("input[value='POINTS']").check()
        page.locator("input#originationAirportCode").fill(origin)
        page.locator("input#destinationAirportCode").fill(destination)
        page.locator("input[value='oneway']").click()
        page.locator("input[value='oneway']").check(force=True)
        page.locator("input#departureDate").fill(f'{date[5:7]}/{date[8:10]}')
        flights = list()
        tries = 0
        rawResponse = None
        while True:
            if tries == 5:
                raise Exception("Unable to get flights for Southwest")
            tries += 1
            with page.expect_response("https://www.southwest.com/api/air-booking/v1/air-booking/page/air/booking/shopping") as response_info:
                page.locator("#form-mixin--submit-button").click()
                rawResponse = response_info.value.json()
                if rawResponse and 'success' in rawResponse:
                    break
                time.sleep(2)
        page.close()
        browser.close()

        results = rawResponse["data"]["searchResults"]["airProducts"][0]["details"]
        flights = standardize_results(results)

        return flights