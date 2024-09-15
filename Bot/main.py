import os
import sys
import fcntl

# Create a lock file in /tmp directory
lock_file_path = '/tmp/main_py.lock'
lock_file = open(lock_file_path, 'w')

try:
    # Try to acquire the lock, if already locked, it will raise an IOError
    fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
except IOError:
    print("Another instance is running. Exiting.")
    sys.exit(0)

# Continue with your main script logic here

# Make sure to release the lock at the end of your script
fcntl.flock(lock_file, fcntl.LOCK_UN)
lock_file.close()


import requests ,time , operator,csv
import numpy as np
from create_order import place_order
from get_position_details import position_details
from TPSL import tpsl
from account import balance
from datetime import datetime
from create_tp_order import place_tp_order
import pandas as pd
from ta.volatility import BollingerBands
from ta.volume import MFIIndicator
from ta.volatility import AverageTrueRange
from ta.momentum import RSIIndicator
import logging  # Add logging module
from secreate import BOT_TOKEN,CHAT_ID

# Setup logging
logging.basicConfig(filename='bot_execution.log', level=logging.INFO, 
                    format='%(asctime)s %(levelname)s %(message)s')

# Log start of the program
logging.info("Bot started")



url = "https://api.coindcx.com/exchange/v1/derivatives/futures/data/active_instruments"
response = requests.get(url)
symbol = response.json()
    
def bb_statergy(symbol, interval,signals):
    now = time.time()
    current_time = int(now)
    seconds_in_day = 60 * 90
    start_date = now - seconds_in_day


    try:
        url = "https://public.coindcx.com/market_data/candlesticks"
        query_params = {
            "pair": symbol,
            "from": start_date,
            "to": current_time,
            "resolution": interval,  # '1' OR '5' OR '60' OR '1D'
            "pcode": "f"
        }
        response = requests.get(url, params=query_params)
        if response.status_code == 200:
            data = response.json()
            data = data['data']
        else:
            logging.error(f"Error: {response.status_code} {symbol}, {response.text}")
            print(f"Error: {response.status_code} {symbol}, {response.text}")
    
        # Convert data to DataFrame
        df = pd.DataFrame(data)
        df['close'] = df['close'].astype(float)
        df['volume'] = df['volume'].astype(float)
        df['high'] = df['high'].astype(float)
        df['low'] = df['low'].astype(float)

        indicator_bb = BollingerBands(df['close'], window=10, window_dev=2, fillna=False)
        indicator_mfi = MFIIndicator(df['high'], low=df['low'], close=df['close'], volume=df['volume'], window=14, fillna=False)
        df['mfi'] = round(indicator_mfi.money_flow_index(), 2)
        df['bb_upper'] = indicator_bb.bollinger_hband()
        df['bb_lower'] = indicator_bb.bollinger_lband()
        bb_difference_perc = round(((df['bb_upper'].iloc[-2] - df['bb_lower'].iloc[-2]) / df['bb_lower'].iloc[-2]) * 100, 2)
        indicator_atr = AverageTrueRange(high=df['high'], low=df['low'], close=df['close'], window=14, fillna=False)
        df['atr'] = indicator_atr.average_true_range()
        indicator_rsi = RSIIndicator(close = df['close'], window = 14, fillna = False)
        df['rsi'] = indicator_rsi.rsi()
        volume24 = sum(df['volume']) * df['close'].iloc[-2]

 
        # Long Position
        sl_for_long = round((df['close'].iloc[-2] - ((df['close'].iloc[-2] - df['low'].iloc[-2]) + (2 * df['atr'].iloc[-2]))), 7)
        risk_amount_long = df['close'].iloc[-2] - sl_for_long
        tp_for_long = round((df['close'].iloc[-2] + (1.1 * risk_amount_long)), 7)

        # Short Position
        sl_for_short = round((((df['high'].iloc[-2] - df['close'].iloc[-2]) + (2 * df['atr'].iloc[-2])) + df['close'].iloc[-2]), 7)
        risk_amount_short = sl_for_short - df['close'].iloc[-2]
        tp_for_short = round((df['close'].iloc[-2] - (1.1 * risk_amount_short)), 7)

    except Exception as e:
        logging.error(f"Error processing data for {symbol}: {e}")
        print(f"Error processing data for {symbol}: {e}")
        return signals

    try:
        if df['close'].iloc[-2] >= df['bb_upper'].iloc[-2] and bb_difference_perc >= 1.5 and df['volume'].iloc[-2] < df['volume'].iloc[-3] and df['mfi'].iloc[-2] >= 75 and df['rsi'].iloc[-2] >= 85 and volume24 >= 30000 :   
            signals.append({"close_price":df['close'].iloc[-2],"Symbol": symbol, "Signal": "sell", "Percentage": bb_difference_perc, "MFI": df['mfi'].iloc[-2], "TP": tp_for_short, "SL": sl_for_short,"RSI":df['rsi'].iloc[-2]})
            logging.info(f"{symbol} sell signal generated")
            print(f"{symbol} sell || {signals[-1]} || {df['rsi'].iloc[-2]} || {df['rsi'].iloc[-2]}")

        elif df['close'].iloc[-2] <= df['bb_lower'].iloc[-2] and bb_difference_perc >= 1.5 and df['volume'].iloc[-2] < df['volume'].iloc[-3] and df['mfi'].iloc[-2] <= 25 and df['rsi'].iloc[-2] <= 15 and volume24 >= 30000:
            signals.append({"close_price":df['close'].iloc[-2],"Symbol": symbol, "Signal": "buy", "Percentage": bb_difference_perc, "MFI": df['mfi'].iloc[-2], "TP": tp_for_long, "SL": sl_for_long,"RSI":df['rsi'].iloc[-2]})
            logging.info(f"{symbol} buy signal generated")
            print(f"{symbol} buy || {signals[-1]} || {df['rsi'].iloc[-2]} || {df['rsi'].iloc[-2]}")
    except Exception as e:
        logging.error(f"Error generating signals for {symbol}: {e}")
        print(f"Error generating signals for {symbol}: {e}")



