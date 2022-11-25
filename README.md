# :package: Amazon Warehouse Scrapper
Follow steal prices for returned items!
## :book: Description
It is the python app - Web Scrapper for checking and saving price histories for Amazon Warehouse items.
## 🚀 Usage
Make sure you have installed:
* [BeautifulSoup4](https://pypi.org/project/beautifulsoup4)
* [lxml](https://pypi.org/project/lxml/)
* [pandas](https://pypi.org/project/pandas)
* [requests](https://pypi.org/project/requests)
* [telegram_send](https://pypi.org/project/telegram_send)
* [openpyxl](https://pypi.org/project/openpyxl)


### Notifying

You can choose between two options of notifying
- By telegram message (preferred option)
- By e-mail

---
### a) Notifying by telegram message
To do so you first need to configure your `telegram_send` package.

To do so:
1) First create your new telegram bot by writing on telegram to the `BotFather` on telegram, and create new bot by using command `/newbot`.
2) After filling all needed data you will be given you HTTP API token for your bot.
3) In CLI use command `telegram-send configure` - paste your token there, then add your freshly created bot on telegram and send him your activation password (code).
4) Voi'la - you can simply use your bot!

---
### b) Notifying by mail

For best experience you should use gmail along with per-app-password for your script.
More about App Password for gmail - [here](https://support.google.com/accounts/answer/185833)

You need to complete the file you can find in: `/config`

`options.txt`

Data examples:

1. Recipient Email
2. Sender Email address
3. Sender Email app-password

![options.txt example screen](https://i.imgur.com/YR5KSeG.png)

---
### Fill with products

To do so, you should modify file in `/config` named:

`tracked_products.csv`

You can add your products, with target price below which you will receive email notifications.

Data examples:

Product link, Our target price

![tracked_products.csv example screen](https://i.imgur.com/Vdin40U.png)

---
### Run

Just run one of the following commands (depending on which notify engine you want to use) at the root of your project:
```
python scrapper.py --notify mail
python scrapper.py --notify telegram
python scrapper.py --notify no-notify
```
Or schedule it to run every X minutes on your machine, by using e.g. crontab like:
```
| every 10min   | your path to scrapper catalog | path to your python         | parameters
*/10 * * * * cd /home/Amazon-Warehouse-Scrapper; /usr/bin/python3 scrapper.py --notify telegram
```

Script does provide logs, along with filling `searching_history.xlsx` file with data from each run.
When finds

---
## Author

👤 **Kamil Gustab**

- Github: [@gustab.kamil](https://github.com/kamil-gustab)
