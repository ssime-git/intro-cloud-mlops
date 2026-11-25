.PHONY: up down reset step reset-step reset-all chown shell console logs wait test

CONSOLE_URL := http://localhost:4566/_floci/ui

# Images Floci starts on demand (EC2 instance, Lambda runtime, web console):
# pulled up front so the first launch does not wait on the network.
PREPULL_IMAGES := public.ecr.aws/amazonlinux/amazonlinux:2023 \
                  public.ecr.aws/lambda/python:3.12 \
                  floci/floci-ui:0.7.0

# Step number of the current branch (step-3-s3-role -> 3; main -> 5).
BRANCH := $(shell git rev-parse --abbrev-ref HEAD 2>/dev/null)
STEP_N := $(or $(shell echo $(BRANCH) | sed -n 's/^step-\([0-9]\).*/\1/p'),5)

up:
	@for img in $(PREPULL_IMAGES); do docker image inspect $$img >/dev/null 2>&1 || docker pull $$img; done
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

# Work terminal inside the runner: every tutorial command is typed here.
shell:
	docker compose exec runner bash

# Opens the Floci web console (first open starts the console container on :4500).
console:
	@if command -v open >/dev/null 2>&1; then open $(CONSOLE_URL); \
	elif command -v xdg-open >/dev/null 2>&1; then xdg-open $(CONSOLE_URL); \
	else echo "Open $(CONSOLE_URL) in your browser"; fi

logs:
	docker compose logs -f floci

test:
	docker compose exec -T runner uv run pytest -q

# Files created from the runner are owned by root on a Linux host: hand them
# back to the user before git touches them.
chown:
	@docker compose exec -T runner chown -R $$(id -u):$$(id -g) /work 2>/dev/null || true

# Go to another step branch. Usage: make step S=step-3-s3-role
# What you created in Floci is kept; lab/ (git-ignored) is kept too.
step: chown
	@test -n "$(S)" || { echo "usage: make step S=<branch>"; exit 1; }
	git checkout $(S)

# Start the current step again from scratch: fresh Floci, an empty lab/, and
# what the previous steps created recreated (scripts/setup-step.sh).
reset-step: chown
	rm -rf lab
	$(MAKE) down
	$(MAKE) up
	docker compose exec -T runner bash scripts/setup-step.sh $(STEP_N)

# Everything from zero: stop and remove all containers, back to step-0-start,
# remove what you created during the tutorials (lab/). Then `make up`.
reset-all: chown
	$(MAKE) down
	rm -rf lab
	git checkout step-0-start
	@echo "Back to step-0-start with a clean environment. Next: make up"

reset:
	$(MAKE) down
	$(MAKE) up

# Floci starts sibling containers (EC2 instances, Lambda runtimes, the console)
# that compose does not know about: remove them too, then the networks.
down:
	-@docker ps -aq --filter label=io.floci=aws | xargs -r docker rm -f >/dev/null
	docker compose down -v --remove-orphans
	-@docker network ls -q --filter label=io.floci=aws | xargs -r docker network rm >/dev/null 2>&1
