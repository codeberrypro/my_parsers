import time

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException


def initialize_driver(options=False):
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(argument=options)
    driver = webdriver.Chrome(options=chrome_options)
    return driver


if __name__ == '__main__':
    start_time = time()
    try:
        drv = initialize_driver()
        # drv.close()
    except Exception as ex:
        print(f'Error while initializing selenium web driver (errmsg: {ex})')
        exit(1)
