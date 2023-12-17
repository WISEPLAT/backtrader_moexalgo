import datetime as dt
import backtrader as bt
import backtrader.analyzers as btanalyzers
from backtrader_moexalgo.moexalgo_store import MoexAlgoStore  # Хранилище AlgoPack

from Config import Config as ConfigMOEX  # для авторизации на Московской Бирже


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
        self.rsi = {}
        for i in range(len(self.datas)):
            ticker = list(self.dnames.keys())[i]    # key name is ticker name
            self.sma1[ticker] = bt.indicators.SMA(self.datas[i], period=8)  # SMA indicator
            self.sma2[ticker] = bt.indicators.SMA(self.datas[i], period=16)  # SMA indicator
            self.rsi[ticker] = bt.indicators.RSI(self.datas[i], period=14)  # RSI indicator

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
                print(f'\t - {ticker} RSI : {self.rsi[ticker][0]}')

                print(f"\t - Free balance: {self.broker.getcash()}")

                order = self.orders[data._name]  # Заявка тикера
                if order and order.status == bt.Order.Submitted:  # Если заявка не на бирже (отправлена брокеру)
                    return  # то ждем постановки заявки на бирже, выходим, дальше не продолжаем
                if not self.getposition(data):  # Если позиции нет
                    if order and order.status == bt.Order.Accepted:  # Если заявка на бирже (принята брокером)
                        print(f"\t - Снимаем заявку {order.p.tradeid} на покупку {data._name}")
                        # self.cancel(order)  # то снимаем ее

                    if self.rsi[ticker] < 30:  # Enter long
                        free_money = self.broker.getcash()
                        price = data.close[0]  # по цене закрытия
                        size = (free_money / price) * 0.01  # 1% от доступных средств

                        print(f" - buy {ticker} size = {size} at price = {price}")
                        self.orders[data._name] = self.buy(data=data, exectype=bt.Order.Limit, price=price, size=size)
                        print(f"\t - Выставлена заявка {self.orders[data._name].p.tradeid} на покупку {data._name}")

                else:  # Если позиция есть
                    if self.rsi[ticker] > 70:
                        print("sell")
                        print(f"\t - Продаем по рынку {data._name}...")
                        self.orders[data._name] = self.close()  # Заявка на закрытие позиции по рыночной цене

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

    symbols = ('SBER', 'LKOH', 'AFLT', 'GMKN', )  # тикеры, по которым будем получать данные

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

    for _symbol in symbols:  # Пробегаемся по всем тикерам
        # Исторические 1-минутные бары за 10000 часов + новые live бары / таймфрейм M1
        timeframe = "M1"
        fromdate = dt.datetime.utcnow() - dt.timedelta(minutes=60*10000)
        data = store.getdata(timeframe=bt.TimeFrame.Minutes, compression=10, dataname=_symbol, fromdate=fromdate, live_bars=False)  # поставьте здесь True - если нужно получать live бары

        cerebro.adddata(data)  # Добавляем данные

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
