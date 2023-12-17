from datetime import date, datetime, time, timedelta
import backtrader as bt
import backtrader.analyzers as btanalyzers
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Хранилище AlgoPack
from strategy_mc import StrategyJustPrintsOHLCVAndSuperCandlesMC  # Торговая система

from Config import Config as ConfigMOEX  # для авторизации на Московской Бирже


# Исторические/новые бары тикера
if __name__ == '__main__':  # Точка входа при запуске этого скрипта

    symbol = 'SBER'  # Тикер в формате <Код тикера>

    store = MoexAlgoStore()  # Хранилище AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Хранилище AlgoPack + авторизация на Московской Бирже

    cerebro = bt.Cerebro(quicknotify=True)  # Инициируем "движок" BackTrader

    cerebro.broker.setcash(2000000)  # Устанавливаем сколько денег
    cerebro.broker.setcommission(commission=0.0015)  # Установить комиссию- 0.15% ... разделите на 100, чтобы удалить %

    today = date.today()  # Сегодняшняя дата без времени
    week_ago = today - timedelta(days=7)  # неделю назад
    days_ago_3 = today - timedelta(days=3)  # три дня назад
    days_ago_10 = today - timedelta(days=10)  # десять дней назад
    days_ago_N = today - timedelta(days=30)  # N дней назад

    # Исторические 5 минутные бары + Super Candles (tradestats: history M5)
    timeframe = "M5"
    data = store.getdata(dataname=symbol, timeframe=bt.TimeFrame.Minutes, compression=5, fromdate=days_ago_N, live_bars=False,
                         super_candles=True,  # для получения свечей SuperCandles с расширенным набором характеристик
                         metric='tradestats',  # + необходимо указать тип получаемых метрик
                         )

    cerebro.adddata(data)  # Добавляем данные
    cerebro.addstrategy(StrategyJustPrintsOHLCVAndSuperCandlesMC, timeframe=timeframe)  # Добавляем торговую систему

    cerebro.addanalyzer(btanalyzers.SQN, _name='SQN')
    cerebro.addanalyzer(btanalyzers.VWR, _name='VWR', fund=True)
    cerebro.addanalyzer(btanalyzers.TimeDrawDown, _name='TDD', fund=True, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='DD', fund=True)
    cerebro.addanalyzer(btanalyzers.Returns, _name='R', fund=True, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(btanalyzers.AnnualReturn, _name='AR', )
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='SR')
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='TradeAnalyzer')

    results = cerebro.run()  # Запуск торговой системы
    # cerebro.plot(style='candle')  # Рисуем график !!! ЕСЛИ, никаких данных с рынка не получили, то здесь будет AttributeError: 'Plot_OldSync' object has no attribute 'mpyplot'

    thestrat = results[0]

    print()
    print("$"*77)
    print(f"Ликвидационная стоимость портфеля: {cerebro.broker.getvalue():.2f}")  # Ликвидационная стоимость портфеля
    print(f"Остаток свободных средств: {cerebro.broker.getcash():.2f}")  # Остаток свободных средств
    print('Активов на сумму: %.2f' % (cerebro.broker.getvalue() - cerebro.broker.getcash()))
    print()
    print('SQN: ', thestrat.analyzers.SQN.get_analysis())
    print('VWR: ', thestrat.analyzers.VWR.get_analysis())
    print('TDD: ', thestrat.analyzers.TDD.get_analysis())
    print('DD: ', thestrat.analyzers.DD.get_analysis())
    print('AR: ', thestrat.analyzers.AR.get_analysis())
    print('Доходность: ', thestrat.analyzers.R.get_analysis())
    print("$" * 77)
