# intro-cloud-mlops

Demos for an AWS/MLOps masterclass using [Floci](https://github.com/floci-io/floci), a local AWS emulator (open-source alternative to LocalStack), driven entirely through Docker containers — nothing is installed on the host machine.

## Why Floci?

Floci runs locally, for free, and exposes an AWS-compatible API (S3, Lambda, IAM, DynamoDB, etc.) on `http://localhost:4566`. It lets you demonstrate cloud architectures (event-driven, IAM, serverless) without an AWS account or any cost.

## Prerequisites

- Docker (tested with [OrbStack](https://orbstack.dev/) on macOS, but any Docker engine works)
- `make`
- [`gh`](https://cli.github.com/) only if you republish this repo

No other tool is required on the host machine: Python, boto3 and zip all run inside containers.

## Quick start

```bash
make up          # start Floci + the Python runner container (boto3)
make demo1        # demo 1: S3 -> Lambda notification
make demo2        # demo 2: IAM policy enforcement
make down         # stop and clean up everything (containers, network)
```

## Structure

```
.
├── docker-compose.yml          # Floci + runner container (python:3.12-slim + boto3)
├── Makefile                    # up/down/demo1/demo2/test/logs/clean targets
├── demos/
│   ├── 01-s3-lambda-notification/   # S3 upload -> automatic Lambda trigger
│   └── 02-iam-policy-enforcement/   # IAM deny/allow with policies
└── tests/                      # unit tests (CSV transform, no S3/Floci needed)
```

Each demo has its own `README.md` with a step-by-step walkthrough and expected output.

## Demo 1 — S3 → Lambda notification

A Python 3.12 Lambda (`predict`) is automatically triggered when a CSV is uploaded under `in/` in the `demo` bucket. It adds a `prediction` column (1 if `score > 0.5`, else 0) and writes the result under `out/`.

See [demos/01-s3-lambda-notification/README.md](demos/01-s3-lambda-notification/README.md).

## Demo 2 — IAM policy enforcement

Demonstrates that Floci actually enforces IAM policies when `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true`: a `junior` user with no permissions is denied `s3:ListAllMyBuckets` (403 `AccessDenied`), then allowed once an inline policy is attached.

See [demos/02-iam-policy-enforcement/README.md](demos/02-iam-policy-enforcement/README.md).

## Security

The Floci container is given `/var/run/docker.sock` as a volume mount, running as `user: root`, so it can launch the Lambda runtime containers itself (sibling-container pattern). This effectively grants it root access to the Docker host. This is required to emulate Lambda, but should be kept to local/demo use with a trusted image only — never in a shared or exposed environment. For this reason port 4566 is also bound to `127.0.0.1` only.

## Notes / differences from real AWS

- IAM policy enforcement is **disabled by default** in Floci — without the `FLOCI_SERVICES_IAM_ENFORCEMENT_ENABLED=true` flag, everything is allowed regardless of the caller's identity.
- The first Lambda trigger is slower (~30s) because Floci pulls the `public.ecr.aws/lambda/python:3.12` runtime image; subsequent triggers are fast.
- IAM policy propagation is instantaneous in Floci, whereas real AWS can introduce a short delay.

## License

MIT — see [LICENSE](LICENSE).
