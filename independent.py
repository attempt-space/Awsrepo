import socket
from flask import Flask, request, jsonify
import logging
import time
import configparser
from futures import *
import re,sys
from binance import ThreadedWebsocketManager

#app object for the application
collector = Flask(__name__)

class trading:
    def __init__(self,message,exchange="testnet"):
        self.exchange= "mainnet"
        self.message= message
        self.initializelogging()
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        self.amountoTrade = config["apinet"]["amountotrade"]
        self.exchange= config["apinet"]["network"]
        self.log = log
        if self.exchange=="testnet":
            user = 'testnetapikeys'
            self.api_key=config[user]["api_id"]
            self.api_secret=config[user]["api_sec"]
        elif self.exchange=="mainnet":
            user='mainnetapikeys'
            self.api_key=config[user]["api_id"]
            self.api_secret=config[user]["api_sec"]
        
    def initializelogging(self):
        self.log = logging.getLogger('Crypto Trading')

    def stopLossExecute(self):
        margin = self.client.account_info()

        for sub in margin["positions"]:
            if sub['symbol'] == self.message["symbol"].upper():
                amt = sub['positionAmt']
                found = re.findall("-?(.*)", amt)
                return self.getexactprecision(float(found[0]))

    def getorders(self):
        allorders = self.client.current_open_orders()
        self.log.info(allorders)
        listofOrders =[]
        depthOrders = {}
        stopOrders = None
        for eachorder in allorders:
            if eachorder["symbol"] == self.message["symbol"].upper() and eachorder["type"] =="TAKE_PROFIT" and eachorder["status"]=="NEW":
                listofOrders.append(eachorder['orderId'])
                depthOrders[eachorder["orderId"]] = eachorder["stopPrice"]
            elif eachorder["symbol"] ==self.message["symbol"].upper() and eachorder["type"]== "STOP" and eachorder["status"] == "NEW":
                stopOrders = eachorder["orderId"]
        try:
            #self.log.info(listofOrders,depthOrders,type(depthOrders),stopOrders)
            print(listofOrders)
            print(depthOrders)
            print(stopOrders)
        except:
            print(listofOrders)
        return listofOrders,depthOrders,stopOrders

    def getConvertedQuantity(self):     
        info = entirefutures
        symbols_n_precision ={}
        for item in info['symbols']: 
            symbols_n_precision[item['symbol']] = item['quantityPrecision'] # not really necessary but here we are...
        print(symbols_n_precision)
        trade_size_in_dollars = self.amountoTrade
        symbol = self.message["symbol"]
        price = self.message["entrypoint"] # For example

        #order_amount = int(self.message["leverage"]) * int(trade_size_in_dollars) / float(price) # size of order in BTC
        order_amount = int(trade_size_in_dollars)* int(self.message["leverage"]) / float(price) # size of order in BTC
        print(symbol.upper(),order_amount)
        precision = symbols_n_precision[symbol.upper()] # the binance-required level of precision

        precise_order_amount = "{:0.0{}f}".format(order_amount, precision) # string of precise order amount that can be used when creating order
        if precise_order_amount == int(0):
            return 1
        else:
            return precise_order_amount


    def getexactprecision(self,quantity):
        info = entirefutures
        symbols_n_precision ={}
        for item in info['symbols']: 
            symbols_n_precision[item['symbol']] = item['quantityPrecision'] # not really necessary but here we are...
        
        symbol = self.message["symbol"]
    

        precision = symbols_n_precision[symbol.upper()] # the binance-required level of precision

        precise_order_amount = "{:0.0{}f}".format(quantity, precision) # string of precise order amount that can be used when creating order
        
        return precise_order_amount
        
    def constructBatchOrders(self,executedquantity):

        tps = self.message["takeprofits"]
        if len(tps) == 4:
            profitpercentage = [0.7,0.1,0.1,0.1]
        elif len(tps) == 3:
            profitpercentage = [0.7,0.2,0.1]
        elif len(tps) == 2:
            profitpercentage =[0.7,0.3]

        quantity = []
        for i in range(len(self.message["takeprofits"])):
            quantity.append(float(profitpercentage[i]) * float(executedquantity))
        self.log.info("Adding Batch order for {}".format(quantity))

        return tps,quantity
    def tps_Quantity(self):
        tempTakeProfits = self.message["takeprofits"]
        self.tps_quantity ={}

        for i in range(len(tempTakeProfits)):
            if i == 0:
                self.tps_quantity.update({tempTakeProfits[i]:self.message["entrypoint"]})
            else:
                self.tps_quantity.update({tempTakeProfits[i]: tempTakeProfits[i-1]})
                
        self.log.info(self.tps_quantity)
        return self.tps_quantity

    def getquantity(self,currentexecutedtp):
        valueforstoploss = self.tps_quantity[float(currentexecutedtp)]
        return valueforstoploss
        
    def watchorders(self,ordersList):
        orderstatus ={}
        for eachorder in ordersList:
            orderstatus[eachorder["orderId"]] = orderstatus[eachorder["status"]]

    def Diff(self,li1, li2):
        return list(set(li1) - set(li2)) + list(set(li2) - set(li1))

    def cleanup(self):
        #check any position left
        time.sleep(0.5)
        checkingposition = self.stopLossExecute()
        if float(checkingposition) != float(0):
            self.log.info("Seems some residual is left,lets clear that also at market price ",checkingposition)
            if self.current_status['side'] =="SELL":
                market_residual = self.client.new_order(self.message["symbol"],"BUY",orderType="MARKET",quantity=self.stopLossExecute(),reduceOnly=True)
                self.log.info("placed Market order at stoploss ",market_residual)
            elif self.current_status['side'] =="BUY":
                market_residual = self.client.new_order(self.message["symbol"],"SELL",orderType="MARKET",quantity=self.stopLossExecute(),reduceOnly=True)
                self.log.info("placed Market order at stoploss ", market_residual)

    def handlemultipleTPs(self,orderExecution):
        self.log.info("Inside handlemultipleTPs  ",orderExecution)
        if orderExecution['e'] == "ACCOUNT_UPDATE":
            balance = orderExecution['a']['P']
            for each in balance:
                if each['s'] == self.message["symbol"].upper():
                    self.totalbalance = re.findall("-?(.*)", each['pa'])[0]
        elif orderExecution['e'] == "ORDER_TRADE_UPDATE":
            time.sleep(0.3)       
            order = orderExecution['o']
            if order["s"] ==self.message["symbol"].upper() and order["ot"]== "TAKE_PROFIT" and order["X"] in  ["FILLED"]:
                currentexecutedOrder = order['i']
                self.log.info(currentexecutedOrder)
                #cancel current stop loss
                loss_cancel = self.client.cancel_order(self.current_stoploss['symbol'],orderId=self.current_stoploss['orderId'])
                self.log.info(loss_cancel)
                self.totalOrders = self.totalOrders -1
                if self.totalOrders:
                    if self.message["position"] == 0:
                        self.current_stoploss = self.client.new_order(self.message["symbol"],"BUY",orderType="STOP",price=self.getquantity(self.globaldepthOrders[currentexecutedOrder]),quantity=self.totalbalance,stopPrice=self.getquantity(self.globaldepthOrders[currentexecutedOrder]))
                    elif self.message["position"] == 1:
                        self.current_stoploss = self.client.new_order(self.message["symbol"],"SELL",orderType="STOP",price= self.getquantity(self.globaldepthOrders[currentexecutedOrder]),quantity=self.totalbalance,stopPrice=self.getquantity(self.globaldepthOrders[currentexecutedOrder]))

                    self.log.info(self.current_stoploss)
                    self.globalallOrders.remove(currentexecutedOrder)
                else:
                    self.twm.stop_socket(self.multipleOrders)
                    self.twm.stop()
            elif order["s"] ==self.message["symbol"].upper() and order["ot"]== "STOP" and order["X"] in  ["FILLED"]:
                listofOrders,depthOrders,stopOrder =self.getorders()
                for eachorder in listofOrders:
                    self.log.info("Cancelled the order ",self.client.cancel_order(self.message["symbol"], eachorder))
                current_orders_count =0
                self.twm.stop_socket(self.multipleOrders)
                self.twm.stop()
                
                self.cleanup()

    def handleorders(self,orderexecution):
        self.log.info(orderexecution)
        if orderexecution['e'] == "ORDER_TRADE_UPDATE":
            current_status = orderexecution['o']
            executed_quantity = current_status['q']
            self.log.info("Executed quantity of Main Order {}".format(executed_quantity))            
            time.sleep(0.3)
            val = ["BUY" if self.message["position"] == 1 else "SELL"]
            if current_status['X'] in ['FILLED','PARTIALLY_FILLED'] and current_status["s"] == self.message["symbol"].upper() and current_status["S"]==val[0]:
                self.log.info("Seems main order is executed & placing OCO orders")
                self.tps_Quantity()

                if current_status['S'] =="SELL":    
                    tps,quantity = self.constructBatchOrders(executed_quantity)
                    for i in range(len(self.message["takeprofits"])):
                        profit = self.client.new_order(self.message["symbol"],"BUY",orderType="TAKE_PROFIT",quantity=self.getexactprecision(quantity[i]),stopPrice=tps[i],price=tps[i])

                        self.log.info("Profit order executed & details are {}".format(profit))
                    self.log.info("Executing Stop Market Order")
                    self.totalOrders = len(self.message["takeprofits"])

                    self.current_stoploss = self.client.new_order(self.message["symbol"],"BUY",orderType="STOP",price=self.message["stoploss"],quantity=executed_quantity,stopPrice=self.message["stoploss"])
                    self.log.info("Loss order executed & details are {}".format(self.current_stoploss))
                    
                elif current_status['S'] =="BUY":
                    tps,quantity = self.constructBatchOrders(executed_quantity)
                    self.log.info("Executing Take Profit Market Order Take profit is {} and quantity is {}".format(tps,quantity))
                    for i in range(len(self.message["takeprofits"])):
                        profit = self.client.new_order(self.message["symbol"],"SELL",orderType="TAKE_PROFIT",quantity=self.getexactprecision(quantity[i]),stopPrice=tps[i],price=tps[i])
                        self.log.info("Profit order executed & details are {}".format(profit))
                    self.log.info("Profit order executed & details are {}".format(profit))
                    self.log.info("Executing Stop Market Order")
                    self.totalOrders = len(self.message["takeprofits"])
                    self.current_stoploss = self.client.new_order(self.message["symbol"],"SELL",orderType="STOP",price=self.message["stoploss"],quantity=executed_quantity,stopPrice=self.message["stoploss"])
                    self.log.info("Loss order executed & details are {}".format(self.current_stoploss))

                self.globalallOrders,self.globaldepthOrders,self.globalstopOrder = self.getorders()
                
                self.twm.stop_socket(self.mainorder)
                self.twm.stop()
                self.twm = ThreadedWebsocketManager(api_key=self.api_key,api_secret=self.api_secret, testnet=False,tld="com")
                self.twm.start()
                self.multipleOrders = self.twm.start_futures_socket(callback=self.handlemultipleTPs)
                self.twm.join()
            elif current_status['X'] in ['CANCELED'] and current_status["s"] == self.message["symbol"].upper():
                self.twm.stop()
                self.twm.stop_socket(self.mainorder)
                
                
    def redirector(self):

        self.twm = ThreadedWebsocketManager(api_key=self.api_key,api_secret=self.api_secret, testnet=False,tld="com")
        # start is required to initialise its internal loop
        self.twm.start()

        # def handle_socket_message(msg):
        #     self.log.info(msg)
        self.mainorder = self.twm.start_futures_socket(callback=self.handleorders)
    
        self.twm.join()

    def perform_trading(self):  
        self.log.info(self.message)
        if self.exchange == "testnet":
            self.client= Client(api_key=self.api_key,sec_key=self.api_secret,testnet=True,symbol=self.message["symbol"])
            self.log.info("ApiKey for trading {} API secret for Trading {} Symbol for Trading {}".format(self.api_key,self.api_secret,self.message["symbol"]))
        elif self.exchange== "mainnet":
            self.client= Client(api_key=self.api_key,sec_key=self.api_secret,testnet=False,symbol=self.message["symbol"])
            self.log.info("ApiKey for trading {} API secret for Trading {} Symbol for Trading {}".format(self.api_key,self.api_secret,self.message["symbol"]))
        if self.message["leverage"]:
            leverage= self.message["leverage"]
            self.client.change_leverage(int(leverage))
        #Changing margin Type to Isolated
        
        self.client.margin_type(self.message["symbol"])
        self.log.info("margin type changing to ISOLATED")

        if self.message["position"]: #if 1 == buy order
            orderid = self.client.new_order(self.message["symbol"],"BUY",orderType="STOP_MARKET",stopPrice=self.message["entrypoint"],quantity=self.getConvertedQuantity())
            self.log.info("order details of Main order {}".format(orderid))
        else:

            orderid = self.client.new_order(self.message["symbol"],"SELL",orderType="STOP_MARKET",stopPrice=self.message["entrypoint"],quantity=self.getConvertedQuantity())
            self.log.info("order details of Main order {}".format(orderid))

        executed_orderid =orderid["orderId"]
        executed_symbol = orderid["symbol"]
        self.log.info("Executed order id {} and its symbol {}".format(executed_orderid,executed_symbol))
        self.redirector()

