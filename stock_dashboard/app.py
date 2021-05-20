"""
Creates a dashboard app for displaying a stock price with a rolling-average
"""

import datetime
from typing import Tuple

import pandas as pd
import streamlit as st
from plotly import graph_objects as pgo
from streamlit.logger import init_tornado_logs

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

    def add_band_multi_color(
        self,
        x: pd.Series,
        y1: pd.Series,
        y2: pd.Series,
        name: str,
        greater_color: str = "rgba(0, 255, 0, 0.5)",
        lesser_color: str = "rgba(255, 0, 0, 0.5)",
    ):
        greater = y2 >= y1
        y1_greater, y1_lesser = y1.copy(), y1.copy()
        y1_greater[~greater] = y2[~greater]
        y1_lesser[greater] = y2[greater]

        self.add_band(x, y1_greater, y2, f"> {name}", color=greater_color)
        self.add_band(x, y1_lesser, y2, f"< {name}", color=lesser_color)

    def add_band(
        self, x: pd.Series, y1: pd.Series, y2: pd.Series, name: str, color=None,
    ):
        line1 = pgo.Scatter(
            x=x, y=y1, mode="lines", name=name, line_color=color, showlegend=False
        )
        line2 = pgo.Scatter(
            x=x,
            y=y2,
            mode="lines",
            name=name,
            fill="tonexty",
            line_color=color,
            fillcolor=color,
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
    start = str(purchase_date)
    stop = str(datetime.datetime.today().date())
    growth = stock.calculate_growth(
        start, stop, reinvest=reinvest, initial_price=price_per_share,
    )
    beat = stock.calculate_growth(
        start, stop, reinvest=reinvest, initial_price=price_per_share, baseline=baseline
    )
    # output the calculated growth
    if (growth is not None) or (beat is not None):
        beat_col.text(f"stock: {growth*100:.2f}%")
        beat_col.text(f"beat: {(beat)*100:.2f}%")


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
        try:  # handles crypto prices which lack some of these field names
            st.write(f"{stock_info.ticker_obj.info['longName']}")
            dividend_yield = stock_info.get_annual_dividend_yield()
            if dividend_yield:
                st.write(f"Annual Dividend Yield: {dividend_yield*100:.2f}%")
            else:
                st.write("Annual Dividend Yield: None")
        except:
            pass

        # calculate the growth relative to the baseline
        stock_growth = stock_info.calculate_growth(start, stop)
        baseline_growth = baseline.calculate_growth(start, stop)
        stock_beat = stock_info.calculate_growth(start, stop, baseline=baseline)
        if (
            (stock_growth is not None)
            or (baseline_growth is not None)
            or (stock_beat is not None)
        ):
            sg_col, bl_col, beat_col = st.beta_columns(3)
            sg_col.text("Stock Growth")
            sg_col.write(f"{stock_growth*100:.2f}%")
            bl_col.text("Baseline Growth")
            bl_col.write(f"{baseline_growth*100:.2f}%")
            beat_col.text("Beat")
            beat_col.write(f"{(stock_beat)*100:.2f}%")

        # create the figure object in plotly for plotting the prices to the dashboard
        prices = stock_info.get_sub_prices_by_day(start, stop)
        baseline_prices = baseline.get_sub_prices_by_day(start, stop)
        bollinger_bands = stock_info.bollinger_bands().loc[prices.index]

        overlay_plotter = StockPlot()
        overlay_plotter.add_line(
            prices.index, prices["Close"], name="price", color="black"
        )
        overlay_plotter.add_line(
            prices.index,
            stock_info.rolling_average(10)[prices.index],
            "10-day Average",
            dash=True,
        )
        overlay_plotter.add_line(
            prices.index,
            stock_info.rolling_average(20)[prices.index],
            "20-day Average",
            dash=True,
        )
        overlay_plotter.add_band(
            bollinger_bands.index,
            bollinger_bands["bollinger_upper"],
            bollinger_bands["bollinger_lower"],
            name="bollinger",
            color="rgba(0, 255, 0, 0.1)",
        )

        st.plotly_chart(
            overlay_plotter.fig, use_container_width=True
        )  # write it to streamlit

        oscillator_plotter = StockPlot()
        oscillator_plotter.add_line(
            prices.index, [0 for i in prices.index], "", color="black"
        )
        oscillator_plotter.add_line(
            prices.index, prices["percent_change"], "percent_change", color="blue"
        )
        oscillator_plotter.add_band_multi_color(
            prices.index,
            pd.Series([0 for i in range(len(prices.index))], index=prices.index),
            prices["log_percent_change"] - baseline_prices["log_percent_change"],
            name="baseline",
        )
        st.plotly_chart(oscillator_plotter.fig, use_container_width=True)

        # add option to calculate custom stock-price
        purchase_history(stock_info, baseline)


if __name__ == "__main__":
    # this is re-run every-time a widget's value changes in streamlit
    run_main()
