import datetime as dt
import backtrader as bt
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Хранилище AlgoPack
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Торговая система

from Config import Config as ConfigMOEX  # для авторизации на Московской Бирже


# Несколько тикеров для нескольких торговых систем по одному временнОму интервалу history + live
if __name__ == '__main__':  # Точка входа при запуске этого скрипта
    
    symbols = ('SBER', 'AFLT')  # тикеры, по которым будем получать данные

    store = MoexAlgoStore()  # Хранилище AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Хранилище AlgoPack + авторизация на Московской Бирже

    cerebro = bt.Cerebro(quicknotify=True)

    for _symbol in symbols:  # Пробегаемся по всем тикерам

        # 1. Исторические 5-минутные бары за последние 120 часов + График т.к. оффлайн/ таймфрейм M5
        fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=120*60)  # берем данные за последние 120 часов
        data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=5, dataname=_symbol, fromdate=fromdate, live_bars=False)

        # 2. Исторические 1-минутные бары за прошлый час + новые live бары / таймфрейм M1
        # fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=60)  # берем данные за последний 1 час
        # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=1, dataname=_symbol, fromdate=fromdate, live_bars=True)

        # 3. Исторические 1-часовые бары за неделю + График т.к. оффлайн/ таймфрейм H1
        # fromdate = dt.datetime.utcnow() - dt.timedelta(hours=24*7)  # берем данные за последнюю неделю от текущего времени
        # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=60, dataname=_symbol, fromdate=fromdate, live_bars=False)

        cerebro.adddata(data)  # Добавляем данные

    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)  # Добавляем торговую систему

    cerebro.run()  # Запуск торговой системы
    cerebro.plot()  # Рисуем график !!! ЕСЛИ, никаких данных с рынка не получили, то здесь будет AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
