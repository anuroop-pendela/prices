import threading
import requests
import time
from main_application.models import Prices
class priceUpdater:

    def __init__(self):
        """
        Constructor to do noting
        """
        print("Price updater Initialized")
        self.exchanges_list={}

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
        self.exchange_meta_data['bitflyer']['params'] = {'product_code':'BTC_JPY'}

        # Metadata for bitflyerFx
        self.exchange_meta_data['bitflyerFx'] = {}
        self.exchange_meta_data['bitflyerFx']['bid'] = 'best_bid'
        self.exchange_meta_data['bitflyerFx']['ask'] = 'best_ask'
        self.exchange_meta_data['bitflyerFx']['params'] = {'product_code':'FX_BTC_JPY'}



        self.__price_updater__()
        # Initiate a thread to make api reuest and store the data into
        # self.t1 = threading.Thread(target=self.__price_updater__)
        # self.t1.setName('startQueuedStrategies')
        # self.t1.start()
        pass


    def  __price_updater__(self):
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
                    r = requests.get(url = self.exchanges_list.get(exchange),params = params)

                    # extracting data in json format
                    data = r.json()
                    bid_price = data.get(bid_var)
                    ask_price = data.get(ask_var)

                    setattr(temp_prices,'bid',bid_price)
                    setattr(temp_prices,'ask',ask_price)
                    setattr(temp_prices,'exchange_name',exchange)
                    temp_prices.save()
                    print(exchange,bid_price,ask_price)
            except Exception as ex:
                print("Faced this exception ",ex)
            finally:
                time.sleep(5)
