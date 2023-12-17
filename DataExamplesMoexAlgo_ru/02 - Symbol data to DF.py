import datetime as dt
import backtrader as bt
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Хранилище AlgoPack
import pandas as pd

from Config import Config as ConfigMOEX  # для авторизации на Московской Бирже


# Торговая система
class StrategySaveOHLCVToDF(bt.Strategy):
    """Сохраняет OHLCV в DF"""
    params = (  # Параметры торговой системы
    )

    def __init__(self):
        self.df = {}
        self.df_tf = {}

    def start(self):
        for data in self.datas:  # Пробегаемся по всем запрошенным тикерам
            ticker = data._name
            self.df[ticker] = []
            self.df_tf[ticker] = store.get_interval(data._timeframe, data._compression)

    def next(self):
        """Приход нового бара тикера"""
        for data in self.datas:  # Пробегаемся по всем запрошенным тикерам
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
                    _interval,  # таймфрейм тикера
                    data.open[0],
                    data.high[0],
                    data.low[0],
                    data.close[0],
                    data.volume[0],
                    _state,
                ))


# Исторические/новые бары тикера
if __name__ == '__main__':  # Точка входа при запуске этого скрипта
    symbol = 'SBER'  # Тикер в формате <Код тикера>

    store = MoexAlgoStore()  # Хранилище AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Хранилище AlgoPack + авторизация на Московской Бирже

    cerebro = bt.Cerebro(quicknotify=True)

    # 1. Исторические D1 бары за 365 дней + График т.к. оффлайн/ таймфрейм D1
    fromdate = dt.datetime.utcnow() - dt.timedelta(days=365)  # берем данные за 365 дней от текущего времени
    data = store.getdata(timeframe=bt.TimeFrame.Days, compression=1, dataname=symbol, fromdate=fromdate, live_bars=False)

    cerebro.adddata(data)  # Добавляем данные
    cerebro.addstrategy(StrategySaveOHLCVToDF, )  # Добавляем торговую систему

    results = cerebro.run()  # Запуск торговой системы

    print(results[0].df)

    df = pd.DataFrame(results[0].df[symbol], columns=["datetime", "open", "high", "low", "close", "volume"])
    print(df)

    tf = results[0].df_tf[symbol]

    # save to file
    df.to_csv(f"{symbol}_{tf}.csv", index=False)

    # save to file
    df[:-5].to_csv(f"{symbol}_{tf}_minus_5_days.csv", index=False)

    cerebro.plot()  # Рисуем график !!! ЕСЛИ, никаких данных с рынка не получили, то здесь будет AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
