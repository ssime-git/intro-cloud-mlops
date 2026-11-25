# Intro to the cloud for ML engineers

We take a small scoring script that runs on a laptop and move it to the cloud in four steps. Each step brings in a new AWS service because the previous step has a concrete problem. Everything runs locally on [Floci](https://github.com/floci-io/floci), an AWS emulator: no AWS account, nothing to pay.

```
v0  laptop          score.py reads customers.csv from the disk
v1  EC2             same script, on a rented machine
v2  EC2 + S3 + role the data leaves the machine
v3  S3 → Lambda     no machine: the file triggers the computation
```

The ML code never changes: it is always the same `add_predictions()` function in `scoring/score.py`.

## Prerequisites

- Docker
- `make` and `git`

Nothing else to install: the AWS CLI, Python and boto3 run in a container.

## How to use this repo

You work in **two terminals**:

| Terminal | How to open it | What you type there |
|---|---|---|
| **Your machine** | any terminal, in the repo folder | `make ...` and `git` commands only |
| **Work terminal** | `make shell` (from your machine) | every `aws`, `python`, `ssh` command of the tutorials |

The work terminal is a container with the AWS CLI. Its folder `/work` **is** your repo folder: a file created there appears in your repo, and the other way round.

The steps, once:

```bash
git clone https://github.com/ssime-git/intro-cloud-mlops.git
```

```bash
cd intro-cloud-mlops
```

```bash
make up
```

Then, **before each tutorial**, on your machine, go to that tutorial's branch and open the work terminal:

```bash
make step S=step-0-start
```

```bash
make shell
```

- Each branch holds the repo as it is at the start of that tutorial: it adds the files the tutorial needs. Switching branch keeps everything you created in Floci (users, instances, buckets).
- What you create goes into `lab/` (keys, policies). Git ignores this folder: nothing you type ends up in a commit, and switching branch never conflicts with it.
- Starting a tutorial without the previous ones, or doing it again: run `make reset-step` after `make step`. It restarts Floci from scratch and recreates what the previous tutorials left behind.
- At the end: `make reset-all` removes everything and brings you back to `step-0-start`.

## Tutorials

| # | Tutorial | Branch |
|---|---|---|
| 0 | [Start your local AWS](docs/00-getting-started.md) | `step-0-start` |
| 1 | [A user, a denial, a policy](docs/01-identity.md) | `step-1-identity` |
| 2 | [Rent a machine (EC2)](docs/02-ec2.md) | `step-2-ec2` |
| 3 | [Data leaves the machine, the machine gets a role](docs/03-s3-and-role.md) | `step-3-s3-role` |
| 4 | [No more machine: S3 triggers Lambda](docs/04-lambda.md) | `step-4-lambda` |
| 5 | [The final architecture, and starting over](docs/05-final-architecture.md) | `step-5-final` |

## Make commands (on your machine)

| Command | What it does |
|---|---|
| `make up` | starts Floci and the work terminal container |
| `make shell` | opens the work terminal |
| `make console` | opens the Floci web console (http://localhost:4566/_floci/ui) |
| `make step S=<branch>` | switches to a tutorial's branch |
| `make reset-step` | starts the current tutorial again from scratch (recreates `lab/` and the resources of the previous tutorials) |
| `make reset-all` | removes everything, back to `step-0-start` |
| `make down` | stops and removes all containers |

## What is in the repo

```
scoring/score.py      the scoring script (add_predictions)
scoring/install.sh    installs the AWS CLI on an EC2 instance at boot
data/customers.csv    the data
pipeline/             deploy.py (S3 → Lambda) and handler.py
infra/main.tf         the same infrastructure in Terraform (to read)
scripts/              setup-step.sh, used by make reset-step
lab/                  (created by you, git-ignored) your keys and policies
docs/                 the tutorials
```

## Floci vs real AWS

The commands are the real AWS ones. A few differences, pointed out in the tutorials:

- EC2 instances are Docker containers, reachable directly on their private IP;
- `scoring/install.sh` points the instance's AWS CLI at Floci: remove that part on a real EC2 instance;
- Lambda logs only contain what the code prints, without the `START`/`REPORT` lines;
- the Floci console has no authentication: it only listens on `127.0.0.1`.
