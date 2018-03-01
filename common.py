
import functools as _ft


class _sel():
    from selenium.webdriver import Firefox, Chrome
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    from selenium.webdriver.support import expected_conditions as expected
    from selenium.webdriver.support.wait import WebDriverWait


def get_driver(browser):
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
    driver.set_window_size(1600, 1600)
    return driver


get_firefox_driver = _ft.partial(get_driver, 'firefox')
get_chrome_driver = _ft.partial(get_driver, 'chrome')
