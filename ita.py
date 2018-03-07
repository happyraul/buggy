
import decimal as _decimal
import functools as _ft
import re as _re

import common as _common


class Price():
    def __init__(self, price):
        pattern = _re.compile(r'^(?P<currency>[^\d]+)(?P<amount>.+)')
        self._price = price
        price = price.replace(',', '')
        match = _re.search(pattern, price)
        if match:
            self.currency = match.group('currency')
            self.amount = _decimal.Decimal(match.group('amount'))

    def __add__(self, other):
        assert self.currency == other.currency, 'Currency should be the same between prices.'
        return Price(f'{self.currency}{self.amount + other.amount}')

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            assert self.currency == other.currency, 'Currency should be the same between prices.'
            return self + other

    def __repr__(self):
        return f'{self.currency}{self.amount}'


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
    # driver.get_screenshot_as_file('000-ita-load.png')

    send_keys(origin, id_='cityPair-orig-0', timeout=7)
    click_suggestion(driver, origin)
    send_keys(destination, id_='cityPair-dest-0')
    click_suggestion(driver, destination)

    send_keys(departure_date, id_='cityPair-outDate-0')
    send_keys(return_date, id_='cityPair-retDate-0')

    driver.find_element_by_id('searchButton-0').click()
    print(f'Searching for `{origin}` to `{destination}` - '
          f'departing `{departure_date}`, returning `{return_date}`...')

    driver.get_screenshot_as_file('001-ita-search-begin.png')
    wait = _sel.WebDriverWait(driver, timeout=60)
    wait.until(lambda driver: not _sel.expected.visibility_of_element_located(
        (_sel.By.XPATH, '//div[contains(text(), "Searching for flights")]')
    )(driver))

    details = []
    divs = []
    for idx in range(1):
        driver.get_screenshot_as_file('003-ita-before-details-click.png')
        button = get_buttons(driver)[idx]
        price = button.text
        print(f'Retrieving itinerary details for `{price}`...')
        button.click()

        wait.until(
            lambda driver: not _sel.expected.visibility_of_element_located((
                _sel.By.XPATH,
                '//div[contains(text(), "Retrieving itinerary details")]'
            ))(driver))

        driver.get_screenshot_as_file(f'004-ita-{idx}-details.png')
        div, parsed = parse_details(driver)
        parsed['price'] = Price(price)
        details.append(parsed)
        divs.append(div)
        return driver, divs, details
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

    details = driver.find_element_by_xpath(
        '//div[contains(text(), "How to buy this ticket")]/'
        'following-sibling::div/following-sibling::div/table/tbody/tr/td/'
        'table/tbody/tr/following-sibling::tr/td/table/tbody'
    )

    base_fares = parse_base_fares(details)
    fat = parse_fat(details)

    fare = dict(base_fares=base_fares, base_fare_total=sum(fare['price'] for fare in base_fares),
                fat=fat, fat_total=sum(surcharge['price'] for surcharge in fat))

    return details_div, {'out': out, 'return': return_, 'fare': fare}


def parse_base_fares(details):
    base_fares = []
    for tr in details.find_elements_by_xpath('tr'):
        if tr and '(rules)' in tr.text:
            description = [
                part.text for part in tr.find_elements_by_xpath('td/table//td')
            ]
            base_fares.append(dict(
                description=', '.join(description),
                price=Price(tr.find_element_by_xpath('td/div').text)
            ))
    return base_fares


def parse_fat(details):
    surcharges = []
    for tr in details.find_elements_by_xpath('tr'):
        if tr and ('(YQ)' in tr.text or '(YR)' in tr.text):
            description, price = tr.text.split('\n')
            surcharges.append(dict(description=description, price=Price(price)))
    return surcharges


def parse_leg(leg):
    rows = leg.find_elements_by_tag_name('tr')
    segments = []
    data = {}

    for row in rows:
        if 'flight' not in data:
            data.update(parse_route(row))
            data.update(parse_schedule(row))
        elif is_route(row):
            segments.append(data)
            data = {}
            data.update(parse_route(row))
        else:
            data.update(parse_layover(row))
    segments.append(data)

    return segments


def is_route(row):
    pattern = _re.compile(
        '^.+\((?P<origin>[A-Z]{3})\).+\((?P<destination>[A-Z]{3})\)'
    )
    route = row.find_element_by_tag_name('div').text
    return _re.search(pattern, route)


def parse_route(row):
    data = {}
    match = is_route(row)
    if match:
        data['origin'] = match.group('origin')
        data['destination'] = match.group('destination')
    return data


def parse_schedule(row):
    parsed = {}
    data = [td.text for td in row.find_elements_by_tag_name('td') if td.text]
    if len(data) == 6:
        flight, depart, arrive, duration, aircraft, booking_code = data
        parsed.update(dict(
            flight=flight,
            depart=depart.split('Dep: ')[1],
            arrive=arrive.split('Arr: ')[1],
            duration=duration,
            aircraft=aircraft,
            booking_code=booking_code,
        ))
    return parsed


def parse_layover(row):
    parsed = {}
    if is_layover(row.text):
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
        parsed['layover'] = {key: value}
    return parsed


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
