# stock-dashboard

Simple dashboard for looking at stock prices. Computes rolling averages in order
to guess-timate the current trend in the stock's price. Also acts as a simple
streamlit dashboard deployed to GCP app-engine.

For example, comparing a 10-day (D10) rolling average with the 20-day (D20)
rolling average are typical metrics to use. If D10 > D20 indicates an up-trend,
while D10 < D20 indicates a down-trend. The expectation is that when these
values cross-over, then there's a buy or sell point opportunity.

## Prerequisites

You must have docker

## Quickstart

### Using pre-built docker container (linux)

For linux OS, run the command
```
make docker-hub-start
```

This will download the pre-built docker container from DockerHub and then create an
instance of the dashboard at ``http://localhost:8080``.

### Using pre-built docker container (windows)
coming soon

### Build locally with docker

For linux OS, run the command
```
make start
```

Which will build the docker container locally, and then put up an instance of the
dashboard at ``http://localhost:8080`.


### Run locally without docker

This is great for dev-work, but not very stable as it's dependent on your local Python
installation and package installations.

Running the command:

```
make dev-start
```

Will set up a locally running instance on port: ``http://localhost:8501``, the
default port for streamlit. Then enter your desired stock ticker info.

## Deploy to GCP

The `Dockerfile` is set up for deploying to GCP App Engine. By default, App
Engine expects to have port 8080 exposed for the docker container. It also
expects the `Dockerfile` and `app.yml` file to exist in the top-level directory
to work properly.

NOTE: DO NOT ADD SECRETS TO THIS DIRECTORY, EVEN UNCHECKED IN. GCP will upload
the entire directory (including hidden files) and creates a new container on
their server. The result is that any secrets contained (e.g. in `.env`) would
also be baked into the resultant image.

To test what the creation of the docker image for GCP, run:

```
make start
```

Which will create a docker image and route streamlit to port 8080. You can then
test the streamlit instance on `http://localhost:8080`.

## Dev Notes

### Streamlit concepts

Streamlit provides a quick and fast python interface for building an interactive
dashboard that can display almost anything (text, graphs, media). Interactions
with the user is carried out with widgets added to the dashboard. On startup,
streamlit will run through the `__main__` body in `stock_dashboard/app.py`.
Whenever a user interacts with a widget, streamlit will re-run the entire
`__main__` body.

To improve efficiency, cache is used inside streamlit internally with the
`@st.cache()` decorator function. The streamlit cache function is relatively
smart. It will check hasehd input values to the function and only re-run the
function when those input values change. Furthermore, it would double-check that
the output value of the function isn't mutated, and throw a warning if so. Thus,
a common pattern is to move functionality that is expensive to compute and
seldom-required to be recomputed into a function with the cache decorator. For
example, API calls to external servers for static data can be enclosed inside
the cache decorator.

Throughout the code, there are additional comments about basic streamlit functionality
for educational purposes.

### GCP Setup

GCP requires you to set-up your environement before running any `gcloud`
commands. Typically, this is done with the command `gcloud init` to set up your
account and log-in information.

Refer to this demo to get started with initializing GCP on your system:
https://cloud.google.com/sdk/docs/quickstart Refer to this demo to get started
with deploying apps onto GCP:
https://cloud.google.com/appengine/docs/standard/python3/building-app/creating-gcp-project

### Use of plotly

A good combination is to use streamlit to create the widgets, and then plotly to
display the plots. The plotly package provides an interactive plot (e.g.
zoom-in) to make it easier for the user to adjust the plot and display
additional information on hover.