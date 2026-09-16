.PHONY: up down logs wait demo1 demo2 clean test

up:
	docker compose up -d
	$(MAKE) wait
	docker compose exec -T runner pip install -q -r requirements.txt

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

demo1:
	docker compose exec -T runner python demos/01-s3-lambda-notification/deploy.py
	docker compose exec -T runner python demos/01-s3-lambda-notification/trigger_and_wait.py

demo2:
	FLOCI_IAM_ENFORCEMENT=true docker compose up -d floci
	$(MAKE) wait
	docker compose exec -T runner python demos/02-iam-policy-enforcement/run_demo.py

test:
	docker compose exec -T runner pip install -q -r requirements.txt pytest
	docker compose exec -T runner python -m pytest -q

down:
	docker compose down -v

clean: down
	rm -f demos/01-s3-lambda-notification/predict.zip
