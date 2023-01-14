import time
import os
import requests
import ftplib

from math import ceil
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select


HEADER = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) ' \
         'Chrome/88.0.4324.150 Safari/537.36 '


def parsing(filter_brand, filter_year, filter_fuel):
    option = webdriver.ChromeOptions()
    option.add_argument(f"--user-agent={HEADER}")
    option.add_argument('--headless')
    option.add_argument('--ignore-certificate-errors')
    option.add_argument('--ignore-ssl-errors')
    driver = webdriver.Chrome(options=option)
    translator = GoogleTranslator(source='ko', target='en')

    driver.get('https://www.lotteautoauction.net/hp/pub/cmm/viewMain.do?introYn=Y')
    auth(driver)
    driver.execute_script("fn_MovePage('1010200')")
    js_functions = []

    filters_brand = ["HD", "KI", "DW", "SS", "SY", "AD", "BE", "BM", "CA", "CL",
                    "CT", "FT", "FO", "GM", "HO", "JA", "LR", "BT", "MI", "NI",
                    "PU", "PO", "SA", "SR", "TO", "VK", "VO", "SZ"]
    filters_fuel = ["G", "D", "L", "I", "K", "T", "E", "H"]
    if filter_brand in filters_brand:
        print(f'Selected filter {filter_brand}')
        driver.execute_script(f"fnSelectCar1('{filter_brand}')")
    else:
        print("Car brand filter not selected or selected wrong value")

    print(f'Selected filter {filter_year}')
    year = Select(driver.find_element_by_id("search_startYyyy"))
    year.select_by_value(filter_year)

    if filter_fuel in filters_fuel:
        print(f'Selected filter {filter_fuel}')
        fuel = Select(driver.find_element_by_id("search_fuelCd"))
        fuel.select_by_value(filter_fuel)
    else:
        print("Fuel type filter not selected or selected wrong value")

    driver.execute_script("fnSearch(1)")
    js_functions = get_links(driver)

    links = make_url(js_functions)
    get_content(driver, links, translator)
    time.sleep(5)
    driver.quit()
    print("Parsing ended")


def auth(driver):
    print('\nAuthentication...\n')
    time.sleep(1)
    driver.execute_script("location.href='/hp/auct/cmm/viewMain.do'")
    login = driver.find_element_by_name('userId')
    password = driver.find_element_by_name('userPwd')
    login.send_keys("154200")
    password.send_keys("0982")
    password.send_keys(Keys.ENTER)
    time.sleep(1)


def get_links(driver):
    table_top = driver.find_element_by_class_name("tbl-top").find_element_by_tag_name("em").text
    print(table_top, 'vehicles on pages')
    number_pages = ceil(int(table_top) / 20)
    page_list = []
    if int(table_top) > 30:
        for page in range(number_pages):
            time.sleep(3)
            table = driver.find_element_by_class_name("tbl-t02").find_element_by_tag_name(
                "tbody").find_elements_by_tag_name("tr")
            for tr in table:
                tr_link = tr.find_element_by_class_name("a_list").get_attribute("onclick")
                page_list.append(tr_link)
            print("\tPage", page + 1, "of", number_pages, "pages.")
            # Get next page
            if (page + 1) != number_pages:
                driver.execute_script(f"fnSearch({page + 2});return false; ")
    else:
        time.sleep(3)
        table = driver.find_element_by_class_name("tbl-t02").find_element_by_tag_name(
            "tbody").find_elements_by_tag_name("tr")
        for tr in table:
            tr_link = tr.find_element_by_class_name("a_list").get_attribute("onclick")
            page_list.append(tr_link)
        print("\tPage", 1)

    return page_list


