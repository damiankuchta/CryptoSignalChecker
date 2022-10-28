from array import array
import json
from multiprocessing.dummy import Array
import datetime
from re import L, S
from telnetlib import SE
import os
from enum import Enum
from turtle import bgcolor


from Trades.Binnance import get_historical_data
from binance.enums import KLINE_INTERVAL_1MINUTE, HistoricalKlinesType

class Bgcolor(Enum):
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TradeTypes(Enum):
    LONG = "LONG",
    SHORT = "SHORT"


class Portfolio():
    def __init__(self, total_capital) -> None:
        self.total_capital = total_capital
        self.percentage_balance = 0
        self.trades = []
        self.succesfull_trades = 0
        self.lost_trades = 0
        self.pending_value = 0

    def open_trade(self, data, capital):
        
        # no data to fill
        if data == {}:
            return

        # capital can be either percentage or a full value
        cap = abs(capital)
        if cap < 1:
            cap = self.total_capital * cap
    
        tr = Trade(
            pair=data['trading_pair'],
            enter_price=data['enter_zone'],
            tp=data['take_profits'],
            sl=['v', data['stop_loss']],
            datetime_order=data['date'],
            trade_type=data['trade_type'],
            capital = cap,
            leavarage=10
        )


        tr.check_trade()

        tr.display_trade() 

        if(tr.trade_net_value < cap):
            self.lost_trades += 1
        else:
            self.succesfull_trades += 1
        
        if(not tr.sl_reached or not len(tr.TP) == tr.tp_reached):
             self.pending_value += tr.STARTING_CAPITAL

        self.total_capital -= cap

        self.total_capital += tr.trade_net_value
        self.percentage_balance += tr.trade_net_procentage

    def display_data(self):
        print("Portfolio: {}, Percentage: {}, WINS: {}, LOSTS: {} In pending: {}".format(self.total_capital, self.percentage_balance, self.succesfull_trades, self.lost_trades, self.pending_value))


