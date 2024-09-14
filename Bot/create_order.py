import hmac
import hashlib
import json
import time
import requests
from secreate import API_KEY, SECREAT_KEY
from get_position_details import position_details

# Enter your API Key and Secret here
key = API_KEY
secret = SECREAT_KEY

# Convert secret to bytes
secret_bytes = bytes(secret, encoding='utf-8')

# Generating a timestamp
def get_timestamp():
    return int(round(time.time() * 1000))

def place_order(side, pair, quantity, leverage=10):
    timeStamp = get_timestamp()

    # Check if there is an existing position
    position_data = position_details(pair)
    if position_data:
        existing_leverage = position_data[0]['leverage']
    else:
        existing_leverage = leverage  # Use the provided leverage if no position exists

    body = {
        "timestamp": timeStamp,  # EPOCH timestamp in milliseconds
        "order": {
            "side": side,  # buy OR sell
            "pair": pair,  # instrument.string
            "order_type": "market_order",  # market_order OR limit_order
            "price": "",  # numeric value or empty for market orders
            "total_quantity": quantity,  # numeric value
            "leverage": existing_leverage,  # Use the existing leverage or provided leverage
            "notification": "no_notification",  # no_notification OR email_notification OR push_notification
            "time_in_force": "good_till_cancel",  # good_till_cancel OR fill_or_kill OR immediate_or_cancel
            "hidden": False,  # True or False
            "post_only": False  # True or False
        }
    }

    json_body = json.dumps(body, separators=(',', ':'))

    # Generate signature
    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()

    url = "https://api.coindcx.com/exchange/v1/derivatives/futures/orders/create"

    headers = {
        'Content-Type': 'application/json',
        'X-AUTH-APIKEY': key,
        'X-AUTH-SIGNATURE': signature
    }

    response = requests.post(url, data=json_body, headers=headers)
    data = response.json()
    print(data)
