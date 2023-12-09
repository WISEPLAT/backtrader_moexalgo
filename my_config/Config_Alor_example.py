# Чтобы получить Refresh Token:
# 0. Для получения тестового логина/пароля демо счета оставить заявку в Telegram на https://t.me/AlorOpenAPI
# 1. Зарегистрироваться на https://alor.dev/login
# 2. Выбрать "Токены для доступа к API"

# Для реального счета:
# 1. Привязать торговый аккаунт
# 2. Выписать токен

# Для демо счета:
# 1. Пройти по ссылке "Токены для ведения торгов в тестовом контуре" - "Begin OAuth authorization flow"
# 2. Ввести тестовый логин/пароль. Нажать "Разрешить"

# Как заполнять переменные портфелей PortfolioStocks, PortfolioFutures, PortfolioFx:
# 1. Запустить скрипт "Examples/02 - Accounts.py"
# 2. Получить портфели для всех рынков
# 3. Заполнить переменные полученными значениями

# Коды торговых серверов для стоп заявок:
TradeServerCode = 'TRADE'  # Рынок Ценных Бумаг
ITradeServerCode = 'ITRADE'  # Рынок Иностранных Ценных Бумаг
FutServerCode = 'FUT1'  # Фьючерсы
OptServerCode = 'OPT1'  # Опционы
FxServerCode = 'FX1'  # Валютный рынок


class ConfigBase:
    """Заготовка счета"""
    UserName: str  # Имя пользователя
    RefreshToken: str  # Токен

    PortfolioStocks: str  # Портфель фондового рынка
    PortfolioFutures: str  # Портфель срочного рынка
    PortfolioFx: str  # Портфель валютного рынка

    Accounts = {}  # Привязка портфелей к биржам
    Boards = {}  # Привязка портфелей/серверов для стоп заявок к площадкам


Config = ConfigBase()  # Торговый счет
Config.UserName = 'P000000'
Config.RefreshToken = 'ffffffff-ffff-ffff-ffff-ffffffffffff'
Config.PortfolioStocks = 'D87777'  # Фондовый рынок
Config.PortfolioFutures = '75777WG'  # Срочный рынок
Config.PortfolioFx = 'G47777'  # Валютный рынок
Config.Accounts = {  # Привязка портфелей к биржам
    Config.PortfolioStocks: ('MOEX', 'SPBX',),  # Фондовый рынок на Московской Бирже (RUB) и СПб Бирже (USD)
    Config.PortfolioFutures: ('MOEX',),  # Срочный рынок на Московской Бирже (RUB)
    Config.PortfolioFx: ('MOEX',)}  # Валютный рынок на Московской Бирже (RUB)
Config.Boards = {  # Привязка портфелей/серверов для стоп заявок к площадкам
    'TQBR': (Config.PortfolioStocks, TradeServerCode),  # Т+ Акции и ДР
    'TQOB': (Config.PortfolioStocks, TradeServerCode),  # МБ ФР: Т+: Гособлигации
    'TQCB': (Config.PortfolioStocks, TradeServerCode),  # МБ ФР: Т+: Облигации
    'RFUD': (Config.PortfolioFutures, FutServerCode)}  # FORTS: Фьючерсы

ConfigIIA = ConfigBase()  # Индивидуальный инвестиционный счет (ИИС)
ConfigIIA.UserName = 'P000000'
ConfigIIA.RefreshToken = 'ffffffff-ffff-ffff-ffff-ffffffffffff'
ConfigIIA.PortfolioStocks = 'D00000'  # Фондовый рынок
ConfigIIA.PortfolioFutures = '0000PSU'  # Срочный рынок
ConfigIIA.PortfolioFx = 'G00000'  # Валютный рынок
ConfigIIA.Accounts = {  # Привязка портфелей к биржам
    ConfigIIA.PortfolioStocks: ('MOEX', 'SPBX',),  # Фондовый рынок на Московской Бирже (RUB) и СПб Бирже (USD)
    ConfigIIA.PortfolioFutures: ('MOEX',),  # Срочный рынок на Московской Бирже (RUB)
    ConfigIIA.PortfolioFx: ('MOEX',)}  # Валютный рынок на Московской Бирже (RUB)
ConfigIIA.Boards = {  # Привязка портфелей/серверов для стоп заявок к площадкам
    'TQBR': (ConfigIIA.PortfolioStocks, TradeServerCode),  # Т+ Акции и ДР
    'TQOB': (ConfigIIA.PortfolioStocks, TradeServerCode),  # МБ ФР: Т+: Гособлигации
    'TQCB': (ConfigIIA.PortfolioStocks, TradeServerCode),  # МБ ФР: Т+: Облигации
    'RFUD': (ConfigIIA.PortfolioFutures, FutServerCode)}  # FORTS: Фьючерсы

ConfigDemo = ConfigBase()  # Демо счет для тестирования
ConfigDemo.UserName = 'P000000'
ConfigDemo.RefreshToken = 'ffffffff-ffff-ffff-ffff-ffffffffffff'
ConfigDemo.PortfolioStocks = 'D00000'  # Фондовый рынок
ConfigDemo.PortfolioFutures = '0000000'  # Срочный рынок
ConfigDemo.PortfolioFx = 'G00000'  # Валютный рынок
ConfigDemo.Accounts = {  # Привязка портфелей к биржам
    ConfigDemo.PortfolioStocks: ('MOEX', 'SPBX',),  # Фондовый рынок на Московской Бирже (RUB) и СПб Бирже (USD)
    ConfigDemo.PortfolioFutures: ('MOEX',),  # Срочный рынок на Московской Бирже (RUB)
    ConfigDemo.PortfolioFx: ('MOEX',)}  # Валютный рынок на Московской Бирже (RUB)
ConfigDemo.Boards = {  # Привязка портфелей/серверов для стоп заявок к площадкам
    'TQBR': (ConfigDemo.PortfolioStocks, TradeServerCode),  # Т+ Акции и ДР
    'TQOB': (ConfigDemo.PortfolioStocks, TradeServerCode),  # МБ ФР: Т+: Гособлигации
    'TQCB': (ConfigDemo.PortfolioStocks, TradeServerCode),  # МБ ФР: Т+: Облигации
    'RFUD': (ConfigDemo.PortfolioFutures, FutServerCode)}  # FORTS: Фьючерсы
