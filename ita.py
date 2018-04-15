
import decimal as _decimal
import functools as _ft
import re as _re
import typing as _typing

import common as _common


short_flights = {
    'MAD': ['MAD', 'XTI', 'XOC', 'GDU', 'XOU', 'OLT', 'AVS', 'CEJ', 'XIV',
            'XJN'],
    'SYD': ['WOL', 'NTL', 'BHS', 'OAG', 'DGE', 'CBR', 'MYA', 'TRO', 'DBO',
            'TMW', 'PQQ'],
    'KUL': ['SZB', 'MKZ', 'DUM', 'KUA', 'IPH', 'JHB', 'PKU', 'KTE', 'AEG',
            'SIN', 'DTB', 'BTH', 'PEN', 'KNO', 'TGG', 'FLZ', 'TNJ', 'KBR',
            'AOR', 'NAW', 'PDG', 'LGK', 'GNS', 'HDY', 'MWK', 'DJB', 'KRC',
            'TST', 'TXE', 'LSW', 'MEQ', 'KBV', 'NST', 'HKT', 'PLM', 'PGK',
            'BKS', 'NTX', 'BTJ', 'URT', 'PXA', 'USM', 'SBG']
}


class Query(_typing.NamedTuple):
    """ITA search query"""
    origin: str
    destination: str
    departure_date: str
    return_date: str


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
        assert self.currency == other.currency, \
            'Currency should be the same between prices.'
        return Price(f'{self.currency}{self.amount + other.amount}')

    def __sub__(self, other):
        assert self.currency == other.currency, \
            'Currency should be the same between prices.'
        return Price(f'{self.currency}{self.amount - other.amount}')

    def __truediv__(self, other):
        assert self.currency == other.currency, \
            'Currency should be the same between prices.'
        return self.amount / other.amount

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            assert self.currency == other.currency, \
                'Currency should be the same between prices.'
            return self + other

    def __repr__(self):
        return f'{self.currency}{self.amount}'


class _sel():
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as expected
    from selenium.webdriver.support.wait import WebDriverWait


def multi_city_search(query, num_details=1, driver=None):
    if driver is None:
        print('Creating driver...')
        driver = _common.get_firefox_driver(width=1280)
    send_keys = _ft.partial(_common.send_keys, driver)
    click = _ft.partial(_common.click, driver)

    url = 'https://matrix.itasoftware.com/'
    print(f'Loading `{url}`...')
    driver.get(url)
    driver.get_screenshot_as_file('000-ita-load.png')

    click(xpath='//div[contains(text(), "Multi-city")]', timeout=7)
    click(xpath='//a[contains(text(), "Add another flight")]')

    # input itinerary
    send_keys(query.origin, xpath=(
        '//div[contains(text(), "Flight 1")]'
        '/parent::div'
        '/following-sibling::div'
        '//input'))
    click_suggestion(driver, query.origin)
    driver.get_screenshot_as_file('001-ita-mc-origin.png')

    send_keys(query.destination, xpath=(
        '//div[contains(text(), "Flight 1")]'
        '/parent::div'
        '/following-sibling::div'
        '/following-sibling::div'
        '/following-sibling::div'
        '//input'))
    click_suggestion(driver, query.destination)
    driver.get_screenshot_as_file('002-ita-mc-dest.png')

    # send_keys(query.destination, xpath=(
    #     '//div[contains(text(), "Flight 2")]'
    #     '/parent::div'
    #     '/following-sibling::div'
    #     '//input'))
    # click_suggestion(driver, query.destination)
    # driver.get_screenshot_as_file('003-ita-mc-return-origin.png')

    send_keys(query.origin, xpath=(
        '//div[contains(text(), "Flight 2")]'
        '/parent::div'
        '/following-sibling::div'
        '/following-sibling::div'
        '/following-sibling::div'
        '//input'))
    click_suggestion(driver, query.origin)
    driver.get_screenshot_as_file('005-ita-mc-input.png')

    # driver.close()

    return driver


