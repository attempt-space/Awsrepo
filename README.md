# Attempt Space Crypto BOT

Best Crypto Bot to automatically trade cryptocurrencies based on signals from Telegram group

# What it does:

Built purely in python to track signals from Telegram group & start listening in web socket.
Depends on Websocket replies will execute the upcoming trades.

# Sample Telegram message:

Long #FLM/USDT 0.61-0.622
Sell @0.63-0.635-0.64-0.65-0.68-0.70-0.75-0.80+

Lev 10x

Stoploss 0.58

And yes you can start parsing your own Telegram message. check out More at Telegram_listener.py

#Parse Config.ini & Telegram_listener.py

Telegram_listener.py 
    - To run this file, start configuring your telegram details at "config.ini"
    - 

[kk]
# THis can be generated by https://my.telegram.org.
api_id = <apiid>
api_hash = <apihash>
phone = +91<MobileNumber>
username = <username of telegram>

[groups]

group2 = <Group ID - telegram>

[apinet]
network = mainnet
#mainnet or testnet You can test this code in mainnet also in Binance testnet
amountotrade = 10 (in dollars)

[mainnetapikeys]
api_id = <api ID Mainnet>
api_sec = <Api sec Key - Binance>


To start run -> python3 Telegram_listner.py

# Independent runs are always awesome 
The main code will do the following
    - Understand trade information from Telegram parsed messages.
    - Once understood, it will place a order which would be "STOP_MARKET" orders
        - A websocket stream will be initiated to check whether the order has been executed.
    - Once the initial orders are full-filled, the very next second, Multiple "Take Profit" and "Stop loss" orders are placed.
        - "STOP LOSS" orders are placed at given Stop loss
    - If TP1 is fullfilled
        - "STOP LOSS" orders are adjusted to TP1.
    - Next, If TP2 is fullfilled
        - "STOP LOSS" orders are adjusted to TP2 & wait for TP3 and TP4 orders.

To execute run -> python3 independent.py


