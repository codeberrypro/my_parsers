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
    js_functions = getLinks(driver)

    links = makeUrl(js_functions)
    getContent(driver, links, translator)
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


def getLinks(driver):
    tableTop = driver.find_element_by_class_name("tbl-top").find_element_by_tag_name("em").text
    print(tableTop, 'vehicles on pages')
    numberOfPages = ceil(int(tableTop) / 20)
    pageList = []
    if int(tableTop) > 30:
        for page in range(numberOfPages):
            time.sleep(3)
            table = driver.find_element_by_class_name("tbl-t02").find_element_by_tag_name(
                "tbody").find_elements_by_tag_name("tr")
            for tr in table:
                trLink = tr.find_element_by_class_name("a_list").get_attribute("onclick")
                pageList.append(trLink)
            print("\tPage", page + 1, "of", numberOfPages, "pages.")
            # Get next page
            if (page + 1) != numberOfPages:
                driver.execute_script(f"fnSearch({page + 2});return false; ")
    else:
        time.sleep(3)
        table = driver.find_element_by_class_name("tbl-t02").find_element_by_tag_name(
            "tbody").find_elements_by_tag_name("tr")
        for tr in table:
            trLink = tr.find_element_by_class_name("a_list").get_attribute("onclick")
            pageList.append(trLink)
        print("\tPage", 1)

    return pageList


