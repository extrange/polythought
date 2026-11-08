# Base image for all stages. Pin the tag and digest for reproducible builds.
FROM python:3.15-slim@sha256:65a65fc7b30b06cb6df4930fd4650697cb23f4c2698ab81fc87e4b031bc36928 AS base

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest@sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490 /uv /uvx /bin/

ENV APP_DIR=/app \
    TZ=Asia/Singapore \
    PYTHONPATH=/app/src \
    UV_CACHE_DIR=/home/user/.cache/uv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    PYTHONUNBUFFERED=1

# Make `python`, `pytest`, etc. resolve to the project virtualenv.
ENV PATH="/app/.venv/bin:$PATH"

# Run as an unprivileged user. UID/GID 1000 matches the bind-mounted
# `db/` and `credentials/` directories created by a typical Linux host user.
RUN groupadd --gid 1000 user \
    && useradd --uid 1000 --gid 1000 --create-home --shell /bin/bash user \
    && mkdir -p "$APP_DIR" \
    && chown user:user "$APP_DIR"

USER user
WORKDIR $APP_DIR

#--------------------

FROM base AS deployment

# Install dependencies first so source-only changes reuse this layer.
RUN --mount=type=cache,target=$UV_CACHE_DIR,uid=1000,gid=1000 \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

COPY --chown=user:user pyproject.toml uv.lock $APP_DIR/
COPY --chown=user:user README.md $APP_DIR/
COPY --chown=user:user src $APP_DIR/src

# Installing the project separately from its dependencies keeps caching optimal.
RUN --mount=type=cache,target=$UV_CACHE_DIR,uid=1000,gid=1000 \
    uv sync --frozen --no-dev

CMD ["python", "-m", "polythought.main"]
