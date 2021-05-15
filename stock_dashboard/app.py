"""
Creates a dashboard app for displaying a stock price with a rolling-average
"""

import datetime
from typing import Tuple

import streamlit as st
import pandas as pd
from plotly import graph_objects as pgo

from stock_dashboard.stock_info import StockInfo

st.set_page_config(layout="wide")


class StockPlot:
    def __init__(self):
        self.fig = pgo.Figure(layout={"hovermode": "x unified"})

    def add_line(self, x: pd.Series, y: pd.Series, name: str, color=None, dash=False):
        self.fig.add_trace(
            pgo.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=name,
                line_color=color,
                line_dash="dash" if dash else None,
            )
        )

    def add_band(
        self, x: pd.Series, y1: pd.Series, y2: pd.Series, name: str, color=None,
    ):
        line1 = pgo.Scatter(x=x, y=y1, mode="lines", name=name, line_color=color)
        line2 = pgo.Scatter(
            x=x, y=y2, mode="lines", name=name, line=line1.line, fill="tonexty"
        )
        self.fig.add_traces([line1, line2])


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
    prices_all["rolling_a"] = info_obj.rolcolumnss_all


def sidebar_set_baseline() -> StockInfo:
    """Set a stock for baseline-comparisons, e.g. FXAIX for S&P500 comparison"""
    selection_map = {"S&P500 (FXAIX)": "FXAIX", "Taiwan High-Div(0056.TW)": "0056.TW"}
    selection = st.sidebar.selectbox("Baseline", list(selection_map.keys()))
    return StockInfo(selection_map[selection])


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


def purchase_history(stock: StockInfo, baseline: StockInfo):
    """Add a calculator to determine gains from historical purchase

    Args:
        stock: The stock to calculate purchase history for
        baseline: The baseline security to comjpare the stock to.
    """
    # set up 4 columns for each field
    date_col, price_col, reinvest_col, beat_col = st.beta_columns([1, 1.5, 0.5, 1])
    date_col.text("Purchase Date")
    price_col.text("Price/Share")
    reinvest_col.text("Reinvest")
    beat_col.text("Growth")

    # get input from user on purhcase date, price and reinvestment or not
    purchase_date = date_col.date_input(
        label="",
        min_value=datetime.date(1900, 1, 1),
        max_value=datetime.datetime.today().date(),
        value=datetime.datetime.today().date(),
    )
    price_per_share = price_col.number_input(
        label="", min_value=0.01, value=0.01, step=0.000001
    )
    reinvest = reinvest_col.radio("", [True, False], index=1)

    # calculate the growth of the stock and the baseline security
    growth = stock.calculate_growth(
        str(purchase_date),
        str(datetime.datetime.today().date()),
        reinvest=reinvest,
        initial_price=price_per_share,
    )
    base_growth = baseline.calculate_growth(
        str(purchase_date),
        str(datetime.datetime.today().date()),
        reinvest=True,  # typical for mutual funds
    )

    # output the calculated growth
    beat_col.text(f"stock: {growth*100:.2f}%")
    beat_col.text(f"beat: {(growth-base_growth)*100:.2f}%")


def run_main():
    """Main method for dashboard to assemble all the pieces of the dashboard"""
    st.title("Stock Analysis")

    # Add a text widget for selecting the stock ticker to display
    ticker = st.text_input(label="Ticker")

    baseline = sidebar_set_baseline()
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
        baseline_growth = baseline.calculate_growth(start, stop)
        sg_col, bl_col, beat_col = st.beta_columns(3)
        sg_col.text("Stock Growth")
        sg_col.write(f"{stock_growth*100:.2f}%")
        bl_col.text("Baseline Growth")
        bl_col.write(f"{baseline_growth*100:.2f}%")
        beat_col.text("Beat")
        beat_col.write(f"{(stock_growth - baseline_growth)*100:.2f}%")

        # create the figure object in plotly for plotting the prices to the dashboard
        prices = stock_info.get_sub_prices_by_day(start, stop)
        bollinger_bands = stock_info.bollinger_bands().loc[prices.index]

        plotter = StockPlot()
        plotter.add_line(prices.index, prices["Close"], name="price")
        plotter.add_line(
            prices.index,
            stock_info.rolling_average(10)[prices.index],
            "10-day Average",
            dash=True,
        )
        plotter.add_line(
            prices.index,
            stock_info.rolling_average(20)[prices.index],
            "20-day Average",
            dash=True,
        )
        plotter.add_band(
            bollinger_bands.index,
            bollinger_bands["bollinger_upper"],
            bollinger_bands["bollinger_lower"],
            name="bollinger",
            color="green",
        )

        st.plotly_chart(plotter.fig, use_container_width=True)  # write it to streamlit

        # add option to calculate custom stock-price
        purchase_history(stock_info, baseline)


if __name__ == "__main__":
    # this is re-run every-time a widget's value changes in streamlit
    run_main()
