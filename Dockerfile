# Runner image for the demos: uv + Python 3.12, dependencies locked via uv.lock,
# plus AWS CLI v2, an SSH client and curl for the hands-on steps.
# Based on Astral's official combined image (recommended way to use uv in Docker).
FROM ghcr.io/astral-sh/uv:0.9.30-python3.12-bookworm-slim

# AWS CLI v2 (official zip, needed for `aws logs tail`), ssh/scp to reach the
# EC2 instances, curl, and less/groff so `aws ... help` works.
RUN apt-get update \
 && apt-get install -y --no-install-recommends curl unzip openssh-client less groff-base ca-certificates \
 && curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-$(uname -m).zip" -o /tmp/awscliv2.zip \
 && unzip -q /tmp/awscliv2.zip -d /tmp \
 && /tmp/aws/install \
 && rm -rf /tmp/aws /tmp/awscliv2.zip /var/lib/apt/lists/*

# Floci reuses private IPs from one EC2 instance to the next: skip host-key
# pinning (the runner only ever SSHes to Floci instances, whatever the Docker
# subnet: 172.x, 192.168.x...), otherwise the second `ssh` to a reused IP fails
# with "REMOTE HOST IDENTIFICATION HAS CHANGED".
# On real AWS, keep host-key checking on.
RUN printf 'Host *\n  StrictHostKeyChecking no\n  UserKnownHostsFile /dev/null\n  LogLevel ERROR\n' \
      > /etc/ssh/ssh_config.d/floci.conf

# Keep the virtualenv outside the bind-mounted /work directory: the repo is
# mounted read-write from the host at runtime (see docker-compose.yml), so a
# venv built for Linux must not live where a macOS/Windows host could see or
# clobber it. UV_LINK_MODE=copy avoids hardlink warnings on mounted volumes.
ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_LINK_MODE=copy \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /work

# Install dependencies from the lockfile only, in a layer that is cached as
# long as pyproject.toml/uv.lock don't change (source code changes below
# won't invalidate this layer or force a re-resolve).
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --all-groups --no-install-project

COPY . .

CMD ["sleep", "infinity"]
