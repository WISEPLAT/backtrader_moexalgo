import backtrader as bt
import math


class StrategyJustPrintsOHLCVAndSuperCandlesMC(bt.Strategy):
    """
    - Отображает статус подключения
    - При приходе нового бара отображает его цены/объем
    - Отображает статус перехода к новым барам
    """
    params = (  # Параметры торговой системы
        ('name', None),  # Название торговой системы
        ('symbols', None),  # Список торгуемых тикеров. По умолчанию торгуем все тикеры
        ('timeframe', ''),
    )

    def log(self, txt, dt=None):
        """Вывод строки с датой на консоль"""
        dt = bt.num2date(self.datas[0].datetime[0]) if not dt else dt  # Заданная дата или дата последнего бара первого тикера ТС
        print(f'{dt.strftime("%d.%m.%Y %H:%M")}, {txt}')  # Выводим дату и время с заданным текстом на консоль

    def __init__(self):
        """Инициализация, добавление индикаторов для каждого тикера"""
        self.isLive = False  # Сначала будут приходить исторические данные

        self.orders = {}  # Организовываем заявки в виде справочника, конкретно для этой стратегии один тикер - одна активная заявка
        for d in self.datas:  # Пробегаемся по всем тикерам
            self.orders[d._name] = None  # Заявки по тикеру пока нет

        # создаем индикаторы для каждого тикера
        self.sma1 = {}
        self.sma2 = {}
        self.crossover = {}
        self.crossdown = {}
        for i in range(len(self.datas)):
            ticker = list(self.dnames.keys())[i]    # key name is ticker name
            self.sma1[ticker] = bt.indicators.SMA(self.datas[i], period=8)  # SMA indicator
            self.sma2[ticker] = bt.indicators.SMA(self.datas[i], period=32)  # SMA indicator

            # signal 1 - пересечение быстрой SMA снизу вверх медленной SMA
            self.crossover[ticker] = bt.ind.CrossOver(self.sma1[ticker], self.sma2[ticker])  # crossover SMA1 and SMA2

            # signal 2 - когда SMA3 находится ниже SMA2
            self.crossdown[ticker] = bt.ind.CrossOver(self.sma2[ticker], self.sma1[ticker])  # crossdown SMA1 and SMA2

    def next(self):
        """Приход нового бара тикера"""
        # if self.p.name:  # Если указали название торговой системы, то будем ждать прихода всех баров
        #     lastdatetimes = [bt.num2date(data.datetime[0]) for data in self.datas]  # Дата и время последнего бара каждого тикера
        #     if lastdatetimes.count(lastdatetimes[0]) != len(lastdatetimes):  # Если дата и время последних баров не идентичны
        #         return  # то еще не пришли все новые бары. Ждем дальше, выходим
        #     print(self.p.name)
        for data in self.datas:  # Пробегаемся по всем запрошенным тикерам
            if not self.p.symbols or data._name in self.p.symbols:  # Если торгуем все тикеры или данный тикер
                ticker = data.p.dataname
                self.log(f'{ticker} - {bt.TimeFrame.Names[data.p.timeframe]} {data.p.compression} - Open={data.open[0]:.2f}, High={data.high[0]:.2f}, Low={data.low[0]:.2f}, Close={data.close[0]:.2f}, Volume={data.volume[0]:.0f}',
                         bt.num2date(data.datetime[0]))

                _date = bt.num2date(data.datetime[0])

                try:
                    if data.p.supercandles[ticker][data.p.metric_name]:
                        print("\tSuper Candle:", data.p.supercandles[ticker][data.p.metric_name][0])
                        _data = data.p.supercandles[ticker][data.p.metric_name][0]
                        _data['datetime'] = _date
                        self.supercandles[ticker][data.p.metric_name].append(_data)
                except:
                    pass

                # некая дополнительная фейковая нагрузка, для загрузки ядра процессора
                for i in range(1, 1000000):
                    z = math.sqrt(64 * 64 * 64 * 64 * 64)

                # торговая логика на двух скользящих
                # сигналы на вход
                signal1 = self.crossover[ticker].lines.crossover[0]  # signal 1 - пересечение быстрой SMA снизу вверх медленной SMA

                # сигналы на выход
                signal2 = self.crossdown[ticker].lines.crossover[0]  # signal 2 - наоборот

                if not self.getposition(data):  # Если позиции нет
                    if signal1 == 1:
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
                    if signal2 == 1:
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

    def notify_data(self, data, status, *args, **kwargs):
        """Изменение статсуса приходящих баров"""
        data_status = data._getstatusname(status)  # Получаем статус (только при live_bars=True)
        _name = data._name if data._name else f"{self.p.name}"
        print(f'{_name} - {bt.TimeFrame.Names[data.p.timeframe]} {data.p.compression} - {data_status}')  # Статус приходит для каждого тикера отдельно
        self.isLive = data_status == 'LIVE'  # В Live режим переходим после перехода первого тикера
