import json
import requests
from bs4 import BeautifulSoup


class ProductHuntScraper:
    def __init__(self):
        self.count_records = count_records
        self.db_path = db_path
        self.host = 'https://www.producthunt.com/posts/'
        self.headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8'
                      ',application/signed-exchange;v=b3;q=0.9',
            'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 '
                          '(KHTML, like Gecko) Chrome/96.0.4664.93 Mobile Safari/537.36'
        }

    def fetch_data(self, url):
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print('Error accessing the site:', e)
            return None

    def parse_data(self, data):
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

    def run(self, url):
        fetched_data = self.fetch_data(url)
        parsed_data = self.parse_data(fetched_data)
        date_published = self.extract_publication_date(parsed_data)

        if date_published:
            user_names = [user_item['username'] for user_item in parsed_data.values() if
                          '__typename' in user_item and user_item['__typename'] == 'User']
            user_urls = [f'https://www.producthunt.com/@{username}' for username in user_names]

if __name__ == "__main__":
    count_records = 2
    db_path = 'custom_db_path.db'
    scraper = ProductHuntScraper()
    base_url = 'https://www.producthunt.com/'
    scraper.run(base_url)
