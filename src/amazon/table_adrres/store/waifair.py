import time

COMPANY = ' WhiteLilyStore'
PHONE_COMPANY = ''


def store_authorization_wayfair(driver, login, password):
    """Authorization in the online store"""
    driver.get('https://www.wayfair.com/')
    input('Need to log in...')


def entry_data_wayfair(driver, *args):
    business_name = args[0]
    buyer_name = args[1]
    address_line = args[2]
    zip_code = args[3]

    driver.get('https://www.wayfair.com/session/secure/account/address_book?')
    time.sleep(3)

    form_name = driver.find_element_by_id('//*[@id="textInput-1"]').send_keys(buyer_name)
    time.sleep(1)
    form_company = driver.find_element_by_id('//*[@id="textInput-2"]').send_keys(buyer_name)
    time.sleep(1)
    form_address = driver.find_element_by_css_selector("label[for='textInput-2']").send_keys(address_line)
    time.sleep(1)
