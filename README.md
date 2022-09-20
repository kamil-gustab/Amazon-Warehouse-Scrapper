# :package: Amazon Warehouse Scrapper
Follow steal prices for returned items!
## :book: Description
It is the python app - Web Scrapper for checking and saving price histories for Amazon Warehouse items.
## 🚀 Usage
Make sure you have installed:
* [requests](https://pypi.org/project/requests)
* [BeautifulSoup4](https://pypi.org/project/beautifulsoup4)
* [pandas](https://pypi.org/project/pandas)
* [openpyxl](https://pypi.org/project/openpyxl/)
* [lxml](https://pypi.org/project/lxml/)

Before run you need to complete 2 files you can find in: `/config`

`1. options.txt`

Data examples:

1. Recipient Email
2. Sender Email address
3. Sender Email password

![options.txt example screen](https://i.imgur.com/YR5KSeG.png)

---
`2. tracked_products.csv`

You can add your products, with target price below which you will receive email notifications.

Data examples:

Product link, Our target price

![tracked_products.csv example screen](https://i.imgur.com/Vdin40U.png)

---
After filling those files just run the following command at the root of your project:
```
python scrapper.py
```
Or schedule it to run every X minutes on your machine.

Script does provide logs, along with filling `searching_history.xlsx` file with data from each run.
When finds

## Author

👤 **Kamil Gustab**

- Github: [@gustab.kamil](https://github.com/kamil-gustab)
