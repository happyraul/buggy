
import functools as _ft
import re as _re

import common as _common


class _sel():
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as expected
    from selenium.webdriver.support.wait import WebDriverWait


def search(origin, destination, departure_date, return_date, driver=None):
    if driver is None:
        print('Creating driver...')
        driver = _common.get_firefox_driver(width=1280)
    send_keys = _ft.partial(_common.send_keys, driver)

    url = 'https://matrix.itasoftware.com/'
    print(f'Loading `{url}`...')
    driver.get(url)
    driver.get_screenshot_as_file('000-ita-load.png')
    # return driver, '', ''

    send_keys(origin, id_='cityPair-orig-0', timeout=7)
    click_suggestion(driver, origin)
    send_keys(destination, id_='cityPair-dest-0')
    click_suggestion(driver, destination)

    send_keys(departure_date, id_='cityPair-outDate-0')
    send_keys(return_date, id_='cityPair-retDate-0')

    driver.find_element_by_id('searchButton-0').click()
    print(f'Searching for `{origin}` to `{destination}` - '
          f'departing `{departure_date}`, returning `{return_date}`...')

    # driver.get_screenshot_as_file('001-search-begin.png')
    wait = _sel.WebDriverWait(driver, timeout=60)
    wait.until(lambda driver: not _sel.expected.visibility_of_element_located(
        (_sel.By.XPATH, '//div[contains(text(), "Searching for flights")]')
    )(driver))
    # driver.get_screenshot_as_file('002-search-end.png')

    details = []
    divs = []
    for idx in range(1):
        button = get_buttons(driver)[idx]
        price = button.text
        print(f'Retrieving itinerary details for `{price}`...')
        button.click()

        wait.until(
            lambda driver: not _sel.expected.visibility_of_element_located((
                _sel.By.XPATH,
                '//div[contains(text(), "Retrieving itinerary details")]'
            ))(driver))

        driver.get_screenshot_as_file(f'003-{idx}-details.png')
        div, parsed = parse_details(driver)
        parsed['price'] = price
        details.append(parsed)
        divs.append(div)
        driver.back()

        wait.until(
            lambda driver: not _sel.expected.visibility_of_element_located((
                _sel.By.XPATH,
                '//div[contains(text(), "Updating flight info")]'
            ))(driver)
        )
    return driver, divs, details


def get_buttons(driver):
    return [button
            for button in driver.find_elements_by_xpath('//div/button/span')
            if button.text]


def parse_details(driver):
    details_div = driver.find_element_by_xpath(
        '//div[contains(text(), "Itinerary")]/following-sibling::div'
    )
    out, return_ = map(parse_leg,
                       details_div.find_elements_by_tag_name('table'))
    return details_div, {'out': out, 'return': return_}


def parse_leg(leg):
    pattern = _re.compile(
        '^.+\((?P<origin>[A-Z]{3})\).+\((?P<destination>[A-Z]{3})\)'
    )
    rows = leg.find_elements_by_tag_name('tr')[1:]
    segments = []
    for segment in [iter(rows[i:i + 3]) for i in range(0, len(rows), 3)]:
        route = next(segment).find_element_by_tag_name('div').text
        match = _re.search(pattern, route)
        data = {}
        if match:
            data['origin'] = match.group('origin')
            data['destination'] = match.group('destination')

        data.update(parse_schedule(next(segment)))
        extra = next(segment, None)
        if extra and is_layover(extra.text):
            data['layover'] = parse_layover(extra)
        segments.append(data)
    return segments


def parse_schedule(row):
    flight, depart, arrive, duration, aircraft, booking_code = [
        td.text for td in row.find_elements_by_tag_name('td') if td.text
    ]
    return dict(
        flight=flight,
        depart=depart.split('Dep: ')[1],
        arrive=arrive.split('Arr: ')[1],
        duration=duration,
        aircraft=aircraft,
        booking_code=booking_code,
    )


def parse_layover(row):
    layover = iter([
        td.text for td in row.find_elements_by_tag_name('td') if td.text
    ])
    data = next(layover)
    while data:
        if is_layover(data):
            key = data.split('Layover in ')[1]
        else:
            value = data
        data = next(layover, None)
    return {key: value}


def is_layover(row):
    return row and 'Layover' in row


def click_suggestion(driver, input_):
    wait = _sel.WebDriverWait(driver, timeout=5)
    suggestions = wait.until(_sel.expected.visibility_of_element_located(
        (_sel.By.CLASS_NAME, 'gwt-SuggestBoxPopup')
    ))

    for suggestion in suggestions.find_elements_by_class_name('item'):
        if f'({input_})' in suggestion.text:
            suggestion.click()
            break


if __name__ == "__main__":
    import pprint as _pp
    _, _, details = search('BOS', 'FRA', '03/14/2018', '03/25/2018')
    _pp.pprint(details)
    # options = _sel.Options()
    # options.add_argument('-headless')
    # driver = _sel.Firefox(executable_path='geckodriver', firefox_options=options)
    # wait = _sel.WebDriverWait(driver, timeout=10)
    # driver.get('https://www.google.com/')
    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.NAME, 'q'))).send_keys(
    #   'headless firefox' + _sel.Keys.ENTER
    # )
    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.CSS_SELECTOR, '#ires a'))).click()
    # print(driver.page_source[:60])
    # driver.quit()

    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, 'cityPair-orig-0'))).send_keys('BOS')
    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, 'cityPair-dest-0'))).send_keys('AMS')
    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, 'cityPair-outDate-0'))).send_keys('03/06/2018')
    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, 'cityPair-retDate-0'))).send_keys('03/20/2018')
    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, 'cityPair-retDate-0'))).send_keys(_sel.Keys.ENTER)