def search(origin, destination, departure_date, return_date, num_details=5,
           driver=None):
    if driver is None:
        print('Creating driver...')
        driver = _common.get_firefox_driver(width=1280)
    send_keys = _ft.partial(_common.send_keys, driver)
    click = _ft.partial(_common.click, driver)

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

    click(id_='searchButton-0')

    print(f'Searching for `{origin}` to `{destination}` - '
          f'departing `{departure_date}`, returning `{return_date}`...')

    driver.get_screenshot_as_file('001-ita-search-begin.png')
    wait = _sel.WebDriverWait(driver, timeout=60)
    try:
        wait.until(
            lambda driver: not _sel.expected.visibility_of_element_located((
                _sel.By.XPATH,
                '//div[contains(text(), "Searching for flights")]'
            ))(driver))
    except Exception:
        driver.get_screenshot_as_file('xxx-ita-timeout.png')
        raise

    buttons = get_buttons(driver)
    limit = min(len(buttons) - 1, num_details)
    print(f'Gonna get details for `{limit}` itineraries')

    details = []
    divs = []
    for idx in range(limit):
        driver.get_screenshot_as_file('003-ita-before-details-click.png')
        button = get_buttons(driver)[idx]
        price = button.text
        print(f'Retrieving itinerary details for `{price}`...')
        button.click()
        try:
            wait.until(
                lambda driver: not _sel.expected.visibility_of_element_located((
                    _sel.By.XPATH,
                    '//div[contains(text(), "Retrieving itinerary details")]'
                ))(driver)
            )
        except Exception:
            driver.get_screenshot_as_file('xxx-ita-timeout.png')
            raise

        driver.get_screenshot_as_file(f'004-ita-{idx}-details.png')
        div, parsed = parse_details(driver, Price(price))
        parsed['price'] = Price(price)
        details.append(parsed)
        divs.append(div)
        driver.back()
        try:
            wait.until(
                lambda driver: not _sel.expected.visibility_of_element_located((
                    _sel.By.XPATH,
                    '//div[contains(text(), "Updating flight info")]'
                ))(driver)
            )
        except Exception:
            driver.get_screenshot_as_file('xxx-ita-timeout.png')
            raise

    return driver, divs, details


def get_buttons(driver):
    return [button
            for button in driver.find_elements_by_xpath('//div/button/span')
            if button.text]


def parse_details(driver, price):
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

    fare = dict(base_fares=base_fares,
                base_fare_total=sum(fare['price'] for fare in base_fares),
                fat=fat,
                fat_total=sum(surcharge['price'] for surcharge in fat))

    fare['other_total'] = price - fare['base_fare_total'] - fare['fat_total']
    fare['best_possible'] = fare['base_fare_total'] + fare['other_total']

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
            surcharges.append(dict(description=description,
                                   price=Price(price)))
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


def find_candidate_fares(num_details=5):
    destinations = [
        'ATL',  # Atlanta, GA
        'LAX',  # Los Angeles, CA
        'ORD',  # Chicago, IL
        'DFW',  # Dallas/Fort Worth, TX
        'JFK',  # New York, NY
        'DEN',  # Denver, CO
        'SFO',  # San Francisco, CA
        'LAS',  # Las Vegas, NV
        'CLT',  # Charlotte, NC
        'SEA',  # Seattle/Tacoma, WA
        'PHX',  # Phoenix, AZ
        'MIA',  # Miami, FL
        'MCO',  # Orlando, FL
        'IAH',  # Houston, TX
        'EWR',  # Newark, NJ
        'MSP',  # Minneapolis/St. Paul, MN
        'BOS',  # Boston, MA
        'DTW',  # Detroit, MI
        'PHL',  # Philadelphia, PA
        'LGA',  # New York, NY
        'FLL',  # Fort Lauderdale, FL
        'BWI',  # Baltimore, MD/Washington, D.C.
        'DCA',  # Washington, D.C.
        'SLC',  # Salt Lake City, UT
        'MDW',  # Chicago, IL
        'IAD',  # Washington, D.C.
        'SAN',  # San Diego, CA
        'HNL',  # Honolulu, HI
        'TPA',  # Tampa, FL
        'PDX',  # Portland, OR
        'DAL',  # Dallas, TX
        'STL',  # St. Louis, MO
        'LIH',  # Lihue, HI
    ]

    origins = [
        'MUC',  # Munich
        'FRA',  # Frankfurt
        'DUS',  # Düsseldorf
        'TXL',  # Berlin
        'HAM',  # Hamburg
        'SXF',  # Berlin
        'CGN',  # Cologne/Bonn
        'STR',  # Stuttgart
    ]

    driver = _common.get_firefox_driver(width=1280)
    details = []
    for origin in origins:
        for destination in destinations:
            try:
                details.extend(search(origin, destination, '12/19/2018',
                                      '01/04/2019', num_details=num_details,
                                      driver=driver)[2])
            except Exception:
                continue

    return details


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
