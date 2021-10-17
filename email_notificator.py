import smtplib
import ssl
import unicodedata
from email.message import EmailMessage


def get_passes():
    with open('config/options.txt', 'r') as f:
        file = f.readlines()
        recipient = file[0].strip()
        username = file[1].strip()
        password = file[2].strip()

    return recipient, username, password


def send_mail(product_name, price, link, price_diff):
    recipient_email, sender_email, sender_password = get_passes()
    product_name = unicodedata.normalize("NFKD", product_name)

    msg = EmailMessage()
    msg.set_content(f'''
    Buy [{product_name}] for {price} euro\n
    Link: {link}\n
    It\'s {price_diff} euro cheaper than your target price! 
    
    Message sent automatically by Amazon Warehouse Scrapper.
    ''')

    msg['Subject'] = 'Buy your product!'
    msg['From'] = 'Amazon Warehouse Scrapper'
    msg['To'] = recipient_email

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(sender_email, sender_password)
        server.send_message(msg)
