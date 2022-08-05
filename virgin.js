import playwright from 'playwright-aws-lambda'
import { addExtra } from 'playwright-extra'
import StealthPlugin from 'puppeteer-extra-plugin-stealth'

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
  
  const standardizeResults = (trip) => {
    let results = []
    return results
  }

export const virginFunc = async(origin, destination, date) => {
    let browser = null;
    let flights = []
    browser = addExtra(await playwright.launchChromium(
        {
            headless:true,
            proxy: {
                "server": 'http://geo.iproyal.com:22323',
                "username": 'itsjafer',
                "password": 'jafer123_country-us_session-pscq2ptc_lifetime-30m'
            }
        }));
    browser.use(StealthPlugin())

    const context = await browser.newContext({
        userAgent:"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
        viewport: { 'width': 1920, 'height': 1080 }
    });

    const page = await context.newPage();

    await page.goto('https://www.virginatlantic.com/in/en')

    let formatted_date = `${date.substring(5,7)}/${date.substring(8,10)}/${date.substring(0,4)}`

    await page.locator("#fromAirportName span.airport-code.d-block").click()
    await page.locator("#search_input").fill(origin)
    await page.locator(".airportLookup-list .airport-code").first().click()

    await page.locator("#toAirportName span.airport-code.d-block").click()
    await page.locator("#search_input").fill(destination)
    await page.locator(".airportLookup-list .airport-code").first().click()

    await page.locator("#chkFlexDate").evaluate(node => node.removeAttribute('visibleLabel'))
    await page.click("#selectTripType-val")
    await page.locator("#ui-list-selectTripType1").click()

    await page.locator("#calDepartLabelCont").click()
    await page.waitForSelector(".dl-datepicker-calendar")

    let tries = 0
    while (true) {
        if (tries == 9) {
            return []
        }
        tries += 1
        if (!await page.isVisible(`a[data-date^='${formatted_date}']`)) {
            await page.locator("a[aria-label='Next']:not([class*='no-next'])").click()
            continue
        }
        await page.locator(`a[data-date^='${formatted_date}']`).click()
        break
    }

    await page.locator("button.donebutton").click()
    await page.waitForSelector(`div[class*='calDispValueCont']:not([class*='open'])`)

    await page.locator('#adv-search').click()
    await page.waitForSelector("#milesLabel")
    await page.locator("#milesLabel").click({force:true})
    await page.locator("#chkFlexDate").evaluate(node => node.removeAttribute('disabled'))
    await page.locator("#chkFlexDate").uncheck({force: true})
    await page.screenshot({path: "screenshot1.png"})


    tries = 0
    while (true) {
        if (tries == 2) {
            console.log(tries)
            return []
        }
        try {
            await page.screenshot({path: "screenshot.png"})
            await page.locator("#btnSubmit").click()
            let response_info = await page.waitForResponse(response => response.url().includes("shop/ow/search") && response.request().method() === "POST")
            console.log(await response_info.text())

            const rawResponse = await response_info.json()
            console.log(rawResponse)
            flights = standardizeResults(rawResponse)
            break
        } catch (e) {
            console.log(e)
            tries += 1
        }
    }
    return JSON.stringify(flights)

}

await virginFunc("LHR", "JFK", "2022-09-01")