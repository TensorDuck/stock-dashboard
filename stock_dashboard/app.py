import streamlit as st
import yfinance
import datetime
import pandas as pd

from typing import Tuple
import plotly.graph_objects as pgo


def get_stock_info_and_history(ticker: str) -> Tuple[dict, pd.DataFrame]:
    """Get the daily historical adjusted price for a stock"""
    ticker_obj = yfinance.Ticker(ticker)
    return ticker_obj.info, ticker_obj.history(period="max")


def sidebar_get_date_range() -> Tuple[datetime.date, datetime.date]:
    """Get the start and end dates in the date range to display"""
    # these show up in the side bar

    # set default values
    end_date = datetime.datetime.today().date()
    start_date = end_date - datetime.timedelta(days=90)

    default_start_date = start_date
    default_end_date = end_date

    # then present default options:
    start_day_count = st.sidebar.radio(
        "Date Range",
        [7, 30, 90, 180, 365, 365 * 5, "Custom"],
        format_func=lambda s: s
        if isinstance(s, str)
        else (f"{s}d" if s < 365 else f"{int(s/365)}y"),
        index=2,
    )

    # if "custom" selected, then display a date range option
    if start_day_count == "Custom":
        start_date = st.sidebar.date_input(
            label="start date",
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.datetime.today().date(),
            value=default_end_date,
        )
        end_date = st.sidebar.date_input(
            label="end date",
            min_value=datetime.date(1900, 1, 1),
            max_value=datetime.datetime.today().date(),
            value=default_end_date,
        )
    else:
        start_date = end_date - datetime.timedelta(days=start_day_count)

    return start_date, end_date


def run_main():
    """Main method for dashboard to assemble all the pieces of the dashboard"""
    st.title("Stock Analysis")

    # Widgets
    # these show up in the main bar
    ticker = st.text_input(label="Ticker")

    start_date, end_date = sidebar_get_date_range()

    # make a plot of what we need to show
    if ticker:
        # get stock prices for the desired date range
        stock_info, prices_all = get_stock_info_and_history(ticker)
        prices_all["rolling_a"] = prices_all["Close"].rolling(10).mean()
        prices_all["rolling_b"] = prices_all["Close"].rolling(20).mean()

        prices = prices_all[
            (prices_all.index >= str(start_date)) & (prices_all.index <= str(end_date))
        ]

        # Write some information to the dashboard
        st.write(f"{stock_info['longName']}")
        dividend_yield = stock_info["trailingAnnualDividendYield"]
        if dividend_yield:
            st.write(f"Annual Dividend Yield: {dividend_yield*100:.2f}%")
        else:
            st.write("Annual Dividend Yield: None")
        # make a figure
        fig = pgo.Figure(layout={"hovermode": "x unified"})
        fig.add_trace(
            pgo.Scatter(x=prices.index, y=prices["Close"], mode="lines", name="price",)
        )
        fig.add_trace(
            pgo.Scatter(
                x=prices.index,
                y=prices["rolling_a"],
                mode="lines",
                name="10-day Average",
            )
        )
        fig.add_trace(
            pgo.Scatter(
                x=prices.index,
                y=prices["rolling_b"],
                mode="lines",
                name="20-day Average",
            )
        )
        st.write(fig)  # write it to streamlit


if __name__ == "__main__":
    run_main()
