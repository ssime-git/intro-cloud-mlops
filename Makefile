.PHONY: up down logs wait demo1 demo2 floci-iam-on floci-iam-off \
        test notebook-setup notebook notebook-test clean

up:
	docker compose up -d --build
	$(MAKE) wait
	docker compose exec -T runner uv sync --all-groups

wait:
	@echo "Waiting for Floci to be ready..."
	@for i in $$(seq 1 60); do \
		docker compose exec -T runner python -c "import urllib.request as u; u.urlopen('http://floci:4566/_floci/health')" 2>/dev/null && exit 0; \
		sleep 2; \
	done; \
	echo "Floci did not become ready within 120s" >&2; exit 1
	@echo "Floci is up."

logs:
	docker compose logs -f floci

floci-iam-on:
	FLOCI_IAM_ENFORCEMENT=true docker compose up -d floci
	$(MAKE) wait

floci-iam-off:
	FLOCI_IAM_ENFORCEMENT=false docker compose up -d floci
	$(MAKE) wait

demo1:
	docker compose exec -T runner uv run python demos/01-s3-lambda-notification/deploy.py
	docker compose exec -T runner uv run python demos/01-s3-lambda-notification/trigger_and_wait.py

demo2: floci-iam-on
	docker compose exec -T runner uv run python demos/02-iam-policy-enforcement/run_demo.py

test:
	docker compose exec -T runner uv run pytest -q

# Registers a Jupyter kernel for this uv-managed venv. Needed once per
# container lifetime (kernelspecs live in the container's home dir, which
# is not bind-mounted and is recreated with the container).
notebook-setup:
	docker compose exec -T runner uv run python -m ipykernel install --user \
		--name intro-cloud-mlops --display-name "Python (intro-cloud-mlops, uv)"

# Opens the masterclass walkthrough in Euporie's terminal UI, live against
# whatever Floci mode is currently running (plain, or IAM-enforced after
# `make floci-iam-on`).
notebook: notebook-setup
	docker compose exec -it runner uv run euporie-notebook notebook/masterclass_demo.ipynb

# Headless regression check: executes every cell and fails on the first
# error. Requires IAM enforcement to be on for the demo 2 cells to behave
# as documented.
notebook-test: floci-iam-on notebook-setup
	docker compose exec -T runner uv run jupyter execute notebook/masterclass_demo.ipynb

down:
	docker compose down -v

clean: down
	rm -f demos/01-s3-lambda-notification/predict.zip