def get_content(driver, links, translator):
    connect = mysql_сonnecting()
    for link in links:
        driver.get(link)

        time.sleep(3)
        main_container = driver.find_element_by_class_name("page-popup")
        vin = main_container.find_element_by_class_name("vehicle-detail"). \
            find_elements_by_class_name("tbl-v02")[0].find_element_by_xpath(".//tbody/tr[7]/td").text
        check_available = f"SELECT `url` FROM `ns_goods` WHERE `code`='{vin}'"
        response = read_query(connect, check_available)
        if len(response) != 0:
            print(f'Row already exist by URL {response[0][0]}')
        else:
            name_db = main_container.find_element_by_class_name("vehicle-tit").find_element_by_class_name("tit").text
            entry_num = main_container.find_element_by_class_name("vehicle-tit").find_element_by_tag_name("strong").text
            price = main_container.find_element_by_class_name("clfix").find_element_by_class_name("vehicle-info"). \
                find_element_by_class_name("starting-price").find_element_by_tag_name("em").text
            info_li = main_container.find_element_by_class_name("clfix").find_element_by_class_name("vehicle-info"). \
                find_element_by_tag_name("ul").find_elements_by_tag_name("li")
            entry_date = info_li[0].find_element_by_tag_name("strong").text
            car_number = info_li[1].find_element_by_tag_name("strong").text
            progress = info_li[2].find_element_by_tag_name("strong").text
            points = info_li[3].find_element_by_tag_name("strong").text

            detail_table = main_container.find_element_by_class_name("vehicle-detail"). \
                find_elements_by_class_name("tbl-v02")[1].find_element_by_tag_name("tbody")
            year_man_db = detail_table.find_element_by_xpath(".//tr[1]/td[1]").text
            mileage_db = detail_table.find_element_by_xpath(".//tr[1]/td[2]").text
            transmission_db = detail_table.find_element_by_xpath(".//tr[2]/td[2]").text
            engine_type_db = detail_table.find_element_by_xpath(".//tr[4]/td[2]").text
            engine_capacity_db = detail_table.find_element_by_xpath(".//tr[5]/td[2]").text
            car_type = detail_table.find_element_by_xpath(".//tr[6]/td[1]").text
            reg_year = detail_table.find_element_by_xpath(".//tr[2]/td[1]").text

            # Images
            images = []
            image_elements = main_container.find_element_by_class_name("vehicle-detail-view").find_element_by_xpath(
                ".//div[contains(@class, 'vehicle-photo-detail swiper-container swiper-container-horizontal')]"). \
                find_element_by_tag_name("ul").find_elements_by_tag_name("li")
            for element in image_elements:
                element = element.find_element_by_tag_name("img")
                images.append(element.get_attribute("src"))
            images.pop(0)
            images = images[:-1]
            defect_image = []
            if len(main_container.find_elements_by_class_name("car-status-map")) != 0:
                def_image = main_container.find_element_by_class_name("car-status-map").find_element_by_tag_name("img"). \
                    get_attribute("src")
                defect_image.append(def_image)

            # Video
            video_url = ''
            video = main_container.find_element_by_id("yesMovie").find_elements_by_id("video")
            if len(video) != 0:
                video_url = video[0].find_element_by_tag_name("source").get_attribute("src")

            video_url = str.replace(video_url, ".MP4?rel=0", ".MP4?rel=1")

            # Translation
            name_db = translator.translate(name_db)
            car_number = translator.translate(car_number)
            progress = translator.translate(progress)
            transmission_db = translator.translate(transmission_db)
            engine_type_db = translator.translate(engine_type_db)
            car_type = translator.translate(car_type)

            # Formatting
            url = vin + "-" + name_db
            url = str.replace(url, '+', '-')
            url = str.replace(url, '.', '-')
            url = str.replace(url, ' ', '-')
            url = str.replace(url, '-(D)', '')
            url = str.replace(url, '-(G)', '')
            url = str.replace(url, '-(L)', '')
            url = str.replace(url, '-(E)', '')
            url = str.replace(url, '/', '')
            url = str.replace(url, 'Ⅱ', '')
            url = url.lower()
            name_db = str.replace(name_db, 'All NEW ', '')
            name_db = str.replace(name_db, 'All New ', '')
            name_db = str.replace(name_db, 'ALL NEW', '')
            name_db = str.replace(name_db, 'ALL New', '')
            name_db = str.replace(name_db, 'THE NEW', '')
            name_db = str.replace(name_db, 'The New', '')
            name_db = str.replace(name_db, 'New ', '')
            name_db = str.replace(name_db, 'All ', '')
            name_db = str.replace(name_db, 'Ⅱ', '')
            points = str.replace(points, " ", "")
            price = float(str.replace(price, " ", "").strip())
            convertation = CurrencyConverter()
            price = float(ceil(convertation.convert(price * 10000, 'KRW', 'USD')))

            engine_capacity_db = (str.replace(engine_capacity_db, " cc", "")).strip()
            engine_capacity_db = str.replace(engine_capacity_db, " ", ".")
            engine_capacity_db = round(float(engine_capacity_db), 1)
            if engine_capacity_db == 998.0:
                engine_capacity_db = 1.0

            mileage_db = (str.replace(mileage_db, " Km", "")).strip()
            mileage_db = int(str.replace(mileage_db, " ", ""))

            chars = ''
            if engine_type_db.lower() == "diesel":
                engine_type_db = "Дизель"
                chars += "|77|"
            elif engine_type_db.lower() == "lpg":
                engine_type_db = 'Газ'
                chars += '|82|'
            elif engine_type_db.lower() == "gasoline":
                engine_type_db = 'Бензин'
                chars += '|79|'
            elif engine_type_db.lower() == "electric":
                engine_type_db = 'Электро'
                chars += '|78|'
            elif engine_type_db.lower() == "hybrid":
                engine_type_db = 'Гибрид'
                chars += '|80|'

            if transmission_db.lower() == 'automatic':
                transmission_db = 'Автомат'
                chars += '|31|'
            elif transmission_db.lower() == 'manual':
                transmission_db = 'Механика'
                chars += '|32|'

            if 'sedan' in car_type.lower():  # carType = 'Седан'
                car_type = "Sedan"
                chars += '|69|'
            elif 'suv' in car_type.lower():  # carType = 'Кроссовер'
                car_type = "SUV"
                chars += '|66|'
            elif 'van' in car_type.lower():  # carType = 'Минивэн'
                car_type = "Van/MiniVan"
                chars += '|68|'

            drive_type_db = 'Не указан'
            if "2wd" in name_db.lower():
                drive_type_db = 'Передний'
                chars += '|72|'
            elif "4wd" in name_db.lower():
                drive_type_db = 'Полный'
                chars += '|73|'
            elif "awd" in name_db.lower():
                drive_type_db = 'Полный'
                chars += '|73|'

            marka_db = ""
            model_db = ""
            # filterParamId
            if 'morning' in name_db.lower():  # Kia
                marka_db = "Kia"
                model_db = "Morning"
                chars += '|113|'
            if 'opirus' in name_db.lower() or 'lovers' in name_db.lower():
                marka_db = "Kia"
                model_db = "Opirus"
                chars += '|173|'
            if 'carnival' in name_db.lower():
                marka_db = "Kia"
                model_db = "Carnival"
                chars += '|120|'
            if 'forte' in name_db.lower() or 'strong couple' in name_db.lower():
                marka_db = "Kia"
                model_db = "Forte"
                chars += '|174|'
            if 'k3' in name_db.lower():
                marka_db = "Kia"
                model_db = "K3"
                chars += '|118|'
            if 'k5' in name_db.lower():
                marka_db = "Kia"
                model_db = "K5"
                chars += '|441|'
            if 'k7' in name_db.lower():
                marka_db = "Kia"
                model_db = "K7"
                chars += '|103|'
            if 'k9' in name_db.lower():
                marka_db = "Kia"
                model_db = "K9"
                chars += '|119|'
            if 'sorento' in name_db.lower():
                marka_db = "Kia"
                model_db = "Sorento"
                chars += '|135|'
            if 'mojave' in name_db.lower() or 'mohave' in name_db.lower():
                marka_db = "Kia"
                model_db = "Mojave"
                chars += '|175|'
            if 'bongo' in name_db.lower() or 'rhino' in name_db.lower():
                marka_db = "Kia"
                model_db = "Bongo"
                chars += '|176|'
            if 'sportage' in name_db.lower():
                marka_db = "Kia"
                model_db = "Sportage"
                chars += '|111|'
            if 'soul' in name_db.lower():
                marka_db = "Kia"
                model_db = "Soul"
                chars += '|136|'
            if 'carens' in name_db.lower() or 'carena' in name_db.lower():
                marka_db = "Kia"
                model_db = "Carens"
                chars += '|177|'
            if 'roche' in name_db.lower() or 'lotze' in name_db.lower():
                marka_db = "Kia"
                model_db = "Roche"
                chars += '|178|'
            if 'serato' in name_db.lower() or 'cerato' in name_db.lower() or 'waxed' in name_db.lower():
                marka_db = "Kia"
                model_db = "Serato"
                chars += '|179|'
            if 'optima' in name_db.lower():
                marka_db = "Kia"
                model_db = "Optima"
                chars += '|180|'
            if 'casta' in name_db.lower():
                marka_db = "Kia"
                model_db = "Casta"
                chars += '|181|'
            if 'combi' in name_db.lower():
                marka_db = "Kia"
                model_db = "Combi"
                chars += '|182|'
            if 'tauner' in name_db.lower() or 'towner' in name_db.lower():
                marka_db = "Kia"
                model_db = "Tauner"
                chars += '|183|'
            if 'hunger pride' in name_db.lower() or 'pride' in name_db.lower():
                marka_db = "Kia"
                model_db = "Hunger Pride"
                chars += '|184|'
            if 'ray' in name_db.lower():
                marka_db = "Kia"
                model_db = "Ray"
                chars += '|132|'
            if 'grandbird' in name_db.lower():
                marka_db = "Kia"
                model_db = "Grandbird"
                chars += '|185|'
            if 'niro' in name_db.lower():
                marka_db = "Kia"
                model_db = "Niro"
                chars += '|186|'
            if 'stinger' in name_db.lower():
                marka_db = "Kia"
                model_db = "Stinger"
                chars += '|121|'
            if 'hunger stony' in name_db.lower():
                marka_db = "Kia"
                model_db = "Hunger Stony"
                chars += '|187|'
            if 'seltos' in name_db.lower():
                marka_db = "Kia"
                model_db = "Seltos"
                chars += '|134|'
            if 'stonic' in name_db.lower():
                marka_db = "Kia"
                model_db = "Stonic"
                chars += '|133|'
            if 'sonata' in name_db.lower():  # Hyundai
                marka_db = "Hyundai"
                model_db = "Sonata"
                chars += '|112|'
            if 'grandeur' in name_db.lower() or 'size' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Grandeur"
                chars += '|105|'
            if 'verna' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Verna"
                chars += '|188|'
            if 'eye certi' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Eye Certi"
                chars += '|189|'
            if 'click' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Click"
                chars += '|190|'
            if 'avante' in name_db.lower() or 'advantageous' in name_db.lower() or 'forward' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Avante"
                chars += '|106|'
            if 'equus' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Equus"
                chars += '|191|'
            if 'starex' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Starex"
                chars += '|192|'
            if 'veracruz' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Veracruz"
                chars += '|193|'
            if 'santa fe' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "SantaFe"
                chars += '|95|'
            if 'santafe' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "SantaFe"
                chars += '|95|'
            if 'tucson' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Tucson"
                chars += '|109|'
            if 'porter' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Porter"
                chars += '|194|'
            if 'country' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Country"
                chars += '|195|'
            if 'grace' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Grace"
                chars += '196'
            if 'dynasty' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Dynasty"
                chars += '|197|'
            if 'lavita' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Lavita"
                chars += '|198|'
            if 'libero' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Libero"
                chars += '|199|'
            if 'marsha' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Marsha"
                chars += '|200|'
            if 'mighty' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Mighty"
                chars += '|201|'
            if 'aerotown' in name_db.lower() or 'aero town' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Aerotown"
                chars += '|202|'
            if 'accent' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Accent"
                chars += '|138|'
            if 'chorus' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Modern Chorus"
                chars += '203'
            if 'terracan' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Terracan"
                chars += '|204|'
            if 'tuscany' in name_db.lower() or 'tuscani' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Tuscany"
                chars += '|205|'
            if 'trajet' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Trajet"
                chars += '|206|'
            if 'truck' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Truck"
                chars += '|207|'
            if 'universe' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Universe"
                chars += '|208|'
            if 'veloster' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Veloster"
                chars += '|140|'
            if 'ipodi' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "iPodi"
                chars += '|209|'
            if 'maxcruise' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Maxcruise"
                chars += '|102|'
            if 'max cruise' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Maxcruise"
                chars += '|102|'
            if 'aslan' in name_db.lower() or 'lion ' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Aslan"
                chars += '|210|'
            if 'green city' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Green City"
                chars += '|211|'
            if 'unicity' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Unicity"
                chars += '|212|'
            if 'solati' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Solati"
                chars += '|213|'
            if 'ionic' in name_db.lower() or 'ioniq' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Ionic"
                chars += '|214|'
            if 'kona' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Kona"
                chars += '|137|'
            if 'csm truck' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Soosan CSM truck"
                chars += '|215|'
            if 'nexo' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Nexo"
                chars += '|216|'
            if 'palisade' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Palisade"
                chars += '|143|'
            if 'sungjin potter' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Sungjin Potter"
                chars += '|217|'
            if 'venue' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Venue"
                chars += '|139|'
            if 'dasan heavy industries mighty' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Dasan Heavy Industries Mighty"
                chars += '|218|'
            if 'i30' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "i30"
                chars += '|141|'
            if 'maxcruz' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "Maxcruz"
                chars += '|142|'
            if 'i40' in name_db.lower():
                marka_db = "Hyundai"
                model_db = "i40"
                chars += '|144|'
            if 'rav4' in name_db.lower():  # Toyota
                marka_db = "Toyota"
                model_db = "Rav4"
                chars += '|219|'
            if 'camry' in name_db.lower():
                marka_db = "Toyota"
                model_db = "Camry"
                chars += '|125|'
            if 'prius' in name_db.lower():
                marka_db = "Toyota"
                model_db = "Prius"
                chars += '|220|'
            if 'avalon' in name_db.lower():
                marka_db = "Toyota"
                model_db = "Avalon"
                chars += '|221|'
            if 'vivi' in name_db.lower():
                marka_db = "Toyota"
                model_db = "Vivi"
                chars += '|222|'
            if 'corolla' in name_db.lower():
                marka_db = "Toyota"
                model_db = "Corolla"
                chars += '|223|'
            if 'sienna' in name_db.lower():
                marka_db = "Toyota"
                model_db = "Sienna"
                chars += '|126|'
            if 'benza' in name_db.lower():
                marka_db = "Toyota"
                model_db = "Benza"
                chars += '|224|'
            if 'fj cruiser' in name_db.lower():
                marka_db = "Toyota"
                model_db = "FJ Cruiser"
                chars += '|225|'
            if 'land cruiser 200' in name_db.lower():
                marka_db = "Toyota"
                model_db = "Land Cruiser 200"
                chars += '|116|'
            if 'es ' in name_db.lower():  # Lexus
                marka_db = "Lexus"
                model_db = "ES"
                chars += '|226|'
            if 'gs ' in name_db.lower():
                marka_db = "Lexus"
                model_db = "GS"
                chars += '|227|'
            if 'ls ' in name_db.lower():
                marka_db = "Lexus"
                model_db = "LS"
                chars += '|228|'
            if 'rx ' in name_db.lower():
                marka_db = "Lexus"
                model_db = "RX"
                chars += '|229|'
            if 'sc ' in name_db.lower():
                marka_db = "Lexus"
                model_db = "SC"
                chars += '|230|'
            if 'gs ' in name_db.lower():
                marka_db = "Lexus"
                model_db = "GS"
                chars += '|231|'
            if 'ct ' in name_db.lower():
                marka_db = "Lexus"
                model_db = "CT"
                chars += '|232|'
            if 'nx ' in name_db.lower():
                marka_db = "Lexus"
                model_db = "NX"
                chars += '|233|'
            if 'rc ' in name_db.lower():
                marka_db = "Lexus"
                model_db = "RC"
                chars += '|234|'
            if 'ux ' in name_db.lower():
                marka_db = "Lexus"
                model_db = "UX"
                chars += '|235|'
            if 'eq900' in name_db.lower():  # Genesis
                marka_db = "Genesis"
                model_db = "EQ900"
                chars += '|94|'
            if 'g80' in name_db.lower():
                marka_db = "Genesis"
                model_db = "G80"
                chars += '|145|'
            if 'g70' in name_db.lower():
                marka_db = "Genesis"
                model_db = "G70"
                chars += '|236|'
            if 'g90' in name_db.lower():
                marka_db = "Genesis"
                model_db = "G90"
                chars += '|237|'
            if 'gv80' in name_db.lower():
                marka_db = "Genesis"
                model_db = "GV80"
                chars += '|238|'
            if 'gv70' in name_db.lower():
                marka_db = "Genesis"
                model_db = "GV70"
                chars += '|239|'
            if 'winstorm' in name_db.lower():  # GM
                marka_db = "GM"
                model_db = "Winstorm"
                chars += '|240|'
            if 'tosca' in name_db.lower():
                marka_db = "GM"
                model_db = "Tosca"
                chars += '|241|'
            if 'alpheon' in name_db.lower():
                marka_db = "GM"
                model_db = "Alpheon"
                chars += '|242|'
            if 'gentra' in name_db.lower():
                marka_db = "GM"
                model_db = "Gentra"
                chars += '|243|'
            if 'lacetti' in name_db.lower():
                marka_db = "GM"
                model_db = "Lacetti"
                chars += '|244|'
            if 'matiz' in name_db.lower():
                marka_db = "GM"
                model_db = "Matiz"
                chars += '|245|'
            if 'damas' in name_db.lower():
                marka_db = "GM"
                model_db = "Damas"
                chars += '|246|'
            if 'veritas' in name_db.lower():
                marka_db = "GM"
                model_db = "Veritas"
                chars += '|247|'
            if 'lab ' in name_db.lower() or 'labo ' in name_db.lower():
                marka_db = "GM"
                model_db = "Lab"
                chars += '|248|'
            if 'statesman' in name_db.lower():
                marka_db = "GM"
                model_db = "Statesman"
                chars += '|249|'
            if 'spark' in name_db.lower():
                marka_db = "GM"
                model_db = "Spark"
                chars += '|124|'
            if 'aveo' in name_db.lower():
                marka_db = "GM"
                model_db = "Aveo"
                chars += '|250|'
            if 'cruise ' in name_db.lower() or 'cruze ' in name_db.lower():
                marka_db = "GM"
                model_db = "Cruise"
                chars += '|251|'
            if 'orlando' in name_db.lower():
                marka_db = "GM"
                model_db = "Orlando"
                chars += '|252|'
            if 'captiva' in name_db.lower():
                marka_db = "GM"
                model_db = "Captiva"
                chars += '|253|'
            if 'malibu' in name_db.lower():
                marka_db = "GM"
                model_db = "Malibu"
                chars += '|254|'
            if 'corvette' in name_db.lower():
                marka_db = "GM"
                model_db = "Corvette"
                chars += '|255|'
            if 'trax' in name_db.lower():
                marka_db = "GM"
                model_db = "Trax"
                chars += '|256|'
            if 'camaro' in name_db.lower():
                marka_db = "GM"
                model_db = "Camaro"
                chars += '|257|'
            if 'impala' in name_db.lower():
                marka_db = "GM"
                model_db = "Impala"
                chars += '|258|'
            if 'volt' in name_db.lower() or 'bolt' in name_db.lower():
                marka_db = "GM"
                model_db = "Volt"
                chars += '|259|'
            if 'equinox' in name_db.lower():
                marka_db = "GM"
                model_db = "Equinox"
                chars += '|260|'
            if 'colorado' in name_db.lower():
                marka_db = "GM"
                model_db = "Colorado"
                chars += '|261|'
            if 'traverse' in name_db.lower():
                marka_db = "GM"
                model_db = "Traverse"
                chars += '|262|'
            if 'trail blazer' in name_db.lower():
                marka_db = "GM"
                model_db = "Trail Blazer"
                chars += '|263|'
            if 'gm express' in name_db.lower():
                marka_db = "GM"
                model_db = "Express"
                chars += '|264|'
            if 'sm3 ' in name_db.lower():  # Renault Samsung
                marka_db = "Renault Samsung"
                model_db = "SM3"
                chars += '|265|'
            if 'sm5 ' in name_db.lower() or 'sm 5' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "SM5"
                chars += '|266|'
            if 'sm7 ' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "SM7"
                chars += '|267|'
            if 'qm5 ' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "QM5"
                chars += '|268|'
            if 'yamujin' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "Yamujin"
                chars += '|269|'
            if 'qm3 ' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "QM3"
                chars += '|270|'
            if 'sm6 ' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "SM6"
                chars += '|271|'
            if 'qm6 ' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "QM6"
                chars += '|272|'
            if 'tweed' in name_db.lower() or 'twizy' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "Tweed"
                chars += '|273|'
            if 'clio' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "Clio"
                chars += '|274|'
            if 'master ' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "Master"
                chars += '|275|'
            if 'captur ' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "Captur"
                chars += '|276|'
            if 'joe ' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "Joe"
                chars += '|277|'
            if 'coban' in name_db.lower():
                marka_db = "Renault Samsung"
                model_db = "Kwangil Indastry Coban Camper"
                chars += '|278|'
            if 'chairman' in name_db.lower():  # Ssangyong
                marka_db = "Ssangyong"
                model_db = "Chairman"
                chars += '|279|'
            if 'rexton' in name_db.lower():
                marka_db = "Ssangyong"
                model_db = "Rexton"
                chars += '|280|'
            if 'rodius' in name_db.lower():
                marka_db = "Ssangyong"
                model_db = "Rodius"
                chars += '|281|'
            if 'actyon' in name_db.lower():
                marka_db = "Ssangyong"
                model_db = "Actyon"
                chars += '|282|'
            if 'kyron' in name_db.lower():
                marka_db = "Ssangyong"
                model_db = "Kyron"
                chars += '|283|'
            if 'musso' in name_db.lower() or 'musser' in name_db.lower():
                marka_db = "Ssangyong"
                model_db = "Musso"
                chars += '|284|'
            if 'istana' in name_db.lower():
                marka_db = "Ssangyong"
                model_db = "Istana"
                chars += '|285|'
            if 'korando ' in name_db.lower():
                marka_db = "Ssangyong"
                model_db = "Korando"
                chars += '|286|'
            if 'tivoli' in name_db.lower():
                marka_db = "Ssangyong"
                model_db = "Tivoli"
                chars += '|287|'
            if 'vintage ' in name_db.lower():  # Aston Martin
                marka_db = "Aston Martin"
                model_db = "Vintage"
                chars += '|288|'
            if 'vanish ' in name_db.lower():
                marka_db = "Aston Martin"
                model_db = "Vanish"
                chars += '|289|'
            if 'a4 ' in name_db.lower():  # Audi
                marka_db = "Audi"
                model_db = "A4"
                chars += '|290|'
            if 'a5 ' in name_db.lower():
                marka_db = "Audi"
                model_db = "A5"
                chars += '|291|'
            if 'a6 ' in name_db.lower():
                marka_db = "Audi"
                model_db = "A6"
                chars += '|292|'
            if 'a8 ' in name_db.lower():
                marka_db = "Audi"
                model_db = "A8"
                chars += '|293|'
            if 'q5 ' in name_db.lower():
                marka_db = "Audi"
                model_db = "Q5"
                chars += '|294|'
            if 'q7 ' in name_db.lower():
                marka_db = "Audi"
                model_db = "Q7"
                chars += '|295|'
            if 'aude r' in name_db.lower():
                marka_db = "Audi"
                model_db = "R"
                chars += '|296|'
            if 'audi s' in name_db.lower():
                marka_db = "Audi"
                model_db = "S"
                chars += '|297|'
            if 'tt ' in name_db.lower():
                marka_db = "Audi"
                model_db = "TT"
                chars += '|298|'
            if 'audi rs' in name_db.lower():
                marka_db = "Audi"
                model_db = "RS"
                chars += '|299|'
            if 'a7 ' in name_db.lower():
                marka_db = "Audi"
                model_db = "A7"
                chars += '|300|'
            if 'q3 ' in name_db.lower():
                marka_db = "Audi"
                model_db = "Q3"
                chars += '|301|'
            if 'audi sq' in name_db.lower():
                marka_db = "Audi"
                model_db = "SQ"
                chars += '|302|'
            if 'audi a1 ' in name_db.lower():
                marka_db = "Audi"
                model_db = "A1"
                chars += '|303|'
            if 'q8 ' in name_db.lower():
                marka_db = "Audi"
                model_db = "Q8"
                chars += '|304|'
            if 'e-tron ' in name_db.lower():
                marka_db = "Audi"
                model_db = "E-tron"
                chars += '|305|'
            if 'q2 ' in name_db.lower():
                marka_db = "Audi"
                model_db = "Q2"
                chars += '|306|'
            if 'flying spur' in name_db.lower():  # Bentley
                marka_db = "Bentley"
                model_db = "Flying Spur"
                chars += '|307|'
            if 'gt contonental' in name_db.lower():
                marka_db = "Bentley"
                model_db = "GT Contonental"
                chars += '|308|'
            if 'gtc contonental' in name_db.lower():
                marka_db = "Bentley"
                model_db = "GTC Contonental"
                chars += '|309|'
            if 'arnage' in name_db.lower():
                marka_db = "Bentley"
                model_db = "Arnage"
                chars += '|310|'
            if 'mulsanne' in name_db.lower():
                marka_db = "Bentley"
                model_db = "Mulsanne"
                chars += '|311|'
            if 'bmw 1' in name_db.lower():  # BMW
                marka_db = "BMW"
                model_db = "1 series"
                chars += '|312|'
            if 'bmw 3' in name_db.lower():
                marka_db = "BMW"
                model_db = "3 series"
                chars += '|313|'
            if 'bmw 5' in name_db.lower():
                marka_db = "BMW"
                model_db = "5 series"
                chars += '|314|'
            if 'bmw 7' in name_db.lower():
                marka_db = "BMW"
                model_db = "7 series"
                chars += '|315|'
            if 'bmw 6' in name_db.lower():
                marka_db = "BMW"
                model_db = "6 series"
                chars += '|316|'
            if 'bmw 4' in name_db.lower():
                marka_db = "BMW"
                model_db = "4 series"
                chars += '|317|'
            if 'bmw 2' in name_db.lower():
                marka_db = "BMW"
                model_db = "2 series"
                chars += '|318|'
            if 'bmw 8' in name_db.lower():
                marka_db = "BMW"
                model_db = "8 series"
                chars += '|319|'
            if 'bmw mini ' in name_db.lower():
                marka_db = "BMW"
                model_db = "MINI"
                chars += '|320|'
            if 'bmw gt' in name_db.lower():
                marka_db = "BMW"
                model_db = "GT"
                chars += '|321|'
            if 'bmw m' in name_db.lower():
                marka_db = "BMW"
                model_db = "M"
                chars += '|322|'
            if 'bmw x' in name_db.lower():
                marka_db = "BMW"
                model_db = "X"
                chars += '|323|'
            if 'bmw z' in name_db.lower():
                marka_db = "BMW"
                model_db = "Z"
                chars += '|324|'
            if 'bmw i' in name_db.lower():
                marka_db = "BMW"
                model_db = "I"
                chars += '|325|'
            if 'cadillac' in name_db.lower():  # Cadillac
                marka_db = "Cadillac"
                model_db = "Cadillac"
                chars += '|326|'
            if 'cadillac' in name_db.lower() and 'sts' in name_db.lower():
                marka_db = "Cadillac"
                model_db = "STS"
                chars += '|327|'
            if 'cadillac' in name_db.lower() and 'cts' in name_db.lower():
                marka_db = "Cadillac"
                model_db = "CTS"
                chars += '|328|'
            if 'cadillac' in name_db.lower() and 'escalade' in name_db.lower():
                marka_db = "Cadillac"
                model_db = "Escalade"
                chars += '|329|'
            if 'cadillac' in name_db.lower() and 'ct6' in name_db.lower():
                marka_db = "Cadillac"
                model_db = "CT6"
                chars += '|330|'
            if 'cadillac' in name_db.lower() and 'xt5' in name_db.lower():
                marka_db = "Cadillac"
                model_db = "XT5"
                chars += '|331|'
            if 'wrangler' in name_db.lower():  # Chrysler/Jeep
                marka_db = "Jeep"
                model_db = "Wrangler"
                chars += '|332|'
            if 'cherokee' in name_db.lower():
                marka_db = "Jeep"
                model_db = "Cherokee"
                chars += '|333|'
            if 'caravan' in name_db.lower():
                marka_db = "Chrysler"
                model_db = "Caravan"
                chars += '|334|'
            if 'chrysler 300c' in name_db.lower():
                marka_db = "Chrysler"
                model_db = "300C"
                chars += '|335|'
            if 'chrysler 300m' in name_db.lower():
                marka_db = "Chrysler"
                model_db = "300M"
                chars += '|336|'
            if 'renegade' in name_db.lower():
                marka_db = "Jeep"
                model_db = "Renegad"
                chars += '|337|'
            if 'ds3 ' in name_db.lower():  # Citroen
                marka_db = "Citroen"
                model_db = "DS3"
                chars += '|338|'
            if 'ds4 ' in name_db.lower():
                marka_db = "Citroen"
                model_db = "DS4"
                chars += '|339|'
            if 'ds5 ' in name_db.lower():
                marka_db = "Citroen"
                model_db = "DS5"
                chars += '|340|'
            if 'cactus' in name_db.lower():
                marka_db = "Citroen"
                model_db = "Cactus"
                chars += '|341|'
            if 'c3 ' in name_db.lower():
                marka_db = "Citroen"
                model_db = "C3"
                chars += '|342|'
            if 'c4 ' in name_db.lower():
                marka_db = "Citroen"
                model_db = "C4"
                chars += '|343|'
            if 'c5 ' in name_db.lower():
                marka_db = "Citroen"
                model_db = "C5"
                chars += '|344|'
            if 'fiat' in name_db.lower() and '500' in name_db.lower():  # Fiat
                marka_db = "Fiat"
                model_db = "500"
                chars += '|345|'
            if 'fremont' in name_db.lower():
                marka_db = "Fiat"
                model_db = "Fremont"
                chars += '|346|'
            if 'ford focus' in name_db.lower():  # Ford
                marka_db = "Ford"
                model_db = "Focus"
                chars += '|347|'
            if 'ford fusion' in name_db.lower():
                marka_db = "Ford"
                model_db = "Fusion"
                chars += '|348|'
            if 'ford explorer' in name_db.lower() or 'explorer' in name_db.lower():
                marka_db = "Ford"
                model_db = "Explorer"
                chars += '|349|'
            if 'ford taurus' in name_db.lower():
                marka_db = "Ford"
                model_db = "Taurus"
                chars += '|350|'
            if 'ford excape' in name_db.lower():
                marka_db = "Ford"
                model_db = "Escape"
                chars += '|351|'
            if 'ford mustang' in name_db.lower():
                marka_db = "Ford"
                model_db = "Mustang"
                chars += '|352|'
            if 'mondeo' in name_db.lower():
                marka_db = "Ford"
                model_db = "Mondeo"
                chars += '|353|'
            if 'ford 500' in name_db.lower():
                marka_db = "Ford"
                model_db = "500"
                chars += '|345|'
            if 'kuga' in name_db.lower():
                marka_db = "Ford"
                model_db = "Kuga"
                chars += '|354|'
            if 'chevy' in name_db.lower() and 'van' in name_db.lower():  # Chevy
                marka_db = "Chevy"
                model_db = "VAN"
                chars += '|355|'
            if 'honda civic' in name_db.lower():  # Honda
                marka_db = "Honda"
                model_db = "Civic"
                chars += '|356|'
            if 'honda accord' in name_db.lower() or 'agreement' in name_db.lower():
                marka_db = "Honda"
                model_db = "Accord"
                chars += '|357|'
            if 'cr-v' in name_db.lower():
                marka_db = "Honda"
                model_db = "CR-V"
                chars += '|358|'
            if 'odyssey' in name_db.lower():
                marka_db = "Honda"
                model_db = "Odyssey"
                chars += '|359|'
            if 'pilot' in name_db.lower():
                marka_db = "Honda"
                model_db = "Pilot"
                chars += '|360|'
            if 'cr-z' in name_db.lower():
                marka_db = "Honda"
                model_db = "CR-Z"
                chars += '|361|'
            if 's660' in name_db.lower():
                marka_db = "Honda"
                model_db = "S660"
                chars += '|362|'
            if 'jaguar' in name_db.lower() and 'xf' in name_db.lower():  # Jaguar
                marka_db = "Jaguar"
                model_db = "XF"
                chars += '|363|'
            if 'jaguar' in name_db.lower() and 'xj' in name_db.lower():
                marka_db = "Jaguar"
                model_db = "XJ"
                chars += '|364|'
            if 'f-type' in name_db.lower():
                marka_db = "Jaguar"
                model_db = "F-Type"
                chars += '|365|'
            if 'jaguar' in name_db.lower() and '20d' in name_db.lower():
                marka_db = "Jaguar"
                model_db = "XE"
                chars += '|366|'
            if 'discovery' in name_db.lower():  # Land Rover
                marka_db = "Land Rover"
                model_db = "Discovery"
                chars += '|367|'
            if 'range rover' in name_db.lower():
                marka_db = "Land Rover"
                model_db = "Range Rover"
                chars += '|368|'
            if 'freelander' in name_db.lower():
                marka_db = "Land Rover"
                model_db = "Freelander"
                chars += '|369|'
            if 'defender' in name_db.lower():
                marka_db = "Land Rover"
                model_db = "Defender"
                chars += '|370|'
            if 'mks' in name_db.lower():  # Lincoln
                marka_db = "Lincoln"
                model_db = "MKS"
                chars += '|371|'
            if 'mkx' in name_db.lower():
                marka_db = "Lincoln"
                model_db = "MKX"
                chars += '|372|'
            if 'mkz' in name_db.lower():
                marka_db = "Lincoln"
                model_db = "MKZ"
                chars += '|373|'
            if 'mkc' in name_db.lower():
                marka_db = "Lincoln"
                model_db = "MKC"
                chars += '|374|'
            if 'levante' in name_db.lower():  # Maserati
                marka_db = "Maserati"
                model_db = "Levante"
                chars += '|375|'
            if 'ghibli' in name_db.lower():
                marka_db = "Maserati"
                model_db = "Ghibli"
                chars += '|376|'
            if 'benz b' in name_db.lower():  # Mercedes Benz
                marka_db = "Mercedes Benz"
                model_db = "B Class"
                chars += '|377|'
            if 'benz c ' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "C Class"
                chars += '|378|'
            if 'benz cls' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "CLS Class"
                chars += '|379|'
            if 'benz e' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "E Class"
                chars += '|380|'
            if 'benz glk' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "GLK Class"
                chars += '|381|'
            if 'benz m ' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "M Class"
                chars += '|382|'
            if 'benz ml' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "ML Class"
                chars += '|383|'
            if 'benz s ' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "S Class"
                chars += '|384|'
            if 'benz slk' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "SLK Class"
                chars += '|385|'
            if 'benz g ' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "G Class"
                chars += '|386|'
            if 'benz sprinter' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "Sprinter"
                chars += '|387|'
            if 'benz a ' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "A Class"
                chars += '|388|'
            if 'benz cla' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "CLA Class"
                chars += '|389|'
            if 'benz gla' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "GLA Class"
                chars += '|390|'
            if 'benz gt' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "GT"
                chars += '|321|'
            if 'benz glc' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "GLC Class"
                chars += '|391|'
            if 'benz gle' in name_db.lower():
                marka_db = "Mercedes Benz"
                model_db = "GLE Class"
                chars += '|392|'
            if 'lancer' in name_db.lower():  # Mitsibishi
                marka_db = "Mitsibishi"
                model_db = "Lancer"
                chars += '|393|'
            if 'outlander' in name_db.lower():
                marka_db = "Mitsibishi"
                model_db = "Outlander"
                chars += '|394|'
            if 'rogue' in name_db.lower():  # Nissan
                marka_db = "Nissan"
                model_db = "Rogue"
                chars += '|395|'
            if 'murano' in name_db.lower():
                marka_db = "Nissan"
                model_db = "Murano"
                chars += '|396|'
            if 'altima' in name_db.lower():
                marka_db = "Nissan"
                model_db = "Altima"
                chars += '|397|'
            if 'cube' in name_db.lower():
                marka_db = "Nissan"
                model_db = "Cube"
                chars += '|398|'
            if 'nissan juke' in name_db.lower():
                marka_db = "Nissan"
                model_db = "Juke"
                chars += '|399|'
            if 'nissan path' in name_db.lower():
                marka_db = "Nissan"
                model_db = "Pathfinder"
                chars += '|400|'
            if 'nissan qashqai' in name_db.lower():
                marka_db = "Nissan"
                model_db = "Qashqai"
                chars += '|401|'
            if 'nissan maxima' in name_db.lower():
                marka_db = "Nissan"
                model_db = "Maxima"
                chars += '|402|'
            if 'infinity fx' in name_db.lower():  # Infinity
                marka_db = "Infinity"
                model_db = "FX"
                chars += '|403|'
            if 'infinity g' in name_db.lower():
                marka_db = "Infinity"
                model_db = "G"
                chars += '|404|'
            if 'infinity m' in name_db.lower():
                marka_db = "Infinity"
                model_db = "M"
                chars += '|322|'
            if 'infinity qx' in name_db.lower():
                marka_db = "Infinity"
                model_db = "QX"
                chars += '|405|'
            if 'infinity q ' in name_db.lower():
                marka_db = "Infinity"
                model_db = "Q"
                chars += '|406|'
            if 'peugeot 207' in name_db.lower():  # Peugeot
                marka_db = "Peugeot"
                model_db = "207"
                chars += '|407|'
            if 'peugeot 307' in name_db.lower():
                marka_db = "Peugeot"
                model_db = "307"
                chars += '|408|'
            if 'peugeot 308' in name_db.lower():
                marka_db = "Peugeot"
                model_db = "308"
                chars += '|409|'
            if 'peugeot 407' in name_db.lower():
                marka_db = "Peugeot"
                model_db = "407"
                chars += '|410|'
            if 'peugeot 508' in name_db.lower():
                marka_db = "Peugeot"
                model_db = "508"
                chars += '|411|'
            if 'peugeot 3008' in name_db.lower():
                marka_db = "Peugeot"
                model_db = "3008"
                chars += '|412|'
            if 'peugeot 208' in name_db.lower():
                marka_db = "Peugeot"
                model_db = "208"
                chars += '|413|'
            if 'peugeot 2008' in name_db.lower():
                marka_db = "Peugeot"
                model_db = "2008"
                chars += '|414|'
            if 'peugeot 5008' in name_db.lower():
                marka_db = "Peugeot"
                model_db = "5008"
                chars += '|415|'
            if 'porche panamera' in name_db.lower():  # Porche
                marka_db = "Porche"
                model_db = "Panamera"
                chars += '|416|'
            if 'porche cayman' in name_db.lower():
                marka_db = "Porche"
                model_db = "Cayman"
                chars += '|417|'
            if 'porche cayenne' in name_db.lower():
                marka_db = "Porche"
                model_db = "Cayenne"
                chars += '|418|'
            if 'saab 9-3' in name_db.lower():  # Saab
                marka_db = "Saab"
                model_db = "9-3"
                chars += '|419|'
            if 'saab 9-5' in name_db.lower():
                marka_db = "Saab"
                model_db = "9-5"
                chars += '|420|'
            if 'beetle' in name_db.lower():  # Volkswagen
                marka_db = "Volkswagen"
                model_db = "Beetle"
                chars += '|421|'
            if 'volkswagen jetta' in name_db.lower():
                marka_db = "Volkswagen"
                model_db = "Jetta"
                chars += '|422|'
            if 'volkswagen passat' in name_db.lower():
                marka_db = "Volkswagen"
                model_db = "Passat"
                chars += '|423|'
            if 'volkswagen phaeton' in name_db.lower():
                marka_db = "Volkswagen"
                model_db = "Phaeton"
                chars += '|424|'
            if 'volkswagen golf' in name_db.lower():
                marka_db = "Volkswagen"
                model_db = "Golf"
                chars += '|425|'
            if 'tiguan' in name_db.lower():
                marka_db = "Volkswagen"
                model_db = "Tiguan"
                chars += '|426|'
            if 'volkswagen touareg' in name_db.lower():
                marka_db = "Volkswagen"
                model_db = "Touareg"
                chars += '|427|'
            if 'volkswagen scirocco' in name_db.lower():
                marka_db = "Volkswagen"
                model_db = "Scirocco"
                chars += '|428|'
            if 'volkswagen polo' in name_db.lower():
                marka_db = "Volkswagen"
                model_db = "Polo"
                chars += '|429|'
            if 'volvo s60' in name_db.lower():  # Volvo
                marka_db = "Volvo"
                model_db = "S60"
                chars += '|430|'
            if 'volvo s80' in name_db.lower():
                marka_db = "Volvo"
                model_db = "S80"
                chars += '|431|'
            if 'volvo xc60' in name_db.lower():
                marka_db = "Volvo"
                model_db = "XC60"
                chars += '|432|'
            if 'volvo xc70' in name_db.lower():
                marka_db = "Volvo"
                model_db = "XC70"
                chars += '|433|'
            if 'volvo xc90' in name_db.lower():
                marka_db = "Volvo"
                model_db = "XC90"
                chars += '|434|'
            if 'volvo s40' in name_db.lower():
                marka_db = "Volvo"
                model_db = "S40"
                chars += '|435|'
            if 'volvo v60' in name_db.lower():
                marka_db = "Volvo"
                model_db = "V60"
                chars += '|436|'
            if 'volvo v40' in name_db.lower():
                marka_db = "Volvo"
                model_db = "V40"
                chars += '437'
            if 'volvo s90' in name_db.lower():
                marka_db = "Volvo"
                model_db = "S90"
                chars += '|438|'
            if 'hustler' in name_db.lower():  # Suzuki
                marka_db = "Suzuki"
                model_db = "Hustler"
                chars += '|439|'
            if 'tata daewoo' in name_db.lower():  # Daewoo
                marka_db = "Daewoo"
                model_db = "Tata"
                chars += '|440|'

            if marka_db == 'Kia':
                chars += '|86|'
            if marka_db == 'Hyundai':
                chars += '|85|'
            if marka_db == 'Toyota':
                chars += '|115|'
            if marka_db == 'Lexus':
                chars += '|107|'
            if marka_db == 'Genesis':
                chars += '|93|'
            if marka_db == 'GM':
                chars += '|87|'
            if marka_db == 'Renault Samsung':
                chars += '|88|'
            if marka_db == 'Ssangyong':
                chars += '|89|'
            if marka_db == 'Aston Martin':
                chars += '|146|'
            if marka_db == 'Audi':
                chars += '|147|'
            if marka_db == 'Bentley':
                chars += '|148|'
            if marka_db == 'BMW' or 'BMW' in name_db:
                chars += '|149|'
            if marka_db == 'Cadillac':
                chars += '|150|'
            if marka_db == 'Chrysler':
                chars += '|151|'
            if marka_db == 'Jeep':
                chars += '|152|'
            if marka_db == 'Citroen':
                chars += '|153|'
            if marka_db == 'Fiat':
                chars += '|154|'
            if marka_db == 'Ford':
                chars += '|155|'
            if marka_db == 'Chevy':
                chars += '|156|'
            if marka_db == 'Honda':
                chars += '|157|'
            if marka_db == 'Jaguar':
                chars += '|158|'
            if marka_db == 'Land Rover':
                chars += '|159|'
            if marka_db == 'Lincoln':
                chars += '|160|'
            if marka_db == 'Maserati':
                chars += '|161|'
            if marka_db == 'Mercedes Benz':
                chars += '|162|'
            if marka_db == 'Mitsubishi':
                chars += '|163|'
            if marka_db == 'Nissan':
                chars += '|164|'
            if marka_db == 'Infinity':
                chars += '|165|'
            if marka_db == 'Peugeot':
                chars += '|166|'
            if marka_db == 'Porsche':
                chars += '|167|'
            if marka_db == 'Saab':
                chars += '|168|'
            if marka_db == 'Volkswagen':
                chars += '|169|'
            if marka_db == 'Volvo':
                chars += '|170|'
            if marka_db == 'Suzuki':
                chars += '|171|'
            if marka_db == 'Rolls Royce':
                chars += '|172|'

            car_class = str.replace(name_db, marka_db.upper(), "")
            car_class = str.replace(car_class, model_db.upper(), "")
            car_class = str.replace(car_class, f"{engine_capacity_db}", "")
            car_class = str.replace(car_class, "(D)", "")
            car_class = str.replace(car_class, "(L)", "")
            car_class = str.replace(car_class, "(G)", "")
            car_class = str.replace(car_class, "2WD", "")
            car_class = str.replace(car_class, "4WD", "")
            car_class = str.replace(car_class, "AWD", "")

            # DateTimeStamp
            time_now = str(datetime.now())

            # Text
            descript = '<dl><dt class="dttle">Информация</dt>' \
                       f'<dd><span class="t">Номер лота: {entry_num}</span></dd>' \
                       f'<dd><span class="t">На аукционе с: {entry_date}</span></dd>' \
                       f'<dd><span class="t">Дата первичной регистрации: {reg_year}</span></dd>' \
                       f'<dd><span class="t">Номерной знак: {car_number}</span></dd>' \
                       f'<dd><span class="t">VIN-номер: {vin}</span></dd>' \
                       f'<dd><span class="t">Статус: {progress}</span></dd>' \
                       f'<dd><span class="t">Оценка: {points}</span></dd></dl>'
            text_db = descript

            # Transfer
            if marka_db == "":
                print("Vehicle was not recognized. Skipped")
            else:
                print('Parsing', marka_db, model_db, year_man_db)

                insert_query = f"INSERT INTO `ns_goods`" \
                              f"(`topItem`, `tree`, `parent`, `visible`, `url`, `mainImage`, `popular`, `name`, `number`, `title`, `description`, `keywords`, `mainPrice`, `priceAllin`, `code`, `chars`, `brandId`, `price`, `units`, `info`, `textRight`, `text`, `changefreq`, `lastmod`, `priority`, `startPrice`, `valuteId`, `attributes`, `newItem`, `actPrice`, `startActPrice`, `attrPrice`, `actAttrPrice`, `mainAttrPrice`, `tree1`, `statusId`, `supplierCode`, `zakPrice`, `supplierId`, `upload`, `canBuy`, `quantity`, `percent`, `actionTime`, `actDate`, `actTime`, `tempid`, `colcom`, `rating`, `inOrder`, `marka`, `model`, `engineType`, `engineСapacity`, `mileage`, `transmission`, `driveType`, `yearMan`, `auctionMark`) " \
                              f"VALUES(1, '|96|', 96, 1, '{url}', 'img//uploads//prebg//{url}(1).jpg', 0, '{name_db}', 100, '', '', '', {price}, '{video_url}', '{vin}', '{chars}', 0, {price}, '', '', '', '{text_db}', 'always', '{time_now}', 0.9, {price}, 1, '', 1, 0, 0, {price}, 0, {price}, '|96|', 7, '', 0, 0, 0, 1, 0, 0, 0, 0, '', '', 0, 0, 0, '{marka_db}', '{model_db}', '{engine_type_db}', '{engine_capacity_db}', {mileage_db}, '{transmission_db}', '{drive_type_db}', '{year_man_db}', '{points}')"
                executeQuery(connect, insert_query, 'Row')

                get_last_id = f"SELECT * FROM `ns_goods` ORDER BY `itemId` DESC LIMIT 1"
                last_id = (read_query(connect, get_last_id))[0][0]

                category_query = f"INSERT INTO `ns_itemcatlink`(`categoryId`, `itemId`)" \
                                f"VALUES (96, {last_id})"
                executeQuery(connect, category_query, 'Category')

                menu_query = f"INSERT INTO `ns_sititem`(`name`, `param`, `itemId`, `bodyId`) " \
                            f"VALUES ('overhead1', 'chaptersMenu', {last_id}, '')"
                executeQuery(connect, menu_query, 'Menu item')

                menu_query = f"INSERT INTO `ns_sititem`(`name`, `param`, `itemId`, `bodyId`) " \
                            f"VALUES ('megamenu', 'megaMenu', {last_id}, '')"
                executeQuery(connect, menu_query, 'Menu item')

                filter_query = f"INSERT INTO `ns_textparam`(`filterId`, `itemId`, `text`, `textInt`)" \
                              f"VALUES (28, {last_id}, '{engine_capacity_db}', {engine_capacity_db})"
                executeQuery(connect, filter_query, 'Filter engineCapacity')

                filter_query = f"INSERT INTO `ns_textparam`(`filterId`, `itemId`, `text`, `textInt`)" \
                              f"VALUES (24, {last_id}, '{year_man_db}', {int(year_man_db)})"
                executeQuery(connect, filter_query, 'Filter yearMan')

                filter_query = f"INSERT INTO `ns_textparam`(`filterId`, `itemId`, `text`, `textInt`)" \
                              f"VALUES (32, {last_id}, '{car_class}', 0)"
                executeQuery(connect, filter_query, 'Filter completation')

                filter_query = f"INSERT INTO `ns_textparam`(`filterId`, `itemId`, `text`, `textInt`)" \
                              f"VALUES (30, {last_id}, '{mileage_db}', {mileage_db})"
                executeQuery(connect, filter_query, 'Filter mileage')

                filter_query = f"INSERT INTO `ns_textparam`(`filterId`, `itemId`, `text`, `textInt`)" \
                              f"VALUES (31, {last_id}, '{points}', 0)"
                executeQuery(connect, filter_query, 'Filter auction point')

                images_ftp(images, url, connect, last_id, flag=False)
                images_ftp(defect_image, url, connect, last_id, flag=True)


