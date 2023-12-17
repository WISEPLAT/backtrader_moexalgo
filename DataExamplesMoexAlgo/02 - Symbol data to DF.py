import datetime as dt
import backtrader as bt
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Storage AlgoPack
import pandas as pd

from Config import Config as ConfigMOEX  # for authorization on the Moscow Stock Exchange


# Trading System
class StrategySaveOHLCVToDF(bt.Strategy):
    """Saves OHLCV in DF"""
    params = (  # Parameters of the trading system
    )

    def __init__(self):
        self.df = {}
        self.df_tf = {}

    def start(self):
        for data in self.datas:  # Running through all the requested tickers
            ticker = data._name
            self.df[ticker] = []
            self.df_tf[ticker] = store.get_interval(data._timeframe, data._compression)

    def next(self):
        """Arrival of a new ticker bar"""
        for data in self.datas:  # Running through all the requested tickers
            ticker = data._name
            _date = bt.num2date(data.datetime[0])

            try:
                if data.p.supercandles[ticker][data.p.metric_name]:
                    print("\tSuper Candle:", data.p.supercandles[ticker][data.p.metric_name][0])
                    _data = data.p.supercandles[ticker][data.p.metric_name][0]
                    _data['datetime'] = _date
                    self.supercandles[ticker][data.p.metric_name].append(_data)
            except:
                pass

            try:
                status = data._state  # 0 - Live data, 1 - History data, 2 - None
                _interval = data.interval
            except Exception as e:
                if data.resampling == 1:
                    status = 22
                    _interval = store.get_interval(data._timeframe, data._compression)
                    _interval = f"_{_interval}"
                else:
                    print("Error:", e)

            if status == 1:
                _state = "Resampled Data"
                if status == 1: _state = "False - History data"
                if status == 0: _state = "True - Live data"

                self.df[ticker].append([bt.num2date(data.datetime[0]), data.open[0], data.high[0], data.low[0], data.close[0], data.volume[0]])

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


# Historical/new bars of ticker
if __name__ == '__main__':  # Entry point when running this script
    symbol = 'SBER'  # Ticker in the format <Ticker code>

    store = MoexAlgoStore()  # Storage AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Storage AlgoPack + authorization on the Moscow Stock Exchange

    cerebro = bt.Cerebro(quicknotify=True)  # Initiating the "engine" BackTrader

    # 1. Historical D1 bars for 365 days + Chart because offline/ timeframe D1
    fromdate = dt.datetime.utcnow() - dt.timedelta(days=365)  # we take data for 365 days from the current time
    data = store.getdata(timeframe=bt.TimeFrame.Days, compression=1, dataname=symbol, fromdate=fromdate, live_bars=False)

    cerebro.adddata(data)  # Adding data
    cerebro.addstrategy(StrategySaveOHLCVToDF, )  # Adding a trading system

    results = cerebro.run()  # Launching a trading system

    print(results[0].df)

    df = pd.DataFrame(results[0].df[symbol], columns=["datetime", "open", "high", "low", "close", "volume"])
    print(df)

    tf = results[0].df_tf[symbol]

    # save to file
    df.to_csv(f"{symbol}_{tf}.csv", index=False)

    # save to file
    df[:-5].to_csv(f"{symbol}_{tf}_minus_5_days.csv", index=False)

    cerebro.plot()  # Draw a chart !!! IF we have not received any data from the market, then here it will be AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
