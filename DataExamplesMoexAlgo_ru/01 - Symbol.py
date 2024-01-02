from datetime import date, datetime, time, timedelta
from backtrader import Cerebro, TimeFrame
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Хранилище AlgoPack
from Strategy import StrategyJustPrintsOHLCVAndSuperCandles  # Торговая система

from Config import Config as ConfigMOEX  # для авторизации на Московской Бирже


# Исторические/новые бары тикера
if __name__ == '__main__':  # Точка входа при запуске этого скрипта

    symbol = 'SBER'  # Тикер в формате <Код тикера>

    store = MoexAlgoStore()  # Хранилище AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Хранилище AlgoPack + авторизация на Московской Бирже

    cerebro = Cerebro(stdstats=False)  # Инициируем "движок" BackTrader. Стандартная статистика сделок и кривой доходности не нужна

    today = date.today()  # Сегодняшняя дата без времени
    week_ago = today - timedelta(days=7)  # неделю назад
    days_ago_5 = today - timedelta(days=5)  # три дня назад
    days_ago_10 = today - timedelta(days=10)  # десять дней назад
    days_ago_N = today - timedelta(days=30)  # N дней назад

    # 1. Все исторические дневные бары за неделю
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Days, fromdate=week_ago)

    # 2. Исторические часовые бары с дожи 4-х цен (four_price_doji) за текущий год
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=60, fromdate=datetime(today.year, 1, 1), todate=datetime(today.year, 12, 31), four_price_doji=True)

    # 3. Исторические 30-и минутные бары с заданной даты неделю назад до последнего бара (resample из M10)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=30, fromdate=week_ago)

    # 4. Исторические 5-и минутные бары первого часа текущей сессиИ без первой 5-и минутки (resample из M5)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=5, fromdate=datetime(today.year, today.month, today.day, 10, 5), todate=datetime(today.year, today.month, today.day, 10, 55))

    # 5. Исторические и новые минутные бары с начала сегодняшней сессии (history + live M1)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=1, fromdate=today, live_bars=True)

    # 7. Исторические и новые 10 минутные бары (history + live M10)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=10, fromdate=days_ago_5, live_bars=True)

    # 8. Исторические и новые 5 минутные бары (history + live M5 resample from M1)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5, live_bars=True)  # Пример с ТФ M5, которого нет в данных, он получается из '1m' (resample)

    # 9. Исторические 5 минутные бары + Super Candles (tradestats: history M5)
    data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5, live_bars=True,
                         super_candles=True,  # для получения свечей SuperCandles с расширенным набором характеристик
                         metric='tradestats',  # + необходимо указать тип получаемых метрик
                         )

    # 10. Исторические 10 минутные бары + Super Candles (tradestats: history + live M10 resample from M5)
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=10, fromdate=days_ago_5, live_bars=True,
    #                      super_candles=True,  # для получения свечей SuperCandles с расширенным набором характеристик
    #                      metric='tradestats',  # + необходимо указать тип получаемых метрик
    #                      )

    # 11. Исторические 5 минутные бары + Super Candles (orderstats: history + live M5)  // Без данных OHLCV == 0.0, т.к. эти данные можно получить 2-м потоком
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5,
    #                      live_bars=True,
    #                      super_candles=True,  # для получения свечей SuperCandles с расширенным набором характеристик
    #                      metric='orderstats',  # + необходимо указать тип получаемых метрик
    #                      )

    # 12. Исторические 5 минутные бары + Super Candles (obstats: history + live M5)  // Без данных OHLCV == 0.0, т.к. эти данные можно получить 2-м потоком
    # data = store.getdata(dataname=symbol, timeframe=TimeFrame.Minutes, compression=5, fromdate=days_ago_5,
    #                      live_bars=True,
    #                      super_candles=True,  # для получения свечей SuperCandles с расширенным набором характеристик
    #                      metric='obstats',  # + необходимо указать тип получаемых метрик
    #                      )

    cerebro.adddata(data)  # Добавляем данные
    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandles)  # Добавляем торговую систему
    cerebro.run()  # Запуск торговой системы
    cerebro.plot(style='candle')  # Рисуем график !!! ЕСЛИ, никаких данных с рынка не получили, то здесь будет AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'
