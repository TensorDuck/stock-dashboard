import pandas as pd
import streamlit as st
from plotly import graph_objects as pgo


class StockPlot:
    def __init__(self):
        self.fig = pgo.Figure(layout={"hovermode": "x unified"})

    def add_line(
        self,
        x: pd.Series,
        y: pd.Series,
        name: str,
        color: str = None,
        dash: bool = False,
    ):
        """Add a line plot

        Args:
            x: The x-values
            y: The y-values
            name: The name of the trace.
            color: The color of the line
            dash: Set to true if line is a dashed line

        """
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
        """ Add a filled-area plot between y2 and y1

        Args:
            x: The x-values
            y1: the lower values of the band.
            y2: The upper values of the band.
            name: Name of the trace.
            Color: color of the line
        """
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

    def add_multi_bar_plots(
        self,
        x: pd.Series,
        y1: pd.Series,
        y2: pd.Series,
        name: str,
        greater_color: str = "rgba(0, 255, 0, 0.5)",
        lesser_color: str = "rgba(255, 0, 0, 0.5)",
    ):
        """Add a histogram where the color is different for y2 > y1 and y2 < y1

        See self.add_bar_plots(). Takes diff = y2-y1, and plots different colors for
        positive and negative diffs.

        Args:
            x: values to bin along
            y1: first value
            y2: second value
            name: The name of both traces
            greater_color: The color for positive diff
            lesser_color: The color for negative diff
        """
        greater = y2 >= y1
        diff = y2 - y1

        self.add_bar_plots(
            x[greater], diff[greater], f"> {name}", color=greater_color,
        )
        self.add_bar_plots(
            x[~greater], diff[~greater], f"< {name}", color=lesser_color,
        )

    def add_bar_plots(
        self,
        x: pd.Series,
        y: pd.Series,
        name: str,
        color: str = "rgba(0, 255, 0, 0.5)",
    ):
        """Add a histogram along x, with heights of the bins from y

        The spacing of the bins is such that there is one value for each bin. The bin
        size is automatically determined to be the minimum spacing value in x.

        Args:
            x: values to bin along
            y: values to use for calculating height of the bins
            name: The name of the trace,
            color: The color of the bar plot
        """
        spacing = min(x.to_series().diff().dropna())
        self.fig.add_traces(
            pgo.Histogram(
                x=x,
                y=y,
                histfunc="sum",
                name=name,
                xbins={
                    "start": min(x) - (spacing / 2),
                    "end": max(x) + (spacing / 2),
                    "size": spacing,
                },  # bins used for histogram
                marker_color=color,
                autobinx=False,
            )
        )

        self.fig.update_layout(barmode="overlay")
