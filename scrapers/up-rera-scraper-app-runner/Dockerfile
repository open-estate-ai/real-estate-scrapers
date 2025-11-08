ARG PYTHON_VERSION=3.12
FROM python:${PYTHON_VERSION}-slim AS base

RUN apt-get update && apt-get install -y \
    libpq-dev build-essential unzip awscli curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Playwright dependencies (system-level dependencies for Chromium)
# Install Playwright browsers for root user first (build stage)
RUN npx -y playwright install --with-deps chromium

RUN adduser --uid 5555 --disabled-password app
WORKDIR /scrapers/up-rera-scraper-app-runner

# Build
FROM base AS build
RUN pip install --no-cache-dir uv
ENV UV_PROJECT_ENVIRONMENT=/scrapers/up-rera-scraper-app-runner/.venv
COPY pyproject.toml uv.lock README.md /scrapers/up-rera-scraper-app-runner/
RUN uv sync --frozen

# Install Playwright browsers in the virtual environment
ENV PATH=/scrapers/up-rera-scraper-app-runner/.venv/bin:$PATH
RUN playwright install chromium

COPY . /scrapers/up-rera-scraper-app-runner
RUN ls -lart /scrapers/up-rera-scraper-app-runner

# Local dev
FROM build AS localdev
ENV PYTHONUNBUFFERED=1 ENV=local

CMD ["hypercorn", "app:app", "--bind", "0.0.0.0:8080", "--reload"]

# Production
FROM base AS dist
COPY --chown=app:app --from=build /scrapers/up-rera-scraper-app-runner /scrapers/up-rera-scraper-app-runner

# Copy Playwright browsers from build stage to app user's home
COPY --chown=app:app --from=build /root/.cache/ms-playwright /home/app/.cache/ms-playwright

USER 5555

ENV PATH=/scrapers/up-rera-scraper-app-runner/.venv/bin:$PATH
ENV PYTHONPATH=/scrapers/up-rera-scraper-app-runner/src
ENV PYTHONUNBUFFERED=1 HYPERCORN_WORKERS=1
ENV PLAYWRIGHT_BROWSERS_PATH=/home/app/.cache/ms-playwright

CMD ["sh", "-c", "hypercorn app:app --bind 0.0.0.0:8080 --workers ${HYPERCORN_WORKERS}"]
