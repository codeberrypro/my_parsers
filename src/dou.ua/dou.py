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

    def decode_email(self, link_decode):
        """Decoding email using a request to the site"""
        response = self.client.get(link_decode, headers=self.HEADERS)
        soup = BeautifulSoup(response.text, features="html.parser")
        try:
            email_code = soup.find('span', attrs={'class': 'cf_email'})['data-cfemail']
            r = int(email_code[:2], 16)
            email = ''.join([chr(int(email_code[i:i + 2], 16) ^ r) for i in range(2, len(email_code), 2)])
            return email
        except (ValueError, TypeError):
            return 'Email not found'

    def get_companies_list(self):
        csrf_token = self.get_csrf_token()
        pattern = 'https://jobs.dou.ua/companies/xhr-load/?'
        self.HEADERS['Referer'] = self.URL

        count = 1
        data_count = 0
        result = []
        while True:
            data_count += 20
            data = dict(csrfmiddlewaretoken=csrf_token, count=data_count)
            second_part = self.client.post(pattern, headers=self.HEADERS, data=data)
            result_html = second_part.json()['html']
            soup = BeautifulSoup(result_html, features="html.parser")
            items = soup.findAll('div', {'class': 'company'})

            if (second_part.json()['last']) or (len(items) >= 520):
                break

            for item in items:
                company = item.find('div', {'class': 'h2'}).find('a').text
                link = item.find('div', {'class': 'h2'}).find('a').get('href')
                link_decode = link + 'offices/'
                decoded_email = self.decode_email(link_decode)
                result.append((company, link, decoded_email))
                print(f"{count}. {company} {link} {decoded_email}")
                count += 1

        return companies


if __name__ == '__main__':
    scraper = DouScraper()
    companies = scraper.get_companies_list()
    print(f"Total: {len(companies)} companies")