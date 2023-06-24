import json
import time
import csv
import datetime

import asyncio
import aiohttp

from bs4 import BeautifulSoup


BOOKS_DATA = []
START_TIME = time.time()

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.106 Safari/537.36"
}


async def get_page_data(session, page):
    url = f"https://www.labirint.ru/genres/2308/?available=1&paperbooks=1&display=table&page={page}"

    async with session.get(url=url, headers=HEADERS) as response:
        response_text = await response.text()
        soup = BeautifulSoup(response_text, "lxml")
        books_items = soup.find("tbody", class_="products-table__body").find_all("tr")

        for item in books_items:
            book_data = item.find_all("td")

            try:
                title = book_data[0].find("a").text.strip()
            except:
                title = ''

            try:
                author = book_data[1].text.strip()
            except:
                author = ''

            try:
                publishing = book_data[2].find_all("a")
                publishing = ":".join([p.text for p in publishing])
            except:
                publishing = ''

            try:
                new_price = int(
                    book_data[3].find("div", class_="price").find("span").find("span").text.strip().replace(" ", ""))
            except:
                new_price = ''

            try:
                old_price = int(book_data[3].find("span", class_="price-gray").text.strip().replace(" ", ""))
            except:
                old_price = ''

            try:
                sale_percent = round(((old_price - new_price) / old_price) * 100)
            except:
                sale_percent = ''

            try:
                status = book_data[-1].text.strip()
            except:
                status = ''

            BOOKS_DATA.append(
                {
                    "title": title,
                    "author": author,
                    "publishing": publishing,
                    "new_price": new_price,
                    "old_price": old_price,
                    "sale_percent": sale_percent,
                    "status": status
                }
            )

        print(f"[INFO] Обработал страницу {page}")


async def gather_data():
    url = "https://www.labirint.ru/genres/2308/?available=1&paperbooks=1&display=table"

    async with aiohttp.ClientSession() as session:
        response = await session.get(url=url, headers=HEADERS)
        soup = BeautifulSoup(await response.text(), "lxml")
        pages_count = int(soup.find("div", class_="pagination-numbers").find_all("a")[-1].text)

        tasks = []
        for page in range(1, pages_count + 1):
            task = asyncio.create_task(get_page_data(session, page))
            tasks.append(task)

        await asyncio.gather(*tasks)


def main():
    asyncio.run(gather_data())
    cur_time = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M")

    with open(f"labirint_{cur_time}_async.json", "w", encoding='UTF-8') as file:
        json.dump(BOOKS_DATA, file, indent=4, ensure_ascii=False)

    with open(f"labirint_{cur_time}_async.csv", "w", encoding='UTF-8') as file:
        writer = csv.writer(file)

        writer.writerow(
            (
                "Название книги",
                "Автор",
                "Издательство",
                "Цена со скидкой",
                "Цена без скидки",
                "Процент скидки",
                "Наличие на складе"
            )
        )

    for book in BOOKS_DATA:
        with open(f"labirint_{cur_time}_async.csv", "a", encoding='UTF-8') as file:
            writer = csv.writer(file)
            writer.writerow(
                (
                    book["book_title"],
                    book["book_author"],
                    book["book_publishing"],
                    book["book_new_price"],
                    book["book_old_price"],
                    book["book_sale"],
                    book["book_status"]
                )
            )

    finish_time = time.time() - START_TIME
    print(f"Затраченное на работу скрипта время: {finish_time}")


if __name__ == "__main__":
    main()