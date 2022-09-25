
all: clean dependencies

venv:
	if [ ! -d ./env ]; then python -m venv ./env; fi

dependencies: venv
	source ./env/bin/activate && pip install --upgrade pip && \
		python -m pip install -e .

clean:
	rm -rf ./env;
	rm -rf ./exchange/*.pyc;
