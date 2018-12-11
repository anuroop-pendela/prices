import threading
import requests
import time
from main_application.models import Prices, RestCallStatus
import traceback
from .bitmex import BitmexWS
import logging
import re
from google.cloud import logging as lg
from google.cloud.logging import DESCENDING,ASCENDING
import os
import time
#import pandas as pd
from datetime import datetime

CLOUD_LOGGER_PATH="/home/ubuntu/Autospreader168/main_application/app/autospreader-201007-firebase-adminsdk-urukp-24c898aebc.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CLOUD_LOGGER_PATH
class priceUpdater:

    def __init__(self):
        """
        Constructor to do noting
        """
        print("Price updater Initialized")
        self.exchanges_list = {}

        # Store the public url's of the exchanges and traverse through them to store data.
        self.exchanges_list['cexio'] = 'https://cex.io/api/ticker/BTC/USD'
        self.exchanges_list['cexioEuro'] = 'https://cex.io/api/ticker/BTC/EUR'
        self.exchanges_list['bitflyer'] = 'https://api.bitflyer.com/v1/ticker'
        self.exchanges_list['bitflyerFx'] = 'https://api.bitflyer.com/v1/ticker'
        self.exchanges_list['coinfloor'] = 'https://webapi.coinfloor.co.uk:8090/bist/XBT/GBP/ticker/'
        self.exchanges_list['bitfinex'] = 'https://api.bitfinex.com/v1/pubticker/btcusd'

        self.exchange_meta_data = {}

        # NOTE: UNLESS UNTILL YOUR EXCHANGE IS IN exchanges_list, exchange_meta_data CAN BE ACCESSED.
        #           PLEASE MAKE SURE YOU HAVE ADDED EXHANGE ONCE CONFIGURED IT'S METADATA.

        # Metadata for cex.io
        self.exchange_meta_data['cexio'] = {}
        self.exchange_meta_data['cexio']['bid'] = 'bid'
        self.exchange_meta_data['cexio']['ask'] = 'ask'

        # Metadata for cex.io Euro
        self.exchange_meta_data['cexioEuro'] = {}
        self.exchange_meta_data['cexioEuro']['bid'] = 'bid'
        self.exchange_meta_data['cexioEuro']['ask'] = 'ask'

        # Metadata for coinfloor
        self.exchange_meta_data['coinfloor'] = {}
        self.exchange_meta_data['coinfloor']['bid'] = 'bid'
        self.exchange_meta_data['coinfloor']['ask'] = 'ask'

        # Metadata for bitfinex
        self.exchange_meta_data['bitfinex'] = {}
        self.exchange_meta_data['bitfinex']['bid'] = 'bid'
        self.exchange_meta_data['bitfinex']['ask'] = 'ask'

        # Metadata for bitflyer
        self.exchange_meta_data['bitflyer'] = {}
        self.exchange_meta_data['bitflyer']['bid'] = 'best_bid'
        self.exchange_meta_data['bitflyer']['ask'] = 'best_ask'
        self.exchange_meta_data['bitflyer']['params'] = {
            'product_code': 'BTC_JPY'}

        # Metadata for bitflyerFx
        self.exchange_meta_data['bitflyerFx'] = {}
        self.exchange_meta_data['bitflyerFx']['bid'] = 'best_bid'
        self.exchange_meta_data['bitflyerFx']['ask'] = 'best_ask'
        self.exchange_meta_data['bitflyerFx']['params'] = {
            'product_code': 'FX_BTC_JPY'}

        # Bitmex WS variables
        self.ws = None
        self.ws_thread = None
        self.ws_object = None
        self.ws_restart = False
        self.t1 = threading.Thread(target=self.__handle_bitmex_websocket__)
        self.t1.setName('__handle_bitmex_websocket__')
        self.t1.start()
        self.t2 = threading.Thread(target=self.__price_updater__)
        self.t2.setName('__price_updater__')
        self.t2.start()
        self.t3 = threading.Thread(target=self.rest_status_updater)
        self.t3.setName('rest_status_updater')
        self.t3.start()

    def __handle_bitmex_websocket__(self, **kwargs):
        try:
            self.ws = BitmexWS()
            self.ws.connect()
            self.ws_thread = self.ws.wst
            self.ws_object = self.ws.ws
            while True:
                # Something went wrong with the Websocket object
                if not self.ws:
                    self.ws = BitmexWS()
                    self.ws.connect()
                # Something went wrong with the websocket.WebSocketApp object
                if not self.ws.ws or not self.ws.ws.sock or not self.ws.ws.sock.connected:
                    # Restart the Websocket
                    try:
                        # Close previous thread
                        if self.ws_object:
                            self.ws_object.close()
                            time.sleep(2)
                        self.ws.subscribed_to_orderbook = False
                        self.ws.exit()
                    except:
                        logging.error('Exception in handleWebsocket inner loop: {}'.format(
                            traceback.format_exc()))
                    time.sleep(2)
                    self.ws.connect()
                    self.ws_thread = self.ws.wst
                    self.ws_object = self.ws.ws
                # If restart is not required sleep for 1s
                if not self.ws_restart:
                    time.sleep(1)

                # If restart is required, skip sleep and recheck
                self.ws_restart = False
        except:
            logging.error("Exception in handleWebsocket main loop: {}".format(
                traceback.format_exc()))

    def __price_updater__(self):
        """
        Function to initiate storing prices data into database.
        """
        while True:
            try:
                for exchange in self.exchanges_list:
                    temp_metadata = self.exchange_meta_data.get(exchange)
                    ask_var = temp_metadata.get('ask')
                    bid_var = temp_metadata.get('bid')
                    params = temp_metadata.get('params')

                    temp_prices = Prices()
                    r = requests.get(url=self.exchanges_list.get(
                        exchange), params=params)

                    # extracting data in json format
                    data = r.json()
                    bid_price = data.get(bid_var,-1)
                    ask_price = data.get(ask_var,-1)
                    print("response for",exchange,data)
                    setattr(temp_prices, 'bid', bid_price)
                    setattr(temp_prices, 'ask', ask_price)
                    setattr(temp_prices, 'exchange_name', exchange)
                    if (bid_price != -1 and ask_price != -1):
                        temp_prices.save()

                    print(exchange, bid_price, ask_price)
            except Exception as ex:
                print("Faced this exception ", ex)
                logging.error('Exception in price_updater: {}'.format(
                    traceback.format_exc()))
            finally:
                time.sleep(5)
    
    def rest_status_updater(self):
        """
        reads logs from stackdriver logger of given filter in descending order
         
        """
        FILTER = 'resource.type="global" AND "bitmexapicall" AND timestamp>"2018-12-06T05:59:50.061075911Z"'
        logging_client = lg.Client(project = "autospreader-201007")
        for entry in logging_client.list_entries(order_by=ASCENDING,filter_=FILTER):# API call
            if entry.payload:
                match_obj = re.search(r'bitmexapicall',entry.payload.get('message'))
                if match_obj:
                    matched = match_obj.string.split('|')
                    print('matched:{}'.format(matched))
                    try:
                        rs = RestCallStatus()
                        rs.log_date = datetime.strptime(matched[0],'%Y-%m-%d %H:%M:%S.%f ')
                        rs.path = matched[5].split(':')[1]
                        rs.verb = matched[6].split(':')[1]
                        rs.query = matched[7].split(':')[1]
                        rs.response_code = matched[8].split(':')[1]
                        rs.save()
                    except:
                        logging.error('Got exception in mysql storage : {}'.format(traceback.format_exc()))
            
            time.sleep(1)
