"""Class for calculating metrics off of a stock price"""
import datetime
from typing import Union

import numpy as np
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
        unadjusted_prices = self.ticker_obj.history(period="max", auto_adjust=False)

        # add additional useful columns
        self.prices["Close_raw"] = unadjusted_prices["Close"]
        self.prices["adjust_factor"] = self.prices["Close"] / self.prices["Close_raw"]
        self.prices["percent_change"] = (
            self.prices["Close"].pct_change(periods=1).fillna(0)
        )
        self.prices["log_percent_change"] = self.prices["percent_change"].apply(
            lambda s: np.log(s + 1)
        )

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

    def calculate_growth(
        self,
        start_date: str,
        end_date: str,
        reinvest: bool = False,
        initial_price: Union[float, None] = None,
        baseline=None,
    ) -> float:
        """Calculate the percentage the stock grew by between start and end date

        The option exists to specify an initial buy-in price, as well as if dividends
        were immediately reinvested in the same security or not. By default, the
        assumption is that the security was bought at closing price with no reinvestment
        of dividends.

        Args:
            start_date: The initial date the stock was bought
            end_date: The final day for comparison
            reinvest: True if dividends were reinvested immediately.
            initial_price: Initial price. Defaults to the closing price of start_date
            baseline[StockInfo]: A baseline to compare the growth against.

        Returns:
            Growth of the security. E.g. 0.02 is 2%.
        """
        sub_prices = self.get_sub_prices_by_day(start_date, end_date)
        if len(sub_prices.index) == 0:  # stock didn't exist at this date
            return None
        min_date = min(sub_prices.index)
        max_date = max(sub_prices.index)
        # set the initial price if not specified
        if initial_price is None:
            if reinvest:
                initial_price = sub_prices["Close"][min_date]
            else:
                initial_price = sub_prices["Close_raw"][min_date]

        if reinvest:
            # just compare the adjusted closing price
            final_price = sub_prices["Close"][max_date]
        else:
            # sum-up all dividends earned and add it to the
            final_price = (
                sub_prices["Close_raw"][max_date] + sub_prices["Dividends"].sum()
            )

        growth = (final_price - initial_price) / initial_price
        if baseline is not None:
            baseline_growth = baseline.calculate_growth(
                start_date, end_date, reinvest=True
            )
            if baseline_growth is None:
                baseline_growth = 0
        else:
            baseline_growth = 0
        return growth - baseline_growth
