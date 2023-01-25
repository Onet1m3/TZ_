import re
import json
import os
from typing import Optional
import requests
from bs4 import BeautifulSoup as BS
from fake_headers import Headers


WEB_URL = "https://www.truckscout24.de"
CARDS_ITEMS = []

def check_dir_or_create() -> None:
    if not os.path.isdir("data"):
        os.mkdir("data")


def create_json_data() -> None:
    data = {
        "ads": [i for i in CARDS_ITEMS]
    } 
    with open('data/new_file.json', 'w', encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _validate_data_to_int(data: str, type_str: str) -> Optional[int]:
    if type_str == "id":
        return int(data.split("_")[1])

    elif type_str == "price" or type_str == "mileage":
        nums = re.findall(r'\d*\.\d+|\d+', data)[0]
        num = nums.replace(".", "")
        return int(num)

    elif type_str == "power":
        return int(data.split(" ")[0])


def get_header_data() -> dict:
        header = Headers(
            headers=True
        )
        return header.generate()

def get_html_body(url: str) -> BS:
    html = requests.get(url, headers=get_header_data()).text
    soup = BS(html, 'lxml')
    return soup

def get_detail_data(detail_page: BS) -> dict():
    _title = detail_page.find('h1').get_text()
    _price_str = detail_page.find('h2', class_="sc-highlighter-4").get_text()
    _price = _validate_data_to_int(_price_str, type_str="price")
    spec_list = detail_page.find('div', class_="sc-expandable-box").find('ul', class_="columns").find_all('li')
    _color = ""
    _power = 0
    for item in spec_list:
        if item.find('div', class_="sc-font-bold").get_text()=="Farbe":
            _color = item.find('div').find_next().get_text()
        if item.find('div', class_="sc-font-bold").get_text()=="Leistung":
            _power = _validate_data_to_int(item.find('div').find_next().get_text(), type_str="power")

    _description = detail_page.find('div', attrs={"data-type": "description"}).get_text() #.find('p').get_text()
    return {
        "title": _title,
        "price": _price,
        "color": _color,
        "power": _power,
        "description": _description
    }
    

def parse_card(cards: BS) -> dict:
    parent = cards.find('div', class_="ls-elem ls-elem-gap")
    card = parent.find('div', class_="ls")
    card_id = parent.find('div', class_="ls-full-item").get_attribute_list("id")
    card_href = card.find('a').get('href')
    card_mileage =  _validate_data_to_int(card.find('div', class_="ls-data-additional").find('div').get_text(), type_str="mileage")
    card_detail_info = get_html_body(f"{WEB_URL}{card_href}")
    detail_data = get_detail_data(card_detail_info.body)
    detail_data.update({
        		"id": _validate_data_to_int(*card_id, type_str="id"),
                "href": f"{WEB_URL}{card_href}",
                "mileage": card_mileage,
    })
    return detail_data


def main() -> None:
    _page = 1
    while True:
        base_url = f"{WEB_URL}/transporter/gebraucht/kuehl-iso-frischdienst/renault?currentpage={_page}"
        soup = get_html_body(base_url)
        try:
            card = parse_card(soup.body.find(id="listResult"))
            CARDS_ITEMS.append(card)
            _page += 1
        except:
            create_json_data()
            break


if __name__ == "__main__":
    check_dir_or_create()
    main()
