import datetime as dt
import backtrader as bt
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Хранилище AlgoPack
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Торговая система

from Config import Config as ConfigMOEX  # для авторизации на Московской Бирже


def get_timeframe(tf, TimeFrame):
    """Преобразуем ТФ в параметры для добавления данных по стратегии"""
    interval = 1  # по умолчанию таймфрейм минутный
    _timeframe = TimeFrame.Minutes  # по умолчанию таймфрейм минутный

    if tf == '1m': interval = 1
    if tf == '5m': interval = 5
    if tf == '10m': interval = 10
    if tf == '1h': interval = 60
    if tf == '1D': _timeframe = TimeFrame.Days
    if tf == '1W': _timeframe = TimeFrame.Weeks
    if tf == '1M': _timeframe = TimeFrame.Months
    return _timeframe, interval


# Склейка истории тикера из файла и Binance (Rollover)
if __name__ == '__main__':  # Точка входа при запуске этого скрипта

    symbol = 'SBER'  # Тикер в формате <Код тикера>

    store = MoexAlgoStore()  # Хранилище AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Хранилище AlgoPack + авторизация на Московской Бирже

    cerebro = bt.Cerebro(quicknotify=True)

    tf = "1D"  # '1m', '10m', '1h', '1D', '1W', '1M'
    _t, _c = get_timeframe(tf, bt.TimeFrame)

    d1 = bt.feeds.GenericCSVData(  # Получаем историю из файла - в котором нет последних 5 дней
        timeframe=_t, compression=_c,  # что-бы был тот же ТФ как и у d2
        dataname=f'{symbol}_{tf}_minus_5_days.csv',  # Файл для импорта из MOEX. Создается из примера 02 - Symbol data to DF.py
        separator=',',  # Колонки разделены запятой
        dtformat='%Y-%m-%d',  # dtformat='%Y-%m-%d %H:%M:%S',  # Формат даты/времени YYYY-MM-DD HH:MM:SS
        openinterest=-1,  # Открытого интереса в файле нет
        sessionend=dt.time(0, 0),  # Для дневных данных и выше подставляется время окончания сессии. Чтобы совпадало с историей, нужно поставить закрытие на 00:00
    )

    fromdate = dt.datetime.utcnow() - dt.timedelta(days=15)  # берем данные за последние 15 дней
    d2 = store.getdata(timeframe=_t, compression=_c, dataname=symbol, fromdate=fromdate, live_bars=False)  # Исторические данные по самому меньшему временному интервалу

    cerebro.rolloverdata(d1, d2, name=symbol)  # Склеенный тикер

    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)  # Добавляем торговую систему

    cerebro.run()  # Запуск торговой системы
    cerebro.plot()  # Рисуем график !!! ЕСЛИ, никаких данных с рынка не получили, то здесь будет AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
