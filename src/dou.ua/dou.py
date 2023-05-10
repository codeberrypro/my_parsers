"""
Freelance project to collect all companies from dou.ua website
Used ajax parsing and requests and BeautifulSoup libraries.

Before running the script, explore the source code of the dou.ua website
If necessary, make changes to the get_csrf_token function.
"""

import requests
from bs4 import BeautifulSoup


class DouScraper:
    def __init__(self):
        self.client = requests.session()
        self.URL = 'https://jobs.dou.ua/companies/'
        self.HEADERS = {'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 '
                                      '(KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36'}

    def __del__(self):
        self.client.close()

    def get_csrf_token(self):
        response = self.client.get(self.URL, headers=self.HEADERS)
        soup = BeautifulSoup(response.text, features="html.parser")
        csrf_token = soup.find('input', {'name': 'csrfmiddlewaretoken'})['value']
        return csrf_token

    def get_companies_list(self):
        csrf_token = self.get_csrf_token()
        pattern = 'https://jobs.dou.ua/companies/xhr-load/?'
        self.HEADERS['Referer'] = self.URL

        count = 1
        data_count = 0
        companies = []

        while True:
            data_count += 20
            data = dict(csrfmiddlewaretoken=csrf_token, count=data_count)
            second_part = self.client.post(pattern, headers=self.HEADERS, data=data)
            result = second_part.json()['html']
            soup = BeautifulSoup(result, features="html.parser")
            items = soup.findAll('div', {'class': 'company'})

            if (second_part.json()['last']) or (len(items) >= 520):
                break

            for item in items:
                company = item.find('div', {'class': 'h2'}).find('a').text
                link = item.find('div', {'class': 'h2'}).find('a').get('href')
                companies.append((company, link))
                print(f"{count}. {company} - {link}")
                count += 1

        return companies


if __name__ == '__main__':
    scraper = DouScraper()
    companies = scraper.get_companies_list()
    print(f"Total: {len(companies)} companies")