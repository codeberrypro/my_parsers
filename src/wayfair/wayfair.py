import csv
import pickle
import re
from datetime import datetime

import requestium
from fake_useragent import UserAgent
from lxml import html
from selenium import webdriver
from selenium_stealth import stealth
from seleniumwire import webdriver as wire_driver  # Import from seleniumwire

from functions import *


ua = UserAgent()


class WayfairParser:
    def __init__(self, use_proxies=False):
        print('[START] Session creation')
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--log-level=3')

        # Chrome is controlled by automated test software
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-gpu')

        # Chrome is controlled by automated test software
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)

        self.proxies = None
        capabilities = None
        self.session = requestium.Session(webdriver_path='../../webdriver_path/chromedriver.exe', browser='chrome',
                                          default_timeout=30)
        self.session.headers.update({'user-agent': ua.chrome})
        # To add chrome_options
        self.session._driver = wire_driver.Chrome(
            './chromedriver',
            options=chrome_options,
            desired_capabilities=capabilities,
        )

        stealth(self.session.driver,
                languages=["en-US", "en"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True,
                )
        self.session.driver.set_page_load_timeout(100)
        print('[START] Get cookies')
        self.set_cookies()
        print('[START] Parser launched')

    def set_cookies(self):
        # Setting/creating session cookies
        self.session.driver.get('https://www.wayfair.com/')
        check_file("cookies.txt")
        try:
            if 'please verify that you are not a robot' in self.session.driver.page_source:
                input('Captcha found...')
            else:
                for cookie in list(pickle.load(open(f"files/cookies.txt", "rb"))):
                    if isinstance(cookie, dict):

                        cookie_add = {'name': cookie.get('name'), 'value': cookie.get('value'),
                                      'path': cookie.get('path'),
                                      'secure': cookie.get('secure')}
                    else:
                        cookie_add = {'name': cookie.name, 'value': cookie.value, 'path': cookie.path,
                                      'secure': cookie.secure}
                    self.session.driver.add_cookie(cookie_add)
            self.session.transfer_driver_cookies_to_session()
        except:
            print("[INFO] Cookies not set")
            try:
                if 'please verify that you are not a robot' in self.session.driver.page_source:
                    input('Captcha found...')
                time.sleep(2)
                with open(f'files/cookies.txt', 'wb') as f:
                    pickle.dump(self.session.cookies, f)
                self.session.transfer_driver_cookies_to_session()
            except Exception as E:
                print("[ERROR] Error getting cookies", E)
                return 0

    def get_current_item(self, this_item):
        print('[GET ITEM]', this_item['url'])
        try:
            headers = {
                "accept": "application/json",
                "accept-language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
                "apollographql-client-name": "@wayfair/sf-ui-product-details",
                "apollographql-client-version": "bf018cf70462a1b6cd67c25ea15ad9c0bd8a3a15",
                "content-type": "application/json",
                "sec-ch-ua": "\" Not;A Brand\";v=\"99\", \"Google Chrome\";v=\"97\", \"Chromium\";v=\"97\"",
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": "\"Windows\"",
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "use-web-hash": "true",
                "x-parent-txid": "I+F9OmH5qDNAZkQF18I0Ag==",
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36'
            }
            url = 'https://www.wayfair.com/graphql?hash=24e17b1e9c2cffd32c2cab2189a5e917%2316dd774cea9d3bd2c887f99be034a1de'
            data = {
                'variables': {'sku': this_item['sku'], 'selectedOptionIds': [], 'withLegacySpecificationsData': False}}
            r = self.session.post(url, json=data, headers=headers)
            save_file('get_item.html', r.text)
            return r.json()
        except Exception as E:
            print('[ERROR] Error getting product information')
            return 0

    def get_page(self, url, page_number, use_button):

        # Parsing a specific page with a given url
        print('[GET]', url)
        r = self.session.get(f"https://www.wayfair.com/a/manufacturer_browse/get_data?"
                             f"category_id=0"
                             f"&caid=0"
                             f"&maid={re.findall('-b[0-9]+', url)[0][2:]}"
                             f"&filter={'a1234567890%7E2147483646' if use_button else ''}"
                             f"&solr_event_id=0"
                             f"&registry_type=0"
                             f"&ccaid=0"
                             f"&curpage={page_number}"
                             f"&itemsperpage=48"
                             f"&refid="
                             f"&sku="
                             f"&search_id="
                             f"&collection_id=0"
                             f"&show_favorites_button=true"
                             f"&registry_context_type_id=0"
                             f"&product_offset=0"
                             f"&load_initial_products_only=false"
                             f"&only_show_grid=false"
                             f"&is_initial_render=false", proxies=self.proxies)
        save_file('last_page.html', r.text)
        if not r.ok:
            save_file('error.html', r.text)
            print('[ERROR] Website request error')
            return 0
        if 'curpage' in url and 'curpage' not in r.url:
            return []
        if not r.text:
            return []
        if 'We can\'t seem to find any products that match your search' in r.text:
            return []
        site_data = html.fromstring(r.text)
        element = site_data.xpath("//script[@id='wfAppData']")
        if element:
            site_json = json.loads(element[0].text)
            react_data_keys = list(site_json['wf']['reactData'].keys())
            products = site_json['wf']['reactData'][react_data_keys[0]]['bootstrap_data']['browse'][
                'browse_grid_objects']
        else:
            elements = site_data.xpath("//script")
            current_element = ''
            for element in elements:
                if 'browse_grid_objects' in str(element.text):
                    current_element = element.text
            current_element = current_element[current_element.find('{'):current_element.rfind('}') + 1]
            try:
                site_json = json.loads(current_element)
            except:
                return []
            products = site_json['application']['props']['browse']['browse_grid_objects']
        self.session.transfer_driver_cookies_to_session()
        with open(f'files/cookies.txt', 'wb') as f:
            pickle.dump(self.session.cookies, f)
        return products

    def get_pages(self, url, use_button=True):

        # Parsing all pages of a specific brand
        if not url.split():
            return [], {}
        if use_button:
            if 'a1234567890~2147483646' not in url:
                url = url.replace('.html', '-a1234567890~2147483646.html')
        else:
            if 'a1234567890~2147483646' in url:
                url = url.replace('-a1234567890~2147483646', '')
                url = url.replace('a1234567890~2147483646', '')
        all_products = []
        all_products_info = {}
        for page_number in range(1, 200):
            current_page_url = url
            if page_number != 1:
                if '?' not in current_page_url:
                    current_page_url += f'?curpage={page_number}'
                else:
                    current_page_url += f'&curpage={page_number}'
            current_page_url = current_page_url.replace('sb0', 'sb1')
            current_page_products = trying(lambda: self.get_page(current_page_url, page_number, use_button))
            if not current_page_products:
                break
            for current_product_sku in current_page_products:
                current_product_info = trying(lambda: self.get_current_item(current_product_sku))
                all_products_info[current_product_sku['sku']] = current_product_info

            print('[INFO] Products found', len(current_page_products))
            if current_page_products == []:
                break
            all_products += current_page_products
        return all_products, all_products_info


def save_to_csv(products, products_info):
    # Saving a list of parsed pages
    try:
        brand = products[0]['manufacturer']
    except:
        brand = 'unknown'
    with open(datetime.strftime(datetime.now(), f"files/{brand}_%d-%m-%Y_%H-%M.csv"), 'w', encoding='UTF8',
              newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        for number, product in enumerate(products):
            try:
                print(f"{number + 1}.", 'SKU:', product['sku'])
                print('URL', product['url'])
                print('Name:', product['product_name'])
                print('Brand:', product['manufacturer'])
                row_to_write = [product['url'], product['product_name'], product['manufacturer']]

                if not product['raw_pricing_data']['pricing']:
                    print('Price not ')
                    row_to_write.append('None')
                else:
                    print('Price:', f"{product['raw_pricing_data']['pricing']['customerPrice']['quantityPrice']['value']}$")
                    row_to_write.append(product['raw_pricing_data']['pricing']['customerPrice']['quantityPrice']['value'])
                    row_to_write.append(product['sku'])
                try:
                    print('Time of delivery:', product['free_ship_text'])
                    row_to_write.append(product['free_ship_text'])
                except:
                    print('Failed to get delivery time')
                    row_to_write.append('')
                try:
                    print('partNumber:',products_info[product['sku']]['data']['product']['manufacturerPartNumber']['partNumber'])
                    row_to_write.append(products_info[product['sku']]['data']['product']['manufacturerPartNumber']['partNumber'])
                except:
                    print('Failed to get partNumber')
                    row_to_write.append('')

                writer.writerow(row_to_write)
            except Exception as E:
                print("[ERROR] Error getting product information", E)
                print(product)


wp = WayfairParser(use_proxies=False)

use_button_setting = False

for current_file_url in get_file('urls_ waifair.txt', is_list=True):
    products, products_info = wp.get_pages(current_file_url, use_button_setting)
    save_to_csv(products, products_info)

wp.session.driver.close()
wp.session.close()
