"""Class for calculating metrics off of a stock price"""
import pandas as pd
import yfinance


class StockInfo:
    def __init__(self, ticker: str):
        """Store stock info and provide internal calculations for common metrics

        By default, the price used is the adjusted price. This typically means:
            * Splits are already accounte dfor
            * Reduction in price from dividends is already accounted for

        In effect, the adjusted closing price is analagous to the scenario of:  buying
        the security at the closing price and then re-investing all dividends into the
        same security on the day they are paid.

        Args:
            ticker: Name of stock ticker to get data for
        """
        self.ticker = ticker
        self.ticker_obj = yfinance.Ticker(ticker)
        self.prices = self.ticker_obj.history(period="max")

    def get_annual_dividend_yield(self) -> float:
        """Get annual dividend yield, i.e. 0.02 for 2% yield in past 12 months"""
        return self.ticker_obj.info["trailingAnnualDividendYield"]

    def rolling_average(self, period: int = 10) -> pd.Series:
        """Calculate preceding 10-day rolling average

        The rolling average is computed backwards in time, so for April 1st, it will
        look at the preceding 10-days of trading and compute an average of the closing
        price.

        Args:
            period: The number of days to include in the rolling average

        Returns:
            Rolling average of closing price for each day
        """
        return self.prices["Close"].rolling(period).mean()

    def bollinger_bands(self, period: int = 20, m_sigma: int = 2) -> pd.DataFrame:
        """Calculate the bollinger bands for the security

        These bands come in a pair of upper+lower bands that indicate how
        volatile the stock is. When the bands grow narrow, the volatility is low. If the bands grow wider, then the volatility is high.

        Bollinger bands is based off of the "Typical Price" (TP) that is computed as a
        the average of the high, low and closing price for each day.

        For more information, see:
        https://www.investopedia.com/terms/b/bollingerbands.asp

        Args:
            period: The number of days to average over
            m_sigma: Number of sigmas to plot the upper and lower bollinger bands.

        Returns:
            Dataframe containing "bollinger_ma", "bollinger_upper", "bollinger_lower"
        """
        typical_price = (
            self.prices["Close"] + self.prices["High"] + self.prices["Low"]
        ) / 3
        moving_average = typical_price.rolling(period).mean()
        moving_sd = typical_price.rolling(period).std()
        df = moving_average.rename("bollinger_ma").to_frame()
        df["bollinger_upper"] = moving_average + (m_sigma * moving_sd)
        df["bollinger_lower"] = moving_average - (m_sigma * moving_sd)

        return df

    def get_sub_prices_by_day(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Get a sub-sample between the start and end dates"""

        return self.prices[
            (self.prices.index >= start_date) & (self.prices.index <= end_date)
        ]

    def calculate_growth(self, start_date: str, end_date: str) -> float:
        """Calculate the percentage the stock grew by between start and end date

        This is the growth between the adjusted closing price.

        """
        sub_prices = self.get_sub_prices_by_day(start_date, end_date)
        min_date = min(sub_prices.index)
        max_date = max(sub_prices.index)
        return (sub_prices["Close"][max_date] - sub_prices["Close"][min_date]) / (
            sub_prices["Close"][min_date]
        )
