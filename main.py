from Telegram.Telegram import Telegram
from Trades.Trade import Portfolio

CHANNEL_NAME = "Wolfx Crypto Futures VIP"

def main():
    tele = Telegram()
    port = Portfolio(1000)

    tele.connect()

    wolfix_channel =  tele.get_channel(CHANNEL_NAME, 300)

    for messages in wolfix_channel.messages[::-1]:
        port.open_trade(messages.get_data(), 0.20)

    port.display_data()

if __name__ == "__main__":
    main()