FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

RUN curl -Ls https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen

# Install Playwright + Chromium for PPR downloads
RUN uv run playwright install chromium --with-deps

COPY scripts/ ./scripts/
COPY api/      ./api/
COPY db/       ./db/
COPY datasets/  ./datasets/

ENV PYTHONPATH=/app/scripts

EXPOSE 8080

CMD ["uv", "run", "python", "api/app.py"]