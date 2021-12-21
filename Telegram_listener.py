from urllib.parse import ParseResultBytes
from telethon import TelegramClient, events
import configparser
import re
import requests

lastexecutedsymbol="temp"
config = configparser.ConfigParser()
config.read('config.ini')
user = 'kk'
api_id_temp = config[user]['api_id']
api_hash = config[user]['api_hash']
phone = config[user]['phone']
username = config[user]['username']
saint = config['groups']['saint']


def handle_hashtag_message(text):
    global lastexecutedsymbol
    print("lastexecutedsymbol ",lastexecutedsymbol)
    buy_sell = ""
    pair = ""
    entry_zone_min = ""
    entry_zone_max = ""
    leverage = "10"
    tp1 = ""
    tp2 = ""
    tp3 = ""
    tp4 = ""
    tp5 = ""
    tp6 = ""
    stop_loss = ""
    flag = 0
    text = text.upper()
    print("inside handle hashtag")
    if "LONG" in text:
        text = text.lower()
        
        zone = re.findall("entry zone\s?:\s?(.*)\s\|\s?(.*)\s\[.*",text)
        print(zone)
        if zone[0][1]:
            entry_zone_min = zone[0][1]
        else:
            entry_zone_min = zone[0][0]
        
        tp= re.findall("target 1\s:\s(.*)\s+(target 2\s:\s(.*))?\s+(target 3\s:\s(.*))?\s+(target 4\s:\s(.*))?",text)
        print(tp)
        tp = tp[0]
        tp1 = tp[0]
        tp2= tp[2]
        tp3 = tp[4]
        tp4 = tp[6]
        listoftps = [tp1,tp2,tp3,tp4]
        if float(entry_zone_min) < float(tp1):
            buy_sell = "LONG"
        else:
            buy_sell = "SHORT"
        actualtp= []
        for each in listoftps:
            if each:
                actualtp.append(each)
        print(actualtp)
        stop_loss = re.findall("stop loss\s?:\s\s?(.*)\s\/",text)[0]
        #stoptarget = stoptarget[0]
        print(stop_loss)
        symbolmatch = re.findall("\$(\w+)\/(\w+)", text)
        print(symbolmatch)
        pair = (symbolmatch[0][0])+str(symbolmatch[0][1])

        profit = [tp1,tp2,tp3,tp4]
        profitconverted = []
        for each in profit:
            if each !="":
                profitconverted.append(float(each))
        if "LONG" in buy_sell:
            position = 1
        elif "SHORT" in buy_sell:
            position = 0
        print(len(pair),pair)
        while("" in profit) :
            profit.remove("")
        data = {'stoploss': stop_loss , 'leverage': '10', 'entrypoint': entry_zone_min, 'symbol': pair, 'position': position, 'message': True,'takeprofits':profitconverted}
        print(data)
        url = "http://localhost:63844/startTrading/"
        try:
            if lastexecutedsymbol.lower() != pair.lower():
                lastexecutedsymbol = pair
                requests.post(url, timeout=1, json=data)
            else:
                lastexecutedsymbol = pair
        except requests.exceptions.ReadTimeout: 
            pass
    else:
        print("I couldn't read the message man... message is \n",text)

@events.register(events.NewMessage(chats=int(saint)))
async def handler(event):
    print(event)
    print(event.message.message)
    print("############",event.reply_markup)
    # if not event.out:
    if event:
        message = event.raw_text
        if (("LONG" or "SHORT" in message) and ("Entry Zone" in message) and ("Target" in message))  and event.reply_markup is None :
            handle_hashtag_message(message)
            pass
        else:
            pass
            

client = TelegramClient(username, api_id_temp, api_hash)
#client.send_message(entity)
with client:
    client.add_event_handler(handler)

    print('(Press Ctrl+C to stop this)')
    client.run_until_disconnected()
