import datetime as dt
import backtrader as bt
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Storage AlgoPack
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Trading System

from Config import Config as ConfigMOEX  # for authorization on the Moscow Stock Exchange


# Multiple time intervals for one ticker: Getting from history + live
if __name__ == '__main__':  # Entry point when running this script

    symbol = 'SBER'  # Ticker in the format <Ticker code>

    store = MoexAlgoStore()  # Storage AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Storage AlgoPack + authorization on the Moscow Stock Exchange

    cerebro = bt.Cerebro(quicknotify=True)  # Initiating the "engine" BackTrader

    # 1. Historical 5-minute bars + 10-minute bars for the last 120 hours + Chart because offline/ timeframe M5 + M10
    fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=120*60)  # we take data for the last 120 hours
    data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=5, dataname=symbol, fromdate=fromdate, live_bars=False)  # Historical data for a small time interval (should go first)
    cerebro.adddata(data)  # Добавляем данные
    data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=10, dataname=symbol, fromdate=fromdate, live_bars=False)  # Historical data for a large time interval

    # # 2. Historical 1-minute + 5-minute bars for the last 5 days + new live bars / timeframe M1 + M5
    # fromdate = dt.datetime.utcnow() - dt.timedelta(days=5)  # we take data for the last 5 days
    # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=1, dataname=symbol, fromdate=fromdate, live_bars=True)  # Historical data for a small time interval (should go first)
    # cerebro.adddata(data)  # Adding data
    # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=5, dataname=symbol, fromdate=fromdate, live_bars=True)  # Historical data for a large time interval

    # # 3. Historical 1-hour bars + 1-day bars for the week + Chart because offline/ timeframe H1 + D1
    # fromdate = dt.datetime.utcnow() - dt.timedelta(hours=24*7)  # we take data for the last 7 days
    # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=60, dataname=symbol, fromdate=fromdate, live_bars=False)  # Historical data for a small time interval (should go first)
    # cerebro.adddata(data)  # Adding data
    # data = store.getdata(timeframe=bt.TimeFrame.Days, compression=1, dataname=symbol, fromdate=fromdate, live_bars=False)  # Historical data for a large time interval

    cerebro.adddata(data)  # Adding data
    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)  # Adding a trading system

    cerebro.run()  # Launching a trading system
    cerebro.plot()  # Draw a chart !!! IF we have not received any data from the market, then here it will be AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
