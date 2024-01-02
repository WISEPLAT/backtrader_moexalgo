from datetime import date, datetime, time, timedelta
from backtrader import Cerebro, TimeFrame
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Storage AlgoPack
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Trading System

from Config import Config as ConfigMOEX  # for authorization on the Moscow Stock Exchange


# Historical/new bars of ticker
if __name__ == '__main__':  # Entry point when running this script

    symbol = 'SBER'  # Ticker in the format <Ticker code>

    store = MoexAlgoStore()  # Storage AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Storage AlgoPack + authorization on the Moscow Stock Exchange

    cerebro = Cerebro(stdstats=False)  # Initiating the "engine" BackTrader

    today = date.today()  # Today's date without time
    week_ago = today - timedelta(days=7)  # a week ago
    days_ago_5 = today - timedelta(days=5)  # three days ago
    days_ago_10 = today - timedelta(days=10)  # ten days ago
    days_ago_N = today - timedelta(days=30)  # N days ago

    # 1. All historical daytime bars for the week
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Days, fromdate=week_ago)

    # 2. Historical hour bars with doji of 4 prices (four_price_doji) for the current year
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=60, fromdate=datetime(today.year, 1, 1), todate=datetime(today.year, 12, 31), four_price_doji=True)

    # 3. Historical 30-minute bars from a given date a week ago to the last bar (resample from M10)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=30, fromdate=week_ago)

    # 4. Historical 5-minute bars of the first hour of the current session without the first 5 minutes (resample из M5)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=5, fromdate=datetime(today.year, today.month, today.day, 10, 5), todate=datetime(today.year, today.month, today.day, 10, 55))

    # 5. Historical and new 1-minute bars from the beginning of today's session (history + live M1)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=1, fromdate=today, live_bars=True)

    # 7. Historical and new 10-minute bars (history + live M10)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=10, fromdate=days_ago_5, live_bars=True)

    # 8. Historical and new 5-minute bars (history + live M5 resample from M1)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5, live_bars=True)  # An example with TF M5, which is not in the data, it is obtained from '1m' (resample)

    # 9. Historical 5-minute bars + Super Candles (tradestats: history M5)
    data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5, live_bars=False,
                         super_candles=True,  # to obtain SuperCandles with an extended set of characteristics
                         metric='tradestats',  # + you must specify the type of metrics you receive
                         )

    # 10. Historical 10-minute bars + Super Candles (tradestats: history + live M10 resample from M5)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=10, fromdate=days_ago_5, live_bars=True,
    #                      super_candles=True,  # to obtain SuperCandles with an extended set of characteristics
    #                      metric='tradestats',  # + you must specify the type of metrics you receive
    #                      )

    # 11. Historical 5-minute bars + Super Candles (orderstats: history + live M5)  // Without OHLCV == 0.0 data, because this data can be obtained by the 2nd stream
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5,
    #                      live_bars=True,
    #                      super_candles=True,  # to obtain SuperCandles with an extended set of characteristics
    #                      metric='orderstats',  # + you must specify the type of metrics you receive
    #                      )

    # 12. Historical 5-minute bars + Super Candles (obstats: history + live M5)  // Without OHLCV == 0.0 data, because this data can be obtained by the 2nd stream
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5,
    #                      live_bars=True,
    #                      super_candles=True,  # to obtain SuperCandles with an extended set of characteristics
    #                      metric='obstats',  # + you must specify the type of metrics you receive
    #                      )

    cerebro.adddata(data)  # Adding data
    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)   # Adding a trading system
    cerebro.run()  # Launching a trading system
    cerebro.plot(style='candle')  # Draw a chart !!! IF we have not received any data from the market, then here it will be AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
