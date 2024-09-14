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

def position_details(pair):
    body = {
        "timestamp": timeStamp,  # EPOCH timestamp in seconds
        "page": "1",
        "size": "1",
        "pairs": pair,
        #"position_ids": "7830d2d6-0c3d-11ef-9b57-0fb0912383a7"

    }

    json_body = json.dumps(body, separators=(',', ':'))

    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

    url = "https://api.coindcx.com/exchange/v1/derivatives/futures/positions"

    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': key,
        'X-AUTH-SIGNATURE': signature
    }

    response = requests.post(url, data=json_body, headers=headers)
    data = response.json()
    print(data)
    return data