def getContent(driver, links, translator):
    connect = mysqlConnecting()
    for link in links:
        driver.get(link)

        time.sleep(3)
        mainContainer = driver.find_element_by_class_name("page-popup")
        vin = mainContainer.find_element_by_class_name("vehicle-detail"). \
            find_elements_by_class_name("tbl-v02")[0].find_element_by_xpath(".//tbody/tr[7]/td").text
        checkAvailabel = f"SELECT `url` FROM `ns_goods` WHERE `code`='{vin}'"
        response = readQuery(connect, checkAvailabel)
        if len(response) != 0:
            print(f'Row already exist by URL {response[0][0]}')
        else:
            nameDB = mainContainer.find_element_by_class_name("vehicle-tit").find_element_by_class_name("tit").text
            entryNum = mainContainer.find_element_by_class_name("vehicle-tit").find_element_by_tag_name("strong").text
            price = mainContainer.find_element_by_class_name("clfix").find_element_by_class_name("vehicle-info"). \
                find_element_by_class_name("starting-price").find_element_by_tag_name("em").text
            infoLi = mainContainer.find_element_by_class_name("clfix").find_element_by_class_name("vehicle-info"). \
                find_element_by_tag_name("ul").find_elements_by_tag_name("li")
            entryDate = infoLi[0].find_element_by_tag_name("strong").text
            carNumber = infoLi[1].find_element_by_tag_name("strong").text
            progress = infoLi[2].find_element_by_tag_name("strong").text
            points = infoLi[3].find_element_by_tag_name("strong").text

            detailTable = mainContainer.find_element_by_class_name("vehicle-detail"). \
                find_elements_by_class_name("tbl-v02")[1].find_element_by_tag_name("tbody")
            yearManDB = detailTable.find_element_by_xpath(".//tr[1]/td[1]").text
            mileageDB = detailTable.find_element_by_xpath(".//tr[1]/td[2]").text
            transmissionDB = detailTable.find_element_by_xpath(".//tr[2]/td[2]").text
            engineTypeDB = detailTable.find_element_by_xpath(".//tr[4]/td[2]").text
            engineCapacityDB = detailTable.find_element_by_xpath(".//tr[5]/td[2]").text
            carType = detailTable.find_element_by_xpath(".//tr[6]/td[1]").text
            regYear = detailTable.find_element_by_xpath(".//tr[2]/td[1]").text

            # Images
            images = []
            imageElements = mainContainer.find_element_by_class_name("vehicle-detail-view").find_element_by_xpath(
                ".//div[contains(@class, 'vehicle-photo-detail swiper-container swiper-container-horizontal')]"). \
                find_element_by_tag_name("ul").find_elements_by_tag_name("li")
            for element in imageElements:
                element = element.find_element_by_tag_name("img")
                images.append(element.get_attribute("src"))
            images.pop(0)
            images = images[:-1]
            defectImage = []
            if len(mainContainer.find_elements_by_class_name("car-status-map")) != 0:
                defImage = mainContainer.find_element_by_class_name("car-status-map").find_element_by_tag_name("img"). \
                    get_attribute("src")
                defectImage.append(defImage)

            # Video
            videoUrl = ''
            video = mainContainer.find_element_by_id("yesMovie").find_elements_by_id("video")
            if len(video) != 0:
                videoUrl = video[0].find_element_by_tag_name("source").get_attribute("src")

            videoUrl = str.replace(videoUrl, ".MP4?rel=0", ".MP4?rel=1")

            # Translation
            nameDB = translator.translate(nameDB)
            carNumber = translator.translate(carNumber)
            progress = translator.translate(progress)
            transmissionDB = translator.translate(transmissionDB)
            engineTypeDB = translator.translate(engineTypeDB)
            carType = translator.translate(carType)

            # Formatting
            URL = vin + "-" + nameDB
            URL = str.replace(URL, '+', '-')
            URL = str.replace(URL, '.', '-')
            URL = str.replace(URL, ' ', '-')
            URL = str.replace(URL, '-(D)', '')
            URL = str.replace(URL, '-(G)', '')
            URL = str.replace(URL, '-(L)', '')
            URL = str.replace(URL, '-(E)', '')
            URL = str.replace(URL, '/', '')
            URL = str.replace(URL, 'Ⅱ', '')
            URL = URL.lower()
            nameDB = str.replace(nameDB, 'All NEW ', '')
            nameDB = str.replace(nameDB, 'All New ', '')
            nameDB = str.replace(nameDB, 'ALL NEW', '')
            nameDB = str.replace(nameDB, 'ALL New', '')
            nameDB = str.replace(nameDB, 'THE NEW', '')
            nameDB = str.replace(nameDB, 'The New', '')
            nameDB = str.replace(nameDB, 'New ', '')
            nameDB = str.replace(nameDB, 'All ', '')
            nameDB = str.replace(nameDB, 'Ⅱ', '')
            points = str.replace(points, " ", "")
            price = float(str.replace(price, " ", "").strip())
            convertation = CurrencyConverter()
            price = float(ceil(convertation.convert(price * 10000, 'KRW', 'USD')))

            engineCapacityDB = (str.replace(engineCapacityDB, " cc", "")).strip()
            engineCapacityDB = str.replace(engineCapacityDB, " ", ".")
            engineCapacityDB = round(float(engineCapacityDB), 1)
            if engineCapacityDB == 998.0:
                engineCapacityDB = 1.0

            mileageDB = (str.replace(mileageDB, " Km", "")).strip()
            mileageDB = int(str.replace(mileageDB, " ", ""))

            chars = ''
            if engineTypeDB.lower() == "diesel":
                engineTypeDB = "Дизель"
                chars += "|77|"
            elif engineTypeDB.lower() == "lpg":
                engineTypeDB = 'Газ'
                chars += '|82|'
            elif engineTypeDB.lower() == "gasoline":
                engineTypeDB = 'Бензин'
                chars += '|79|'
            elif engineTypeDB.lower() == "electric":
                engineTypeDB = 'Электро'
                chars += '|78|'
            elif engineTypeDB.lower() == "hybrid":
                engineTypeDB = 'Гибрид'
                chars += '|80|'

            if transmissionDB.lower() == 'automatic':
                transmissionDB = 'Автомат'
                chars += '|31|'
            elif transmissionDB.lower() == 'manual':
                transmissionDB = 'Механика'
                chars += '|32|'

            if 'sedan' in carType.lower():  # carType = 'Седан'
                carType = "Sedan"
                chars += '|69|'
            elif 'suv' in carType.lower():  # carType = 'Кроссовер'
                carType = "SUV"
                chars += '|66|'
            elif 'van' in carType.lower():  # carType = 'Минивэн'
                carType = "Van/MiniVan"
                chars += '|68|'

            driveTypeDB = 'Не указан'
            if "2wd" in nameDB.lower():
                driveTypeDB = 'Передний'
                chars += '|72|'
            elif "4wd" in nameDB.lower():
                driveTypeDB = 'Полный'
                chars += '|73|'
            elif "awd" in nameDB.lower():
                driveTypeDB = 'Полный'
                chars += '|73|'

            markaDB = ""
            modelDB = ""
            # filterParamId
            if 'morning' in nameDB.lower():  # Kia
                markaDB = "Kia"
                modelDB = "Morning"
                chars += '|113|'
            if 'opirus' in nameDB.lower() or 'lovers' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Opirus"
                chars += '|173|'
            if 'carnival' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Carnival"
                chars += '|120|'
            if 'forte' in nameDB.lower() or 'strong couple' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Forte"
                chars += '|174|'
            if 'k3' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "K3"
                chars += '|118|'
            if 'k5' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "K5"
                chars += '|441|'
            if 'k7' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "K7"
                chars += '|103|'
            if 'k9' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "K9"
                chars += '|119|'
            if 'sorento' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Sorento"
                chars += '|135|'
            if 'mojave' in nameDB.lower() or 'mohave' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Mojave"
                chars += '|175|'
            if 'bongo' in nameDB.lower() or 'rhino' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Bongo"
                chars += '|176|'
            if 'sportage' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Sportage"
                chars += '|111|'
            if 'soul' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Soul"
                chars += '|136|'
            if 'carens' in nameDB.lower() or 'carena' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Carens"
                chars += '|177|'
            if 'roche' in nameDB.lower() or 'lotze' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Roche"
                chars += '|178|'
            if 'serato' in nameDB.lower() or 'cerato' in nameDB.lower() or 'waxed' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Serato"
                chars += '|179|'
            if 'optima' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Optima"
                chars += '|180|'
            if 'casta' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Casta"
                chars += '|181|'
            if 'combi' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Combi"
                chars += '|182|'
            if 'tauner' in nameDB.lower() or 'towner' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Tauner"
                chars += '|183|'
            if 'hunger pride' in nameDB.lower() or 'pride' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Hunger Pride"
                chars += '|184|'
            if 'ray' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Ray"
                chars += '|132|'
            if 'grandbird' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Grandbird"
                chars += '|185|'
            if 'niro' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Niro"
                chars += '|186|'
            if 'stinger' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Stinger"
                chars += '|121|'
            if 'hunger stony' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Hunger Stony"
                chars += '|187|'
            if 'seltos' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Seltos"
                chars += '|134|'
            if 'stonic' in nameDB.lower():
                markaDB = "Kia"
                modelDB = "Stonic"
                chars += '|133|'
            if 'sonata' in nameDB.lower():  # Hyundai
                markaDB = "Hyundai"
                modelDB = "Sonata"
                chars += '|112|'
            if 'grandeur' in nameDB.lower() or 'size' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Grandeur"
                chars += '|105|'
            if 'verna' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Verna"
                chars += '|188|'
            if 'eye certi' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Eye Certi"
                chars += '|189|'
            if 'click' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Click"
                chars += '|190|'
            if 'avante' in nameDB.lower() or 'advantageous' in nameDB.lower() or 'forward' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Avante"
                chars += '|106|'
            if 'equus' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Equus"
                chars += '|191|'
            if 'starex' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Starex"
                chars += '|192|'
            if 'veracruz' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Veracruz"
                chars += '|193|'
            if 'santa fe' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "SantaFe"
                chars += '|95|'
            if 'santafe' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "SantaFe"
                chars += '|95|'
            if 'tucson' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Tucson"
                chars += '|109|'
            if 'porter' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Porter"
                chars += '|194|'
            if 'country' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Country"
                chars += '|195|'
            if 'grace' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Grace"
                chars += '196'
            if 'dynasty' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Dynasty"
                chars += '|197|'
            if 'lavita' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Lavita"
                chars += '|198|'
            if 'libero' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Libero"
                chars += '|199|'
            if 'marsha' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Marsha"
                chars += '|200|'
            if 'mighty' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Mighty"
                chars += '|201|'
            if 'aerotown' in nameDB.lower() or 'aero town' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Aerotown"
                chars += '|202|'
            if 'accent' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Accent"
                chars += '|138|'
            if 'chorus' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Modern Chorus"
                chars += '203'
            if 'terracan' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Terracan"
                chars += '|204|'
            if 'tuscany' in nameDB.lower() or 'tuscani' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Tuscany"
                chars += '|205|'
            if 'trajet' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Trajet"
                chars += '|206|'
            if 'truck' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Truck"
                chars += '|207|'
            if 'universe' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Universe"
                chars += '|208|'
            if 'veloster' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Veloster"
                chars += '|140|'
            if 'ipodi' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "iPodi"
                chars += '|209|'
            if 'maxcruise' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Maxcruise"
                chars += '|102|'
            if 'max cruise' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Maxcruise"
                chars += '|102|'
            if 'aslan' in nameDB.lower() or 'lion ' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Aslan"
                chars += '|210|'
            if 'green city' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Green City"
                chars += '|211|'
            if 'unicity' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Unicity"
                chars += '|212|'
            if 'solati' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Solati"
                chars += '|213|'
            if 'ionic' in nameDB.lower() or 'ioniq' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Ionic"
                chars += '|214|'
            if 'kona' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Kona"
                chars += '|137|'
            if 'csm truck' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Soosan CSM truck"
                chars += '|215|'
            if 'nexo' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Nexo"
                chars += '|216|'
            if 'palisade' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Palisade"
                chars += '|143|'
            if 'sungjin potter' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Sungjin Potter"
                chars += '|217|'
            if 'venue' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Venue"
                chars += '|139|'
            if 'dasan heavy industries mighty' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Dasan Heavy Industries Mighty"
                chars += '|218|'
            if 'i30' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "i30"
                chars += '|141|'
            if 'maxcruz' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "Maxcruz"
                chars += '|142|'
            if 'i40' in nameDB.lower():
                markaDB = "Hyundai"
                modelDB = "i40"
                chars += '|144|'
            if 'rav4' in nameDB.lower():  # Toyota
                markaDB = "Toyota"
                modelDB = "Rav4"
                chars += '|219|'
            if 'camry' in nameDB.lower():
                markaDB = "Toyota"
                modelDB = "Camry"
                chars += '|125|'
            if 'prius' in nameDB.lower():
                markaDB = "Toyota"
                modelDB = "Prius"
                chars += '|220|'
            if 'avalon' in nameDB.lower():
                markaDB = "Toyota"
                modelDB = "Avalon"
                chars += '|221|'
            if 'vivi' in nameDB.lower():
                markaDB = "Toyota"
                modelDB = "Vivi"
                chars += '|222|'
            if 'corolla' in nameDB.lower():
                markaDB = "Toyota"
                modelDB = "Corolla"
                chars += '|223|'
            if 'sienna' in nameDB.lower():
                markaDB = "Toyota"
                modelDB = "Sienna"
                chars += '|126|'
            if 'benza' in nameDB.lower():
                markaDB = "Toyota"
                modelDB = "Benza"
                chars += '|224|'
            if 'fj cruiser' in nameDB.lower():
                markaDB = "Toyota"
                modelDB = "FJ Cruiser"
                chars += '|225|'
            if 'land cruiser 200' in nameDB.lower():
                markaDB = "Toyota"
                modelDB = "Land Cruiser 200"
                chars += '|116|'
            if 'es ' in nameDB.lower():  # Lexus
                markaDB = "Lexus"
                modelDB = "ES"
                chars += '|226|'
            if 'gs ' in nameDB.lower():
                markaDB = "Lexus"
                modelDB = "GS"
                chars += '|227|'
            if 'ls ' in nameDB.lower():
                markaDB = "Lexus"
                modelDB = "LS"
                chars += '|228|'
            if 'rx ' in nameDB.lower():
                markaDB = "Lexus"
                modelDB = "RX"
                chars += '|229|'
            if 'sc ' in nameDB.lower():
                markaDB = "Lexus"
                modelDB = "SC"
                chars += '|230|'
            if 'gs ' in nameDB.lower():
                markaDB = "Lexus"
                modelDB = "GS"
                chars += '|231|'
            if 'ct ' in nameDB.lower():
                markaDB = "Lexus"
                modelDB = "CT"
                chars += '|232|'
            if 'nx ' in nameDB.lower():
                markaDB = "Lexus"
                modelDB = "NX"
                chars += '|233|'
            if 'rc ' in nameDB.lower():
                markaDB = "Lexus"
                modelDB = "RC"
                chars += '|234|'
            if 'ux ' in nameDB.lower():
                markaDB = "Lexus"
                modelDB = "UX"
                chars += '|235|'
            if 'eq900' in nameDB.lower():  # Genesis
                markaDB = "Genesis"
                modelDB = "EQ900"
                chars += '|94|'
            if 'g80' in nameDB.lower():
                markaDB = "Genesis"
                modelDB = "G80"
                chars += '|145|'
            if 'g70' in nameDB.lower():
                markaDB = "Genesis"
                modelDB = "G70"
                chars += '|236|'
            if 'g90' in nameDB.lower():
                markaDB = "Genesis"
                modelDB = "G90"
                chars += '|237|'
            if 'gv80' in nameDB.lower():
                markaDB = "Genesis"
                modelDB = "GV80"
                chars += '|238|'
            if 'gv70' in nameDB.lower():
                markaDB = "Genesis"
                modelDB = "GV70"
                chars += '|239|'
            if 'winstorm' in nameDB.lower():  # GM
                markaDB = "GM"
                modelDB = "Winstorm"
                chars += '|240|'
            if 'tosca' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Tosca"
                chars += '|241|'
            if 'alpheon' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Alpheon"
                chars += '|242|'
            if 'gentra' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Gentra"
                chars += '|243|'
            if 'lacetti' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Lacetti"
                chars += '|244|'
            if 'matiz' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Matiz"
                chars += '|245|'
            if 'damas' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Damas"
                chars += '|246|'
            if 'veritas' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Veritas"
                chars += '|247|'
            if 'lab ' in nameDB.lower() or 'labo ' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Lab"
                chars += '|248|'
            if 'statesman' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Statesman"
                chars += '|249|'
            if 'spark' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Spark"
                chars += '|124|'
            if 'aveo' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Aveo"
                chars += '|250|'
            if 'cruise ' in nameDB.lower() or 'cruze ' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Cruise"
                chars += '|251|'
            if 'orlando' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Orlando"
                chars += '|252|'
            if 'captiva' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Captiva"
                chars += '|253|'
            if 'malibu' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Malibu"
                chars += '|254|'
            if 'corvette' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Corvette"
                chars += '|255|'
            if 'trax' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Trax"
                chars += '|256|'
            if 'camaro' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Camaro"
                chars += '|257|'
            if 'impala' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Impala"
                chars += '|258|'
            if 'volt' in nameDB.lower() or 'bolt' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Volt"
                chars += '|259|'
            if 'equinox' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Equinox"
                chars += '|260|'
            if 'colorado' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Colorado"
                chars += '|261|'
            if 'traverse' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Traverse"
                chars += '|262|'
            if 'trail blazer' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Trail Blazer"
                chars += '|263|'
            if 'gm express' in nameDB.lower():
                markaDB = "GM"
                modelDB = "Express"
                chars += '|264|'
            if 'sm3 ' in nameDB.lower():  # Renault Samsung
                markaDB = "Renault Samsung"
                modelDB = "SM3"
                chars += '|265|'
            if 'sm5 ' in nameDB.lower() or 'sm 5' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "SM5"
                chars += '|266|'
            if 'sm7 ' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "SM7"
                chars += '|267|'
            if 'qm5 ' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "QM5"
                chars += '|268|'
            if 'yamujin' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "Yamujin"
                chars += '|269|'
            if 'qm3 ' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "QM3"
                chars += '|270|'
            if 'sm6 ' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "SM6"
                chars += '|271|'
            if 'qm6 ' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "QM6"
                chars += '|272|'
            if 'tweed' in nameDB.lower() or 'twizy' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "Tweed"
                chars += '|273|'
            if 'clio' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "Clio"
                chars += '|274|'
            if 'master ' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "Master"
                chars += '|275|'
            if 'captur ' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "Captur"
                chars += '|276|'
            if 'joe ' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "Joe"
                chars += '|277|'
            if 'coban' in nameDB.lower():
                markaDB = "Renault Samsung"
                modelDB = "Kwangil Indastry Coban Camper"
                chars += '|278|'
            if 'chairman' in nameDB.lower():  # Ssangyong
                markaDB = "Ssangyong"
                modelDB = "Chairman"
                chars += '|279|'
            if 'rexton' in nameDB.lower():
                markaDB = "Ssangyong"
                modelDB = "Rexton"
                chars += '|280|'
            if 'rodius' in nameDB.lower():
                markaDB = "Ssangyong"
                modelDB = "Rodius"
                chars += '|281|'
            if 'actyon' in nameDB.lower():
                markaDB = "Ssangyong"
                modelDB = "Actyon"
                chars += '|282|'
            if 'kyron' in nameDB.lower():
                markaDB = "Ssangyong"
                modelDB = "Kyron"
                chars += '|283|'
            if 'musso' in nameDB.lower() or 'musser' in nameDB.lower():
                markaDB = "Ssangyong"
                modelDB = "Musso"
                chars += '|284|'
            if 'istana' in nameDB.lower():
                markaDB = "Ssangyong"
                modelDB = "Istana"
                chars += '|285|'
            if 'korando ' in nameDB.lower():
                markaDB = "Ssangyong"
                modelDB = "Korando"
                chars += '|286|'
            if 'tivoli' in nameDB.lower():
                markaDB = "Ssangyong"
                modelDB = "Tivoli"
                chars += '|287|'
            if 'vintage ' in nameDB.lower():  # Aston Martin
                markaDB = "Aston Martin"
                modelDB = "Vintage"
                chars += '|288|'
            if 'vanish ' in nameDB.lower():
                markaDB = "Aston Martin"
                modelDB = "Vanish"
                chars += '|289|'
            if 'a4 ' in nameDB.lower():  # Audi
                markaDB = "Audi"
                modelDB = "A4"
                chars += '|290|'
            if 'a5 ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "A5"
                chars += '|291|'
            if 'a6 ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "A6"
                chars += '|292|'
            if 'a8 ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "A8"
                chars += '|293|'
            if 'q5 ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "Q5"
                chars += '|294|'
            if 'q7 ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "Q7"
                chars += '|295|'
            if 'aude r' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "R"
                chars += '|296|'
            if 'audi s' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "S"
                chars += '|297|'
            if 'tt ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "TT"
                chars += '|298|'
            if 'audi rs' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "RS"
                chars += '|299|'
            if 'a7 ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "A7"
                chars += '|300|'
            if 'q3 ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "Q3"
                chars += '|301|'
            if 'audi sq' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "SQ"
                chars += '|302|'
            if 'audi a1 ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "A1"
                chars += '|303|'
            if 'q8 ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "Q8"
                chars += '|304|'
            if 'e-tron ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "E-tron"
                chars += '|305|'
            if 'q2 ' in nameDB.lower():
                markaDB = "Audi"
                modelDB = "Q2"
                chars += '|306|'
            if 'flying spur' in nameDB.lower():  # Bentley
                markaDB = "Bentley"
                modelDB = "Flying Spur"
                chars += '|307|'
            if 'gt contonental' in nameDB.lower():
                markaDB = "Bentley"
                modelDB = "GT Contonental"
                chars += '|308|'
            if 'gtc contonental' in nameDB.lower():
                markaDB = "Bentley"
                modelDB = "GTC Contonental"
                chars += '|309|'
            if 'arnage' in nameDB.lower():
                markaDB = "Bentley"
                modelDB = "Arnage"
                chars += '|310|'
            if 'mulsanne' in nameDB.lower():
                markaDB = "Bentley"
                modelDB = "Mulsanne"
                chars += '|311|'
            if 'bmw 1' in nameDB.lower():  # BMW
                markaDB = "BMW"
                modelDB = "1 series"
                chars += '|312|'
            if 'bmw 3' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "3 series"
                chars += '|313|'
            if 'bmw 5' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "5 series"
                chars += '|314|'
            if 'bmw 7' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "7 series"
                chars += '|315|'
            if 'bmw 6' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "6 series"
                chars += '|316|'
            if 'bmw 4' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "4 series"
                chars += '|317|'
            if 'bmw 2' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "2 series"
                chars += '|318|'
            if 'bmw 8' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "8 series"
                chars += '|319|'
            if 'bmw mini ' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "MINI"
                chars += '|320|'
            if 'bmw gt' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "GT"
                chars += '|321|'
            if 'bmw m' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "M"
                chars += '|322|'
            if 'bmw x' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "X"
                chars += '|323|'
            if 'bmw z' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "Z"
                chars += '|324|'
            if 'bmw i' in nameDB.lower():
                markaDB = "BMW"
                modelDB = "I"
                chars += '|325|'
            if 'cadillac' in nameDB.lower():  # Cadillac
                markaDB = "Cadillac"
                modelDB = "Cadillac"
                chars += '|326|'
            if 'cadillac' in nameDB.lower() and 'sts' in nameDB.lower():
                markaDB = "Cadillac"
                modelDB = "STS"
                chars += '|327|'
            if 'cadillac' in nameDB.lower() and 'cts' in nameDB.lower():
                markaDB = "Cadillac"
                modelDB = "CTS"
                chars += '|328|'
            if 'cadillac' in nameDB.lower() and 'escalade' in nameDB.lower():
                markaDB = "Cadillac"
                modelDB = "Escalade"
                chars += '|329|'
            if 'cadillac' in nameDB.lower() and 'ct6' in nameDB.lower():
                markaDB = "Cadillac"
                modelDB = "CT6"
                chars += '|330|'
            if 'cadillac' in nameDB.lower() and 'xt5' in nameDB.lower():
                markaDB = "Cadillac"
                modelDB = "XT5"
                chars += '|331|'
            if 'wrangler' in nameDB.lower():  # Chrysler/Jeep
                markaDB = "Jeep"
                modelDB = "Wrangler"
                chars += '|332|'
            if 'cherokee' in nameDB.lower():
                markaDB = "Jeep"
                modelDB = "Cherokee"
                chars += '|333|'
            if 'caravan' in nameDB.lower():
                markaDB = "Chrysler"
                modelDB = "Caravan"
                chars += '|334|'
            if 'chrysler 300c' in nameDB.lower():
                markaDB = "Chrysler"
                modelDB = "300C"
                chars += '|335|'
            if 'chrysler 300m' in nameDB.lower():
                markaDB = "Chrysler"
                modelDB = "300M"
                chars += '|336|'
            if 'renegade' in nameDB.lower():
                markaDB = "Jeep"
                modelDB = "Renegad"
                chars += '|337|'
            if 'ds3 ' in nameDB.lower():  # Citroen
                markaDB = "Citroen"
                modelDB = "DS3"
                chars += '|338|'
            if 'ds4 ' in nameDB.lower():
                markaDB = "Citroen"
                modelDB = "DS4"
                chars += '|339|'
            if 'ds5 ' in nameDB.lower():
                markaDB = "Citroen"
                modelDB = "DS5"
                chars += '|340|'
            if 'cactus' in nameDB.lower():
                markaDB = "Citroen"
                modelDB = "Cactus"
                chars += '|341|'
            if 'c3 ' in nameDB.lower():
                markaDB = "Citroen"
                modelDB = "C3"
                chars += '|342|'
            if 'c4 ' in nameDB.lower():
                markaDB = "Citroen"
                modelDB = "C4"
                chars += '|343|'
            if 'c5 ' in nameDB.lower():
                markaDB = "Citroen"
                modelDB = "C5"
                chars += '|344|'
            if 'fiat' in nameDB.lower() and '500' in nameDB.lower():  # Fiat
                markaDB = "Fiat"
                modelDB = "500"
                chars += '|345|'
            if 'fremont' in nameDB.lower():
                markaDB = "Fiat"
                modelDB = "Fremont"
                chars += '|346|'
            if 'ford focus' in nameDB.lower():  # Ford
                markaDB = "Ford"
                modelDB = "Focus"
                chars += '|347|'
            if 'ford fusion' in nameDB.lower():
                markaDB = "Ford"
                modelDB = "Fusion"
                chars += '|348|'
            if 'ford explorer' in nameDB.lower() or 'explorer' in nameDB.lower():
                markaDB = "Ford"
                modelDB = "Explorer"
                chars += '|349|'
            if 'ford taurus' in nameDB.lower():
                markaDB = "Ford"
                modelDB = "Taurus"
                chars += '|350|'
            if 'ford excape' in nameDB.lower():
                markaDB = "Ford"
                modelDB = "Escape"
                chars += '|351|'
            if 'ford mustang' in nameDB.lower():
                markaDB = "Ford"
                modelDB = "Mustang"
                chars += '|352|'
            if 'mondeo' in nameDB.lower():
                markaDB = "Ford"
                modelDB = "Mondeo"
                chars += '|353|'
            if 'ford 500' in nameDB.lower():
                markaDB = "Ford"
                modelDB = "500"
                chars += '|345|'
            if 'kuga' in nameDB.lower():
                markaDB = "Ford"
                modelDB = "Kuga"
                chars += '|354|'
            if 'chevy' in nameDB.lower() and 'van' in nameDB.lower():  # Chevy
                markaDB = "Chevy"
                modelDB = "VAN"
                chars += '|355|'
            if 'honda civic' in nameDB.lower():  # Honda
                markaDB = "Honda"
                modelDB = "Civic"
                chars += '|356|'
            if 'honda accord' in nameDB.lower() or 'agreement' in nameDB.lower():
                markaDB = "Honda"
                modelDB = "Accord"
                chars += '|357|'
            if 'cr-v' in nameDB.lower():
                markaDB = "Honda"
                modelDB = "CR-V"
                chars += '|358|'
            if 'odyssey' in nameDB.lower():
                markaDB = "Honda"
                modelDB = "Odyssey"
                chars += '|359|'
            if 'pilot' in nameDB.lower():
                markaDB = "Honda"
                modelDB = "Pilot"
                chars += '|360|'
            if 'cr-z' in nameDB.lower():
                markaDB = "Honda"
                modelDB = "CR-Z"
                chars += '|361|'
            if 's660' in nameDB.lower():
                markaDB = "Honda"
                modelDB = "S660"
                chars += '|362|'
            if 'jaguar' in nameDB.lower() and 'xf' in nameDB.lower():  # Jaguar
                markaDB = "Jaguar"
                modelDB = "XF"
                chars += '|363|'
            if 'jaguar' in nameDB.lower() and 'xj' in nameDB.lower():
                markaDB = "Jaguar"
                modelDB = "XJ"
                chars += '|364|'
            if 'f-type' in nameDB.lower():
                markaDB = "Jaguar"
                modelDB = "F-Type"
                chars += '|365|'
            if 'jaguar' in nameDB.lower() and '20d' in nameDB.lower():
                markaDB = "Jaguar"
                modelDB = "XE"
                chars += '|366|'
            if 'discovery' in nameDB.lower():  # Land Rover
                markaDB = "Land Rover"
                modelDB = "Discovery"
                chars += '|367|'
            if 'range rover' in nameDB.lower():
                markaDB = "Land Rover"
                modelDB = "Range Rover"
                chars += '|368|'
            if 'freelander' in nameDB.lower():
                markaDB = "Land Rover"
                modelDB = "Freelander"
                chars += '|369|'
            if 'defender' in nameDB.lower():
                markaDB = "Land Rover"
                modelDB = "Defender"
                chars += '|370|'
            if 'mks' in nameDB.lower():  # Lincoln
                markaDB = "Lincoln"
                modelDB = "MKS"
                chars += '|371|'
            if 'mkx' in nameDB.lower():
                markaDB = "Lincoln"
                modelDB = "MKX"
                chars += '|372|'
            if 'mkz' in nameDB.lower():
                markaDB = "Lincoln"
                modelDB = "MKZ"
                chars += '|373|'
            if 'mkc' in nameDB.lower():
                markaDB = "Lincoln"
                modelDB = "MKC"
                chars += '|374|'
            if 'levante' in nameDB.lower():  # Maserati
                markaDB = "Maserati"
                modelDB = "Levante"
                chars += '|375|'
            if 'ghibli' in nameDB.lower():
                markaDB = "Maserati"
                modelDB = "Ghibli"
                chars += '|376|'
            if 'benz b' in nameDB.lower():  # Mercedes Benz
                markaDB = "Mercedes Benz"
                modelDB = "B Class"
                chars += '|377|'
            if 'benz c ' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "C Class"
                chars += '|378|'
            if 'benz cls' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "CLS Class"
                chars += '|379|'
            if 'benz e' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "E Class"
                chars += '|380|'
            if 'benz glk' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "GLK Class"
                chars += '|381|'
            if 'benz m ' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "M Class"
                chars += '|382|'
            if 'benz ml' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "ML Class"
                chars += '|383|'
            if 'benz s ' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "S Class"
                chars += '|384|'
            if 'benz slk' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "SLK Class"
                chars += '|385|'
            if 'benz g ' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "G Class"
                chars += '|386|'
            if 'benz sprinter' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "Sprinter"
                chars += '|387|'
            if 'benz a ' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "A Class"
                chars += '|388|'
            if 'benz cla' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "CLA Class"
                chars += '|389|'
            if 'benz gla' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "GLA Class"
                chars += '|390|'
            if 'benz gt' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "GT"
                chars += '|321|'
            if 'benz glc' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "GLC Class"
                chars += '|391|'
            if 'benz gle' in nameDB.lower():
                markaDB = "Mercedes Benz"
                modelDB = "GLE Class"
                chars += '|392|'
            if 'lancer' in nameDB.lower():  # Mitsibishi
                markaDB = "Mitsibishi"
                modelDB = "Lancer"
                chars += '|393|'
            if 'outlander' in nameDB.lower():
                markaDB = "Mitsibishi"
                modelDB = "Outlander"
                chars += '|394|'
            if 'rogue' in nameDB.lower():  # Nissan
                markaDB = "Nissan"
                modelDB = "Rogue"
                chars += '|395|'
            if 'murano' in nameDB.lower():
                markaDB = "Nissan"
                modelDB = "Murano"
                chars += '|396|'
            if 'altima' in nameDB.lower():
                markaDB = "Nissan"
                modelDB = "Altima"
                chars += '|397|'
            if 'cube' in nameDB.lower():
                markaDB = "Nissan"
                modelDB = "Cube"
                chars += '|398|'
            if 'nissan juke' in nameDB.lower():
                markaDB = "Nissan"
                modelDB = "Juke"
                chars += '|399|'
            if 'nissan path' in nameDB.lower():
                markaDB = "Nissan"
                modelDB = "Pathfinder"
                chars += '|400|'
            if 'nissan qashqai' in nameDB.lower():
                markaDB = "Nissan"
                modelDB = "Qashqai"
                chars += '|401|'
            if 'nissan maxima' in nameDB.lower():
                markaDB = "Nissan"
                modelDB = "Maxima"
                chars += '|402|'
            if 'infinity fx' in nameDB.lower():  # Infinity
                markaDB = "Infinity"
                modelDB = "FX"
                chars += '|403|'
            if 'infinity g' in nameDB.lower():
                markaDB = "Infinity"
                modelDB = "G"
                chars += '|404|'
            if 'infinity m' in nameDB.lower():
                markaDB = "Infinity"
                modelDB = "M"
                chars += '|322|'
            if 'infinity qx' in nameDB.lower():
                markaDB = "Infinity"
                modelDB = "QX"
                chars += '|405|'
            if 'infinity q ' in nameDB.lower():
                markaDB = "Infinity"
                modelDB = "Q"
                chars += '|406|'
            if 'peugeot 207' in nameDB.lower():  # Peugeot
                markaDB = "Peugeot"
                modelDB = "207"
                chars += '|407|'
            if 'peugeot 307' in nameDB.lower():
                markaDB = "Peugeot"
                modelDB = "307"
                chars += '|408|'
            if 'peugeot 308' in nameDB.lower():
                markaDB = "Peugeot"
                modelDB = "308"
                chars += '|409|'
            if 'peugeot 407' in nameDB.lower():
                markaDB = "Peugeot"
                modelDB = "407"
                chars += '|410|'
            if 'peugeot 508' in nameDB.lower():
                markaDB = "Peugeot"
                modelDB = "508"
                chars += '|411|'
            if 'peugeot 3008' in nameDB.lower():
                markaDB = "Peugeot"
                modelDB = "3008"
                chars += '|412|'
            if 'peugeot 208' in nameDB.lower():
                markaDB = "Peugeot"
                modelDB = "208"
                chars += '|413|'
            if 'peugeot 2008' in nameDB.lower():
                markaDB = "Peugeot"
                modelDB = "2008"
                chars += '|414|'
            if 'peugeot 5008' in nameDB.lower():
                markaDB = "Peugeot"
                modelDB = "5008"
                chars += '|415|'
            if 'porche panamera' in nameDB.lower():  # Porche
                markaDB = "Porche"
                modelDB = "Panamera"
                chars += '|416|'
            if 'porche cayman' in nameDB.lower():
                markaDB = "Porche"
                modelDB = "Cayman"
                chars += '|417|'
            if 'porche cayenne' in nameDB.lower():
                markaDB = "Porche"
                modelDB = "Cayenne"
                chars += '|418|'
            if 'saab 9-3' in nameDB.lower():  # Saab
                markaDB = "Saab"
                modelDB = "9-3"
                chars += '|419|'
            if 'saab 9-5' in nameDB.lower():
                markaDB = "Saab"
                modelDB = "9-5"
                chars += '|420|'
            if 'beetle' in nameDB.lower():  # Volkswagen
                markaDB = "Volkswagen"
                modelDB = "Beetle"
                chars += '|421|'
            if 'volkswagen jetta' in nameDB.lower():
                markaDB = "Volkswagen"
                modelDB = "Jetta"
                chars += '|422|'
            if 'volkswagen passat' in nameDB.lower():
                markaDB = "Volkswagen"
                modelDB = "Passat"
                chars += '|423|'
            if 'volkswagen phaeton' in nameDB.lower():
                markaDB = "Volkswagen"
                modelDB = "Phaeton"
                chars += '|424|'
            if 'volkswagen golf' in nameDB.lower():
                markaDB = "Volkswagen"
                modelDB = "Golf"
                chars += '|425|'
            if 'tiguan' in nameDB.lower():
                markaDB = "Volkswagen"
                modelDB = "Tiguan"
                chars += '|426|'
            if 'volkswagen touareg' in nameDB.lower():
                markaDB = "Volkswagen"
                modelDB = "Touareg"
                chars += '|427|'
            if 'volkswagen scirocco' in nameDB.lower():
                markaDB = "Volkswagen"
                modelDB = "Scirocco"
                chars += '|428|'
            if 'volkswagen polo' in nameDB.lower():
                markaDB = "Volkswagen"
                modelDB = "Polo"
                chars += '|429|'
            if 'volvo s60' in nameDB.lower():  # Volvo
                markaDB = "Volvo"
                modelDB = "S60"
                chars += '|430|'
            if 'volvo s80' in nameDB.lower():
                markaDB = "Volvo"
                modelDB = "S80"
                chars += '|431|'
            if 'volvo xc60' in nameDB.lower():
                markaDB = "Volvo"
                modelDB = "XC60"
                chars += '|432|'
            if 'volvo xc70' in nameDB.lower():
                markaDB = "Volvo"
                modelDB = "XC70"
                chars += '|433|'
            if 'volvo xc90' in nameDB.lower():
                markaDB = "Volvo"
                modelDB = "XC90"
                chars += '|434|'
            if 'volvo s40' in nameDB.lower():
                markaDB = "Volvo"
                modelDB = "S40"
                chars += '|435|'
            if 'volvo v60' in nameDB.lower():
                markaDB = "Volvo"
                modelDB = "V60"
                chars += '|436|'
            if 'volvo v40' in nameDB.lower():
                markaDB = "Volvo"
                modelDB = "V40"
                chars += '437'
            if 'volvo s90' in nameDB.lower():
                markaDB = "Volvo"
                modelDB = "S90"
                chars += '|438|'
            if 'hustler' in nameDB.lower():  # Suzuki
                markaDB = "Suzuki"
                modelDB = "Hustler"
                chars += '|439|'
            if 'tata daewoo' in nameDB.lower():  # Daewoo
                markaDB = "Daewoo"
                modelDB = "Tata"
                chars += '|440|'

            if markaDB == 'Kia':
                chars += '|86|'
            if markaDB == 'Hyundai':
                chars += '|85|'
            if markaDB == 'Toyota':
                chars += '|115|'
            if markaDB == 'Lexus':
                chars += '|107|'
            if markaDB == 'Genesis':
                chars += '|93|'
            if markaDB == 'GM':
                chars += '|87|'
            if markaDB == 'Renault Samsung':
                chars += '|88|'
            if markaDB == 'Ssangyong':
                chars += '|89|'
            if markaDB == 'Aston Martin':
                chars += '|146|'
            if markaDB == 'Audi':
                chars += '|147|'
            if markaDB == 'Bentley':
                chars += '|148|'
            if markaDB == 'BMW' or 'BMW' in nameDB:
                chars += '|149|'
            if markaDB == 'Cadillac':
                chars += '|150|'
            if markaDB == 'Chrysler':
                chars += '|151|'
            if markaDB == 'Jeep':
                chars += '|152|'
            if markaDB == 'Citroen':
                chars += '|153|'
            if markaDB == 'Fiat':
                chars += '|154|'
            if markaDB == 'Ford':
                chars += '|155|'
            if markaDB == 'Chevy':
                chars += '|156|'
            if markaDB == 'Honda':
                chars += '|157|'
            if markaDB == 'Jaguar':
                chars += '|158|'
            if markaDB == 'Land Rover':
                chars += '|159|'
            if markaDB == 'Lincoln':
                chars += '|160|'
            if markaDB == 'Maserati':
                chars += '|161|'
            if markaDB == 'Mercedes Benz':
                chars += '|162|'
            if markaDB == 'Mitsubishi':
                chars += '|163|'
            if markaDB == 'Nissan':
                chars += '|164|'
            if markaDB == 'Infinity':
                chars += '|165|'
            if markaDB == 'Peugeot':
                chars += '|166|'
            if markaDB == 'Porsche':
                chars += '|167|'
            if markaDB == 'Saab':
                chars += '|168|'
            if markaDB == 'Volkswagen':
                chars += '|169|'
            if markaDB == 'Volvo':
                chars += '|170|'
            if markaDB == 'Suzuki':
                chars += '|171|'
            if markaDB == 'Rolls Royce':
                chars += '|172|'

            carClass = str.replace(nameDB, markaDB.upper(), "")
            carClass = str.replace(carClass, modelDB.upper(), "")
            carClass = str.replace(carClass, f"{engineCapacityDB}", "")
            carClass = str.replace(carClass, "(D)", "")
            carClass = str.replace(carClass, "(L)", "")
            carClass = str.replace(carClass, "(G)", "")
            carClass = str.replace(carClass, "2WD", "")
            carClass = str.replace(carClass, "4WD", "")
            carClass = str.replace(carClass, "AWD", "")

            # DateTimeStamp
            timeNow = str(datetime.now())

            # Text
            descript = '<dl><dt class="dttle">Информация</dt>' \
                       f'<dd><span class="t">Номер лота: {entryNum}</span></dd>' \
                       f'<dd><span class="t">На аукционе с: {entryDate}</span></dd>' \
                       f'<dd><span class="t">Дата первичной регистрации: {regYear}</span></dd>' \
                       f'<dd><span class="t">Номерной знак: {carNumber}</span></dd>' \
                       f'<dd><span class="t">VIN-номер: {vin}</span></dd>' \
                       f'<dd><span class="t">Статус: {progress}</span></dd>' \
                       f'<dd><span class="t">Оценка: {points}</span></dd></dl>'
            textDB = descript

            # Transfer
            if markaDB == "":
                print("Vehicle was not recognized. Skipped")
            else:
                print('Parsing', markaDB, modelDB, yearManDB)

                insertQuery = f"INSERT INTO `ns_goods`" \
                              f"(`topItem`, `tree`, `parent`, `visible`, `url`, `mainImage`, `popular`, `name`, `number`, `title`, `description`, `keywords`, `mainPrice`, `priceAllin`, `code`, `chars`, `brandId`, `price`, `units`, `info`, `textRight`, `text`, `changefreq`, `lastmod`, `priority`, `startPrice`, `valuteId`, `attributes`, `newItem`, `actPrice`, `startActPrice`, `attrPrice`, `actAttrPrice`, `mainAttrPrice`, `tree1`, `statusId`, `supplierCode`, `zakPrice`, `supplierId`, `upload`, `canBuy`, `quantity`, `percent`, `actionTime`, `actDate`, `actTime`, `tempid`, `colcom`, `rating`, `inOrder`, `marka`, `model`, `engineType`, `engineСapacity`, `mileage`, `transmission`, `driveType`, `yearMan`, `auctionMark`) " \
                              f"VALUES(1, '|96|', 96, 1, '{URL}', 'img//uploads//prebg//{URL}(1).jpg', 0, '{nameDB}', 100, '', '', '', {price}, '{videoUrl}', '{vin}', '{chars}', 0, {price}, '', '', '', '{textDB}', 'always', '{timeNow}', 0.9, {price}, 1, '', 1, 0, 0, {price}, 0, {price}, '|96|', 7, '', 0, 0, 0, 1, 0, 0, 0, 0, '', '', 0, 0, 0, '{markaDB}', '{modelDB}', '{engineTypeDB}', '{engineCapacityDB}', {mileageDB}, '{transmissionDB}', '{driveTypeDB}', '{yearManDB}', '{points}')"
                executeQuery(connect, insertQuery, 'Row')

                getLastId = f"SELECT * FROM `ns_goods` ORDER BY `itemId` DESC LIMIT 1"
                lastId = (readQuery(connect, getLastId))[0][0]

                categoryQuery = f"INSERT INTO `ns_itemcatlink`(`categoryId`, `itemId`)" \
                                f"VALUES (96, {lastId})"
                executeQuery(connect, categoryQuery, 'Category')

                menuQuery = f"INSERT INTO `ns_sititem`(`name`, `param`, `itemId`, `bodyId`) " \
                            f"VALUES ('overhead1', 'chaptersMenu', {lastId}, '')"
                executeQuery(connect, menuQuery, 'Menu item')

                menuQuery = f"INSERT INTO `ns_sititem`(`name`, `param`, `itemId`, `bodyId`) " \
                            f"VALUES ('megamenu', 'megaMenu', {lastId}, '')"
                executeQuery(connect, menuQuery, 'Menu item')

                filterQuery = f"INSERT INTO `ns_textparam`(`filterId`, `itemId`, `text`, `textInt`)" \
                              f"VALUES (28, {lastId}, '{engineCapacityDB}', {engineCapacityDB})"
                executeQuery(connect, filterQuery, 'Filter engineCapacity')

                filterQuery = f"INSERT INTO `ns_textparam`(`filterId`, `itemId`, `text`, `textInt`)" \
                              f"VALUES (24, {lastId}, '{yearManDB}', {int(yearManDB)})"
                executeQuery(connect, filterQuery, 'Filter yearMan')

                filterQuery = f"INSERT INTO `ns_textparam`(`filterId`, `itemId`, `text`, `textInt`)" \
                              f"VALUES (32, {lastId}, '{carClass}', 0)"
                executeQuery(connect, filterQuery, 'Filter completation')

                filterQuery = f"INSERT INTO `ns_textparam`(`filterId`, `itemId`, `text`, `textInt`)" \
                              f"VALUES (30, {lastId}, '{mileageDB}', {mileageDB})"
                executeQuery(connect, filterQuery, 'Filter mileage')

                filterQuery = f"INSERT INTO `ns_textparam`(`filterId`, `itemId`, `text`, `textInt`)" \
                              f"VALUES (31, {lastId}, '{points}', 0)"
                executeQuery(connect, filterQuery, 'Filter auction point')

                imagesFTP(images, URL, connect, lastId, flag=False)
                imagesFTP(defectImage, URL, connect, lastId, flag=True)


