import hmac
import hashlib
import base64
import json
import time
import requests
from secreate import API_KEY,SECREAT_KEY
# Enter your API Key and Secret here. If you don't have one, you can generate it from the website.
key = API_KEY
secret = SECREAT_KEY
# python3

def balance():
    secret_bytes = bytes(secret, encoding='utf-8')

    # Generating a timestamp
    timeStamp = int(round(time.time() * 1000))
    body = {
        "timestamp": timeStamp

    }
    json_body = json.dumps(body, separators=(',', ':'))
    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
    url = "https://api.coindcx.com/exchange/v1/derivatives/futures/wallets"
    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': key,
        'X-AUTH-SIGNATURE': signature
    }
    response = requests.get(url, data=json_body, headers=headers)
    data = response.json()
    balance = data[0]["balance"]
    locked_balance = data[0]["locked_balance"]

    return balance 