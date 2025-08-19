.PHONY: data optimise visualise all clean

data:
	python scripts/fetch_data.py --config config.yaml

optimise:
	python scripts/optimise.py --config config.yaml

visualise:
	python scripts/visualise.py --config config.yaml

all: data optimise visualise

clean:
	rm -rf data/* output/*
