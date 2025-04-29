# syntax=docker/dockerfile:1

### --- Stage 1: Builder ---
FROM python:3.13.3-slim-bullseye AS builder

WORKDIR /build

# Copy only necessary files to build the wheel
COPY pyproject.toml src/ ./

# Build wheel
RUN pip wheel --no-deps --wheel-dir /wheels .

### --- Stage 2: Runtime ---
FROM python:3.13.3-slim-bullseye

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install runtime dependencies
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      firefox-esr \
      curl \
      libdbus-glib-1-2 \
      libgtk-3-0 \
      libnss3 \
      libxss1 \
      libasound2 \
      fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

# Install the built wheel
COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

# Run app
CMD ["python3", "-m", "instagram_cookie_generator.main"]
