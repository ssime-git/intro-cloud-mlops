# intro-cloud-mlops

Demos for an AWS/MLOps masterclass using [Floci](https://github.com/floci-io/floci), a local AWS emulator (open-source alternative to LocalStack), driven entirely through Docker containers — nothing is installed on the host machine. Dependencies inside the containers are managed with [uv](https://docs.astral.sh/uv/).

## Why Floci?

Floci runs locally, for free, and exposes an AWS-compatible API (S3, Lambda, IAM, DynamoDB, etc.) on `http://localhost:4566`. It lets you demonstrate cloud architectures (event-driven, IAM, serverless) without an AWS account or any cost.

## Prerequisites

- Docker (tested with [OrbStack](https://orbstack.dev/) on macOS, but any Docker engine works)
- `make`
- [`gh`](https://cli.github.com/) only if you republish this repo

No other tool is required on the host machine: Python, uv, boto3 and Euporie all run inside containers, resolved from `uv.lock`.

## Quick start

```bash
make up          # build the runner image (uv sync), start Floci + runner
make demo1        # demo 1: S3 -> Lambda notification
make demo2        # demo 2: IAM policy enforcement
make notebook      # live, step-by-step walkthrough of both demos (Euporie)
make down         # stop and clean up everything (containers, network)
```

## Structure

```
.
├── Dockerfile                  # runner image: uv + Python 3.12, deps from uv.lock
├── pyproject.toml / uv.lock     # dependency manifest, resolved & locked with uv
├── docker-compose.yml          # Floci + runner container
├── Makefile                    # up/down/demo1/demo2/notebook/test/clean targets
├── demos/
│   ├── 01-s3-lambda-notification/   # S3 upload -> automatic Lambda trigger
│   └── 02-iam-policy-enforcement/   # IAM deny/allow with policies
├── notebook/                   # Euporie notebook for live presentation
└── tests/                      # unit tests (CSV transform, no S3/Floci needed)
```

Each demo has its own `README.md` with a step-by-step walkthrough and expected output.

## Demo 1 — S3 → Lambda notification

A Python 3.12 Lambda (`predict`) is automatically triggered when a CSV is uploaded under `in/` in the `demo` bucket. It adds a `prediction` column (1 if `score > 0.5`, else 0) and writes the result under `out/`.

See [demos/01-s3-lambda-notification/README.md](demos/01-s3-lambda-notification/README.md).

## Demo 2 — IAM policy enforcement

Demonstrates that Floci actually enforces IAM policies when `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true`: a `junior` user with no permissions is denied `s3:ListAllMyBuckets` (403 `AccessDenied`), then allowed once an inline policy is attached.

See [demos/02-iam-policy-enforcement/README.md](demos/02-iam-policy-enforcement/README.md).

## Live walkthrough notebook (Euporie)

[`notebook/masterclass_demo.ipynb`](notebook/masterclass_demo.ipynb) drives both demos as a terminal Jupyter notebook, one AWS call per cell — no `deploy.py`/`run_demo.py` black boxes, so every mechanism (IAM role, least-privilege policy, permission, event notification, IAM deny/allow) is visible and can be run, discussed, and re-run live during the masterclass.

```bash
make up
make notebook
```

`make notebook` registers a Jupyter kernel for the uv-managed venv and opens the notebook in [Euporie](https://github.com/joouha/euporie)'s terminal UI. Demo 2's cells need Floci restarted with IAM enforcement first — run `make floci-iam-on` in another terminal before reaching that section (instructions are also in the notebook itself).

To sanity-check the whole notebook non-interactively (e.g. after editing it):

```bash
make notebook-test
```

## Dependency management (uv)

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`, split into groups:

- base (`boto3`) — what the demo scripts need
- `dev` (`pytest`, `ruff`, `nbclient`) — testing and linting
- `notebook` (`euporie`, `ipykernel`, `jupyter-client`) — the live walkthrough

The runner image installs all groups at build time (`uv sync --frozen --all-groups`) into `/opt/venv`, kept outside the bind-mounted repo so the Linux venv never leaks onto the host filesystem. `make up` re-runs `uv sync` after starting the containers, so editing `pyproject.toml` and re-running `make up` picks up new dependencies without a full rebuild. To add a dependency yourself, edit `pyproject.toml` and run `uv lock` (from a container, e.g. `docker compose exec runner uv lock`, or with `uv` installed locally) to update `uv.lock`, then commit both files.

## Security

The Floci container is given `/var/run/docker.sock` as a volume mount, running as `user: root`, so it can launch the Lambda runtime containers itself (sibling-container pattern). This effectively grants it root access to the Docker host. This is required to emulate Lambda, but should be kept to local/demo use with a trusted image only — never in a shared or exposed environment. For this reason port 4566 is also bound to `127.0.0.1` only.

## Notes / differences from real AWS

- IAM policy enforcement is **disabled by default** in Floci — without the `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true` flag, everything is allowed regardless of the caller's identity.
- The first Lambda trigger is slower (~30s) because Floci pulls the `public.ecr.aws/lambda/python:3.12` runtime image; subsequent triggers are fast.
- IAM policy propagation is instantaneous in Floci, whereas real AWS can introduce a short delay.

## License

MIT — see [LICENSE](LICENSE).
