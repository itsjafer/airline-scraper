import json
import requests
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync
from common import StandardFlight, USER_AGENT, VIEWPORT, BLOCKED_RESOURCES
import math
import datetime
import re

def convertTo24(time):
    in_time = datetime.datetime.strptime(time, "%I:%M %p")
    out_time = datetime.datetime.strftime(in_time, "%H:%M")
    return out_time

def addToDate(date, days):
    date_1 = datetime.datetime.strptime(date, "%Y-%m-%d")
    end_date = date_1 + datetime.timedelta(days=days)
    return datetime.datetime.strftime(end_date, "%Y-%m-%d")

def standardize_results(rawResponse, date):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
                headless=False,
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
        page.goto("https://m.alaskaair.com/shopping/?timeout=true", wait_until="networkidle")
        page.set_content(rawResponse)

        elements = page.query_selector_all(".optionList > li")
        results = []
        for element in elements:
            flightNo = element.query_selector('.optionHeaderFltNum').inner_text()
            if not flightNo.strip().startswith("Flight"):
                flightNo = f"Unknown ({flightNo.strip()[0]} flights)"
            else:
                flightNo = flightNo.split(" ")[1]

            airlineCode = element.query_selector('.optionHeader > img').evaluate("node => node.src").split("/")[-1]
            origin = element.query_selector('.optionDeparts .optionCityCode').inner_text()
            destination = element.query_selector('.left .optionCityCode').inner_text()


            departureDate = date # for now, assume correct date
            departureTime = element.query_selector(".optionDeparts .optionTime .b").inner_text()
            arrivalTime = element.query_selector(".left .optionTime .b").inner_text()
            try:
                addDays = element.query_selector('.left .optionTime .arrivalDaysDifferent').inner_text()
            except:
                addDays = None

            result = StandardFlight(
                f"{departureDate} {convertTo24(departureTime)}:00", 
                f"{addToDate(departureDate, int(addDays[1])) if addDays else departureDate} {convertTo24(arrivalTime)}:00", 
                origin, 
                destination, 
                f"{airlineCode} {flightNo}", 
                0, 
                []
            )

            fares = element.query_selector_all(".fare-ctn div[style='display: block;']:not(.fareNotSelectedDisabled)")

            for fare in fares:
                milesAndCash = fare.query_selector(".farepriceaward").inner_text()
                cabin = fare.query_selector('.farefam').inner_text()
                if (not milesAndCash or not cabin):
                    continue
                
                miles = milesAndCash.split("+")[0]
                numeric_miles = int(float(re.sub(r'[^\d.]+', '', miles)) * 1000)

                cash = milesAndCash.split("+")[1]
                numeric_cash = int(float(re.sub(r'[^\d.]+', '', cash)))

                standardCabin = { "Main": "economy", "First Class": "business" }[cabin] if airlineCode == "AS" else { "Main": "economy", "Partner Business": "business", "First Class": "business" }[cabin]
                flightFare = {
                    "cash": numeric_cash,
                    "miles": numeric_miles,
                    "currencyOfCash": "USD",
                    "cabin": standardCabin,
                    "bookingClass": None,
                    "scraper": "Alaska Airlines"       
                }
                result.fares.append(flightFare)
            results.append(result)
        return results

                

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
        raise Exception("Did not receive 200 from Alaska")
    rawResponse = x.text
    flights = standardize_results(rawResponse, date)

    return flights