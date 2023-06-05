import sqlite3
import requests


class FarfetchParser:
    def __init__(self, result):
        self._host = 'https://www.farfetch.com/uk/shopping/men/hoodies-2/items.aspx?page=1&view=90&sort=4&q=hoodie'
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:108.0) Gecko/20100101 Firefox/108.0'
        }
        self._db_name = result

    def create_items_table(self):
        with sqlite3.connect(self._db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE IF NOT EXISTS items '
                           '(id INTEGER PRIMARY KEY AUTOINCREMENT, '
                           'title TEXT, '
                           'brand TEXT, '
                           'price TEXT, '
                           'url TEXT)')

    def insert_item(self, title, brand, price, url):
        with sqlite3.connect(self._db_name) as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO items (title, brand, price, url) VALUES (?, ?, ?, ?)',
                           (title, brand, price, url))

    def parse(self):
        count = 0
        for page in range(101):
            params = {
                'page': page,
                'view': '90',
                'sort': '4',
                'q': 'hoodie',
                'pagetype': 'Shopping',
                'rootCategory': 'Men',
                'pricetype': 'FullPrice',
                'c-category': '136398',
            }

            response = requests.get('https://www.farfetch.com/uk/plpslice/listing-api/products-facets',
                                    params=params, headers=self._headers)
            items = response.json()['listingItems']['items']
            for x in items:
                title = x['shortDescription']
                brand = x['brand']['name']
                price = x['priceInfo']['formattedFinalPrice']
                url = 'https://www.farfetch.com' + x['url']
                self.insert_item(title, brand, price, url)
                count += 1
                print(count, title, brand, price, url)


if __name__ == '__main__':
    parser = FarfetchParser('result.db')
    parser.create_items_table()
    parser.parse()