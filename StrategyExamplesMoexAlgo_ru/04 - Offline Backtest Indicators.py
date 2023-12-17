import datetime as dt
import backtrader as bt
import backtrader.analyzers as btanalyzers
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Хранилище AlgoPack

from Config import Config as ConfigMOEX  # для авторизации на Московской Бирже


class UnderOver(bt.Indicator):
    lines = ('underover',)
    params = dict(data2=20)
    plotinfo = dict(plot=True)

    def __init__(self):
        self.l.underover = self.data < self.p.data2             # данные под data2 == 1


# Торговая система
class RSIStrategy(bt.Strategy):
    """
    Демонстрация live стратегии с индикаторами SMA, RSI
    """
    params = (  # Параметры торговой системы
        ('timeframe', ''),
    )

    def __init__(self):
        """Инициализация, добавление индикаторов для каждого тикера"""
        self.orders = {}  # Организовываем заявки в виде справочника, конкретно для этой стратегии один тикер - одна активная заявка
        for d in self.datas:  # Пробегаемся по всем тикерам
            self.orders[d._name] = None  # Заявки по тикеру пока нет

        # создаем индикаторы для каждого тикера
        self.sma1 = {}
        self.sma2 = {}
        self.sma3 = {}
        self.crossover = {}
        self.underover_sma = {}
        self.rsi = {}
        self.underover_rsi = {}
        for i in range(len(self.datas)):
            ticker = list(self.dnames.keys())[i]    # key name is ticker name
            self.sma1[ticker] = bt.indicators.SMA(self.datas[i], period=9)  # SMA1 indicator
            self.sma2[ticker] = bt.indicators.SMA(self.datas[i], period=30)  # SMA2 indicator
            self.sma3[ticker] = bt.indicators.SMA(self.datas[i], period=60)  # SMA3 indicator

            # signal 1 - пересечение быстрой SMA снизу вверх медленной SMA
            self.crossover[ticker] = bt.ind.CrossOver(self.sma1[ticker], self.sma2[ticker])  # crossover SMA1 and SMA2

            # signal 2 - когда SMA3 находится ниже SMA2
            self.underover_sma[ticker] = UnderOver(self.sma3[ticker].lines.sma, data2=self.sma2[ticker].lines.sma)

            self.rsi[ticker] = bt.indicators.RSI(self.datas[i], period=20)  # RSI indicator

            # signal 3 - когда RSI находится ниже 30
            self.underover_rsi[ticker] = UnderOver(self.rsi[ticker].lines.rsi, data2=30)

    def next(self):
        """Приход нового бара тикера"""
        for data in self.datas:  # Пробегаемся по всем запрошенным барам всех тикеров
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
                    _interval,  # таймфрейм тикера
                    data.open[0],
                    data.high[0],
                    data.low[0],
                    data.close[0],
                    data.volume[0],
                    _state,
                ))

                try:
                    if data.p.supercandles[0]:
                        print("\tSuper Candle:", data.p.supercandles[0])
                except:
                    pass

                print(f'\t - RSI =', self.rsi[ticker][0])
                print(f"\t - crossover =", self.crossover[ticker].lines.crossover[0])

                print(f"\t - Free balance: {self.broker.getcash()}")

                # сигналы на вход
                signal1 = self.crossover[ticker].lines.crossover[0]  # signal 1 - пересечение быстрой SMA снизу вверх медленной SMA
                signal2 = self.underover_sma[ticker]  # signal 2 - когда SMA3 находится ниже SMA2

                # сигналы на выход
                signal3 = self.underover_rsi[ticker]  # signal 3 - когда RSI находится ниже 30

                if not self.getposition(data):  # Если позиции нет
                    if signal1 == 1:
                        if signal2 == 1:
                            # buy
                            free_money = self.broker.getcash()
                            price = data.close[0]  # по цене закрытия
                            size = (free_money / price) * 0.25  # 25% от доступных средств
                            print("-"*50)
                            print(f"\t - buy {ticker} size = {size} at price = {price}")
                            self.orders[data._name] = self.buy(data=data, exectype=bt.Order.Limit, price=price, size=size)
                            print(f"\t - Выставлена заявка {self.orders[data._name].p.tradeid} на покупку {data._name}")
                            print("-" * 50)

                else:  # Если позиция есть
                    if signal3 == 1:
                        # sell
                        print("-" * 50)
                        print(f"\t - Продаем по рынку {data._name}...")
                        self.orders[data._name] = self.close()  # Заявка на закрытие позиции по рыночной цене
                        print("-" * 50)

    def notify_order(self, order):
        """Изменение статуса заявки"""
        order_data_name = order.data._name  # Имя тикера из заявки
        print("*"*50)
        self.log(f'Заявка номер {order.ref} {order.info["order_number"]} {order.getstatusname()} {"Покупка" if order.isbuy() else "Продажа"} {order_data_name} {order.size} @ {order.price}')
        if order.status == bt.Order.Completed:  # Если заявка полностью исполнена
            if order.isbuy():  # Заявка на покупку
                self.log(f'Покупка {order_data_name} Цена: {order.executed.price:.2f}, Объём: {order.executed.value:.2f}, Комиссия: {order.executed.comm:.2f}')
            else:  # Заявка на продажу
                self.log(f'Продажа {order_data_name} Цена: {order.executed.price:.2f}, Объём: {order.executed.value:.2f}, Комиссия: {order.executed.comm:.2f}')
                self.orders[order_data_name] = None  # Сбрасываем заявку на вход в позицию
        print("*" * 50)

    def notify_trade(self, trade):
        """Изменение статуса позиции"""
        if trade.isclosed:  # Если позиция закрыта
            self.log(f'Прибыль по закрытой позиции {trade.getdataname()} Общая={trade.pnl:.2f}, Без комиссии={trade.pnlcomm:.2f}')

    def log(self, txt, dt=None):
        """Вывод строки с датой на консоль"""
        dt = bt.num2date(self.datas[0].datetime[0]) if not dt else dt  # Заданная дата или дата текущего бара
        print(f'{dt.strftime("%d.%m.%Y %H:%M")}, {txt}')  # Выводим дату и время с заданным текстом на консоль