def make_url(functions):
    links = []
    for function in functions:
        function = str.replace(function, 'fnPopupCarView(', '')
        function = str.replace(function, '); return false;', '')
        function_arguments = function.split(',')
        for argument in function_arguments:
            index = function_arguments.index(argument)
            argument = str.replace(argument, '"', '')
            function_arguments[index] = argument
        url = f"https://www.lotteautoauction.net/hp/auct/myp/entry/selectMypEntryCarDetPop.do?searchMngDivCd=" \
              f"{function_arguments[0]}&searchMngNo={function_arguments[1]}&searchExhiRegiSeq={function_arguments[2]} "
        links.append(url)
    return links


# Download images and transfer via FTP and  MySQL
def images_ftp(links, filename, connect, last_id, flag):
    path = os.getcwd() + "\\temp\\"
    for link in links:
        if flag is True:
            index = 1001
        else:
            index = links.index(link) + 1
        r = requests.get(link, allow_redirects=True)
        file = open(f"{path}{filename}({index}).jpg", "wb")
        file.write(r.content)
        file.close()
        try:
            file_to_send = open(f'{path}\\{filename}({index}).jpg', "rb")
            with ftplib.FTP(host="185.98.5.170", user="youcar21", passwd="_tV2x9w9") as ftp:
                ftp.cwd('/img/uploads/prebg/')
                ftp.storbinary(f'STOR {filename}({index}).jpg', file_to_send)
                ftp.close()
            file_to_send.close()

            add_image = f"INSERT INTO `ns_images`(`itemId`, `number`, `previewsm`, `previewmed`, `previewbg`)" \
                       f"VALUES ({last_id}, {index}, 'img//uploads//prebg//{filename}({index}).jpg', 'img//uploads//prebg//{filename}({index}).jpg', 'img//uploads//prebg//{filename}({index}).jpg')"
            executeQuery(connect, add_image, f'Image {index}')
        except Exception as e:
            print('Error:', e)


