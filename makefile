REMOTE_IMAGE_REPO:=klopezva/exchange_server

all: clean dependencies

venv:
	if [ ! -d ./env ]; then python -m venv ./env; fi

dependencies: venv
	source ./env/bin/activate && pip install --upgrade pip && \
		python -m pip install .

clean:
	rm -rf ./env;
	rm -rf ./exchange/*.pyc;

build:
	docker build -t exchange_server .

push:
	docker image tag exchange_server $(REMOTE_IMAGE_REPO)
	docker image push $(REMOTE_IMAGE_REPO)

publish: build push
