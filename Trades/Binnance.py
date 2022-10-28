

import json
from binance import Client
from binance.enums import HistoricalKlinesType

client =  Client("rIqI8sICGlGeIOQ3EhXoU10leXtCGAGCqNjFxzJpiI8EFD7Ev3KR2S64HJom0QCV", "MxKov8XSmDHFYDuve8qdE2KLXEUkbvJnWYMJw7Q1SmMAV6VGXusdRz7qnhP3BamH")

def get_historical_data(pair: str, klines_type: HistoricalKlinesType, interval):

    # todo: change this to UTC timpes
    print("loading data for {}, intervals: {}".format(pair, interval))

    file = client.get_historical_klines(
        symbol=pair, 
        interval=interval, 
        start_str="01/01/22 10:00",
        klines_type= klines_type, 
        limit=1000)

    with open("pairs_data\{}_{}.json".format(pair, interval), 'w') as outfile:
        json.dump(file, outfile)


