import time
from selenium.webdriver.common.keys import Keys

COMPANY = ' WhiteLilyStore'
PHONE_COMPANY = ''


def entry_data_target(driver, *args):
    # https://www.target.com/account/addresses/new
    buyer_name = args[1]
    last_name = args[7]
    address_line = args[2]
    zip_code = args[3]

    driver.get('https://www.target.com/account/addresses/new')
    time.sleep(4)
    form_zip_code = driver.find_element_by_id('zip_code').send_keys(zip_code)
    time.sleep(1)
    form_first_name = driver.find_element_by_id('first_name').send_keys(buyer_name)
    time.sleep(1)
    form_last_name = driver.find_element_by_id('last_name').send_keys(last_name)
    time.sleep(1)
    form_address = driver.find_element_by_id('address_line1').send_keys(address_line)
    time.sleep(1)
    
    form_phone = driver.find_element_by_id('phone_number').send_keys(PHONE_COMPANY)
    time.sleep(1)
    print(f'buyer_name: {buyer_name}\n zip_code: {zip_code}\n')

    try:
        flag_click = driver.find_element_by_css_selector("label[for='default_address']").click()
    except:
        print('Help the script press the button: ✔️ Set as my preferred shipping address  😂')
        print(input('And press after the ENTER..'))

    time.sleep(2)
    html = driver.find_element_by_tag_name('html')
    for i in range(10):
        html.send_keys(Keys.DOWN)

    time.sleep(4)
    button_save = driver.find_element_by_css_selector("div[class='styles__FormButtonColumn-sc-ya1w6r-5 clDVQK']").click()
    time.sleep(6)
    print('-------Done TargetMerx-----------------')

