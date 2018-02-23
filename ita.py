
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
    wait = _sel.WebDriverWait(driver, timeout=60)
    return driver, wait


def search(origin, destination, departure_date, return_date):
	driver, wait = get_driver()
	url = 'https://matrix.itasoftware.com/'
	driver.get(url)

	send_keys(wait, 'cityPair-orig-0', origin)
	click_suggestion(origin, wait)
	driver.get_screenshot_as_file('01-origin.png')

	send_keys(wait, 'cityPair-dest-0', destination)
	click_suggestion(destination, wait)
	driver.get_screenshot_as_file('02-destination.png')

	send_keys(wait, 'cityPair-outDate-0', departure_date)
	driver.get_screenshot_as_file('03-dep-date.png')
	send_keys(wait, 'cityPair-retDate-0', return_date)
	driver.get_screenshot_as_file('04-ret-date.png')

	wait.until(_sel.expected.visibility_of_element_located(
		(_sel.By.ID, 'searchButton-0')
	)).click()
	driver.get_screenshot_as_file('05-search-start.png')

	wait.until(lambda driver: not _sel.expected.visibility_of_element_located(
		(_sel.By.CLASS_NAME, 'IR6M2QD-n-c')
	)(driver))
	driver.get_screenshot_as_file('06-search-end.png')

	driver.get_screenshot_as_file('07-matrix.png')
	return driver, wait


def send_keys(wait, id_, value):
	wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, id_))).send_keys(value)


def click_suggestion(input_, wait):
	suggestions = wait.until(_sel.expected.visibility_of_element_located(
		(_sel.By.CLASS_NAME, 'gwt-SuggestBoxPopup')
	))

	for suggestion in suggestions.find_elements_by_class_name('item'):
		if f'({input_})' in suggestion.text:
			suggestion.click()
			break

if __name__ == "__main__":
    options = _sel.Options()
    options.add_argument('-headless')
    driver = _sel.Firefox(executable_path='geckodriver', firefox_options=options)
    wait = _sel.WebDriverWait(driver, timeout=10)
    driver.get('https://www.google.com/')
    wait.until(_sel.expected.visibility_of_element_located((_sel.By.NAME, 'q'))).send_keys(
    	'headless firefox' + _sel.Keys.ENTER
    )
    wait.until(_sel.expected.visibility_of_element_located((_sel.By.CSS_SELECTOR, '#ires a'))).click()
    print(driver.page_source[:60])
    driver.quit()

    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, 'cityPair-orig-0'))).send_keys('BOS')
    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, 'cityPair-dest-0'))).send_keys('AMS')
    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, 'cityPair-outDate-0'))).send_keys('03/06/2018')
    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, 'cityPair-retDate-0'))).send_keys('03/20/2018')
    # wait.until(_sel.expected.visibility_of_element_located((_sel.By.ID, 'cityPair-retDate-0'))).send_keys(_sel.Keys.ENTER)