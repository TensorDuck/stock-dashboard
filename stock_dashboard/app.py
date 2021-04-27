"""
Creates a dashboard app for displaying a stock price with a rolling-average
"""

import datetime
from typing import Tuple

import streamlit as st
from plotly import graph_objects as pgo

from stock_dashboard.stock_info import StockInfo

FXAIX_BASELINE = StockInfo("FXAIX")  # baseline S&P 500 index fund


@st.cache(show_spinner=True, max_entries=10, ttl=300, allow_output_mutation=True)
def get_stock_info_and_history(ticker: str) -> StockInfo:
    """Get the daily historical adjusted price for a stock

    Use caching to speed-up this process. By default, cache is maintained for up to the
    10 most recent function calls. Also, all cached items will expire after 300 seconds.

    Note, the returned objects should not mutate. If the cached objects are mutated
    after this function call, there will be a CachedObjectMutationWarning.
    """
    return StockInfo(ticker)
    prices_all = info_obj.prices

    # add additional columns to prices (i.e. rolling average)
    prices_all["rolling_a"] = info_obj.rolling_average(10)
    prices_all["rolling_b"] = info_obj.rolling_average(20)

    return info_obj.ticker_obj.info, prices_all


def sidebar_get_date_range() -> Tuple[datetime.date, datetime.date]:
    """Get the start and end dates in the date range to display

    These widgest will be displayed in the sidebar. The resultant start/end
    dates selected with this widget is then returned, rather than the widget values
    themselves.
    """
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

    if start_day_count == "Custom":
        # if "custom" selected, then display a date range option widgets
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
        # If a typical value is selected, calculated the date range
        start_date = end_date - datetime.timedelta(days=start_day_count)

    return start_date, end_date


def purchase_history():
    date_col, price_col, share_col, beat_col = st.beta_columns(4)
    date_col.text("Purchase Date")
    price_col.text("Price/Share")
    share_col.text("Number of Shares")
    beat_col.text("S&P 500 Beat")
    purchase_date = date_col.date_input(
        label="",
        min_value=datetime.date(1900, 1, 1),
        max_value=datetime.datetime.today().date(),
        value=datetime.datetime.today().date(),
    )
    price_per_share = price_col.number_input(
        label="", min_value=0.0, value=0.0, step=0.000001
    )
    n_shares = share_col.number_input(label="", min_value=0, value=0, step=1)

    if purchase_date and price_per_share and n_shares:
        beat_col.write("100")


def run_main():
    """Main method for dashboard to assemble all the pieces of the dashboard"""
    st.title("Stock Analysis")

    # Add a text widget for selecting the stock ticker to display
    ticker = st.text_input(label="Ticker")

    start_date, end_date = sidebar_get_date_range()

    # make a plot of what we need to show
    if ticker:
        start, stop = str(start_date), str(end_date)
        # get stock prices for the desired date range
        stock_info = get_stock_info_and_history(ticker)

        # Display some basic stock information to the dashboard
        st.write(f"{stock_info.ticker_obj.info['longName']}")
        dividend_yield = stock_info.get_annual_dividend_yield()
        if dividend_yield:
            st.write(f"Annual Dividend Yield: {dividend_yield*100:.2f}%")
        else:
            st.write("Annual Dividend Yield: None")

        # calculate the growth relative to the baseline
        stock_growth = stock_info.calculate_growth(start, stop)
        baseline_growth = FXAIX_BASELINE.calculate_growth(start, stop)
        sg_col, bl_col, beat_col = st.beta_columns(3)
        sg_col.text("Stock Growth")
        sg_col.write(f"{stock_growth*100:.2f}%")
        bl_col.text("S&P 500 Growth")
        bl_col.write(f"{baseline_growth*100:.2f}%")
        beat_col.text("Beat")
        beat_col.write(f"{(stock_growth - baseline_growth)*100:.2f}%")

        # create the figure object in plotly for plotting the prices to the dashboard
        prices = stock_info.get_sub_prices_by_day(start, stop)
        fig = pgo.Figure(layout={"hovermode": "x unified"})
        fig.add_trace(
            pgo.Scatter(x=prices.index, y=prices["Close"], mode="lines", name="price",)
        )
        fig.add_trace(
            pgo.Scatter(
                x=prices.index,
                y=stock_info.rolling_average(10)[prices.index],
                mode="lines",
                name="10-day Average",
            )
        )
        fig.add_trace(
            pgo.Scatter(
                x=prices.index,
                y=stock_info.rolling_average(20)[prices.index],
                mode="lines",
                name="20-day Average",
            )
        )

        # calculate bollinger bands
        bollinger_bands = stock_info.bollinger_bands().loc[prices.index]
        fig.add_trace(
            pgo.Scatter(
                x=bollinger_bands.index,
                y=bollinger_bands["bollinger_upper"],
                mode="lines",
                name="bollinger_lower",
            )
        )
        fig.add_trace(
            pgo.Scatter(
                x=bollinger_bands.index,
                y=bollinger_bands["bollinger_lower"],
                mode="lines",
                name="bollinger_upper",
                fill="tonexty",
            )
        )
        st.write(fig)  # write it to streamlit


if __name__ == "__main__":
    # this is re-run every-time a widget's value changes in streamlit
    run_main()
