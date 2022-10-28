from email import message
from telethon import TelegramClient

from Trades.Trade import TradeTypes

class Telegram():
    def __init__(self) -> None:
        self.phone = "0000"
        self.api_id = 00000
        self.api_hash = "########"
        self.username = "########"
        self.client = TelegramClient(self.username, self.api_id, self.api_hash)

    def connect(self):
       self.client.start(phone=self.phone)
       self.client.connect()

    def get_channel(self, channel_name, limit):
        async def gm():
            
            channel_entity = None
            async for channel in self.client.iter_dialogs():
                if channel.name == channel_name:
                    channel_entity = await self.client.get_entity(channel.id)
                    break

            if channel_entity is None:
                print("no channel with name: {}".format(channel_name))
                return

            m = []
            async for message in self.client.iter_messages(channel_entity, limit):
                m.append(Message(message.message, message.date))  

            return Channel(channel_entity, m)

        return self.client.loop.run_until_complete(gm())


class Channel():
    def __init__(self, channel_entity, messages):
        self.channel_entity = channel_entity
        self.messages = messages



class Message():
    def __init__(self, message, date) -> None:
        self.message = message.split()
        self.date = date
        self.is_trading_signal = True
        
        # if self.is_trading_signal:
        try:
            self.trading_pair = self._get_trading_pair()
            self.enter_zone = self._get_eneter_zone()
            self.take_profits = self._get_take_profits()
            self.stop_loss = self._get_stop_loss()
            self.trade_type = self._get_type_of_trade(self.stop_loss, self.take_profits[0])
        except (IndexError, ValueError) as e:
            self.is_trading_signal = False


    def get_data(self):
        if(self.is_trading_signal):
            return {
                "trading_pair": self.trading_pair,
                 "enter_zone": self.enter_zone,
                 "take_profits": self.take_profits,
                 "stop_loss":self.stop_loss,
                 "trade_type": self.trade_type,
                 "date": self.date}
        return {}

    def _get_trading_pair(self):
        return self.message[0].replace("/", "")

    def _get_trading_pair(self):
        return self.message[0].replace("/", "")

    def _get_type_of_trade(self, stop_loss, take_profit):

        if stop_loss > take_profit:
            return TradeTypes.SHORT
        return TradeTypes.LONG

    def _get_stop_loss(self):
        for index, SL in enumerate(self.message):
            if "SL" in SL:
                return float(self.message[index + 1])
        
    def _get_take_profits(self):
        take_profits = []
        for index, TP in enumerate(self.message):
            if "TP" in TP:
                take_profits.append(float(self.message[index+1]))
        return take_profits

    def _get_eneter_zone(self):
        for index, m in enumerate(self.message):
            if m in ['above:', 'below:']:
                enter_zone = self.message[index+1].split("-")[0]
                return float(enter_zone)

    def print_data(self):
        print(self.trading_pair, self.enter_zone, self.take_profits, self.stop_loss, self.trade_type)


        