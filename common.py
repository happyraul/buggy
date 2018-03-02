
import functools as _ft


class _sel():
    from selenium.webdriver import Firefox, Chrome
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as expected
    from selenium.webdriver.support.wait import WebDriverWait


def get_driver(browser, height=1600, width=1600):
    """Create a chrome or firefox driver"""
    options_cls = getattr(_sel, f'{browser.capitalize()}Options')
    driver_cls = getattr(_sel, browser.capitalize())
    options = options_cls()
    options.add_argument('-headless')
    kwargs = {
        'executable_path': (
            'chromedriver' if browser.lower() == 'chrome' else 'geckodriver'
        ),
        f'{browser.lower()}_options': options
    }
    driver = driver_cls(**kwargs)
    driver.set_window_size(width, height)
    return driver


get_firefox_driver = _ft.partial(get_driver, 'firefox')
get_chrome_driver = _ft.partial(get_driver, 'chrome')


def send_keys(driver, value, id_=None, name=None, timeout=None, clear=False):
    """Send the value as input to the field identified by id_ or name.
    Optionally, wait for the input to become visible, and/or clear it first"""
    if timeout:
        wait = _sel.WebDriverWait(driver, timeout=timeout)
        selector = _sel.By.ID if id_ else _sel.By.NAME
        expectation = _sel.expected.visibility_of_element_located(
            (selector, id_ or name)
        )
        field = wait.until(expectation)
    else:
        if id_:
            field = driver.find_element_by_id(id_)
        else:
            field = driver.find_element_by_name(name)

    if clear:
        field.clear()
    field.send_keys(value)
