.PHONY: test demo

test:
	python3 -m pytest tests -q

demo:
	python3 -m sourcehunter.demo