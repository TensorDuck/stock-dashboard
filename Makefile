.PHONY: build, start, stop, dev-start, lint, gcp-upload

-include .env

#note, containing grc.io tells docker push what address to push the image to
CONTAINER_NAME=stock-dashboard
VERSION=0.1.0
DOCKER_HUB_NAME=tensorduck/$(CONTAINER_NAME)

build:
	docker build -f Dockerfile -t $(CONTAINER_NAME):latest .

release: build
	docker tag $(CONTAINER_NAME):latest $(DOCKER_HUB_NAME):latest
	docker push $(DOCKER_HUB_NAME):latest
	docker tag $(CONTAINER_NAME):latest $(DOCKER_HUB_NAME):$(VERSION)
	docker push $(DOCKER_HUB_NAME):$(VERSION)

docker-hub-start:
	docker pull $(DOCKER_HUB_NAME):$(VERSION)
	docker run --rm -p 8080:8080 --name $(CONTAINER_NAME) -dt $(DOCKER_HUB_NAME):$(VERSION)

start: build
	docker run --rm -p 8080:8080 --name $(CONTAINER_NAME) -dt $(CONTAINER_NAME):latest

stop:
	docker stop $(CONTAINER_NAME)

dev-start:
	PYTHONPATH=`pwd` streamlit run stock_dashboard/app.py

lint:
	black stock_dashboard
	isort stock_dashboard

gcp-upload:
	gcloud app deploy app.yml