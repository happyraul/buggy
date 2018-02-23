
class _sel():
    from selenium.webdriver import Firefox
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.firefox.options import Options
    from selenium.webdriver.support import expected_conditions as expected
    from selenium.webdriver.support.wait import WebDriverWait


def get_driver():
    options = _sel.Options()
    options.add_argument('-headless')
    driver = _sel.Firefox(executable_path='geckodriver', firefox_options=options)
    return driver


def search(origin, destination, departure_date, return_date):
    print('Creating driver...')
    driver = get_driver()
    url = 'https://matrix.itasoftware.com/'
    print(f'Loading {url}...')
    driver.get(url)

    send_keys(driver, 'cityPair-orig-0', origin, timeout=5)
    click_suggestion(driver, origin)
    send_keys(driver, 'cityPair-dest-0', destination)
    click_suggestion(driver, destination)

    send_keys(driver, 'cityPair-outDate-0', departure_date)
    send_keys(driver, 'cityPair-retDate-0', return_date)

    driver.find_element_by_id('searchButton-0').click()
    print(f'Searching for {origin} to {destination} - '
          f'departing {departure_date}, returning {return_date}...')

    wait = _sel.WebDriverWait(driver, timeout=60)
    wait.until(lambda driver: not _sel.expected.visibility_of_element_located(
        (_sel.By.CLASS_NAME, 'IR6M2QD-n-c')
    )(driver))
    driver.get_screenshot_as_file('01-search-end.png')

    return driver


def send_keys(driver, id_, value, timeout=None):
    if timeout:
        wait = _sel.WebDriverWait(driver, timeout=timeout)
        expectation = _sel.expected.visibility_of_element_located((_sel.By.ID, id_))
        field = wait.until(expectation)
    else:
        field = driver.find_element_by_id(id_)

    field.send_keys(value)


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
    search('BOS', 'AMS', '03/14/2018', '03/25/2018')
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