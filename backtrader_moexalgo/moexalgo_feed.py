from collections import deque
from datetime import datetime, time

import pandas as pd

from backtrader.feed import DataBase
from backtrader.utils import date2num

from backtrader import TimeFrame as tf
from moexalgo import Ticker

import time as _time


class MoexAlgoData(DataBase):
    """Класс получения исторических и live данных по тикеру"""
    params = (
        ('drop_newest', False),
        ('supercandles', {}),  # данные по Super Candles
        ('metric_name', 'none'),  # данные по Super Candles
    )
    
    # States for the Finite State Machine in _load
    _ST_LIVE, _ST_HISTORBACK, _ST_OVER = range(3)

    def __init__(self, store, **kwargs):  # def __init__(self, store, timeframe, compression, from_date, live_bars):
        """Инициализация необходимых переменных"""
        self.interval = None
        self.timeframe = tf.Minutes
        self.compression = 1
        self.from_date = None
        self.live_bars = None

        self.super_candles = False
        self.metric = ''

        self.limit = 10_000  # Какое кол-во записей будем получать в каждом запросе через moexalgo. Максимум 50_000

        self.skip_first_date = None  # Если убираем бары на первую дату
        self.skip_last_date = None  # Если убираем бары на последнюю дату
        self.four_price_doji = True  # Если удаляем дожи 4-х цен

        self.get_live_bars_from = None  # с какой даты получаем live бары

        self.symbol = self.p.dataname

        self.p.supercandles[self.symbol] = {
            "tradestats": [],
            "orderstats": [],
            "obstats": [],
            "none": []
        }

        if hasattr(self.p, 'timeframe'): self.timeframe = self.p.timeframe
        if hasattr(self.p, 'compression'): self.compression = self.p.compression
        if hasattr(self.p, 'fromdate'): self.from_date = datetime.combine(self.p.fromdate, time.min)

        if 'live_bars' in kwargs: self.live_bars = kwargs['live_bars']
        if 'skip_first_date' in kwargs: self.skip_first_date = kwargs['skip_first_date']
        if 'skip_last_date' in kwargs: self.skip_last_date = kwargs['skip_last_date']
        if 'four_price_doji' in kwargs: self.four_price_doji = kwargs['four_price_doji']

        if 'super_candles' in kwargs: self.super_candles = kwargs['super_candles']
        if 'metric' in kwargs:
            self.metric = kwargs['metric']
            self.p.metric_name = self.metric
        else:
            self.metric = self.p.metric_name

        self._store = store
        self._data = deque()

        self.all_history_data = None  # Вся история по тикеру

        # print("Ok", self.timeframe, self.compression, self.from_date, self._store, self.live_bars, self.symbol, self.super_candles, self.metric)

    def _load(self):
        """Метод загрузки"""
        if self._state == self._ST_OVER:
            return False
        elif self._state == self._ST_LIVE:
            # return self._load_kline()
            if self._load_kline():
                return True
            else:
                self._start_live()
        elif self._state == self._ST_HISTORBACK:
            if self._load_kline():
                return True
            else:
                self._start_live()

    def _load_kline(self):
        """Обработка одной строки данных"""
        try:
            kline = self._data.popleft()
        except IndexError:
            return None

        _super_candle = {}

        if type(kline) == list:  # fix
            timestamp, open_, high, low, close, volume = None, 0.0, 0.0, 0.0, 0.0, 0.0
            if not self.super_candles:  # если нужны обычные свечи
                timestamp, open_, high, low, close, volume = kline
            else:
                if self.metric == 'tradestats':
                    datetime_, pr_open, pr_high, pr_low, pr_close, pr_change, trades, vol, val, pr_std, disb, pr_vwap, \
                        trades_b, vol_b, val_b, pr_vwap_b, trades_s, vol_s, val_s, pr_vwap_s = kline
                    timestamp = datetime_
                    open_ = pr_open
                    high = pr_high
                    low = pr_low
                    close = pr_close
                    volume = vol
                    _super_candle = {'pr_change': pr_change, 'trades': trades, 'val': val,
                                     'pr_std': pr_std, 'disb': disb, 'pr_vwap': pr_vwap, 'trades_b': trades_b,
                                     'vol_b': vol_b, 'val_b': val_b, 'pr_vwap_b': pr_vwap_b,
                                     'trades_s': trades_s, 'vol_s': vol_s, 'val_s':val_s, 'pr_vwap_s': pr_vwap_s}

                if self.metric == 'orderstats':
                    datetime_, put_orders, put_orders_b, put_orders_s, put_vol, put_vol_b, put_vol_s, put_val, \
                        put_val_b, put_val_s, cancel_orders, cancel_orders_b, cancel_orders_s, cancel_vol, \
                        cancel_vol_b, cancel_vol_s, cancel_val, cancel_val_b, cancel_val_s, put_vwap_b, \
                        put_vwap_s, cancel_vwap_b, cancel_vwap_s = kline
                    timestamp = datetime_
                    _super_candle = {'put_orders': put_orders, 'put_orders_b': put_orders_b,
                                     'put_orders_s': put_orders_s, 'put_vol': put_vol, 'put_vol_b': put_vol_b,
                                     'put_vol_s': put_vol_s, 'put_val': put_val, 'put_val_b': put_val_b,
                                     'put_val_s': put_val_s, 'cancel_orders': cancel_orders,
                                     'cancel_orders_b': cancel_orders_b, 'cancel_orders_s': cancel_orders_s,
                                     'cancel_vol': cancel_vol,'cancel_vol_b': cancel_vol_b,
                                     'cancel_vol_s': cancel_vol_s, 'cancel_val': cancel_val,
                                     'cancel_val_b': cancel_val_b, 'cancel_val_s': cancel_val_s,
                                     'put_vwap_b': put_vwap_b, 'put_vwap_s': put_vwap_s,
                                     'cancel_vwap_b': cancel_vwap_b, 'cancel_vwap_s': cancel_vwap_s}

                if self.metric == 'obstats':
                    datetime_, spread_bbo, spread_lv10, spread_1mio, levels_b, levels_s, vol_b, vol_s, val_b, \
                        val_s, imbalance_vol_bbo, imbalance_val_bbo, imbalance_vol, imbalance_val, vwap_b, \
                        vwap_s, vwap_b_1mio, vwap_s_1mio = kline
                    timestamp = datetime_
                    _super_candle = {'spread_bbo': spread_bbo, 'spread_lv10': spread_lv10, 'spread_1mio': spread_1mio,
                                     'levels_b': levels_b, 'levels_s': levels_s, 'vol_b': vol_b, 'vol_s': vol_s,
                                     'val_b': val_b, 'val_s': val_s, 'imbalance_vol_bbo': imbalance_vol_bbo,
                                     'imbalance_val_bbo': imbalance_val_bbo, 'imbalance_vol': imbalance_vol,
                                     'imbalance_val': imbalance_val, 'vwap_b': vwap_b, 'vwap_s': vwap_s,
                                     'vwap_b_1mio': vwap_b_1mio, 'vwap_s_1mio': vwap_s_1mio}

            self.lines.datetime[0] = date2num(timestamp)
            self.lines.open[0] = open_
            self.lines.high[0] = high
            self.lines.low[0] = low
            self.lines.close[0] = close
            self.lines.volume[0] = volume

            # через словарь добавляем данные по Super Candles
            if self.super_candles:
                self.p.supercandles[self.symbol][self.metric].insert(0, _super_candle)
            else:
                self.p.supercandles[self.symbol][self.metric].insert(0, None)

        return True

    def _start_live(self):
        """Получение live данных"""
        while True:
            if self.live_bars:

                if self._state != self._ST_LIVE:
                    print(f"Live started for ticker: {self.symbol}")
                    self._state = self._ST_LIVE
                    self.put_notification(self.LIVE)

                if not self.get_live_bars_from:
                    # self.get_live_bars_from = datetime.now().date()
                    self.get_live_bars_from = datetime.combine(datetime.now().date(), time.min)
                else:
                    # self.get_live_bars_from = self.get_live_bars_from.date()
                    self.get_live_bars_from = datetime.combine(self.get_live_bars_from.date(), time.min)

                if not self.super_candles:  # если нужны обычные свечи
                    klines, get_live_bars_from = self.get_candles(from_date=self.get_live_bars_from,
                                                                  symbol=self.symbol,
                                                                  interval=self.interval,
                                                                  skip_first_date=self.skip_first_date,
                                                                  skip_last_date=self.skip_last_date,
                                                                  four_price_doji=self.four_price_doji)
                else:  # если нужны Super свечи
                    klines, get_live_bars_from = self.get_super_candles(from_date=self.get_live_bars_from,
                                                                        symbol=self.symbol,
                                                                        interval=self.interval,
                                                                        metric=self.metric)

                if not klines.empty:  # если есть, что обрабатывать
                    new_klines = klines.values.tolist()  # берем новые строки данных
                    _klines = []
                    for kline in new_klines:
                        if kline not in self.all_history_data:  # если такой строки данных нет,
                            self.all_history_data.append(kline)
                            _klines.append(kline)
                    self._data.extend(_klines)  # отправляем в обработку

                    if _klines:  # если получили новые данные
                        break

                # здесь можно оптимизировать через потоки и запрашивать не так часто, пересчитывая сколько ждать
                _time.sleep(1)

            else:
                self._state = self._ST_OVER
                break

    def haslivedata(self):
        return self._state == self._ST_LIVE and self._data

    def islive(self):
        return True
        
    def start(self):
        """Получение исторических данных"""
        DataBase.start(self)

        # если ТФ задан не корректно, то ничего не делаем
        self.interval = self._store.get_interval(self.timeframe, self.compression)
        if self.interval is None:
            self._state = self._ST_OVER
            self.put_notification(self.NOTSUPPORTED_TF)
            return

        # если не можем получить данные по тикеру, то ничего не делаем
        self.symbol_info = self._store.get_symbol_info(self.symbol)
        if self.symbol_info is None:
            self._state = self._ST_OVER
            self.put_notification(self.NOTSUBSCRIBED)
            return

        # получение исторических данных
        if self.from_date:
            self._state = self._ST_HISTORBACK
            self.put_notification(self.DELAYED)  # Отправляем уведомление об отправке исторических (не новых) баров

            if not self.super_candles:  # если нужны обычные свечи
                klines, get_live_bars_from = self.get_candles(from_date=self.from_date,
                                                              symbol=self.symbol,
                                                              interval=self.interval,
                                                              skip_first_date=self.skip_first_date,
                                                              skip_last_date=self.skip_last_date,
                                                              four_price_doji=self.four_price_doji)  # , is_test=True
            else:  # если нужны Super свечи
                klines, get_live_bars_from = self.get_super_candles(from_date=self.from_date,
                                                                    symbol=self.symbol,
                                                                    interval=self.interval,
                                                                    metric=self.metric)  # , is_test=True
            self.get_live_bars_from = get_live_bars_from

            klines = klines.values.tolist()
            self.all_history_data = klines  # при первом получении истории - её всю записываем в виде list

            try:
                if self.p.drop_newest:
                    klines.pop()
                self._data.extend(klines)
            except Exception as e:
                print("Exception (try set from_date in utc format):", e)

        else:
            self._start_live()

    def get_candles(self, from_date, symbol, interval, skip_first_date=False, skip_last_date=False, four_price_doji=True, is_test=False):
        """Получение баров, используем библиотеку moexalgo
            :param date from_date: С какой даты получаем данные
            :param str symbol: Код тикера
            :param str interval: Временной интервал '1m', '10m', '1h', '1D', '1W', '1M' + '5m' resampling from '1m' + '30m' resampling from '10m'
            :param bool skip_first_date: Убрать бары на первую полученную дату
            :param bool skip_last_date: Убрать бары на последнюю полученную дату
            :param bool four_price_doji: Оставить бары с дожи 4-х цен
            :param bool is_test: Для проведения live теста в offline
        """

        last_date = datetime(2020, 1, 1)  # Получать данные будем с первой возможной даты и времени Алгопака
        if from_date and from_date >= last_date:
            last_date = from_date  # Получать данные будем с указанной даты
        last_dt = last_date

        # проверяем, нужно ли делать resample
        resample = False
        interval_to = None
        if interval == '5m':
            resample = True
            interval = '1m'
            interval_to = '5T'  # is equal for '5m (pandas)

        if interval == '30m':
            resample = True
            interval = '10m'
            interval_to = '30T'  # is equal for '30m (pandas)

        df = pd.DataFrame()
        get_live_bars_from = None
        till_date = datetime.now().date()  # Получать данные будем до текущей даты
        ticker = Ticker(symbol)  # Пока реализуем только для тикеров ММВБ
        while True:  # Будем получать данные пока не получим все
            iterator = ticker.candles(date=last_date, till_date=till_date, period=interval,
                                      limit=self.limit)  # История. Максимум, 50000 баров
            rows_list = []  # Будем собирать строки в список
            try:
                for it in iterator:  # Итерируем генератор
                    rows_list.append(it.__dict__)  # Класс превращаем в словарь, добавляем строку в список
            except:  # if error - we are in notebook
                rows_list = iterator

            if len(rows_list):
                stats = pd.DataFrame(rows_list)  # Из списка создаем pandas DataFrame
                stats.rename(columns={'begin': 'datetime'}, inplace=True)  # Переименовываем колонку даты и времени

                if len(stats):
                    stats = stats[['datetime', 'open', 'high', 'low', 'close', 'volume']]  # Отбираем нужные колонки

                if skip_first_date:  # Если убираем бары на первую дату
                    len_with_first_date = len(stats)  # Кол-во баров до удаления на первую дату
                    first_date = stats.iloc[0]['datetime'].date()  # Первая дата
                    stats.drop(stats[(stats['datetime'].date() == first_date)].index, inplace=True)  # Удаляем их
                    print(self.symbol, f' - Удалено баров на первую дату {first_date}: {len_with_first_date - len(stats)}')
                if skip_last_date:  # Если убираем бары на последнюю дату
                    len_with_last_date = len(stats)  # Кол-во баров до удаления на последнюю дату
                    last_date = stats.iloc[-1]['datetime'].date()  # Последняя дата
                    stats.drop(stats[(stats['datetime'].date() == last_date)].index, inplace=True)  # Удаляем их
                    print(self.symbol, f' - Удалено баров на последнюю дату {last_date}: {len_with_last_date - len(stats)}')
                if not four_price_doji:  # Если удаляем дожи 4-х цен
                    len_with_doji = len(stats)  # Кол-во баров до удаления дожи
                    stats.drop(stats[(stats['high'] == stats['low'])].index,
                               inplace=True)  # Удаляем их по условия High == Low
                    print(self.symbol, ' - Удалено дожи 4-х цен:', len_with_doji - len(stats))
                if len(stats) == 0:  # Если нечего объединять
                    print(self.symbol, '- Новых записей нет')
                    break  # то дальше не продолжаем

                last_stats_dt = stats.iloc[-1]['datetime']  # Последняя полученная дата и время
                last_stats_date = last_stats_dt.date()  # Последняя полученная дата
                if last_stats_dt == last_dt:  # Если не получили новые значения
                    # print(self.symbol, '- Все данные получены')
                    get_live_bars_from = last_stats_dt
                    break  # то дальше не продолжаем

                print(self.symbol, '- Получены данные с', stats.iloc[0]['datetime'], 'по', last_stats_dt)

                last_dt = last_stats_dt  # Запоминаем последние полученные дату и время
                last_date = last_stats_date  # и дату

                df = pd.concat([df, stats]).drop_duplicates(keep='last')  # Добавляем новые данные в существующие. Удаляем дубликаты. Сбрасываем индекс
            elif not len(rows_list) and not self.live_bars:
                break

        # если требуется сделать resample
        if resample and not df.empty:
            ohlc_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum',
                # 'value': 'sum',
            }
            df.set_index('datetime', inplace=True)
            df.index = pd.to_datetime(df.index, format='%Y-%m-%d %H:%M:%S')  # Переводим индекс в формат datetime
            df_res = df.resample(interval_to).agg(ohlc_dict)
            df_res = df_res[df_res['open'].notna()]  # just take the rows where 'open' is not NA
            df_res.reset_index(inplace=True)
            df = df_res.copy()

        # test for live in offline
        if is_test:
            df.drop(df.tail(4).index,inplace=True) # drop last n rows
            get_live_bars_from = df.iloc[-1]['datetime']
            return df, get_live_bars_from

        return df, get_live_bars_from

    def get_super_candles(self, from_date, symbol, interval="5m", metric='tradestats', is_test=False):
        """Получение метрики тикера, используем библиотеку moexalgo
            :param date from_date: С какой даты получаем данные
            :param str symbol: Код тикера
            :param str interval: Временной интервал '5m' - биржа отдает только такой интервал для Super Candles
            :param str metric: Метрика. 'tradestats' - сделки, 'orderstats' - заявки, 'obstats' - стакан
            :param bool is_test: Для проведения live теста в offline
        """

        last_date = datetime(2020, 1, 1)  # Получать данные будем с первой возможной даты и времени Алгопака
        if from_date and from_date >= last_date:
            last_date = from_date  # Получать данные будем с указанной даты
        last_dt = last_date

        last_date = last_date.date()
        last_dt = last_dt.date()

        # проверяем, нужно ли делать resample
        resample = False
        interval_to = None
        if interval == '10m':
            resample = True
            interval = '5m'
            interval_to = '10T'  # is equal for '10m (pandas)

        if interval == '30m':
            resample = True
            interval = '5m'
            interval_to = '30T'  # is equal for '30m (pandas)

        df = pd.DataFrame()
        get_live_bars_from = None
        till_date = datetime.now().date()  # Получать данные будем до текущей даты
        ticker = Ticker(symbol)  # Пока реализуем только для тикеров ММВБ
        while True:  # Будем получать данные пока не получим все
            if metric == 'tradestats':  # Сделки
                iterator = ticker.tradestats(date=last_date, till_date=till_date, limit=self.limit)
            elif metric == 'orderstats':  # Заявки
                iterator = ticker.orderstats(date=last_date, till_date=till_date, limit=self.limit)
            elif metric == 'obstats':  # Стакан
                iterator = ticker.obstats(date=last_date, till_date=till_date, limit=self.limit)
            else:
                print(self.symbol, 'Метрика указана неверно')
                break

            rows_list = []  # Будем собирать строки в список
            try:
                for it in iterator:  # Итерируем генератор
                    rows_list.append(it.__dict__)  # Класс превращаем в словарь, добавляем строку в список
            except:  # if error - we are in notebook
                rows_list = iterator

            if len(rows_list):
                stats = pd.DataFrame(rows_list)  # Из списка создаем pandas DataFrame
                stats.drop('secid', axis='columns', inplace=True)  # Удаляем колонку тикера. Название тикера есть в имени файла
                stats.rename(columns={'ts': 'datetime'}, inplace=True)  # Переименовываем колонку даты и времени
                stats['datetime'] -= pd.Timedelta(minutes=5)  # 5-и минутку с датой и временем окончания переводим в дату и время начала для синхронизации с OHLCV

                last_stats_dt = stats.iloc[-1]['datetime']  # Последняя полученная дата и время
                last_stats_date = last_stats_dt.date()  # Последняя полученная дата
                if last_stats_dt == last_dt:  # Если не получили новые значения
                    # print(self.symbol, 'Все данные получены')
                    get_live_bars_from = last_stats_dt
                    break  # то выходим, дальше не продолжаем

                print(self.symbol, '- Получены данные с', stats.iloc[0]['datetime'], 'по', last_stats_dt)

                last_dt = last_stats_dt  # Запоминаем последние полученные дату и время
                last_date = last_stats_date  # и дату

                df = pd.concat([df, stats]).drop_duplicates(keep='last')  # Добавляем новые данные в существующие. Удаляем дубликаты. Сбрасываем индекс
            elif not len(rows_list) and not self.live_bars:
                break

        # если требуется сделать resample для tradestats
        if resample and not df.empty and metric == 'tradestats':
            df.rename(columns={'pr_open': 'open', 'pr_high': 'high', 'pr_low': 'low', 'pr_close': 'close', }, inplace=True)  # Переименовываем колонку даты и времени
            ohlc_dict = {
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'pr_change': 'sum',
                'trades': 'sum',
                'vol': 'sum',
                'val': 'sum',
                'pr_std': 'sum',
                'disb': 'sum',
                'pr_vwap': 'sum',
                'trades_b': 'sum',
                'vol_b': 'sum',
                'val_b': 'sum',
                'pr_vwap_b': 'sum',
                'trades_s': 'sum',
                'vol_s': 'sum',
                'val_s': 'sum',
                'pr_vwap_s': 'sum',
            }
            df.set_index('datetime', inplace=True)
            df.index = pd.to_datetime(df.index, format='%Y-%m-%d %H:%M:%S')  # Переводим индекс в формат datetime
            df_res = df.resample(interval_to).agg(ohlc_dict)
            df_res = df_res[df_res['open'].notna()]  # just take the rows where 'open' is not NA
            df_res.reset_index(inplace=True)
            df = df_res.copy()
            df.rename(columns={'open': 'pr_open', 'high': 'pr_high', 'low': 'pr_low', 'close': 'pr_close', }, inplace=True)  # Переименовываем колонку даты и времени

        # test for live in offline
        if is_test:
            df.drop(df.tail(4).index, inplace=True)  # drop last n rows
            get_live_bars_from = df.iloc[-1]['datetime']
            return df, get_live_bars_from

        return df, get_live_bars_from
