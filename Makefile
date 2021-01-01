.PHONY: build, start, stop, dev-start, lint, gcp-upload

-include .env

#note, containing grc.io tells docker push what address to push the image to
CONTAINER_NAME=stock-dashboard

build:
	docker build -f Dockerfile -t $(CONTAINER_NAME):latest .

start: build
	docker run --rm -p 8080:8080 --name $(CONTAINER_NAME) -dt $(CONTAINER_NAME):latest

stop:
	docker stop $(CONTAINER_NAME)

dev-start:
	streamlit run stock_dashboard/app.py

lint:
	black stock_dashboard
	isort stock_dashboard

gcp-upload:
	gcloud app deploy app.yml