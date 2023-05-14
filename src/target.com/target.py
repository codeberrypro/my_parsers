import csv
import re
from datetime import datetime
from threading import Thread

import requests
from fake_useragent import UserAgent

from functions import *

ua = UserAgent()
count_threads = 0
MAX_THREADS = 10

custom_headers = {
    "User-agent": ua.chrome,
    "Content-type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Accept": "*/*",
    "X-Requested-With": "XMLHttpRequest",
}


def thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()

    return wrapper


@thread
def get_product(url, all_page_products_):
    global count_threads
    print('[GET]', url)
    count_threads += 1
    try:
        product_id = re.findall('A-[0-9a-zA-Z]+', url)[0][2:]
        new_ulr = f"https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1" \
                  f"?key=ff457966e64d5e877fdbad070f276d18ecec4a01" \
                  f"&tcin={product_id}" \
                  f"&store_id=2448" \
                  f"&pricing_store_id=2448" \
                  f"&has_financing_options=true" \
                  f"&visitor_id=017E9C46D94D0201AFF11E501B7230FB" \
                  f"&has_size_context=true" \
                  f"&latitude=37.3465576171875" \
                  f"&longitude=-96.4493408203125" \
                  f"&state=KS" \
                  f"&zip=67346"

        r = requests.get(new_ulr)
        count_threads -= 1
        if not r.ok:
            print('[ERROR] request failed')
            save_file('err.html', r.text)
            return 0
        if not r.json():
            return 1
        all_page_products_.append(r.json())
        return 1
    except Exception as E:
        print('[ERROR] Error getting product information', E)
        count_threads -= 1
        return 1


def get_page(url):
    print('[GET]', url)
    try:
        global stop_this_page
        r = requests.get(url, headers=custom_headers)
        save_file('index.html', r.text)
        site_json = r.json()
        return site_json['data']['search']['products']
    except Exception as E:
        print(E)
        return 0


def get_pages(url):
    category = re.findall('N-[0-9a-zA-Y]+', url)[0][2:]
    try:
        faceted_value = re.findall('N-[0-9a-zA-Z]+', url)[0]
        faceted_value = faceted_value[faceted_value.find(category) + len(category) + 1:]
    except:
        faceted_value = ''
    all_page_products = []
    for offset in range(0, 1500, 24):
        url = f'https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v1' \
              f'?key=ff457966e64d5e877fdbad070f276d18ecec4a01' \
              f'&category={category}' \
              f'&channel=WEB' \
              f'&count=24' \
              f'&default_purchasability_filter=true' \
              f'&faceted_value={faceted_value}' \
              f'&include_sponsored=true' \
              f'&offset={offset}' \
              f'&page=/c/{category}' \
              f'&platform=desktop' \
              f'&pricing_store_id=2448' \
              f'&store_ids=2448,1944,1943,1945,905' \
              f'&useragent=Mozilla%2F5.0+%28Windows+NT+10.0%3B+Win64%3B+x64%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F97.0.4692.99+Safari%2F537.36' \
              f'&visitor_id=017E9C46D94D0201AFF11E501B7230FB'

        print(url)
        current_page_products = trying(lambda: get_page(url))
        if not current_page_products:
            break
        this_products = []
        for product in current_page_products:
            while count_threads >= MAX_THREADS:
                time.sleep(.1)
            trying(lambda: get_product(product['item']['enrichment']['buy_url'], this_products))
            time.sleep(.1)
        while count_threads > 0:
            time.sleep(.1)
        all_page_products += this_products

    return all_page_products


def save_to_csv(products, category_name=False):
    # Saving a list of parsed pages
    main_brand = ''
    if category_name:
        try:
            main_brand = str(products[0]['data']['product']['item']['primary_brand']['name']) + '_'
        except:
            main_brand = 'unknown_'
    with open(datetime.strftime(datetime.now(), f"files/{main_brand}%d-%m-%Y-%H_%M.csv"), 'w', encoding='UTF8',
              newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        for number, product in enumerate(products):
            try:
                title = product['data']['product']['item']['product_description']['title']
                print(f"{number + 1}.", 'Name:', title)
                buy_url = product['data']['product']['item']['enrichment']['buy_url']
                print('URL', buy_url)
                try:
                    upc = product['data']['product']['children'][0]['item']['primary_barcode']
                except:
                    upc = product['data']['product']['item']['primary_barcode']
                print('UPC:', upc)
                try:
                    cost = product['data']['product']['price']['current_retail']
                except:
                    cost = product['data']['product']['price']['current_retail_min']
                print('Price:', cost)
                try:
                    brand = product['data']['product']['item']['primary_brand']['name']
                except:
                    brand = ''
                row_to_write = [buy_url, brand, title, cost, upc]
                writer.writerow(row_to_write)
            except Exception as E:
                print("[ERROR] Error getting product information", E)
                print(product)


def get_target_category():
    for current_file_url in get_file('target_category.txt', is_list=True):
        all_products_target_category = []
        try:
            if not current_file_url.strip():
                continue
            all_products_target_category += get_pages(current_file_url)
        except Exception as E:
            print('[ERROR] Category parsing error', E)
        if all_products_target_category:
            save_to_csv(all_products_target_category, True)


def get_target_url():
    this_products = []
    for current_file_url in get_file('target_url.txt', is_list=True):
        try:
            while count_threads >= MAX_THREADS:
                time.sleep(.1)
            trying(lambda: get_product(current_file_url, this_products))
            time.sleep(.1)
        except Exception as E:
            print('[ERROR] Product parsing error', E)
    while count_threads > 0:
        time.sleep(.1)
    if this_products:
        save_to_csv(this_products)


if __name__ == "__main__":
    USE_CATEGORY = True
    if USE_CATEGORY:
        get_target_category()
    else:
        get_target_url()

