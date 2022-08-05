import playwright from 'playwright-aws-lambda'
import fetch from "node-fetch"
import { addExtra } from 'playwright-extra'
import StealthPlugin from 'puppeteer-extra-plugin-stealth'
import HttpsProxyAgent from 'https-proxy-agent'

function StandardFlight(departTime, arrivalTime, origin, destination, flightNo, duration, fares) {
  return {
    departureDateTime: departTime,
    arrivalDateTime: arrivalTime,
    origin: origin,
    destination: destination,
    flightNo: flightNo,
    duration: duration,
    fares: fares
  }
}
const BLOCKED_RESOURCES = [
  "*/favicon.ico", ".css", ".jpg", ".jpeg", ".png", ".svg", ".woff",
  "*.optimizely.com", "everesttech.net", "userzoom.com", "doubleclick.net", "googleadservices.com", "adservice.google.com/*",
  "connect.facebook.com", "connect.facebook.net", "sp.analytics.yahoo.com"]
  
const standardizeResults = async (rawResponse, date) => {
  const zeroPad = num => (num.toString().length === 1 ? `0${num}` : num)
    const convertTo24 = time => { const d = new Date(`1/1/2020 ${time}`); return `${zeroPad(d.getHours())}:${zeroPad(d.getMinutes())}` }
    const addToDate = (date, days) => { const d = new Date(date); d.setDate(d.getDate() + days); return d.toISOString().split("T")[0] }
  let browser = null;
  let results = []
  browser = addExtra(await playwright.launchChromium(
      {
          headless:true,
      }));
  browser.use(StealthPlugin())

  const context = await browser.newContext({
      userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
      viewport: { 'width': 1920, 'height': 1080 }
  });

  const page = await context.newPage();
  const client = await page.context().newCDPSession(page);
  await client.send("Network.setBlockedURLs", { urls: BLOCKED_RESOURCES })
  await page.goto("https://m.alaskaair.com/shopping/?timeout=true", {waitUntil: "networkidle", timeout: 60000})

  await page.setContent(rawResponse)
  let elements = await page.$$(".optionList > li")
  for (let element of elements) {
    let flightNo = await (await element.$('.optionHeaderFltNum'))?.innerText()
    if (!flightNo) {
      continue
    }
    if (!flightNo?.trim().startsWith("Flight")) {
      flightNo = `Unknown (${flightNo.trim()[0]} flights)`
    } else {
      flightNo = flightNo.split(" ")[1]
    }


    let airlineCode = (await element.$eval(".optionHeader > img", node => node.src)).split("/").splice(-1)[0]
    let origin = await (await element.$(".optionDeparts .optionCityCode"))?.innerText()
    let destination = await (await element.$(".left .optionCityCode"))?.innerText()

    let departureDate = date
    let departureTime = await (await element.$(".optionDeparts .optionTime .b"))?.innerText()
    let arrivalTime = await (await element.$(".left .optionTime .b"))?.innerText()

    let addDays = await (await element.$('.left .optionTime .arrivalDaysDifferent'))?.innerText()

    let result = StandardFlight(
      `${departureDate} ${convertTo24(departureTime)}:00`,
      `${addDays ? addToDate(departureDate, addDays[1]) : departureDate} ${convertTo24(arrivalTime)}:00`,
      origin,
      destination,
      `${airlineCode} ${flightNo}`,
      0,
      []
    )

    let fares = await element.$$(".fare-ctn div[style='display: block;']:not(.fareNotSelectedDisabled)")

    for(let fare of fares) {
      let milesAndCash = await (await fare.$(".farepriceaward"))?.innerText()
      let cabin = await (await fare.$('.farefam'))?.innerText()

      if (!milesAndCash || !cabin) {
        continue
      }

      let miles = milesAndCash.split("+")[0]
      let numericMiles = parseFloat(miles.replace('[^\d.]+', '')) * 1000

      let cash = milesAndCash.split("+")[1]
      let numericCash = cash.replace(/[^\d.]+/g, '')

      let standardCabin = airlineCode === "AS" ? { Main: "economy", "First Class": "business" }[cabin] : { Main: "economy", "Partner Business": "business", "First Class": "business" }[cabin]

      let flightFare = {
        "cash": numericCash,
        "miles": numericMiles,
        "currencyOfCash": "USD",
        "cabin": standardCabin,
        "bookingClass": null,
        "scraper": "Alaska Airlines"
      }

      result.fares.push(flightFare)
    }
    results.push(result)
  }

  return results
}

export const alaskaFunc = async (origin, destination, date) => {
  const url = 'https://m.alaskaair.com/shopping/flights'
  let body = `acheId=&ClientStateCode=CA&SaveFields.DepShldrSel=False&SaveFields.RetShldrSel=False&SaveFields.SelDepOptId=-1&SaveFields.SelDepFareCode=&SaveFields.SelRetOptId=-1&SaveFields.SelRetFareCode=&SearchFields.IsAwardBooking=true&SearchFields.IsAwardBooking=false&SearchFields.SearchType=OneWay&SearchFields.DepartureCity=${origin}&SearchFields.ArrivalCity=${destination}&SearchFields.DepartureDate=${date}&SearchFields.ReturnDate=&SearchFields.NumberOfTravelers=1&SearchFields.PriceType=Lowest&SearchFields.UpgradeOption=none&SearchFields.DiscountCode=&DiscountCode=&SourcePage=Search&deals-link=&SearchFields.IsCalendar=false`

  let header = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://m.alaskaair.com",
    "referer": "https://m.alaskaair.com/shopping/?timeout=true",
    "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"
  }

  let agent = new HttpsProxyAgent(process.env.USER_ID)

  const raw = await fetch(url ,{
    method: "POST",
    headers: header,
    body: body,
    agent: agent
  })

  const resp = await raw.text()

  if (!raw.ok)
      throw new Error(resp)
  
  const flights = await standardizeResults(resp, date)
  return JSON.stringify(flights)

};