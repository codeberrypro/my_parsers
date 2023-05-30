import pandas as pd
import requests
from bs4 import BeautifulSoup


class EbayScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome"
                          "/107.0.0.0 Safari/537.36",
        }
        self.params = {
            '_nkw': 'iphone',  # search query
            '_pgn': 1,  # page number
            '_ipg': 200  # number of products per page
        }

        self.data = []

    def extract_data(self):
        while True:
            page = requests.get('https://www.ebay.com/sch/i.html', params=self.params, headers=self.headers, timeout=30)
            soup = BeautifulSoup(page.text, 'lxml')

            print(f"Extracting page: {self.params['_pgn']}")
            print("-" * 10)

            for products in soup.select(".s-item__info"):
                try:
                    price = products.select_one(".s-item__price").text
                except:
                    price = None
                try:
                    link = products.select_one(".s-item__link")["href"]
                except:
                    link = None
                try:
                    title = products.select_one(".s-item__title span").text
                except:
                    title = None

                self.data.append({
                    "title": title,
                    "price": price,
                    "link": link
                })
                print(title, link, price)

            if soup.select_one(".pagination__next"):
                self.params['_pgn'] += 1
            else:
                break

    def save_data(self):
        df = pd.DataFrame(self.data)
        df.to_csv('ebay_data.csv', index=False)


scraper = EbayScraper()
scraper.extract_data()
scraper.save_data()
