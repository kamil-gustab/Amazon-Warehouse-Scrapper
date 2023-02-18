import argparse
import email_notificator
import logging
import pandas
import requests
import telegram_send
import os
from bs4 import BeautifulSoup
from datetime import datetime

HEADERS = ({'User-Agent':
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/94.0.4606.81 Safari/537.36',
            'Accept-Language': 'en-US, en;q=0.5'})


def notify_telegram(product_name, price, link, price_diff):
    try:
        message = f'''
            We found match for one of your items:\n
            [{product_name}] for {price}\n
            Link: {link}\n
            It\'s {price_diff} cheaper than your target price!
            '''
        telegram_send.send(messages=[message])
    except Exception as e:
        logging.error(f'telegram_send wasnt configured propertly, error:\n{e}')


def format_price(price_str_):
    dot_sep = price_str_.find(".")
    coma_sep = price_str_.find(",")
    if dot_sep > 0:
        price_str_ = price_str_[:dot_sep]
    elif coma_sep > 0:
        price_str_ = price_str_[:coma_sep]
    price = int(''.join(i for i in price_str_ if i.isdigit()))
    return price


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--notify', type=str, required=True,
                        choices=['mail', 'no-notify', 'telegram'])
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()
    log_lvl = logging.INFO
    if args.debug:
        log_lvl = logging.DEBUG

    logging.basicConfig(
        level=log_lvl,
        filename='logs.log',
        format="%(levelname)s : %(asctime)s : %(message)s"
    )

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
            # If can't get Product title, then skips product
            continue

        # Checking if item is unavailable
        try:
            info = soup.select("#outOfStock .a-text-bold")[0].get_text()
            logging.debug(f"[{link}] out of stock, skipping..")
            continue
        # If available - checking warehouse price
        except IndexError:
            logging.debug(f"[{link}] in stock,"
                           " checking warehouse price..")
            try:
                # Might have problem with inting when price don't exist
                div_a = '#olpLinkWidget_feature_div .a-color-base'
                price_str_a = soup.select(div_a)[0].get_text()[:6]
                div_b = '#usedAccordionRow .a-price-whole'
                price_str_b = soup.select(div_b)[0].get_text()[:6]

                if format_price(price_str_a) < format_price(price_str_b):
                    price = format_price(price_str_a)
                else:
                    price = format_price(price_str_b)

            # If no warehouse - checking detail price
            except IndexError:
                logging.debug(f"Couldn't find WH price,"
                               " checking detail price..")
                try:
                    div = '#newAccordionRow_0 .a-price-whole'
                    price_str = soup.select(div)[0].get_text()[:6]
                    price = format_price(price_str)
                except IndexError:
                    logging.debug(f"Retrying with detail price..")
                    try:
                        div = '#corePrice_feature_div .a-price-whole'
                        price_str = soup.select(div)[0].get_text()[:6]
                        price = format_price(price_str)
                    except IndexError:
                        logging.debug(f"Couldn't find detail price for, skipping..")
                        continue

        # Sending email notifications if price is lower than our Target price
        try:
            if price < products.target_price[prod_number] \
                    and args.notify == "mail":
                email_notificator.send_mail(
                    product_name=product_name,
                    price=price,
                    link=products.link[prod_number],
                    price_diff=round(
                        products.target_price
                        [prod_number] - price, 2)
                )
                logging.info(
                    f'Sending email notification about '
                    f'[{product_name}] for: {price}')
            elif price < products.target_price[prod_number] \
                    and args.notify == "telegram":
                notify_telegram(
                    product_name=product_name,
                    price=price,
                    link=products.link[prod_number],
                    price_diff=round(
                        products.target_price
                        [prod_number] - price, 2)
                )
                logging.info(
                    f'Sending telegram notification about '
                    f'[{product_name}] for: {price}')
        except TypeError:
            pass

        data = pandas.DataFrame({
            'Date': date_now,
            'Link': link,
            'Product name': product_name,
            'Target price': products.target_price[prod_number],
            'Actual price': price
        }, index=[prod_number])

        recent_data = recent_data.append(data)
        logging.info(f'Patching [{product_name}] to data set.')

    previous_searches = f'{search_data_path}/searching_history.xlsx'
    previous_data = pandas.read_excel(previous_searches)
    logging.info('Collecting previous data.')

    complete_data = previous_data.append(recent_data, sort=False)
    logging.info('Appending recent data, and merging with previous data.')

    complete_data.to_excel('search_data/searching_history.xlsx', index=False)
