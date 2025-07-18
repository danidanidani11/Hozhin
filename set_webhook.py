import requests

TOKEN = "7954708829:AAFg7Mwj5-iGwIsUmfDRr6ZRJZr2jZ28jz0"
URL = f"https://hozhin.onrender.com/{TOKEN}"  # آدرس سایتت در Render

set_webhook_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
response = requests.get(set_webhook_url, params={"url": URL})
print(response.json())
