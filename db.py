
import datetime as _dt
import decimal as _decimal
import functools as _ft
import operator as _op

import common as _common


class _sel():
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as expected
    from selenium.webdriver.support.wait import WebDriverWait


destinations = [
    # ('Berlin', _dt.timedelta(seconds=60 * 60 * 5)),
    ('Aachen', _dt.timedelta(seconds=60 * 60 * 6)),
    # ('Hamburg', _dt.timedelta(seconds=60 * 60 * 7)),
]

travel_dates = [
    # '08.04.2018',
    '15.04.2018',
]


def search(origin, destination, departure_date=None, driver=None, best=False,
           duration_limit=None):
    if driver is None:
        print('Creating driver...')
        driver = _common.get_chrome_driver()

    send_keys = _ft.partial(_common.send_keys, driver)

    print('Getting bahn.de...')
    driver.get('https://bahn.de')
    send_keys(origin, id_='js-auskunft-autocomplete-from', timeout=6)
    send_keys(destination, id_='js-auskunft-autocomplete-to')
    driver.find_element_by_id('0').click()

    if departure_date:
        send_keys(departure_date, name='date', clear=True)
        driver.get_screenshot_as_file('000-db.png')
        driver.find_element_by_id('js-auskunft-autocomplete-from').click()
        time_field = driver.find_element_by_name('time')
        for _ in range(5):
            time_field.send_keys(_sel.Keys.BACK_SPACE)
        driver.get_screenshot_as_file('000-db-back.png')
        send_keys('14:00', name='time')

    print(f'Submitting search for `{destination}`...')
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
                departure_time=result.find_element_by_xpath(
                    "tr[@class='firstrow']/td[@class='time']").text.strip(),
                duration=parse_duration(result),
                price=parse_price(result)
            ))

    if duration_limit:
        results = [result for result in results
                   if result['duration'] < duration_limit]

    # FIXME: how to fix the duration so its readable
    # results = [
    #     dict(**result, duration=str(result['duration'])) for result in results
    # ]

    if best:
        results = sorted(results, key=_op.itemgetter('price'))[0]

    return driver, results


def parse_duration(result):
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
    print()
    return min(
        _decimal.Decimal(price.split(' EUR')[0].replace(',', '.'))
        for price in prices
    )


def has_price(result):
    return bool(result.find_elements_by_class_name('fareOutput'))


def best_price():
    results = {}
    driver = _common.get_chrome_driver()
    for destination, duration_limit in destinations:
        for date in travel_dates:
            _, result = search('Munich', destination, departure_date=date,
                               best=True, driver=driver,
                               duration_limit=duration_limit)
            if destination not in results or \
                    results[destination]['price'] > result['price']:
                results[destination] = result
                results[destination]['date'] = date
    return results
