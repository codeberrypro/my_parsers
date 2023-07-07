import time
from selenium.webdriver.common.keys import Keys

COMPANY = ' WhiteLilyStore'
PHONE_COMPANY = ''


def store_authorization_webstaurantstore(driver, login, password):
    driver.get('https://www.webstaurantstore.com/myaccount/')
    time.sleep(4)
    except_button = driver.find_element_by_xpath('//*[@id="gdprBannerMount"]/div/div/div/div[3]/button').click()
    login = driver.find_element_by_id('email').send_keys(login)
    time.sleep(1)
    password = driver.find_element_by_id('password').send_keys(password)
    time.sleep(1)
    click = driver.find_element_by_id('the_login_button').click()


def entry_data_webstaurantstore(driver, *args):
    login = args[0]
    password = args[1]
    business_name = args[0]
    buyer_name = args[1]
    address_line = args[2]
    zip_code = args[3]
    phone = args[4]

    driver.get('https://www.webstaurantstore.com/myaccount/shipping/?returnUrl=')
    html = driver.find_element_by_tag_name('html')
    for i in range(10):
        html.send_keys(Keys.DOWN)

    time.sleep(1)
    form_name = driver.find_element_by_id('fullShipName').send_keys(buyer_name)
    time.sleep(1)
    form_company = driver.find_element_by_id('shipcompany').send_keys(business_name)
    time.sleep(1)
    form_address = driver.find_element_by_id('shipaddr').send_keys(address_line)
    time.sleep(1)
    form_zip_code = driver.find_element_by_id('shipzip').send_keys(zip_code)
    time.sleep(1)
    form_phone = driver.find_element_by_id('wholeShipPhoneNumber').send_keys(PHONE_COMPANY)
    time.sleep(3)
    button_save = driver.find_element_by_id('ship_save_info_button').click()
    print('-------WebRestMerx-----------------')
