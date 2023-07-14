import time
from selenium.webdriver.common.keys import Keys

COMPANY = ' WhiteLilyStore'  # если не указан в амазон для физ лиц
PHONE_COMPANY = '18049640370'


def entry_data_katon(driver, *args):
    business_name = args[0]
    buyer_name = args[1]
    last_name = args[7]
    address_line = args[2]
    zip_code = args[3]
    phone = args[4]
    city = args[5]
    state = args[6]

    driver.get('https://www.katom.com/account/saved-shipping')

    time.sleep(4)
    form_first_name = driver.find_element_by_id('shipping_first_name').send_keys(buyer_name)
    time.sleep(1)
    form_last_name = driver.find_element_by_id('shipping_last_name').send_keys(last_name)
    time.sleep(1)
    form_address = driver.find_element_by_id('shipping_address').send_keys(address_line)
    time.sleep(1)
    form_zip_code = driver.find_element_by_id('shipping_zip').send_keys(zip_code)
    time.sleep(1)
    form_city = driver.find_element_by_id('shipping_city').send_keys(city)
    time.sleep(1)
    form_phone = driver.find_element_by_id('shipping_phone').send_keys(PHONE_COMPANY)
    time.sleep(1)

    print(f'Введите штат {state}')
    print(input('Введите штат...'))

    time.sleep(2)
    flat_click = driver.find_element_by_id('shipping_primary').click()
    time.sleep(2)
    button_save = driver.find_element_by_css_selector("button[type='submit']").click()
    time.sleep(6)
    print('-------katomMerx-----------------')
