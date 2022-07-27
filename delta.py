import json
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from common import StandardFlight, USER_AGENT, VIEWPORT

def standardize_results(raw):
    results = list()
    for itinerary in raw["itinerary"]:
        trip = itinerary['trip'][0]

        flight = StandardFlight(
            trip['schedDepartLocalTs'].replace("T", " "), 
            trip['schedArrivalLocalTs'].replace("T", " "), 
            trip["originAirportCode"], 
            trip["destAirportCode"], 
            ", ".join([f'{segment["marketingCarrier"]["code"]} {segment["marketingFlightNum"]}' for segment in trip["flightSegment"]]), 
            sum([segment['totalAirTime']['day'] * 24 * 60 + segment['totalAirTime']['hour'] * 60 + segment['totalAirTime']['minute'] for segment in trip["flightSegment"]]), 
            []
            )

        fares = trip['viewSeatUrls'][0]["fareOffer"]["itineraryOfferList"]
        for fare in fares:
            if (not fare) or (fare['soldOut']) or (not fare['offered']):
                continue

            miles = 0
            cash = -1
            currencyOfCash = "USD"
            if fare['totalPrice'] and fare['totalPrice']['miles'] and fare['totalPrice']['miles']['miles']:
                miles = fare['totalPrice']['miles']['miles']
            else:
                continue
            if fare['totalPrice'] and fare['totalPrice']['currency'] and fare['totalPrice']['currency']['code']:
                currencyOfCash = fare['totalPrice']['currency']['code']
            else: 
                continue
            if fare['totalPrice'] and fare['totalPrice']['currency'] and fare['totalPrice']['currency']['amount']:
                cash = fare['totalPrice']['currency']['amount']
            else:
                continue
            cabin = "business" if fare['brandInfoByFlightLegs'][0]['cos'][0] == "O" else "economy"
            fare = {
                        "cabin": cabin,
                        "miles": miles,
                        "cash": cash,
                        "currencyOfCash": currencyOfCash,
                        "bookingClass": fare['brandInfoByFlightLegs'][0]['cos'],
                    }
            try:
                index, existingFare = next((i,v) for i,v in enumerate(flight.fares) if v['cabin'] == cabin)
                if miles < existingFare['miles']:
                    flight.fares[index] = fare
            except:
                flight.fares.append(fare)
        results.append(flight)
    return results   

def get_flights(origin, destination, date):
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(
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
    page.locator(".airportLookup-list .airport-code").first.click()

    page.locator("#toAirportName span.airport-code.d-block").click()
    page.locator("#search_input").fill(destination)
    page.locator(".airportLookup-list .airport-code").first.click()

    page.locator("select[name='selectTripType']").select_option("ONE_WAY")

    page.locator("#calDepartLabelCont").click()
    page.wait_for_selector(".dl-datepicker-calendar")

    tries = 0
    while True:
        if tries == 9:
            return []
        tries += 1
        if not page.is_visible(f"a[data-date^='{formatted_date}']"):
            page.locator("a[aria-label='Next']:not([class*='no-next'])").click()
            continue
        page.locator(f"a[data-date^='{formatted_date}']", ).click()
        break

    page.locator("button.donebutton").click()
    page.wait_for_selector(f"div[class*='calDispValueCont']:not([class*='open'])")

    page.locator("#shopWithMiles").click(force=True)
    page.locator("#chkFlexDate").evaluate("node => node.removeAttribute('disabled')")
    page.locator("#chkFlexDate").uncheck(force=True)


    flights = list()
    with page.expect_response(lambda response: "shop/ow/search" in response.url) as response_info:
        page.locator("#btnSubmit").click()
        rawResponse = response_info.value.json()
        flights = standardize_results(rawResponse)
    page.close()
    browser.close()
    playwright.stop()

    return flights