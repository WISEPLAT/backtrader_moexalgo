import datetime as dt
import backtrader as bt
import backtrader.analyzers as btanalyzers
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Storage AlgoPack

from Config import Config as ConfigMOEX  # for authorization on the Moscow Stock Exchange


# Trading system
class RSIStrategy(bt.Strategy):
    """
    Live strategy demonstration with SMA, RSI indicators
    """
    params = (  # Trading System Parameters
        ('timeframe', ''),
    )

    def __init__(self):
        """Initialization, adding indicators for each ticker"""
        self.orders = {}  # We organize orders in the form of a directory, specifically for this strategy, one ticker is one active order
        for d in self.datas:  # Running through all the tickers
            self.orders[d._name] = None  # There is no order for ticker yet

        # создcreating indicators for each ticker
        self.sma1 = {}
        self.sma2 = {}
        self.rsi = {}
        for i in range(len(self.datas)):
            ticker = list(self.dnames.keys())[i]    # key name is ticker name
            self.sma1[ticker] = bt.indicators.SMA(self.datas[i], period=8)  # SMA indicator
            self.sma2[ticker] = bt.indicators.SMA(self.datas[i], period=16)  # SMA indicator
            self.rsi[ticker] = bt.indicators.RSI(self.datas[i], period=14)  # RSI indicator

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

                print(f"\t - Free balance: {self.broker.getcash()}")

                order = self.orders[data._name]  # order of ticker
                if order and order.status == bt.Order.Submitted:  # If the order is not on the stock exchange (sent to the broker)
                    return  # then we are waiting for the order to be placed on the stock exchange, we leave, we do not continue further
                if not self.getposition(data):  # if no position
                    if order and order.status == bt.Order.Accepted:  # If the order is on the exchange (accepted by the broker)
                        print(f"\t - Cancel order {order.p.tradeid} to buy {data._name}")
                        # self.cancel(order)  # then cancel it

                    if self.rsi[ticker] < 30:  # Enter long
                        free_money = self.broker.getcash()
                        price = data.close[0]  # by price close
                        size = (free_money / price) * 0.01  # 1% from free money

                        print(f" - buy {ticker} size = {size} at price = {price}")
                        self.orders[data._name] = self.buy(data=data, exectype=bt.Order.Limit, price=price, size=size)
                        print(f"\t - The order {self.orders[data._name].p.tradeid} to buy {data._name}")

                else:  # if no position
                    if self.rsi[ticker] > 70:
                        print("sell")
                        print(f"\t - Sell by market {data._name}...")
                        self.orders[data._name] = self.close()  # An order to close a position at the market price

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


if __name__ == '__main__':

    symbol = 'SBER'  # Ticker in the format <Ticker code>
    symbol2 = 'LKOH'  # Ticker in the format <Ticker code>

    store = MoexAlgoStore()  # Storage AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Storage AlgoPack + authorization on the Moscow Stock Exchange

    cerebro = bt.Cerebro(quicknotify=True)  # Initiating the "engine" BackTrader

    cerebro.broker.setcash(2000000)  # Setting the amount of money
    cerebro.broker.setcommission(commission=0.0015)  # Set the commission to 0.15%... divide by 100 to remove %

    # # live connecting to a broker - to comment out these two lines Offline + you still need to import the broker library
    # broker = store.getbroker()
    # cerebro.setbroker(broker)

    # ------------------------------------------------------
    # Attention! - Now it's Offline for testing strategies #
    # ------------------------------------------------------

    # # Historical 10-minute bars for 10,000 hours + new live bars / M10 timeframe
    timeframe = "M10"
    fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=60*10000)
    data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=10, dataname=symbol, fromdate=fromdate, live_bars=False)  # set True here - if you need to receive live bars
    data2 = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=10, dataname=symbol2, fromdate=fromdate, live_bars=False)  # set True here - if you need to receive live bars

    cerebro.adddata(data)  # Adding data
    cerebro.adddata(data2)  # Adding data

    cerebro.addstrategy(RSIStrategy, timeframe=timeframe)  # Adding a trading system

    cerebro.addanalyzer(btanalyzers.SQN, _name='SQN')
    cerebro.addanalyzer(btanalyzers.VWR, _name='VWR', fund=True)
    cerebro.addanalyzer(btanalyzers.TimeDrawDown, _name='TDD', fund=True, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='DD', fund=True)
    cerebro.addanalyzer(btanalyzers.Returns, _name='R', fund=True, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(btanalyzers.AnnualReturn, _name='AR', )
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='SR')
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='TradeAnalyzer')

    results = cerebro.run()  # Launching a trading system
    cerebro.plot()  # Drawing a graph

    thestrat = results[0]

    print()
    print("$"*77)
    print(f"Liquidation value of the portfolio: {cerebro.broker.getvalue():.2f}")  # Liquidation value of the portfolio
    print(f"Remaining available funds: {cerebro.broker.getcash():.2f}")  # Remaining available funds
    print('Assets in the amount of: %.2f' % (cerebro.broker.getvalue() - cerebro.broker.getcash()))
    print()
    print('SQN: ', thestrat.analyzers.SQN.get_analysis())
    print('VWR: ', thestrat.analyzers.VWR.get_analysis())
    print('TDD: ', thestrat.analyzers.TDD.get_analysis())
    print('DD: ', thestrat.analyzers.DD.get_analysis())
    print('AR: ', thestrat.analyzers.AR.get_analysis())
    print('Profitability: ', thestrat.analyzers.R.get_analysis())
    print("$" * 77)
