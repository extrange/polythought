# Polythought Bot

Source code for [@PolythoughtBot][polythought-bot], which collects links for the
[Polythought] channel and posts them every day at 07:00 (Asia/Singapore).

## Development

The project uses [devenv](https://devenv.sh) for a reproducible shell with
Python 3.15, uv, and the git hooks:

```bash
devenv shell
```

On shell entry devenv runs `uv sync --frozen` and installs the commit hooks
defined in [`devenv.nix`](devenv.nix). The generated `.pre-commit-config.yaml` is
ignored; edit `devenv.nix` to change hooks. Run the hook suite with:

```bash
devenv test
```

Without devenv, install Python 3.15 and [uv](https://docs.astral.sh/uv/) and use:

```bash
uv sync
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

Settings are read from environment variables (see
`src/polythought/settings.py`); optional settings have sane defaults, so only
the required ones in [`.env.example`](.env.example) need real values. The test
suite provides dummy values in `tests/conftest.py`, so no real credentials are
needed to run it.

## CI/CD

[`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on every push to any
branch and on every pull request:

- Ruff lint and format checks
- Pyright type checking
- Pytest
- TruffleHog secret scanning
- A Docker build of the `deployment` target

On pushes to `main` and to `v*` tags, the same workflow publishes the image to
the GitHub Container Registry as `ghcr.io/extrange/polythought`, tagged with
`latest`, the branch/tag name, and a `sha-` prefix.

## Deployment

`compose.yml` pulls the image that CI built rather than building locally:

```bash
docker compose pull
docker compose up -d
```

If the GHCR package is private, log in first:

```bash
echo "$GITHUB_TOKEN" | docker login ghcr.io -u <username> --password-stdin
```

Pin a specific build by setting `POLYTHOUGHT_IMAGE`:

```bash
POLYTHOUGHT_IMAGE=ghcr.io/extrange/polythought:sha-abc1234 docker compose up -d
```

To build and run the image from a local checkout instead:

```bash
docker compose -f compose.yml -f compose.build.yml up --build
```

Configuration is split three ways:

- Credentials and secrets (`API_ID`, `API_HASH`, `BOT_TOKEN`) go in `.env`; copy
  [`.env.example`](.env.example) and fill it in.
- Deployment-specific settings (`CHANNEL_ID`, `MY_CHAT_ID`, `SESSION_FILE`) are
  inlined in `compose.yml`.
- Everything else (`DEBUG`, `DB_PATH`, `CAMOFOX_URL`, `TZ`) has a sane
  default in `src/polythought/settings.py` and only needs overriding when the
  default does not fit.

`compose.yml` starts a dedicated camofox browser alongside the bot. Page titles
are resolved through its HTTP API at `http://polythought-camofox:9377` by
default; override that with `CAMOFOX_URL`.

[Polythought]: https://t.me/polythought
[polythought-bot]: https://t.me/PolythoughtBot
