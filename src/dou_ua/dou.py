import requests
from bs4 import BeautifulSoup


URL = 'https://jobs.dou.ua/companies/'
HEADERS = {
    'User-Agent': ' Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/106.0.0.0 Mobile Safari/537.36'
}


def get_companies():
    client = requests.session()
    first_part = client.get(URL, headers=HEADERS)
    soup = BeautifulSoup(first_part.text, features="html.parser")
    if soup.find('ul', {'class': 'l-items'}) is None:
        response = None

    elif soup.find('div', {'class': 'more-btn'}) is None:
        response = first_part

    else:
        result = first_part.text  # сохраняем html первой порции
        pattern = 'https://jobs.dou.ua/companies/xhr-load/?'

        data_count = 0
        sss = soup.find_all('script')[5]
        csrf = sss.text.split(';')[0].split('=')[1].replace('"', '')[1:]
        HEADERS['Referer'] = URL

        while True:
            data_count += 20
            data = dict(csrfmiddlewaretoken=csrf, count=data_count)
            second_part = client.post(pattern, headers=HEADERS, data=data)
            result = second_part.json()['html']

            soup = BeautifulSoup(result, features="html.parser")
            items = soup.findAll('div', {'class': 'company'})

            if (second_part.json()['last']) or (len(items) >= 520):
                break

        count = 0
        for item in items:
            company = item.find('div', {'class': 'h2'}).find('a').text
            link = item.find('div', {'class': 'h2'}).find('a').get('href')
            count += 1

            print(company, link)
        print(len(items))
        response = result

    client.close()
    return response


get_companies()