def makeUrl(functions):
    links = []
    for function in functions:
        function = str.replace(function, 'fnPopupCarView(', '')
        function = str.replace(function, '); return false;', '')
        functionArguments = function.split(',')
        for argument in functionArguments:
            index = functionArguments.index(argument)
            argument = str.replace(argument, '"', '')
            functionArguments[index] = argument
        url = f"https://www.lotteautoauction.net/hp/auct/myp/entry/selectMypEntryCarDetPop.do?searchMngDivCd=" \
              f"{functionArguments[0]}&searchMngNo={functionArguments[1]}&searchExhiRegiSeq={functionArguments[2]} "
        links.append(url)
    return links


# Download images and transfer via FTP and  MySQL
def imagesFTP(links, filename, connect, lastId, flag):
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
            fileToSend = open(f'{path}\\{filename}({index}).jpg', "rb")
            with ftplib.FTP(host="185.98.5.170", user="youcar21", passwd="_tV2x9w9") as ftp:
                ftp.cwd('/img/uploads/prebg/')
                ftp.storbinary(f'STOR {filename}({index}).jpg', fileToSend)
                ftp.close()
            fileToSend.close()

            addImage = f"INSERT INTO `ns_images`(`itemId`, `number`, `previewsm`, `previewmed`, `previewbg`)" \
                       f"VALUES ({lastId}, {index}, 'img//uploads//prebg//{filename}({index}).jpg', 'img//uploads//prebg//{filename}({index}).jpg', 'img//uploads//prebg//{filename}({index}).jpg')"
            executeQuery(connect, addImage, f'Image {index}')
        except Exception as e:
            print('Error:', e)


def mysqlConnecting():
    connection = None
    print('Connecting to database...')
    try:
        connection = mysql.connector.connect(
            host='185.98.5.170',
            user='p-16561_youcarusr',
            passwd='8j!tpB11',
            database='p-16561_youcarbase21'
        )
        print('MySQL Database connection successful')
    except Error as err:
        print(f"Connection error: {err}")
    return connection


# Function for SELECT query to DB
def readQuery(connection, query):
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        result = cursor.fetchall()
        return result
    except Error as err:
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