@collector.route('/startTrading/',methods=['POST'])
def index():
    try:
        data= request.get_json()
    except (ValueError,KeyError,TypeError,AttributeError):
        return jsonify("invalid format/data")
    cryptoAgent = trading(data)
    agent = cryptoAgent.perform_trading()
    empty = {}
    return empty


def get_futuresprecisionDetail():
    api_key = '6fda2f274e99aa3e20b15436ade90bb437b6a7aef13fcbe66d4e38cf6a9416eb'
    api_secret = '0f215bbece4e3dfa1f9a8cf5a0588002b6bb0389d6e0c4d5af6e61cc882cf019'

    client = Client(api_key, api_secret)
    global entirefutures
    entirefutures = client.futures_exchange_info() # request info on all futures symbols

def main():
    #server details
    host, port, alt_port = '0.0.0.0', 63844,63845
    #debug mode
    debug = False
    get_futuresprecisionDetail()
    try:
        log.info("********************************************************************************")
        log.info("* Product Name  : Start of Crypto Trading ")
        log.info("* Start Date    : %s" %time.strftime("%Y-%m-%d"))
        log.info("* Start Time    : %s" %time.strftime("%H:%M:%S"))
        log.info("********************************************************************************")
        log.info("********************************************************************************")
        collector.run(host=host, port=port, debug=debug, threaded=True)

    except socket.error:
        try:
            collector.run(host=host, port=alt_port, debug=debug, threaded=True)
        except socket.error:
            collector.run(host=host, port=0, debug=debug, threaded=True)

if __name__ == '__main__':
    log = logging.getLogger('Crypto Trading')
    log.setLevel(logging.DEBUG)
    FORMAT = '%(asctime)-15s.%(msecs)-5d %(name)-20s %(levelname)-7s Function - %(funcName)s: Line - %(lineno)d %(message)s'
    DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
    formatter      = logging.Formatter(fmt = FORMAT, datefmt = DATE_FORMAT)
    handler_stream = logging.StreamHandler()
    handler_stream.setFormatter(formatter)
    handler_stream.setLevel(logging.INFO)
    log.addHandler(handler_stream)
    handler_file = logging.FileHandler('CryptoTrading_%s.log' %time.strftime("%Y%m%d_%H%M%S"))
    handler_file.setFormatter(formatter)
    log.addHandler(handler_file)
    main()

    