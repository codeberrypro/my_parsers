import csv
import atexit

from time import time, sleep
from proxy import proxies
from random import randint

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


def check_captcha(driver):
    try:
        captcha = driver.find_element(By.CLASS_NAME, 'sc-human-challenge-content')
        element = captcha.find_element(By.ID, 'px-captcha')
        sleep(2)
        print('captcha detected trying to solve...')
        action = ActionChains(driver)
        action.move_to_element_with_offset(element, randint(10, 30), randint(10, 30)).click_and_hold().perform()
        sleep(10)
        action.release(element)
        action.perform()
        sleep(0.2)
        action.release(element)
    except NoSuchElementException:
        # print('captcha not found')
        return True
    except Exception as ex:
        print(f'error while solving captcha {ex}')


def check_page_load(driver, delay, name, var='xpath', check_capt=True):
    try:
        if not check_captcha(driver) and check_capt:
            return False
        if var == 'xpath':
            my_elem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.XPATH, name)))
        elif var == 'class':
            my_elem = WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, name)))
        return True
    except TimeoutException:
        print('element not found (timeout)')
        return False
    except NoSuchElementException:
        print('element not found')
        return False


def write_to_file(data):
    with open('output.csv', 'a', newline='') as f:
        order = ['url', 'name', 'price_f', 'price_f1', 'variants_f', 'variants_f1']
        writer = csv.DictWriter(f, delimiter=';', fieldnames=order)
        writer.writerow(data)


def write_to_errors_file(url):
    print(f'посмотрите errors.txt')
    with open('errors.txt', 'a') as e_file:
        e_file.write(f'\n{url}')


def recreate_proxy_connection(driver, pr):
    driver.close()
    service_args = f'--proxy={proxies[pr].split("#")[0]} --proxy-auth={proxies[pr].split("#")[1]}' if proxies[pr] != '' else None
    # print(pr, service_args)
    return initialize_driver(options=service_args) if pr != None else initialize_driver()


def start(driver):
    success = 0
    errors = 0
    pr = prr = 0
    with open('file.txt') as file:
        lines = [line.strip() for line in file.readlines()]
        for line in range(len(lines)):
            try:
                print(f'[{line + 1}/{len(lines)} {format((line + 1) / (len(lines) / 100), ".1f")}%]  {lines[line]} [PROXY: {proxies[pr].split("#")[0]}]')
                driver.get(lines[line])
                # sleep(1)                      # SLOW DOWN PARSER

                for i in range(5):
                    if not check_page_load(driver, 3, "sc-pc-title-full-desktop", var='class'):
                        sleep(2)
                    else:
                        break
                else:
                    # Exit loop iteration when money is returned
                    errors += 1
                    write_to_errors_file(lines[line])
                    pr = randint(0, len(proxies) - 2)
                    if pr == prr: pr += 1
                    prr = pr
                    driver = recreate_proxy_connection(driver, pr)
                    continue
                name = driver.find_element(By.CLASS_NAME, 'sc-pc-title-full-desktop').text.split('\n')[1]
                try:
                    price = driver.find_element(By.CLASS_NAME, 'sc-pc-channel-price').text
                except NoSuchElementException:
                    print('price not found')
                    price = 'CURRENTPRICE:None#CURRENTPRICE:None#'
                if price != '':
                    price_f = [price.replace('\n', '#').replace(' ', '').replace(',', '').split('CURRENTPRICE:')[1].split('#')[0], price.replace('\n', '#').replace(' ', '').replace(',', '').split('CURRENTPRICE:')[-1].split('#')[0]]
                else:
                    price_f = ['', '']
                if price_f[0] == price_f[-1]:
                    price_f[-1] = ''
                try:
                    # Search field with options (upc)
                    for i in range(5):
                        if check_page_load(driver, 3, "sc-pc-variants", var='class', check_capt=False):
                            break
                    variants_box = driver.find_element(By.CLASS_NAME, 'sc-pc-variants')
                    variants_a = variants_box.find_elements(By.CLASS_NAME, 'variant')
                    variants_d = variants_box.find_elements(By.CLASS_NAME, 'variant-unavailable')
                    variants = []
                    for var in variants_a:
                        variants.append(var.text)
                    for var in variants_d:
                        if not var in variants_a:
                            variants.append(var.text)
                except NoSuchElementException:
                    variants = ['']
                if len(variants) == 0:
                    variants = ['']

                # Write to csv file
                variants_f = []
                for v in variants: variants_f.append(v)
                if len(variants_f) == 1: variants_f.append('')
                data = {'url': driver.current_url,
                        'name': name.replace(",", ""),
                        'price_f': price_f[0],
                        'price_f1': price_f[-1],
                        'variants_f': variants_f[0],
                        'variants_f1': variants_f[-1]}
                write_to_file(data)
                success += 1
            except Exception as ex:
                print(f'Ошибка при парсинге объекта ({ex})')
                write_to_errors_file(lines[line])
                errors += 1

            # Recreating a session with a new proxy
            pr = randint(0, len(proxies) - 2)
            if pr == prr: pr += 1
            prr = pr
            driver = recreate_proxy_connection(driver, pr)

    print(f'parsing end! succes:{success} errors:{errors} total:{success + errors}')
    exit(0)


def on_exit(_start_time: int, driver):
    pass


if __name__ == '__main__':
    start_time = time()
    try:
        drv = initialize_driver()
        # drv.close()
    except Exception as ex:
        print(f'Error while initializing selenium web driver (errmsg: {ex})')
        exit(1)
    atexit.register(on_exit, _start_time=int(start_time), driver=drv)
    try:
        start(drv)
    except Exception as ex:
        print(f'Error while running script (errmsg: {ex})')
        exit(2)