def count_digits_after_decimal(number):
    # Convert the number to a string
    number_str = str(number)
    # Split the string at the decimal point
    if '.' in number_str:
        decimal_part = number_str.split('.')[1]
        # Return the length of the decimal part
        return len(decimal_part)
    else:
        return 0  # If there is no decimal point, return 0


def bot(interval):
        
        url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'

        balance_c = float(balance())
        funds = round(balance_c,2)*0.7

        signalss = []

        print("No Open position running statergy")
        logging.info("No open positions; starting strategy")
        for i in symbol:
            bb_statergy(i,interval,signals= signalss)

        signalss.sort(key=operator.itemgetter('Percentage','MFI'), reverse=True)

        # The best signal is the first one in the sorted list
        try:
            best_signal = signalss[0]

            close_price = best_signal["close_price"]
            token = best_signal["Symbol"]
            trade_signal = best_signal["Signal"]
            percentage =best_signal["Percentage"]
            mfi = best_signal["MFI"]
            rsi = best_signal["RSI"]
            take_profit = best_signal["TP"]
            stop_loss = best_signal["SL"]
            date_time = datetime.now()
            print(trade_signal)
            balance_c = balance()

            #Get quantity
            quantity = round((funds*10)/close_price)
            print(funds)
            print(quantity)

            place_order(side=trade_signal,pair=token,quantity=quantity)

            time.sleep(10)

            postion_details_data = position_details(token)
            price = postion_details_data[0]["avg_price"]
            id = postion_details_data[0]["id"]
            active_pos = postion_details_data[0]["active_pos"]

            decimal = count_digits_after_decimal(close_price)

            if trade_signal == "buy" :
                tp = round(take_profit,decimal) 
                sl = round(stop_loss,decimal)
                place_tp_order(side="sell",pair=token,activ_pos=active_pos,tp=tp)
                print(sl,tp,id)
                tpsl(id=id,sl=sl)
                payload = {
                        'chat_id': CHAT_ID,
                        'text': f"Signal for {best_signal} \n Current Portfolio value is {balance_c} \n buy Price is {price} for 15 min "
                    }
                
                # Send the request
                response = requests.post(url, data=payload)

                # Check the response
                if response.status_code == 200:
                    print('Message sent successfully!')
                else:
                    print('Failed to send message:', response.text)
            
            elif trade_signal == "sell" :
                sl = round(stop_loss,decimal) 
                tp = round(take_profit,decimal)
                place_tp_order(side="buy",pair=token,activ_pos=-(active_pos),tp=tp)
                print(sl,tp)
                tpsl(id=id,sl=sl)
                payload = {
                        'chat_id': CHAT_ID,
                        'text': f"Signal for {best_signal} \n Current Portfolio value is {balance_c} \n buy Price is {price} for 15 min "
                    }
                # Send the request
                response = requests.post(url, data=payload)

                # Check the response
                if response.status_code == 200:
                    print('Message sent successfully!')
                else:
                    print('Failed to send message:', response.text)

            csv_file = [{"DateTime":date_time,"Token": token, "signal": trade_signal, "previous_closing": close_price,"buy/sell":price, "percentage": percentage, "SL": sl, "TP": tp,"interval":"15 min","Balance":balance_c,"RSI":rsi,"MFI":mfi}]
            with open('Trade_details_.csv', mode='a', newline='') as file:
                fieldnames = ["DateTime","Token", "signal", "previous_closing","buy/sell", "percentage", "SL", "TP","interval","Balance","RSI","MFI"]
                writer = csv.DictWriter(file, fieldnames=fieldnames)

                if file.tell() == 0:
                    writer.writeheader()
                
                writer.writerows(csv_file)
            print("Data saved to CSV successfully.")
                
        except IndexError:
            print("No signals generated.")
        except Exception as e:
            print(f"Error in bot execution: {e}")

def run_every_5_minutes():
    while True:

        # Calculate the time until the next 30-minute mark
        current_time = time.localtime()
        minutes = current_time.tm_min
        seconds = current_time.tm_sec
        
        # Calculate sleep time to the next 30-minute mark
        sleep_time = (15 - minutes % 15) * 60 - seconds

        sleep_time += 1

        print(f"Sleeping for {sleep_time} seconds.")
        
        time.sleep(sleep_time)
        bot(15)

if __name__ == "__main__":
    run_every_5_minutes()

 









