# git clone https://github.com/cia76/FinamPy
# pip install pytz grpcio google protobuf google-cloud-datastore

import datetime as dt
import backtrader as bt
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Storage AlgoPack

# пример live торговли для Finam
from FinamPy import FinamPy  # Коннект к Финам API - для выставления заявок на покупку/продажу
from FinamPy.proto.tradeapi.v1.common_pb2 import BUY_SELL_BUY, BUY_SELL_SELL
from my_config.Config_Finam import Config  # Файл конфигурации

from Config import Config as ConfigMOEX  # for authorization on the Moscow Stock Exchange


# Trading system
class RSIStrategy(bt.Strategy):
    """
    Demonstration of the live strategy - we buy 1 lot once in the market and sell it once in the market through 3 bars
    """
    params = (  # Trading System Parameters
        ('timeframe', ''),
        ('live_prefix', ''),  # prefix for submitting orders in live
        ('info_tickers', []),  # information on tickers
        ('fp_provider', ''),  # Connect to the Finam API - for placing buy/sell orders
        ('client_id', ''),  # Connect to the Finam API - for placing buy/sell orders
        ('security_board', ''),  # Connect to the Finam API - for placing buy/sell orders
    )

    def __init__(self):
        """Initialization, adding indicators for each ticker"""
        self.orders = {}  # We organize orders in the form of a directory, specifically for this strategy, one ticker is one active order
        for d in self.datas:  # Running through all the tickers
            self.orders[d._name] = None  # There is no order for ticker yet

        # creating indicators for each ticker
        self.sma1 = {}
        self.sma2 = {}
        self.rsi = {}
        for i in range(len(self.datas)):
            ticker = list(self.dnames.keys())[i]    # key name is ticker name
            self.sma1[ticker] = bt.indicators.SMA(self.datas[i], period=8)  # SMA indicator
            self.sma2[ticker] = bt.indicators.SMA(self.datas[i], period=16)  # SMA indicator
            self.rsi[ticker] = bt.indicators.RSI(self.datas[i], period=14)  # RSI indicator

        self.buy_once = {}
        self.sell_once = {}
        self.order_time = None
        self.client_id = self.p.client_id
        self.security_board = self.p.security_board

    def start(self):
        for d in self.datas:  # Running through all the tickers
            self.buy_once[d._name] = False
            self.sell_once[d._name] = False

    def next(self):
        """The arrival of a new ticker bar"""
        for data in self.datas:  # We run through all the requested bars of all tickers
            ticker = data._name
            status = data._state  # 0 - Live data, 1 - History data, 2 - None
            _interval = self.p.timeframe
            _date = bt.num2date(data.datetime[0])

            try:
                if data.p.supercandles[ticker][data.p.metric_name]:
                    print("\tSuper Candle:", data.p.supercandles[ticker][data.p.metric_name][0])
                    _data = data.p.supercandles[ticker][data.p.metric_name][0]
                    _data['datetime'] = _date
                    self.supercandles[ticker][data.p.metric_name].append(_data)
            except:
                pass

            if status in [0, 1]:
                if status: _state = "False - History data"
                else: _state = "True - Live data"

                print('{} / {} [{}] - Open: {}, High: {}, Low: {}, Close: {}, Volume: {} - Live: {}'.format(
                    bt.num2date(data.datetime[0]),
                    data._name,
                    _interval,  # ticker timeframe
                    data.open[0],
                    data.high[0],
                    data.low[0],
                    data.close[0],
                    data.volume[0],
                    _state,
                ))
                print(f'\t - {ticker} RSI : {self.rsi[ticker][0]}')

                if status != 0: continue  # if not live, then we do not enter the position!

                print(f"\t - Free balance: {self.broker.getcash()}")

                if not self.buy_once[ticker]:  # Enter long
                    free_money = self.broker.getcash()
                    print(f" - free_money: {free_money}")

                    # lot = self.p.info_tickers[ticker]['securities']['LOTSIZE']
                    # size = 1 * lot  # we will buy 1 lot - we will not check for money, we believe that they are there)
                    # price = self.format_price(ticker, data.close[0] * 0.995)  # buy at close price -0.005% - to prevent buy
                    # # price = 273.65
                    # print(f" - buy {ticker} size = {size} at price = {price}")

                    # self.orders[data._name] = self.buy(data=data, exectype=bt.Order.Limit, price=price, size=size)
                    rez = self.p.fp_provider.new_order(client_id=self.client_id, security_board=self.security_board,
                                                       security_code=ticker,
                                                       buy_sell=BUY_SELL_BUY, quantity=1,
                                                       use_credit=True,
                                                       )  # we do not specify the price to buy by market

                    self.order_time = dt.datetime.now()
                    print(f"We have put up an order to buy 1 lot {ticker}:", rez)
                    print("\t - transaction:", rez.transaction_id)
                    print("\t - time:", self.order_time)

                    # print(f"\t - The order {self.orders[data._name]} to buy {data._name}")

                    self.buy_once[ticker] = len(self)  # for a one-time purchase + write down the number of the bar

                else:  # If there is a position, because we buy immediately on the market
                    print(self.sell_once[ticker], self.buy_once[ticker], len(self), len(self) > self.buy_once[ticker] + 3)
                    if not self.sell_once[ticker]:  # if we are not selling yet
                        if self.buy_once[ticker] and len(self) > self.buy_once[ticker] + 3:  # if we have a position on the 3rd bar after the purchase
                            print("sell")
                            print(f"\t - Sell by market {data._name}...")

                            # self.orders[data._name] = self.close()  # close position by market
                            rez = self.p.fp_provider.new_order(client_id=self.client_id, security_board=self.security_board,
                                                               security_code=ticker,
                                                               buy_sell=BUY_SELL_SELL, quantity=1,
                                                               use_credit=True,
                                                               )  # we do not specify the price to buy by market
                            self.order_time = None

                            print(f"Выставили заявку на продажу 1 лота {ticker}:", rez)
                            print("\t - транзакция:", rez.transaction_id)
                            print("\t - время:", self.order_time)

                            self.sell_once[ticker] = True  # to prevent double sell

    def notify_order(self, order):
        """Changing the status of the order"""
        order_data_name = order.data._name  # The name of the ticker from the order
        print("*" * 50)
        self.log(f'Order number {order.ref} {order.info["order_number"]} {order.getstatusname()} {"Buy" if order.isbuy() else "Sell"} {order_data_name} {order.size} @ {order.price}')
        if order.status == bt.Order.Completed:  # If the order is fully executed
            if order.isbuy():  # if the order is buy
                self.log(f'Buy {order_data_name} Price: {order.executed.price:.2f}, Val: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
            else:  # if the order is sell
                self.log(f'Sell {order_data_name} Price: {order.executed.price:.2f}, Val: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.orders[order_data_name] = None  # Resetting the order
        print("*" * 50)

    def notify_trade(self, trade):
        """Changing the position status"""
        if trade.isclosed:  # If the position is closed
            self.log(f'Profit on a closed position {trade.getdataname()} Total={trade.pnl:.2f}, Comm={trade.pnlcomm:.2f}')

    def log(self, txt, dt=None):
        """Output a date string to the console"""
        dt = bt.num2date(self.datas[0].datetime[0]) if not dt else dt  # The set date or the date of the current bar
        print(f'{dt.strftime("%d.%m.%Y %H:%M")}, {txt}')  # Output the date and time with the specified text to the console

    def format_price(self, ticker, price):
        """
        The function of rounding up the price step by keeping the signs of decimal places
        print(round_custom_f(0.022636, 0.000005, 6)) --> 0.022635
        """
        step = self.p.info_tickers[ticker]['securities']['MINSTEP']  # we keep the minimum price step
        signs = self.p.info_tickers[ticker]['securities']['DECIMALS']  # we keep the number of decimal places

        val = round(price / step) * step
        return float(("{0:." + str(signs) + "f}").format(val))


def get_some_info_for_tickers(tickers, live_prefix):
    """Function for getting information on tickers"""
    info = {}
    for ticker in tickers:
        i = store.get_symbol_info(ticker)
        info[f"{live_prefix}{ticker}"] = i
    return info


if __name__ == '__main__':

    # broker Finam [FinamPy]: git clone https://github.com/cia76/FinamPy
    # broker Alor [AlorPy]: git clone https://github.com/cia76/AlorPy
    # broker Tinkoff [TinkoffPy]: git clone https://github.com/cia76/TinkoffPy
    # ANY broker who has a terminal Quik[QuikPy]: git clone https://github.com/cia76/QuikPy

    # an example for Finam
    live_prefix = ''  # prefix for submitting applications in live
    fp_provider = FinamPy(Config.AccessToken)  # Connect to the Finam API - for placing buy/sell orders
    client_id = Config.ClientIds[0]  # client id
    security_board = "TQBR"  # class tickers

    symbol = 'SBER'  # Ticker in the format <Ticker code>
    # symbol2 = 'LKOH'  # Ticker in the format <Ticker code>

    store = MoexAlgoStore()  # Storage AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Storage AlgoPack + authorization on the Moscow Stock Exchange

    cerebro = bt.Cerebro(quicknotify=True)  # Initiating the "engine" BackTrader

    # we will make a live connection to the broker directly

    # --------------------------------------------------------
    # Attention! - Now this is the Live mode of the strategy #
    # --------------------------------------------------------

    info_tickers = get_some_info_for_tickers([symbol, ], live_prefix)  # we take information about the ticker (minimum price step, number of decimal places)

    # live 1-minute bars / timeframe M1
    timeframe = "M1"
    fromdate = dt.datetime.utcnow()
    data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=1, dataname=symbol, fromdate=fromdate,
                         live_bars=True, name=f"{live_prefix}{symbol}")  # set True here - if you need to receive live bars # name - you need it to submit live applications
    # data2 = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=1, dataname=symbol2, fromdate=fromdate, live_bars=True)  # set True here - if you need to receive live bars

    cerebro.adddata(data)  # Adding data
    # cerebro.adddata(data2)  # Adding data

    cerebro.addstrategy(RSIStrategy, timeframe=timeframe, live_prefix=live_prefix, info_tickers=info_tickers,
                        fp_provider=fp_provider,
                        client_id=client_id,
                        security_board=security_board)  # Adding a trading system

    cerebro.run()  # Launching a trading system
    # cerebro.plot()  # Drawing a graph is not necessary in live mode
