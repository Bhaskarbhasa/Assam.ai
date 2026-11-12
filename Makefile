.PHONY: all test test-p1 test-p2 p1-demo p2-demo p2-cli dashboard run-api

all: test

install:
	pip install -r requirements.txt

test: test-p1 test-p2

test-p1:
	python -m pytest problem1_agent_social_network/tests -v

test-p2:
	python -m pytest problem2_linux_hardware_assistant/tests -v

p1-demo:
	python problem1_agent_social_network/demo_simulator.py

p2-demo:
	python problem2_linux_hardware_assistant/demo_queries.py

p2-cli:
	python problem2_linux_hardware_assistant/app/cli.py

run-api:
	uvicorn app.main:app --reload --app-dir problem1_agent_social_network --port 8000

dashboard:
	streamlit run web_dashboard/app.py
