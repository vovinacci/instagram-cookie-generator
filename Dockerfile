# syntax=docker/dockerfile:1

### --- Stage 1: Builder ---
FROM python:3.13.11-slim-trixie AS builder

WORKDIR /build

# Copy only necessary files to build the wheel
COPY pyproject.toml src/ ./

# Build wheel
# hadolint ignore=DL3013
RUN pip install --no-cache-dir --upgrade pip && \
    pip wheel --no-deps --wheel-dir /wheels .

### --- Stage 2: Runtime ---
FROM python:3.13.11-slim-trixie

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

ARG BUILD_DATETIME=now
ARG CONTAINER_IMAGE_VERSION=source
ARG VCS_REF=HEAD

# Labels as per https://github.com/opencontainers/image-spec/blob/master/annotations.md
LABEL org.opencontainers.image.authors="vovin@lurk.kyiv.ua" \
      org.opencontainers.image.created="${BUILD_DATETIME}" \
      org.opencontainers.image.revision="${VCS_REF}" \
      org.opencontainers.image.source="https://github.com/vovinacci/instagram-cookie-generator" \
      org.opencontainers.image.title="instagram-cookie-generator" \
      org.opencontainers.image.description="Manage Instagram cookies, save them in Netscape HTTP Cookie File format " \
      org.opencontainers.image.vendor="Volodymyr Shcherbinin (vovin)" \
      org.opencontainers.image.version="${CONTAINER_IMAGE_VERSION}"

WORKDIR /app

# Install runtime dependencies
# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      curl \
      firefox-esr \
      fonts-liberation \
      libasound2 \
      libdbus-glib-1-2 \
      libgtk-3-0 \
      libnss3 \
      libxss1 && \
    apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/* /var/cache/debconf/*-old /var/lib/dpkg/*-old /var/log/* /tmp/* /var/tmp/*

# Install the built wheel
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-compile /wheels/* && \
    rm -fr /wheels

# Drop privileges
RUN addgroup --system app && adduser --system --ingroup app --home /app app && \
    chown -R app:app /app
USER app

# Run app
CMD ["python3", "-m", "instagram_cookie_generator.main"]
