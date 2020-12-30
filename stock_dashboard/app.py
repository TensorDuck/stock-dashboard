import streamlit as st
import yfinance
import datetime

import plotly.graph_objects as pgo


def get_stock_info_and_history(ticker: str):
    """Get the daily historical adjusted price for a stock"""
    ticker_obj = yfinance.Ticker(ticker)
    return ticker_obj.info, ticker_obj.history(period="max")


def run_main():
    """Main method for dashboard to assemble all the pieces of the dashboard"""
    st.title("Stock Analysis")

    # Widgets
    # these show up in the main bar
    ticker = st.text_input(label="Ticker")
    # these show up in the side bar
    oldest_date = st.sidebar.date_input(
        label="Oldest Date",
        min_value=datetime.date(1900, 1, 1),
        max_value=datetime.datetime.today().date() - datetime.timedelta(days=1),
        value=datetime.datetime.today().date() - datetime.timedelta(days=30),
    )

    # make a plot of what we need to show
    if ticker:
        # get stock prices for the desired date range
        stock_info, prices_all = get_stock_info_and_history(ticker)
        prices_all["rolling_a"] = prices_all["Close"].rolling(10).mean()
        prices_all["rolling_b"] = prices_all["Close"].rolling(20).mean()

        prices = prices_all[prices_all.index >= str(oldest_date)]

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
