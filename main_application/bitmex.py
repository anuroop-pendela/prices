import websocket
import time
import datetime
import hmac
import hashlib
import json
import threading
import ssl
import sys
import decimal
import traceback
import pickle
from urllib.parse import urlparse, urlunparse
import logging

from main_application.models import Prices

class BitmexWS(object):

    def __init__(self):
        self.exchange = 'bitmex'
        self.__reset()
        self.message_counter = 0
        self.base_url = "https://www.bitmex.com/api/v1/"
        self.data = {}
        self.keys = {}
        self.exited = False
        self._error = None
        self.ws = None
        self.wst = None
        self.ticker_ask = -1
        self.ticker_bid = -1
        self.ticker_last = 0

    def connect(self, endpoint="https://www.bitmex.com/api/v1/", symbol="XBTUSD"):
        '''Connect to the websocket and initialize data stores.'''
        logging.info("Bitmex_Exchange | Connecting WebSocket")
        self.symbol = symbol

        # We can subscribe right in the connection querystring, so let's build that.
        # Subscribe to all pertinent endpoints
        #subscriptions = [sub + ':' + symbol for sub in ["quote", "trade"]]
        subscriptions = [sub + ':' + symbol
                         for sub in ["quote"]]  # "orderBookL2"

        logging.info('Bitmex_Exchange | subscriptions : %s' %
                     (subscriptions))

        # Get WS URL and connect.
        urlParts = list(urlparse(endpoint))
        urlParts[0] = urlParts[0].replace('http', 'ws')
        urlParts[2] = "/realtime?subscribe=" + ",".join(subscriptions)
        wsURL = urlunparse(urlParts)
        logging.info("Bitmex_Exchange | Connecting to %s" % (wsURL))
        self.__connect(wsURL)

    #
    # Data methods
    #

    def error(self, err):
        self._error = err
        logging.error("Bitmex_Exchange | Error: %s" % (err))
        self.exit()

    def exit(self):
        self.exited = True
        logging.error(
            'Bitmex_Exchange | web-socket exit method | the prices here are ask_price : {} | bid price :{} '.format(self.ticker_ask, self.ticker_bid))
        self.ws.close()

    #
    # Private methods
    #

    def __connect(self, wsURL):
        '''Connect to the websocket in a thread.'''
        self.ws = websocket.WebSocketApp(
            wsURL,
            on_message=self.__on_message,
            on_close=self.__on_close,
            on_open=self.__on_open,
            on_error=self.__on_error,
        )

        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.setName('bitmex_ws.run_forever')
        self.wst.start()
        # Wait for connect before continuing
        conn_timeout = 5
        try:
            while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout and not self._error:
                time.sleep(1)
                conn_timeout -= 1
            if not conn_timeout or self._error:
                logging.error(
                    "Bitmex_Exchange | Couldn't connect to WS! Exiting System. | Error : %s" % (self._error))

                self.exit()

        except:

            logging.error(
                "Bitmex_Exchange | Error in connection: {}" .format(traceback.format_exc()))

    def __on_message(self, ws, message):
        '''Handler for parsing WS messages.'''
        message = json.loads(message)
        # log message
        logging.info(
            "Bitmex_Exchange | json.dumps(message) = %s" % (json.dumps(message)))
        self.message_counter += 1
        table = message['table'] if 'table' in message else None
        action = message['action'] if 'action' in message else None

        try:
            if 'subscribe' in message:
                if message['success']:
                    logging.info(
                        "Bitmex_Exchange | Subscribed to %s." % (message['subscribe']))
                else:

                    self.error(
                        "Bitmex_Exchange | Unable to subscribe to %s. Error: \"%s\" Please check and restart."
                        % (message['request']['args'][0], message['error']))

            elif 'status' in message:
                if message['status'] == 400:

                    self.error(message['error'])
                if message['status'] == 401:

                    self.error(
                        "Bitmex_Exchange | API Key incorrect, please check and restart.")
            elif action:

                if table not in self.data:
                    self.data[table] = []

                if table not in self.keys:
                    self.keys[table] = []

                # There are four possible actions from the WS:
                # 'partial' - full table image
                # 'insert'  - new row
                # 'update'  - update row
                # 'delete'  - delete row
                if action == 'partial':
                    #logging.info("Bitmex_Exchange | %s: partial" %(table))
                    self.data[table] += message['data']
                    # Keys are communicated on partials to let you know how to uniquely identify
                    # an item. We use it for updates.
                    self.keys[table] = message['keys']
                elif action == 'insert':
                    # logging.info('Bitmex_Exchange | %s: inserting %s'
                    #                  % ( table,
                    #                     message['data']))
                    self.data[table] += message['data']

                    # Limit the max length of the table to avoid excessive memory usage.
                    # Don't trim orders because we'll lose valuable state if we do.

                elif action == 'update':
                    #logging.info('Bitmex_Exchange | %s: updating %s'% ( table,message['data']))
                    # Locate the item in the collection and update it.
                    for updateData in message['data']:
                        item = findItemByKeys(self.keys[table],
                                              self.data[table], updateData)
                        if not item:
                            continue  # No item found to update. Could happen before push

                        # Log executions

                        # Update this item.
                        item.update(updateData)

                elif action == 'delete':
                    #logging.info('Bitmex_Exchange | %s: deleting %s'% (table,message['data']))
                    # Locate the item in the collection and remove it.
                    for deleteData in message['data']:
                        item = findItemByKeys(self.keys[table],
                                              self.data[table], deleteData)
                        try:
                            self.data[table].remove(item)

                        except:

                            logging.error('Bitmex_Exchange | exception on %s 2' % (
                                self.data[table].remove(item)))
                else:
                    raise Exception(
                        "Bitmex_Exchange | Unknown action: %s" % (action))

                # do at this indent level
                #

                data_dict = self.data
                if table == 'quote':
                    if 'askPrice' in data_dict['quote'][-1]:
                        if abs(data_dict['quote'][-1]['askPrice'] - self.ticker_last) >= 0.1:
                            #print('data_dict: ', data_dict)
                            self.ticker_last = data_dict['quote'][-1]['askPrice']
                            self.ticker_bid = data_dict['quote'][-1]['bidPrice']
                            self.ticker_ask = data_dict['quote'][-1]['askPrice']

                            temp_prices = Prices()
                            setattr(temp_prices, 'bid', self.ticker_bid)
                            setattr(temp_prices, 'ask', self.ticker_ask)
                            setattr(temp_prices, 'exchange_name', 'bitmex')
                            print("bitmex",self.ticker_bid,self.ticker_ask)
                            temp_prices.save()


                            logging.info("Bitmex_Exchange | websocket updated ask_price: {} and bid_price: {}" .format(
                                self.ticker_ask, self.ticker_bid))
                    else:
                        logging.warning('Bitmex_Exchange | No ask price')
        except:

            logging.error('Bitmex_Exchange | Exception : %s' %
                          (traceback.format_exc()))

    def __on_open(self, ws):
        logging.info("Bitmex_Exchange | Websocket Opened.")

    def __on_close(self, ws):
        logging.error('Bitmex_Exchange | Websocket Closed')
        self.exit()

    def __on_error(self, ws, error):
        if not self.exited:
            self.error(error)

    def __reset(self):
        self.data = {}
        self.keys = {}
        self.exited = False
        self._error = None

    def get_ticker(self):
        try:
            response = self.data['quote'][-1]
            self.ticker_ask = response.get('askPrice')
            self.ticker_bid = response.get('bidPrice')
        except:
            logging.error('Exception in get_ticker: {}'.format(
                traceback.format_exc()))


def findItemByKeys(keys, table, matchData):
    for item in table:
        matched = True
        for key in keys:
            if item[key] != matchData[key]:
                matched = False
        if matched:
            return item


if __name__ == "__main__":

    b = BitmexWS()
