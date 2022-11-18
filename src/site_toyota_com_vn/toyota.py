import requests
import json
import re
import csv

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"}

res = requests.get("https://www.toyota.com.vn/api/common/provinces", headers=headers)
cookie = {"D1N": re.findall(r"[a-z, A-Z, 0-9]{30,40}", res.text)[0]}


def write_csv(data):
    with open('toyota_com_vn.csv', 'a', newline='', encoding="utf-8") as f:
        order = ['link', 'phone', 'adres']
        writer = csv.DictWriter(f, delimiter=';', fieldnames=order)
        writer.writerow(data)


def get_ids():
    ids_json = json.loads(requests.get("https://www.toyota.com.vn/api/common/provinces", headers=headers, cookies=cookie).text)
    ids_list = []
    for i in ids_json["Data_Ext"]["result"]["items"]:
        ids_list.append(i["id"])
    return ids_list


def get_info():
    for i in get_ids():
        info_json = json.loads(requests.get("https://www.toyota.com.vn/api/common/dealerbyprovinceidanddistrictid",
                                            params={"provinceId": i, "districtId": ""}, headers=headers,
                                            cookies=cookie).text)

        for info in info_json["Data_Ext"]["result"]:
            try:
                phone = info["phone"][:13] + '**'
                adres = info["address"]
                link = info["linkWebsite"]

                data = {
                    'link': link,
                    'phone': phone,
                    'adress': adres,
                }
                write_csv(data)
            except:
                continue
    print("Parsing finished")


get_info()
