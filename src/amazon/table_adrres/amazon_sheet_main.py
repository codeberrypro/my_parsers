'''
https://docs.google.com/spreadsheets/d/1_TA5IWppAxSZOwmkmZaMeUum_G22Yko_iCyx9FtELT0/edit?usp=sharing
https://docs.google.com/spreadsheets/d/19mNf0zyt0gDSlNhWgjsAS6sSRZIj7vSXZu5n7YExSHY/edit#gid=403295928

WebRestMerx
WayfairMerx
KatomMerx
TargetMerx
HomedepotMerx
'''

import time
import gspread
from fake_useragent import UserAgent
from selenium import webdriver
from selenium_stealth import stealth


ua = UserAgent()

COMPANY = ' WhiteLilyStore'  # name company
PHONE_COMPANY = ''


def initialize_driver():
    """Driver initialization"""
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--log-level=3')

    # Chrome is controlled by automated test software
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML"
        ", like Gecko) Chrome/98.0.4758.102 Mobile Safari/537.36")

    driver = webdriver.Chrome(executable_path='chromedriver.exe', options=chrome_options)

    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            )
    return driver


def initialize_gspread_api():
    """Connected to google sheet api"""
    gc = gspread.service_account(filename='sheet.json')  # название файла с сервисным аккаунтом
    sh = gc.open_by_key('1UHUJt2guYcXtUF-FU7L7k7y1TKbxTRwZW8AYvCn5bTE')  # ID гугл таблицы
    worksheet = sh.worksheet('testlist')  # Название листа для записи данных
    return worksheet


def get_value_google_sheet(worksheet, driver):
    """Read data by fields"""
    values_list = worksheet.get_values()
    for value in values_list:
        password = value[22]
        login = value[21]
        online_supplier = value[20]
        phone = value[14]
        zip_code = value[13]
        address_line = value[10]
        buyer_name = value[9]
        business_name = value[8]
        city = value[11]
        state = value[12]

        print(password, login, online_supplier, phone, zip_code, address_line, business_name, buyer_name, city, state)


def main():
    driver_initialize = initialize_driver()
    initialize_gspread = initialize_gspread_api()
    get_value_google_sheet(initialize_gspread, driver_initialize)


if __name__ == '__main__':
    main()




