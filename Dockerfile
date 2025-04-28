FROM python:3.13.3-slim-bullseye

ENV GECKODRIVER_VERSION=v0.36.0

WORKDIR /app

# hadolint ignore=DL3008
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      firefox-esr \
      wget \
      curl \
      unzip \
      libdbus-glib-1-2 \
      libgtk-3-0 \
      libnss3 \
      libxss1 \
      libasound2 \
      fonts-liberation && \
    rm -rf /var/lib/apt/lists/*

RUN wget -nv https://github.com/mozilla/geckodriver/releases/download//${GECKODRIVER_VERSION}/geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz && \
    tar -xvzf geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz && \
    mv geckodriver /usr/local/bin/ && \
    chmod +x /usr/local/bin/geckodriver && \
    rm -f geckodriver-${GECKODRIVER_VERSION}-linux64.tar.gz && \
    geckodriver --version

COPY pyproject.toml src/ ./

RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1

CMD ["python3", "-m", "instagram_cookie_updater.main"]
