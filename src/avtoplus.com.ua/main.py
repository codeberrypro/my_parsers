"""
Freelance project, unloads all products from a competitor's website.

Parsing:
    price
    header
    Pictures
    rating
    url
    delivery

"""

import csv
import time

import requests
from bs4 import BeautifulSoup


HEADERS = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.9',
    'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko)'
                  ' Chrome/96.0.4664.93 Mobile Safari/537.36'
}


def get_url(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=11)
        if r.ok:  # status code 200
            return r
        else:
            print('Ошибка доступа к сайту:', r.status_code)
    except requests.exceptions.ReadTimeout:
        print("\n Переподключение к серверам \n")
        time.sleep(3)


def write_csv(data):
    with open('avto5_plus.csv', 'a', newline='', encoding="utf-8") as f:
        order = ['link', 'title', 'description', 'rating', 'price_usd', 'price_ua',
                 'lot', 'quality', 'delivery', 'compatibles_model', 'imgs']
        writer = csv.DictWriter(f, delimiter=';', fieldnames=order)
        writer.writerow(data)


def get_shop(ads):
    for i in ads:
        link = 'https://avto-plus.com.ua' + i.find('a').get('href').strip()
        time.sleep(1)
        htmls = get_url(link)
        soup = BeautifulSoup(htmls.text, 'html.parser')

        title = soup.find('section', attrs={'class': 'model-breadcrumbs bg-white'}).get_text(strip=True)
        description = soup.find('div', attrs={'class': 'description__body text-static'}).get_text(
            strip=True).replace('?', ' ')

        # Get a price 10% less than on the website
        price_us = soup.find('div', attrs={'class': 'basket-button__usd'}).get_text(strip=True).split('$')[1]
        price_usd_percent = int(price_us) / 100 * 10
        price_usd = int(price_us) - int(price_usd_percent)
        price_usd = str(price_usd) + '$'

        # Get a price 10% less than on the website
        price_ua = soup.find('div', attrs={'class': 'basket-button__uah'}).get_text(strip=True).split('грн')[0]
        price_ua_percent = int(price_ua) / 100 * 10
        price_ua = int(price_ua) - int(price_ua_percent)
        price_ua = str(price_ua) + 'грн'

        lot = soup.find('div', attrs={'class': 'info-part__lot'}).get_text(strip=True).split(':')[1]
        quality = soup.find('div', attrs={'class': 'info-part__quality'}).get_text(strip=True)
        delivery = soup.find('div', attrs={'class': 'info-part__delivery info-part__delivery-group'}).get_text(
            strip=True)

        try:
            compatibles_model1 = soup.find('td', attrs={'class': 'compatible-table'}).get_text(strip=True)
            compatibles_model = compatibles_model1.find('td', attrs={'class': 'compatible__model'}).get_text(
                strip=True)
        except:
            compatibles_model = ''

        try:
            rating_like = soup.find('span', attrs={'class': 'product-rating__like'}).get_text(strip=True)
            try:
                rating_dislike = soup.find('span', attrs={'class': 'product-rating__dislike'}).get_text(strip=True)
                if len(set([str(x) for x in range(2000)]) & set(rating_dislike)) == 0:
                    rating_dislike = '0'

            except:
                rating_dislike = '0'

            rating_percent = soup.find('span', attrs={'class': 'product-rating__percent'}).get_text(strip=True)
            rating = f"Рейтинг продавця в Польщі Позитивних: - {rating_like} Негативних - {rating_dislike} {rating_percent}:                                    "
        except:
            rating = 'Немає рейтингу продавця'

        product = soup.find('section', attrs={'class': 'product'})
        img = product.find('div', attrs={'class': 'product__gallery js-init-gallery'})
        link_image = img.find_all('a', attrs={'class': 'product__small-picture js-small-pic'})

        img_1 = link_image[0].get('href')
        try:
            img_2 = link_image[1].get('href')
        except:
            img_2 = None

        try:
            img_3 = link_image[2].get('href')
        except:
            img_3 = None

        try:
            img_4 = link_image[3].get('href')
        except:
            img_4 = None

        mg = f"{img_1}, {img_2}, {img_3}, {img_4}"

        data = {
            'link': link,
            'title': title,
            'description': description,
            'compatibles_model': compatibles_model,
            'rating': rating,
            'price_usd': price_usd,
            'price_ua': price_ua,
            'lot': lot,
            'quality': quality,
            'delivery': delivery,
            'imgs': mg,
        }
        write_csv(data)


def main():
    with open('input_category.txt') as file:
        lines = [line.strip() for line in file.readlines()]

        page = 1
        while True:
            for line in lines:
                line = line.split('1/')[0]
                url = f"{line}{page}"

                print(f'[INFO] парсим страницу {page}')
                html = get_url(url)
                soup = BeautifulSoup(html.text, 'html.parser')
                ads = soup.find_all('div', attrs={'class': 'goods__item product-card product-card--categoryPage'})

                if(len(ads)):
                    get_shop(ads)
                    page += 1
                else:
                    break


if __name__ == '__main__':
    main()
