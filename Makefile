.PHONY: install test format run lint docker-build docker-run docker-test all

install:
	pip install --upgrade pip &&\
		pip install -r requirements.txt

test:
	pytest -vv --cov=mgfhub --cov=core --cov=utils --cov=pages tests/test_*.py

test-cov:
	pytest -vv --cov=mgfhub --cov=core --cov=utils --cov=pages tests/test_*.py --cov-report term-missing

format:
	black . *.py core/*.py utils/*.py pages/*.py tests/*.py

run:
	streamlit run mgfhub.py

lint:
	pylint --disable=R,C,W0622 *.py core/*.py monitor/*.py utils/*.py pages/*.py tests/*.py

docker-build:
	docker build -t mgfhub .

docker-run:
	docker run -d --name test-container -p 8501:8501 mgfhub

docker-test:
	sleep 10  # give the app some time to start
	curl --fail http://localhost:8501/_stcore/health
	docker stop test-container

all: install lint test format

docker: docker-build docker-run docker-test

all-docker: install test format run lint docker-build docker-run docker-test
