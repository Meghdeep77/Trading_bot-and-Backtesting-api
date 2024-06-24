from lumibot.brokers import Alpaca
from lumibot.backtesting import YahooDataBacktesting
from lumibot.strategies.strategy import Strategy
from lumibot.traders import Trader
from datetime import datetime
from alpaca_trade_api import REST
from timedelta import Timedelta
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer



nltk.download('vader_lexicon')
sia = SentimentIntensityAnalyzer()

API_KEY = "PK844AXXBJDO2YMPFDTK"
API_SECRET = "pedhi4YL6F2DQ0YCqKUnC4lmXPo5lomS4rE0hISE"
BASE_URL = "https://paper-api.alpaca.markets"

ALPACA_CREDS = {
    "API_KEY":API_KEY,
    "API_SECRET": API_SECRET,
    "PAPER": True
}

class MLTrader(Strategy):
    def initialize(self, symbol:str="YESBANK.NS",cash_at_risk:float=0.5):
        self.symbol = symbol
        self.cash_at_risk = cash_at_risk
        self.sleeptime = "24H"
        self.last_trade = None
        self.api = REST(base_url=BASE_URL, key_id=API_KEY, secret_key=API_SECRET)

    def position_sizing(self):
        cash = self.get_cash()
        last_price = self.get_last_price(self.symbol)
        quantity =round( (cash * self.cash_at_risk) / last_price)
        return cash,last_price,quantity

    def get_dates(self):
        today = self.get_datetime()
        three_days_prior = today - Timedelta(days=3)
        return today.strftime('%Y-%m-%d'), three_days_prior.strftime('%Y-%m-%d')

    def get_sentiment(self):
        today, three_days_prior = self.get_dates()
        news = self.api.get_news(symbol=self.symbol,
                                 start=three_days_prior,
                                 end=today)
        news = [ev.__dict__["_raw"]["headline"] for ev in news]
        sentiment = sia.polarity_scores(str(news))['compound']
        print(news)
        print(sentiment)
        return  sentiment

    def on_trading_iteration(self):
        cash, last_price, quantity = self.position_sizing()
        sentiment = self.get_sentiment()

        if cash > last_price:
            if sentiment > 0.3:
                if self.last_trade == 'sell':
                    self.sell_all()
                order = self.create_order(
                    self.symbol,
                    quantity,
                    "buy",
                    type="bracket",
                    take_profit_price=last_price * 1.20,
                    stop_loss_price=last_price * .95
                )
                self.submit_order(order)
                self.last_trade = "buy"
        elif sentiment < 0:
            if self.last_trade == "buy":
                self.sell_all()
            order = self.create_order(
                self.symbol,
                quantity,
                "sell",
                type="bracket",
                take_profit_price=last_price * .8,
                stop_loss_price=last_price * 1.05
            )
            self.submit_order(order)
            self.last_trade = "sell"




start_date = datetime(2024,1,1)
end_date = datetime(2024,4,25)
broker = Alpaca(ALPACA_CREDS)
strategy = MLTrader(name='mlstrat', broker=broker,
                    parameters={"symbol":"YESBANK.NS"})
strategy.backtest(
    YahooDataBacktesting,
    start_date,
    end_date,
    parameters={"symbol":"YESBANK.NS"}
)