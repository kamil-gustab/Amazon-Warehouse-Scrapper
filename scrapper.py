import argparse
import email_notificator
import json
import logging
import pandas
import requests
import telegram_send
import os
from bs4 import BeautifulSoup
from datetime import datetime
from random import randint

HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avi"
    "f,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-language": "en-US,en;q=0.9,pl;q=0.8",
    "cache-control": "max-age=0",
    "device-memory": "8",
    "dnt": "1",
    "downlink": "10",
    "dpr": "1",
    "ect": "4g",
    "rtt": "100",
    "sec-ch-device-memory": "8",
    "sec-ch-dpr": "1",
    "sec-ch-ua": "^\^Google",
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": "^\^Windows^^",
    "sec-ch-ua-platform-version": "^\^10.0.0^^",
    "sec-ch-viewport-width": "910",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
    "viewport-width": "910"
}


def load_proxies():
    logging.info('Loading proxies..')
    raw_request = requests.get(
        "https://raw.githubusercontent.com/mertguvencli/http-proxy-list/main/proxy-list/data.json").text
    proxies_list = json.loads(raw_request)
    return proxies_list


def notify_telegram(product_name, price, link, price_diff, config_path=None):
    try:
        message = f'''
            We found match for one of your items:\n
            [{product_name}] for {price}\n
            Link: {link}\n
            It\'s {price_diff} cheaper than your target price!
            '''
        if config_path:
            telegram_send.send(messages=[message], conf=config_path)
        else:
            telegram_send.send(messages=[message])
    except Exception as e:
        logging.error(f'telegram_send wasnt configured propertly, error:\n{e}')


def format_price(price_str_):
    if price_str_ is not None:
        dot_sep = price_str_.find(".")
        coma_sep = price_str_.find(",")
        if coma_sep > 0:
            price_str_ = price_str_[:coma_sep]
        elif dot_sep > 0:
            price_str_ = price_str_[:dot_sep]
        try:
            price = int(''.join(i for i in price_str_ if i.isdigit()))
        except ValueError:
            # temp solution, just crazy huge price for comparasion
            price = 9999999
        return price
    else:
        # temp solution, just crazy huge price for comparasion
        return 9999999


def get_prod_title(soup_obj):
    try:
        product_name = soup_obj.find(id="productTitle").get_text().strip()
        return product_name
    except AttributeError:
        logging.debug(
                f'Couldnt find product name for {link}')
        # If can't get Product title, then skips product
        return None


def check_prod_availability(soup_obj):
    """Function checks product's availability, returns True if is available"""
    try:
        soup_obj.select("#outOfStock .a-text-bold")[0].get_text()
        logging.debug(f"[{link}] out of stock, skipping..")
        return False
    # If available - checking warehouse price
    except IndexError:
        logging.debug(f"[{link}] in stock, checking warehouse price..")
        return True


def get_detail_price(soup_obj):
    logging.debug("Checking detail price..")
    try:
        div = '#newAccordionRow_0 .a-price-whole'
        price_str = soup_obj.select(div)[0].get_text()[:6]
        price = format_price(price_str)
        return price
    except IndexError:
        logging.debug("Retrying with detail price..")
        try:
            div = '#corePrice_feature_div .a-price-whole'
            price_str = soup_obj.select(div)[0].get_text()[:6]
            price = format_price(price_str)
            return price
        except IndexError:
            logging.debug("Couldn't find detail price for, skipping..")
            return None


def get_wh_price(el_name, soup_obj):
    try:
        element = soup_obj.select(el_name)[0].get_text()[:6]
    except IndexError:
        # when didn't find anything
        return None
    return element


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config",
        help="Provide absolute path to the custom telegram_send config file.",
        type=str,
        required=False
    )
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
    proxy_list = load_proxies()

    for prod_number, link in enumerate(products.link):
        # loop for each item to brute force through errors
        while True:
            rand_prxy = proxy_list[randint(0, len(proxy_list)-1)]
            proxy = {
                "http": f"http://{rand_prxy['ip']}:{rand_prxy['port']}",
                "https": f"https://{rand_prxy['ip']}:{rand_prxy['port']}"
            }
            logging.debug(f"Trying with proxy: {rand_prxy['ip']}:{rand_prxy['port']}")
            try:
                page = requests.get(products.link[prod_number], proxies=proxy, headers=HEADERS, timeout=15)
                # page = requests.get(products.link[prod_number], proxies=proxy, headers=HEADERS)
                soup = BeautifulSoup(page.content, features='lxml')
                if "To discuss automated access to Amazon data" in str(soup):
                    logging.warning("Cooldown from amazon applied, trying different proxy..")
                elif "This item cannot be shipped to your selected delivery location" in str(soup):
                    logging.warning("Wrong proxy location for item, trying different proxy..")
                else:
                    break
            except TimeoutError:
                logging.warning("Proxy or destination server timed out, retrying..")
            except requests.exceptions.ConnectTimeout:
                logging.warning("Proxy or destination server timed out, retrying..")
            except requests.exceptions.ProxyError:
                logging.warning("Proxy error happened, retrying w/ different one..")
            except requests.exceptions.ConnectionError:
                logging.warning("Cennection error happened, retrying w/ different proxy..")
            except requests.exceptions.SSLError:
                logging.warning("SSLError happened, retrying w/ different proxy..")

        product_name = get_prod_title(soup)
        # If couldn't find prod name
        if product_name is None:
            continue
        # Checking if item is available
        if not check_prod_availability(soup):
            continue
        else:
            # Giving a try for different divs, and taking cheapest.
            div_a = '#olpLinkWidget_feature_div .a-color-base'
            price_str_a = get_wh_price(div_a, soup)

            div_b = '#usedAccordionRow .a-price-whole'
            price_str_b = get_wh_price(div_b, soup)

            div_c = '#olpLinkWidget_feature_div .a-price-whole'
            price_str_c = get_wh_price(div_c, soup)

            # Taking lowest price from different tries
            price = min(
                format_price(price_str_a),
                format_price(price_str_b),
                format_price(price_str_c)
            )
            if price == 9999999:
                price = get_detail_price(soup)
                if price is None:
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
                if args.config:
                    notify_telegram(
                        product_name=product_name,
                        price=price,
                        link=products.link[prod_number],
                        price_diff=round(
                            products.target_price
                            [prod_number] - price, 2),
                        config_path=args.config
                    )
                else:
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

        if price < 9999999:
            logging.info(f'Finally found [{product_name}] for: {price}')
            data = pandas.DataFrame({
                'Date': date_now,
                'Link': link,
                'Product name': product_name,
                'Target price': products.target_price[prod_number],
                'Actual price': price
            }, index=[prod_number])
            recent_data = recent_data.append(data)
            logging.info(f'Patching [{product_name}] to data set.')

    # logging only when found anything
    if not recent_data.empty:
        previous_searches = f'{search_data_path}/searching_history.xlsx'
        previous_data = pandas.read_excel(previous_searches)
        logging.info('Collecting previous data.')

        complete_data = previous_data.append(recent_data, sort=False)
        logging.info('Appending recent data, and merging with previous data.')

        complete_data.to_excel('search_data/searching_history.xlsx', index=False)
