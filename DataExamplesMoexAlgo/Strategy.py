import backtrader as bt


class StrategyJustPrintsOHLCVAndSuperCandles(bt.Strategy):
    """
    - Displays the connection status
    - When a new bar arrives, it displays its prices/volume
    - Displays the status - historical bars or live
    """
    params = (  # Parameters of the trading system
        ('name', None),  # Name of the trading system
        ('symbols', None),  # List of traded tickers. By default, we trade all tickers
    )

    def log(self, txt, dt=None):
        """Output a date with string to the console"""
        dt = bt.num2date(self.datas[0].datetime[0]) if not dt else dt  # date of the last bar of the first ticker of the vehicle
        print(f'{dt.strftime("%d.%m.%Y %H:%M")}, {txt}')  # Output the date and time with the specified text to the console

    def __init__(self):
        """Initialization of the trading system"""
        self.isLive = False  # Historical data will come first

    def next(self):
        """Arrival of a new ticker candle"""
        # if self.p.name:  # If you have specified the name of the trading system, then we will wait for the arrival of all bars
        #     lastdatetimes = [bt.num2date(data.datetime[0]) for data in self.datas]  # Date and time of the last bar of each ticker
        #     if lastdatetimes.count(lastdatetimes[0]) != len(lastdatetimes):  # If the date and time of the last bars are not identical
        #         return  # then all the new bars haven't arrived yet. We wait further, we go out
        #     print(self.p.name)
        for data in self.datas:  # Running through all the requested tickers
            if not self.p.symbols or data._name in self.p.symbols:  # If we trade all tickers or this ticker
                ticker = data.p.dataname
                _date = bt.num2date(data.datetime[0])
                self.log(f'{ticker} - {bt.TimeFrame.Names[data.p.timeframe]} {data.p.compression} - Open={data.open[0]:.2f}, High={data.high[0]:.2f}, Low={data.low[0]:.2f}, Close={data.close[0]:.2f}, Volume={data.volume[0]:.0f}',
                         bt.num2date(data.datetime[0]))
                try:
                    if data.p.supercandles[ticker][data.p.metric_name]:
                        print("\tSuper Candle:", data.p.supercandles[ticker][data.p.metric_name][0])
                        _data = data.p.supercandles[ticker][data.p.metric_name][0]
                        _data['datetime'] = _date
                        self.supercandles[ticker][data.p.metric_name].append(_data)
                except:
                    pass

    def notify_data(self, data, status, *args, **kwargs):
        """Changing the status of incoming bars"""
        data_status = data._getstatusname(status)  # Getting the status (only when live_bars=True)
        _name = data._name if data._name else f"{self.p.name}"
        print(f'{_name} - {bt.TimeFrame.Names[data.p.timeframe]} {data.p.compression} - {data_status}')  # The status comes for each ticker separately
        self.isLive = data_status == 'LIVE'  # We switch to Live mode after switching to the first ticker
