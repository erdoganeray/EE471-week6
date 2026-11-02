# Speech-studio website (Week 5 Task 1) in a container.
# Build context is the EE471-week5 submodule:
#   docker build -f Task-1-Docker/speech-studio/Dockerfile -t speech-studio EE471-week5

# Base image: Debian bookworm with Python 3.12. "slim" leaves out compilers and docs (~150 MB instead of ~1 GB).
# Bookworm is pinned because the Azure Speech SDK lists it as a supported Linux.
FROM python:3.12-slim-bookworm

# Native libraries the Azure Speech SDK loads at runtime: OpenSSL for HTTPS/WebSocket to Azure,
# CA certificates to trust Azure's TLS certificate, and ALSA (the SDK links against it even without a speaker).
# The apt cache is deleted in the same RUN so it never ends up in an image layer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libssl3 ca-certificates libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Print logs immediately (no buffering) and don't write .pyc files
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Requirements are copied and installed before the source code: Docker caches each step,
# so editing app.py later reuses this layer instead of reinstalling every package.
COPY Week-5-Task-1/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY Week-5-Task-1/ .

# Run as a normal user instead of root, so a bug in the app cannot change the container's system files
RUN useradd --create-home appuser
USER appuser

# Documents the port the app listens on (publishing it to the host is done with -p / compose "ports")
EXPOSE 5000

# Gunicorn instead of "python app.py": Flask's built-in server is for development only.
# 0.0.0.0 accepts connections from outside the container (127.0.0.1 would only accept the container itself).
# Speech-to-text can wait up to 120 s for Azure, so the worker timeout is raised above Gunicorn's 30 s default.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--threads", "4", "--timeout", "150", "app:app"]
