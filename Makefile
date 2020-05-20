.PHONY: clean build init run-test test-report type-check test

PROJECT=newsthreads

which-version:
	@pip --version
	@python3 --version
	@which python3

clean:
	@rm -rf build stubs

init:
	@( \
		echo python3.6 -m venv .env; \
		python3.6 -m venv .env; \
		. .env/bin/activate; \
		echo pip3 install -r requirements.txt; \
		pip3 install -r requirements.txt; \
	)

build: | lint type-check test-report pip-freeze

lint:
	@( \
		if [ -z ${VIRTUAL_ENV} ];\
			then echo "Activating virtual environment";\
			. .env/bin/activate;\
		fi;\
		flake8 ${PROJECT} tests; \
	)

run-test:
	@( \
		if [ -z ${VIRTUAL_ENV} ];\
			then echo "Activating virtual environment";\
			. .env/bin/activate;\
		fi;\
		pytest tests ${PROJECT} --doctest-modules; \
	)

type-check:
	@( \
		if [ -z ${VIRTUAL_ENV} ];\
			then echo "Activating virtual environment";\
			. .env/bin/activate;\
		fi;\
		stubgen -o stubs ${PROJECT}/config.py ${PROJECT}/logging_init.py; \
		mypy --namespace-packages ${PROJECT}; \
	)

test: type-check run-test lint

pip-freeze:
	@( \
		if [ -z ${VIRTUAL_ENV} ];\
			then echo "Activating virtual environment";\
			. .env/bin/activate;\
		fi;\
		pip3 freeze | sort > requirements.freeze.txt; \
	)

test-report:
	@( \
		if [ -z ${VIRTUAL_ENV} ];\
			then echo "Activating virtual environment";\
			. .env/bin/activate;\
		fi;\
		pytest tests --junit-xml=build/test-results.xml; \
	)
