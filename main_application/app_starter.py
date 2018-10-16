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

        self.exchange_meta_data = {}
        self.exchange_meta_data['cexio'] = {}
        self.exchange_meta_data['cexio']['bid'] = 'bid'
        self.exchange_meta_data['cexio']['ask'] = 'ask'
        self.exchange_meta_data['cexioEuro'] = {}
        self.exchange_meta_data['cexioEuro']['bid'] = 'bid'
        self.exchange_meta_data['cexioEuro']['ask'] = 'ask'

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
                    ask_var = self.exchange_meta_data.get(exchange)['ask']
                    bid_var = self.exchange_meta_data.get(exchange)['bid']

                    temp_prices = Prices()
                    r = requests.get(url = self.exchanges_list.get(exchange))

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
