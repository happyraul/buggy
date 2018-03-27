
import datetime as _dt
import decimal as _decimal
import functools as _ft
import operator as _op
import typing as _typing

import common as _common


class _sel():
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as expected
    from selenium.webdriver.support.wait import WebDriverWait


# destinations = [
#     # ('Berlin', _dt.timedelta(seconds=60 * 60 * 5)),
#     ('Aachen', _dt.timedelta(seconds=60 * 60 * 6), ),
#     # ('Hamburg', _dt.timedelta(seconds=60 * 60 * 7)),
# ]


class Query(_typing.NamedTuple):
    destination: str
    departure: str
    duration_limit: _dt.timedelta = None
    origin: str = 'Munich'
    latest_arrival: _dt.time = None


queries = [
    # Query(
    #     destination='Aachen', departure=_dt.datetime(2018, 4, 18, 18),
    #     duration_limit=_dt.timedelta(seconds=60 * 60 * 6),
    #     latest_arrival=_dt.datetime(2018, 4, 19, 2)
    # ),

    Query(
        destination='Aachen', departure=_dt.datetime(2018, 4, 12, 18),
        duration_limit=_dt.timedelta(seconds=60 * 60 * 6),
        latest_arrival=_dt.datetime(2018, 4, 13, 2)
    ),

    Query(
        destination='Aachen', departure=_dt.datetime(2018, 4, 19, 18),
        duration_limit=_dt.timedelta(seconds=60 * 60 * 6),
        latest_arrival=_dt.datetime(2018, 4, 20, 2)
    ),
]


# travel_dates = [
#     # '08.04.2018',
#     '15.04.2018',
# ]

# class Duration(_dt.timedelta):
#
#     def __new__(cls, *args, **kwargs):
#         _dt.timedelta.
#
#     def __repr__(self):
#         return str(self)


def search(query, driver=None, best=False):
    if driver is None:
        print('Creating driver...')
        driver = _common.get_chrome_driver()

    send_keys = _ft.partial(_common.send_keys, driver)

    print('Getting bahn.de...')
    driver.get('https://bahn.de')
    send_keys(query.origin, id_='js-auskunft-autocomplete-from', timeout=6)
    send_keys(query.destination, id_='js-auskunft-autocomplete-to')
    driver.find_element_by_id('0').click()

    if query.departure:
        send_keys(query.departure.strftime('%d.%m.%Y'), name='date',
                  clear=True)
        driver.get_screenshot_as_file('000-db.png')
        driver.find_element_by_id('js-auskunft-autocomplete-from').click()
        time_field = driver.find_element_by_name('time')
        for _ in range(5):
            time_field.send_keys(_sel.Keys.BACK_SPACE)
        driver.get_screenshot_as_file('000-db-back.png')
        send_keys(query.departure.strftime('%H:%M'), name='time')

    print(f'Submitting search for `{query.destination}`...')
    driver.get_screenshot_as_file('001-db.png')
    driver.find_element_by_class_name('js-submit-btn').click()
    driver.get_screenshot_as_file('002-db.png')

    print('Waiting for page to load...')
    wait = _sel.WebDriverWait(driver, timeout=15)
    later_btn = wait.until(_sel.expected.visibility_of_element_located(
        (_sel.By.CLASS_NAME, 'later')
    ))
    results = driver.find_element_by_class_name('resultContentHolder')
    for i in range(3):
        later_btn = driver.find_element_by_class_name('later')
        # with open(f'00{i}-db-search-results.png', 'wb') as file:
        #     file.write(results.screenshot_as_png())

        later_btn.click()

    driver.get_screenshot_as_file('003-db.png')

    results = []
    for result in driver.find_elements_by_class_name('boxShadow'):
        if has_price(result):
            results.append(dict(
                departure_time=parse_time(result.find_element_by_xpath(
                    "tr[@class='firstrow']/td[@class='time']"
                ).text.strip(), query.departure),

                arrival_time=parse_time(result.find_element_by_xpath(
                    "tr[@class='last']/td[@class='time']"
                ).text.strip(), query.departure),

                duration=parse_duration(result),
                price=parse_price(result)
            ))

    if query.latest_arrival:
        results = [result for result in results
                   if result['arrival_time'] < query.latest_arrival]

    if query.duration_limit:
        results = [result for result in results
                   if result['duration'] < query.duration_limit]

    results = [
        dict(result, departure_time=str(result['departure_time']),
             duration=str(result['duration']),
             arrival_time=str(result['arrival_time'])) for result in results
    ]

    if best:
        results = sorted(results, key=_op.itemgetter('price'))[0]

    return driver, results


def parse_time(time, departure):
    """turn string time into python time"""
    hour, minute = map(int, time.split(':'))
    day = departure.day if hour >= departure.hour else departure.day + 1
    return _dt.datetime(departure.year, departure.month, day, hour, minute)


def parse_duration(result):
    """turn string duration into python timedelta"""
    duration = result.find_element_by_xpath(
        "tr[@class='firstrow']/td[contains(@class, 'duration') "
        "and contains(@class, 'lastrow')]"
    ).text.strip()
    hours, minutes = map(int, duration.split(':'))
    return _dt.timedelta(seconds=60 * 60 * hours + 60 * minutes)


def parse_price(result):
    prices = [
        price.text.strip() for price in
        result.find_elements_by_class_name('fareOutput')
    ]
    return min(
        _decimal.Decimal(price.split(' EUR')[0].replace(',', '.'))
        for price in prices
    )


def has_price(result):
    return bool(result.find_elements_by_class_name('fareOutput'))


def best_price():
    results = {}
    driver = _common.get_chrome_driver()
    for query in queries:
        _, result = search(query, best=True, driver=driver)
        if query.destination not in results or \
                results[query.destination]['price'] > result['price']:
            results[query.destination] = result
            results[query.destination]['date'] = query.departure
    return results


if __name__ == '__main__':
    print(best_price())
