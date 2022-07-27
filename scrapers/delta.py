import json
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
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

        stealth_sync(page)

        page.goto('https://www.delta.com/flight-search/book-a-flight', wait_until="networkidle")

        formatted_date = f'{date[5:7]}/{date[8:10]}/{date[0:4]}'

        # Fill in values
        page.locator("#fromAirportName span.airport-code.d-block").click()
        page.locator("#search_input").fill(origin)
        page.locator(".airportLookup-list .airport-code").click()

        page.locator("#toAirportName span.airport-code.d-block").click()
        page.locator("#search_input").fill(destination)
        page.locator(".airportLookup-list .airport-code").click()

        page.screenshot(path="screenshot.png")

        page.locator("select[name='selectTripType']").select_option("ONE_WAY")

        page.locator("#calDepartLabelCont").click()
        page.wait_for_selector(".dl-datepicker-calendar")
        page.locator(f"a[data-date^='{formatted_date}']").click()
        page.wait_for_selector(f"a[data-date^='{formatted_date}'][class*='dl-selected-date']")

        page.locator("button.donebutton").click()
        page.wait_for_selector(f"div[class*='calDispValueCont']:not([class*='open'])")

        page.locator("#shopWithMiles").click()

        page.locator("#btnSubmit").click()
        
        errorMsg = page.locator("#advance-search-global-err-msg")
        if errorMsg:
            errorText = errorMsg.evaluate("node => node.innertext")
            if "no results" in errorText:
                return []

        with page.expect_response(lambda response: "shop/ow/search" in response.url and response.request.method == "POST") as response_info:
            rawResponse = response_info.value.json()
            print(rawResponse)
        browser.close()

        return flights

print(get_flights("MDW", "LGA", "2022-09-23"))