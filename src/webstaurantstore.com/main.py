import csv
import time
from datetime import datetime
from threading import Thread
from tkinter import Tk, filedialog

import requests
import win32api
from lxml import html

DOMAIN = 'https://www.webstaurantstore.com'


MAX_THREADS = 10
total_checked = 0
categories_checked = 0
all_categories = 0




class CategoryParser:

    def __init__(self, category_url):
        self.category_url = category_url
        self.all_urls = []
        self.getting_urls = True
        self.output = []
        self.active_threads = 0
        self.checker_urls()
        self.get_all_pages()

    def get_current_page(self, page=''):
        r = requests.get(self.category_url + page)
        with open('html.html', 'w', encoding='utf-8') as f:
            f.write(r.text)
        site = html.fromstring(r.text)
        number_urls = 0
        for el in site.xpath('//div[@id="product_listing"]/div'):
            current_element = el.xpath('.//a[@class="block"]/@href')[0]
            number_urls += 1
            self.all_urls.append(current_element)
        return number_urls

    def get_all_pages(self):
        for page_num in range(1, 100):
            page = ''
            if page_num != 0:
                page = f'{"&" if "?" in self.category_url else "?"}page={page_num}'
            number_urls = trying(lambda: self.get_current_page(page))
            print('Goods received', number_urls)
            if number_urls == 0:
                break
        self.getting_urls = False

    @thread
    def check_product(self, url):
        self.active_threads += 1
        try:
            print(f'[GET] {DOMAIN + url}')
            r = requests.get(DOMAIN + url)
            current_product = html.fromstring(r.text)
            page_header, price, price_case, upc_code, product_ship_note = '', '', '', '', ''
            try:
                page_header = current_product.xpath('//h1[@class="page-header"]/text()')[0]
            except:
                print('Failed to get product name')
                self.active_threads -= 1
                return -1
            try:
                price = current_product.xpath('//p[@class="price"]/text()')[0].replace('$', '')
            except:
                print('Failed to get item price')
            try:
                price_case = current_product.xpath('//td/text()')[0].replace('$', '')
            except:
                print('Failed to get another item price')
            try:
                upc_code = current_product.xpath('//span[@class="product__stat-desc"]/text()')[0]
            except:
                print('Failed to get UPC')
            try:
                product_ship_note = current_product.xpath('//div[@class="product__ship-note"]/strong/text()')[0].strip()
            except:
                try:
                    product_ship_note = current_product.xpath('//div[@class="product__ship"]/text()')[0].strip()
                except:
                    print('Failed to get delivery time')
            print(page_header, price, price_case, upc_code, product_ship_note)
            self.output.append([DOMAIN + url, page_header, price, price_case, upc_code, product_ship_note])

            global total_checked
            total_checked += 1
            self.active_threads -= 1
            win32api.SetConsoleTitle(f'Category {categories_checked}/{all_categories} ({len(self.output)}/'
                                     f'{len(self.output) + len(self.all_urls)}) Total tested:{total_checked}')
            return 1
        except Exception as E:
            print('Error getting product information', E)
            self.active_threads -= 1
            return -1




if __name__ == "__main__":
    win32api.SetConsoleTitle('Run')
    file_categories = get_file_name()
    if not file_categories:
        input('Path specified incorrectly..')
    with open(file_categories) as f:
        categories = f.read().strip().split('\n')
    all_categories = len(categories)
    print('Get', all_categories, 'categories')

    finish_list = []
    try:
        for category in categories:
            categories_checked += 1
            CurrentParser = CategoryParser(category)
            while CurrentParser.active_threads > 0 or CurrentParser.all_urls:
                time.sleep(.5)
            finish_list += CurrentParser.output
    except Exception as E:
        print('Error receiving goods')

    try:
        with open(datetime.strftime(datetime.now(), f"%d-%m-%Y_%H-%M.csv"), 'w', encoding='UTF8',
                  newline='') as csvfile:
            writer = csv.writer(csvfile)
            for product in finish_list:
                writer.writerow(product)
    except Exception as E:
        print('File save error')
