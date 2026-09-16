# Runner image for the demos: uv + Python 3.12, dependencies locked via uv.lock.
# Based on Astral's official combined image (recommended way to use uv in Docker).
FROM ghcr.io/astral-sh/uv:0.9.30-python3.12-bookworm-slim

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
