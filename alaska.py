import json
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from common import StandardFlight, USER_AGENT, VIEWPORT
import math

def standardize_results(rawResponse):
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

        page.goto("https://m.alaskaair.com/shopping/?timeout=true", wait_until="networkidle")
        page.set_content(rawResponse)

        elements = page.query_selector_all(".optionList > li")

        for element in elements:
            flightNo = element.query_selector('.optionHeaderFltNum').get_attribute("innerText")
            if not flightNo.trim().startswith("Flight"):
                continue

            airlineCode = element.query_selector('.optionsHeader > img').get_attribute("src").split("/")[-1].split(".")[0]
            origin = element.query_selector('optionDeparts .optionCityCode').get_attribute('innerText')
            destination = element.query_selector('.left .optionCityCode').get_attribute('innerText')

            print(airlineCode, flightNo, origin, destination)

def get_flights(origin, destination, date):
    url = 'https://m.alaskaair.com/shopping/flights'
    body = f'CacheId=&ClientStateCode=CA&SaveFields.DepShldrSel=False&SaveFields.RetShldrSel=False&SaveFields.SelDepOptId=-1&SaveFields.SelDepFareCode=&SaveFields.SelRetOptId=-1&SaveFields.SelRetFareCode=&SearchFields.IsAwardBooking=true&SearchFields.IsAwardBooking=false&SearchFields.SearchType=OneWay&SearchFields.DepartureCity={origin}&SearchFields.ArrivalCity={destination}&SearchFields.DepartureDate={date}&SearchFields.ReturnDate=&SearchFields.NumberOfTravelers=1&SearchFields.PriceType=Lowest&SearchFields.UpgradeOption=none&SearchFields.DiscountCode=&DiscountCode=&SourcePage=Search&deals-link=&SearchFields.IsCalendar=false'

    header = {
      "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
      "content-type": "application/x-www-form-urlencoded",
      "origin": "https://m.alaskaair.com",
      "referer": "https://m.alaskaair.com/shopping/?timeout=true",
      "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"
    
    }

    x = requests.post(url, headers=header, data=body)

    if not x.ok:
        return []
    flights = []
    rawResponse = x.text
    flights = standardize_results(rawResponse)

    return flights

get_flights("ORD", "LGA", "2022-09-01")