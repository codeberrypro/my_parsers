import json
import re
import threading
import time
import sqlite3

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


class ProductHuntScraper:
    def __init__(self):
        self.count_records = count_records
        self.db_path = db_path
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--disable-gpu')

        self.host = 'https://www.producthunt.com/posts/'
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
                      ',application/signed-exchange;v=b3;q=0.9',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/96.0.4664.93 Mobile Safari/537.36'
        }

    def fetch_data(self, url):
        """
        Получение данных по URL с использованием HTTP-запросов.
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print('Error accessing the site:', e)
            return None

    def parse_data(self, data):
        """
        Парсинг JSON-данных из HTML-контента.
        """
        try:
            soup = BeautifulSoup(data, 'html.parser')
            script_element = soup.find('script', {'id': '__NEXT_DATA__'})
            json_text = script_element.string
            json_data = json.loads(json_text)
            json_dat = json_data['props']['apolloState']
            return json_dat
        except Exception as e:
            print('Error parsing data:', e)
            return None

    def get_user_data(self, data):
        """
        Получеем urls пользователей из JSON-данных.
        """
        user_data = []
        if data is None:
            return user_data

        for key, value in data.items():
            if '__typename' in value and value['__typename'] == 'User':
                user_data.append(value)
        return user_data

    def get_linkedin_urls(self, user_urls):
        """
        Получение ссылок на профили LinkedIn.
        """
        linkedin_urls = []
        for url in user_urls:
            self.driver.get(url)
            time.sleep(3)
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            try:
                linkedin_url = soup.find('a', href=re.compile(r"producthunt.com\.com"))
                if linkedin_url:
                    linkedin_urls.append(linkedin_url.get('href'))
                else:
                    linkedin_urls.append('')
            except:
                linkedin_urls.append('')

        return linkedin_urls

    def save_to_database(self, date_published, url, linkedin_url):
        """
        Сохранение пар URL и LinkedIn URL в базу данных SQLite.
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
               CREATE TABLE IF NOT EXISTS get_linkedin_urls (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   date_published TEXT NOT NULL,
                   url TEXT NOT NULL,
                   linkedin_url TEXT NOT NULL
               )
           ''')

        # Проверяем что переменные url, linkedin_url не пустые
        if linkedin_url and cursor.execute('SELECT id FROM get_linkedin_urls WHERE url = ? AND linkedin_url = ?',
                                           (url, linkedin_url)).fetchone() is None:
            # Добавить уникальное значение linkedin_url в базу данных.
            cursor.execute('INSERT INTO get_linkedin_urls (date_published, url, linkedin_url) VALUES (?, ?, ?)',
                           (date_published, url, linkedin_url))

            conn.commit()
            print(self.saved_records, date_published, url, linkedin_url)

            # Код который сохраняет нужное количество данных
            self.saved_records += 1
            if self.saved_records >= self.count_records + 1:
                print(f'Saved {self.saved_records - 1}, Date {date_published}')
                conn.close()
                self.driver.quit()
                self.driver.close()  # Закритие driver
                raise StopIteration

    def selenium_thread(self, user_urls, date_published):
        self.driver = webdriver.Chrome(options=self.chrome_options)
        linkedin_urls = self.get_linkedin_urls(user_urls)
        self.driver.quit()  # закрываем driver

        for url, linkedin_url in zip(user_urls, linkedin_urls):
            self.save_to_database(date_published, url, linkedin_url)

    def extract_publication_date(self, data):
        for key, value in data.items():
            if key.startswith("Post") and 'slug' in value:
                user_data = value
                _date = user_data['createdAt']
                return str(_date).split('T')[0]
        return None

    def process_data(self, data, date_published):
        if data is None:
            return

        user_names = {
            user_item['username']
            for user_item in data
            if '__typename' in user_item
               and user_item['__typename'] == 'User'
        }
        user_urls = [
            f'https://www.producthunt.com/@{username}'
            for username in user_names
        ]

        linkedin_urls = self.get_linkedin_urls(user_urls)

        for url, linkedin_url in zip(user_urls, linkedin_urls):
            self.save_to_database(date_published, url, linkedin_url)

    def run(self, url):
        self.saved_records = 1
        fetched_data = self.fetch_data(url)
        parsed_data = self.parse_data(fetched_data)
        date_published = self.extract_publication_date(parsed_data)

        if date_published:
            user_names = [user_item['username'] for user_item in parsed_data.values() if
                          '__typename' in user_item and user_item['__typename'] == 'User']
            user_urls = [f'https://www.producthunt.com/@{username}' for username in user_names]

            driver_thread = threading.Thread(target=self.selenium_thread, args=(user_urls, date_published))
            driver_thread.start()
            self.process_data(parsed_data, date_published)
        else:
            print("Дата не найдена")


if __name__ == "__main__":
    count_records = 2  # количество пользователей
    db_path = 'custom_db_path.db'  # путь к сохранению базы

    scraper = ProductHuntScraper()
    base_url = 'https://www.producthunt.com/'
    scraper.run(base_url)