import backtrader as bt


class StrategyJustPrintsOHLCVAndSuperCandles(bt.Strategy):
    """
    - Отображает статус подключения
    - При приходе нового бара отображает его цены/объем
    - Отображает статус перехода к новым барам
    """
    params = (  # Параметры торговой системы
        ('name', None),  # Название торговой системы
        ('symbols', None),  # Список торгуемых тикеров. По умолчанию торгуем все тикеры
    )

    def log(self, txt, dt=None):
        """Вывод строки с датой на консоль"""
        dt = bt.num2date(self.datas[0].datetime[0]) if not dt else dt  # Заданная дата или дата последнего бара первого тикера ТС
        print(f'{dt.strftime("%d.%m.%Y %H:%M")}, {txt}')  # Выводим дату и время с заданным текстом на консоль

    def __init__(self):
        """Инициализация торговой системы"""
        self.isLive = False  # Сначала будут приходить исторические данные

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
        """Изменение статсуса приходящих баров"""
        data_status = data._getstatusname(status)  # Получаем статус (только при live_bars=True)
        _name = data._name if data._name else f"{self.p.name}"
        print(f'{_name} - {bt.TimeFrame.Names[data.p.timeframe]} {data.p.compression} - {data_status}')  # Статус приходит для каждого тикера отдельно
        self.isLive = data_status == 'LIVE'  # В Live режим переходим после перехода первого тикера
