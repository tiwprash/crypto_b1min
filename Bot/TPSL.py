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
secret_bytes = bytes(secret, encoding='utf-8')

# Generating a timestamp
timeStamp = int(round(time.time() * 1000))

def tpsl(id,sl):
    body = {
    "timestamp": timeStamp, # EPOCH timestamp in seconds
    "id": id, # position.id
    # "take_profit": {
    #     "stop_price": tp,
    #      # required for take_profit_limit orders
    #     "order_type": "take_profit_market" # take_profit_limit OR take_profit_market
    # },
    "stop_loss": {
      "stop_price": sl,
      "order_type": "stop_market" # stop_limit OR stop_market
  }
    }




    json_body = json.dumps(body, separators = (',', ':'))

    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

    url = "https://api.coindcx.com/exchange/v1/derivatives/futures/positions/create_tpsl"

    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': key,
        'X-AUTH-SIGNATURE': signature
    }

    response = requests.post(url, data = json_body, headers = headers)
    data = response.json()
    print(data)