if __name__ == '__main__':
    
    symbol = 'SBER'  # Тикер в формате <Код тикера>
    symbol2 = 'LKOH'  # Тикер в формате <Код тикера>

    store = MoexAlgoStore()  # Хранилище AlgoPack
    # store = MoexAlgoStore(login=ConfigMOEX.Login, password=ConfigMOEX.Password)  # Хранилище AlgoPack + авторизация на Московской Бирже

    cerebro = bt.Cerebro(quicknotify=True)  # Инициируем "движок" BackTrader

    cerebro.broker.setcash(2000000)  # Устанавливаем сколько денег
    cerebro.broker.setcommission(commission=0.0015)  # Установить комиссию- 0.15% ... разделите на 100, чтобы удалить %

    # # live подключение к брокеру - для Offline закомментировать эти две строки + еще нужен импорт библиотеки брокера
    # broker = store.getbroker()
    # cerebro.setbroker(broker)

    # -----------------------------------------------------------
    # Внимание! - Теперь это Offline для тестирования стратегий #
    # -----------------------------------------------------------

    # # Исторические 10-минутные бары за 10000 часов + новые live бары / таймфрейм M10
    # timeframe = "M10"
    # fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=60*10000)
    # data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=10, dataname=symbol, fromdate=fromdate, live_bars=False)  # поставьте здесь True - если нужно получать live бары
    # data2 = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=10, dataname=symbol2, fromdate=fromdate, live_bars=False)  # поставьте здесь True - если нужно получать live бары

    timeframe = "M5"
    fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=5 * 1000)
    data = store.getdata(dataname=symbol, timeframe=bt.TimeFrame.Minutes, compression=5, fromdate=fromdate, live_bars=False,
                         super_candles=True,  # для получения свечей SuperCandles с расширенным набором характеристик
                         metric='tradestats',  # + необходимо указать тип получаемых метрик
                         )
    data2 = store.getdata(dataname=symbol2, timeframe=bt.TimeFrame.Minutes, compression=5, fromdate=fromdate,
                         live_bars=False,
                         super_candles=True,  # для получения свечей SuperCandles с расширенным набором характеристик
                         metric='tradestats',  # + необходимо указать тип получаемых метрик
                         )

    # Исторические D1 бары за 365 дней + новые live бары / таймфрейм D1
    # timeframe = "D1"
    # fromdate = dt.datetime.utcnow() - dt.timedelta(days=365*3)
    # data = store.getdata(timeframe=bt.TimeFrame.Days, compression=1, dataname=symbol, fromdate=fromdate, live_bars=False)  # поставьте здесь True - если нужно получать live бары
    # data2 = store.getdata(timeframe=bt.TimeFrame.Days, compression=1, dataname=symbol2, fromdate=fromdate, live_bars=False)  # поставьте здесь True - если нужно получать live бары

    cerebro.adddata(data)  # Добавляем данные
    cerebro.adddata(data2)  # Добавляем данные

    cerebro.addstrategy(RSIStrategy, timeframe=timeframe)  # Добавляем торговую систему

    cerebro.addanalyzer(btanalyzers.SQN, _name='SQN')
    cerebro.addanalyzer(btanalyzers.VWR, _name='VWR', fund=True)
    cerebro.addanalyzer(btanalyzers.TimeDrawDown, _name='TDD', fund=True, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(btanalyzers.DrawDown, _name='DD', fund=True)
    cerebro.addanalyzer(btanalyzers.Returns, _name='R', fund=True, timeframe=bt.TimeFrame.Days)
    cerebro.addanalyzer(btanalyzers.AnnualReturn, _name='AR', )
    cerebro.addanalyzer(btanalyzers.SharpeRatio, _name='SR')
    cerebro.addanalyzer(btanalyzers.TradeAnalyzer, _name='TradeAnalyzer')

    results = cerebro.run()  # Запуск торговой системы
    cerebro.plot()  # Рисуем график

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