def mysql_сonnecting():
    print('Connecting to database...')
    try:
        connection = mysql.connector.connect(
            host='185.98.5.170',
            user='p-16561_youcarusr',
            passwd='8j!tpB11',
            database='p-16561_youcarbase21'
        )
        print('MySQL Database connection successful')
        return connection
    except Exception as err:
        print(f"Connection error: {err}")


# Function for SELECT query to DB
def read_query(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Exception as err:
        print(f"Error: {err}")


# Function for INSERT query to DB
def executeQuery(connection, query, string):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
        print(f"\t{string} added")
    except Error as err:
        print(f"Error: {err}")


if __name__ == '__main__':
    filtrBrand = input("Input car brand. Exaple:\n\t"
                       "Hyundai - HD\n\t"
                       "Kia - KI\n\t"
                       "GM Korea - DW\n\t"
                       "Renault Samsung Motors - SS\n\t"
                       "Ssangyong - SY\n\t"
                       "Audi - AD\n\t"
                       "Bentley - BE\n\t"
                       "BMW - BM\n\t"
                       "Cadillac - CA\n\t"
                       "Chrysler - CL\n\t"
                       "Citroen - CT\n\t"
                       "Fiat - FT\n\t"
                       "Ford - FO\n\t"
                       "General Motors - GM\n\t"
                       "Honda - HO\n\t"
                       "Jaguar - JA\n\t"
                       "Land-Rover - LR\n\t"
                       "Mercedes Benz - BT\n\t"
                       "Mitsubishi - MI\n\t"
                       "Nissan - NI\n\t"
                       "Peugeot - PU\n\t"
                       "Porsche - PO\n\t"
                       "Saab - SA\n\t"
                       "Subaru - SR\n\t"
                       "Toyota - TO\n\t"
                       "Volkswagen - VK\n\t"
                       "Volvo - VO\n\t"
                       "Suzuki - SZ\n(Else press enter): ")
    filtrYear = input("Input year: ")
    filtrFuel = input("Input fuel type. Example:\n\t"
                      "Gasoline - G\n\t"
                      "Desel - D\n\t"
                      "LPG - L\n\t"
                      "LPI Hybrid - I\n\t"
                      "Gasoline hybrid - K\n\t"
                      "Diesel hybrid - T\n\t"
                      "Electricity - E\n\t"
                      "Gasoline/LPG - H\n(Else press enter): ")
    parsing(filtrBrand, filtrYear, filtrFuel)
