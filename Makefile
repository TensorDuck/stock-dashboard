.PHONY: build, start, stop, lint

-include .env

#note, containing grc.io tells docker push what address to push the image to
CONTAINER_NAME=stock-dashboard

build:
	docker build -f Dockerfile -t $(CONTAINER_NAME):latest .

start: build
	docker run -p 8501:8501 --name $(CONTAINER_NAME) -dt $(CONTAINER_NAME):latest

stop:
	docker stop $(CONTAINER_NAME)

dev-start:
	streamlit run stock_dashboard/app.py

lint:
	black stock_dashboard
	isort stock_dashboard