class Trade():
    def __init__(self, 
        pair: str, 
        capital: float,
        enter_price: float, 
        tp: array, 
        sl: float, 
        datetime_order: datetime.datetime, 
        trade_type: TradeTypes, 
        leavarage: int = 10, 
        timeout: int = 1,
        ) -> None:
        
        self.TRADE_TYPE = trade_type
        self.ENTER_PRICE: float = enter_price
        self.TP: array = tp
        self.SL: float = self._calc_stop_loss(sl, leavarage, trade_type) 
        self.ORDER_TIMESTAMP: str = datetime_order.timestamp() * 1000
        self.TIMEOUT: int = timeout*3600000*24
        self.LEVARAGE: int = leavarage
        self.PAIR: str = pair
        self.DATA = []
        self.STARTING_CAPITAL: float = capital

        self.trade_caopital: float = capital
        self.trade_net_value: float = 0
        self.trade_net_procentage: float = 0
        self.tp_reached = 0
        self.sl_reached = False
        self.trade_entered = False
        self.closed_trade = False
        self.close_trade_timestamp = 0
        self.trade_duration = 0
        self.curret_percentage = 0

    def display_trade(self):
        # print( + "stop loss, loss: {}, date: {}".format(int(loss), datetime.datetime.fromtimestamp(TIMESTAMP/1000) ) + '\033[0m')
        # print( + "take profit {}, profit: {}, date: {}".format(self.tp_reached, int(profit), datetime.datetime.fromtimestamp(TIMESTAMP/1000) ) + '\033[0m')

        if(self.closed_trade and not self.trade_entered):
            print("trade expired")
            return

        if self.sl_reached :
            color = Bgcolor.FAIL.value
        elif len(self.TP) == self.tp_reached:
            color = Bgcolor.OKGREEN.value
        else:
            color = Bgcolor.WARNING.value

        print(color + "Start: {}, End: {}, percentage: {}, pair: {}, TP hit: {} Duration: {} TradeType: {} TIMESTAMP: {}".format(self.STARTING_CAPITAL, 
        int(self.trade_net_value), 
        int(self.trade_net_procentage), 
        self.PAIR,
        self.tp_reached,
        self.trade_duration,
        self.TRADE_TYPE.value,
        self.ORDER_TIMESTAMP,
        ) + Bgcolor.HEADER.value)
        

    def _calc_stop_loss(self, sl, lavarage, trade_type):
        return sl[1]



    def check_trade(self):
        self._get_data()
        print("check for {}".format(self.PAIR))
        for candle in self.DATA:
            
            TIMESTAMP = float(candle[0])
            HIGH = float(candle[2])
            LOW = float(candle[3])

            if TIMESTAMP < self.ORDER_TIMESTAMP:
                continue

            if self.trade_entered is not True:
                if self._is_trade_expired(TIMESTAMP):
                    self._exit_trade(TIMESTAMP)
                    
                    # print(TIMESTAMP, self.ORDER_TIMESTAMP)
                    break
                self.trade_entered = self._check_enter_conditions(HIGH, LOW)
            else:
            
                if self._is_trade_closed():
                    self._exit_trade(TIMESTAMP)
                    break
                elif self._is_stop_loss_reached(HIGH, LOW):
                    self._stop_loss()
                elif self._is_take_profit_reached(HIGH, LOW):
                    self._take_profit()

    def _is_take_profit_reached(self, high: float, low: float):
        return (self.TRADE_TYPE == TradeTypes.LONG and high >= self.TP[self.tp_reached]) or (self.TRADE_TYPE == TradeTypes.SHORT and low <= self.TP[self.tp_reached])

    def _is_stop_loss_reached(self, high:float, low: float):
        return (self.TRADE_TYPE == TradeTypes.LONG and low <= self.SL) or (self.TRADE_TYPE == TradeTypes.SHORT and high >= self.SL)

    def _is_trade_closed(self):
        return self.trade_entered and (self.sl_reached or self.tp_reached == len(self.TP))

    def _check_enter_conditions(self, HIGH, LOW):
        if(HIGH >= self.ENTER_PRICE and self.TRADE_TYPE is TradeTypes.LONG) or \
        (LOW <= self.ENTER_PRICE and self.TRADE_TYPE is TradeTypes.SHORT):
            return True
        return False

    def _is_trade_expired(self, TIMESTAMP):
        return (TIMESTAMP > self.ORDER_TIMESTAMP + self.TIMEOUT) and not self.trade_entered

    def _exit_trade(self, TIMESTAMP):
        self.close_trade_timestamp = TIMESTAMP
        self.closed_trade = True
        self.trade_net_value += self.trade_caopital
        self.trade_duration = int((self.close_trade_timestamp - self.ORDER_TIMESTAMP)/3600000)

    def _stop_loss(self):
        percent_decrease = (self.ENTER_PRICE - self.SL)/self.ENTER_PRICE
        percent_decrease_lavagared = abs(percent_decrease * self.LEVARAGE)



        loss = abs(self.trade_caopital * percent_decrease_lavagared)*-1

        self.trade_net_value += self.trade_caopital + loss
        self.trade_net_procentage = -(self.STARTING_CAPITAL - self.trade_net_value)/self.STARTING_CAPITAL*100
        self.trade_caopital = 0

        self.sl_reached = True

        
    def _take_profit(self):
        percent_increase = (self.TP[self.tp_reached] - self.ENTER_PRICE)/self.ENTER_PRICE
        percent_increase_lavagared = percent_increase * self.LEVARAGE

        used_capital_for_tp = self.STARTING_CAPITAL * (1/len(self.TP))

        profit = abs(used_capital_for_tp * percent_increase_lavagared)

        self.trade_net_procentage += abs((percent_increase_lavagared*100)/len(self.TP))
        self.trade_caopital -= used_capital_for_tp
        self.trade_net_value +=  profit + used_capital_for_tp
        self.tp_reached += 1

        


    def _get_data(self):

            INTETRVAL = KLINE_INTERVAL_1MINUTE
            KLINES_TYPE = HistoricalKlinesType.FUTURES
            FILE_NAME = "pairs_data\{}_{}.json".format(self.PAIR, INTETRVAL)

            if not os.path.isfile(FILE_NAME):
                print("File for {}_{} does not exist ".format(self.PAIR, INTETRVAL))
                get_historical_data(self.PAIR, KLINES_TYPE, INTETRVAL)
            with open(FILE_NAME, "r") as data:
                self.DATA = json.load(data)


        