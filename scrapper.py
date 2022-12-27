import argparse
import email_notificator
import logging
import pandas
import requests
import telegram_send
import os
from bs4 import BeautifulSoup
from datetime import datetime


logging.basicConfig(
    level=logging.DEBUG,
    filename='logs.log',
    format="%(levelname)s : %(asctime)s : %(message)s"
)

HEADERS = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/94.0.4606.81 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})


def notify_telegram(product_name, price, link, price_diff):
    try:
        message = f'''
            We found match for one of your items:\n
            [{product_name}] for {price} euro\n
            Link: {link}\n
            It\'s {price_diff} euro cheaper than your target price!
            '''
        telegram_send.send(messages=[message])
    except Exception as e:
        logging.error(f'telegram_send wasnt configured propertly, error:\n{e}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--notify', type=str, required=True,
                        choices=['mail', 'no-notify', 'telegram'])
    args = parser.parse_args()

    config_path = os.path.abspath("config")
    search_data_path = os.path.abspath("search_data")

    # Reading file
    products = pandas.read_csv(f'{config_path}/tracked_products.csv', sep=',')
    date_now = datetime.now().strftime('%Y-%m-%d %H:%M')
    recent_data = pandas.DataFrame()

    for prod_number, link in enumerate(products.link):
        # Fetching urls
        page = requests.get(products.link[prod_number], headers=HEADERS)

        # Using BeautifulSoup for reading lxml
        soup = BeautifulSoup(page.content, features='lxml')

        try:
            product_name = soup.find(id="productTitle").get_text().strip()
        except AttributeError:
            logging.debug(
                    f'Couldnt find product name for {link}')
            continue
            # If can't get Product title, then skips product
            continue

        # Checking price for used items from Amazon Warehouse
        try:
            div = '#olpLinkWidget_feature_div .a-color-base'
            warehouse_price = round(float(soup.select(div)
                                          [0].get_text()[:6].
                                          replace(',', '.')) * 1.033616, 2)
        except IndexError:
            # If product doesn't have its price
            logging.debug(
                    f'Couldnt find price for {product_name}')
            continue

        # Sending email notifications if price is lower than our Target price
        try:
            if warehouse_price < products.target_price[prod_number] \
                    and args.notify == "mail":
                email_notificator.send_mail(
                    product_name=product_name,
                    price=warehouse_price,
                    link=products.link[prod_number],
                    price_diff=round(
                        products.target_price
                        [prod_number] - warehouse_price, 2)
                )
                logging.info(
                    f'Sending email notification about '
                    f'[{product_name}] for: {warehouse_price}')
            elif warehouse_price < products.target_price[prod_number] \
                    and args.notify == "telegram":
                notify_telegram(
                    product_name=product_name,
                    price=warehouse_price,
                    link=products.link[prod_number],
                    price_diff=round(
                        products.target_price
                        [prod_number] - warehouse_price, 2)
                )
                logging.info(
                    f'Sending telegram notification about '
                    f'[{product_name}] for: {warehouse_price}')
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

    previous_searches = f'{search_data_path}/searching_history.xlsx'
    previous_data = pandas.read_excel(previous_searches)
    logging.info('Collecting previous data.')

    complete_data = previous_data.append(recent_data, sort=False)
    logging.info('Appending recent data, and merging with previous data.')

    complete_data.to_excel('search_data/searching_history.xlsx', index=False)
