import email_notificator
import requests
import pandas
import os
import logging
from bs4 import BeautifulSoup
from datetime import datetime
from glob import glob


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s : %(asctime)s : %(message)s"
)

HEADERS = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})

if __name__ == "__main__":
    # Reading file
    products = pandas.read_csv('config/tracked_products.csv', sep=',')
    date_now = datetime.now().strftime('%Y-%m-%d %H:%M')
    recent_data = pandas.DataFrame()

    for prod_number, link in enumerate(products.link):
        # Fetching urls
        page = requests.get(products.link[prod_number], headers=HEADERS)

        # Using BeautifulSoup for reading lxml
        soup = BeautifulSoup(page.content, features='lxml')
        product_name = soup.find(id="productTitle").get_text().strip()

        # Checking price for used items from Amazon Warehouse
        try:
            warehouse_price = round(float(soup.select('#olpLinkWidget_feature_div .a-color-base')
                                          [0].get_text()[:6].replace(',', '.'))*1.033616, 2)
        except IndexError:
            warehouse_price = 'not available'

        # Sending email notifications if price is lower than our Target price
        try:
            if warehouse_price < products.target_price[prod_number]:
                email_notificator.send_mail(
                    product_name=product_name,
                    price=warehouse_price,
                    link=products.link[prod_number],
                    price_diff=round(products.target_price[prod_number] - warehouse_price, 2)
                )
                logging.info(f'Sending email notification about [{product_name}] for: {warehouse_price}')
        except TypeError:
            pass

        data = pandas.DataFrame({
            'Date': date_now,
            'Link': link,
            'Product name': product_name,
            'Target price': products.target_price[prod_number],
            'Actual price': warehouse_price
        }, index=[prod_number])

        recent_data = recent_data.append(data)
        logging.info(f'Patching [{product_name}] to data set.')

    abs_path = os.path.abspath("search_data")
    previous_searches = glob(f'{abs_path}/*.xlsx')[-1]
    previous_data = pandas.read_excel(previous_searches)
    logging.info(f'Collecting previous data.')

    complete_data = previous_data.append(recent_data, sort=False)
    logging.info(f'Appending recent data, and merging with previous data.')

    complete_data.to_excel('search_data/searching_history.xlsx', index=False)
