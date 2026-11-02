# Voice-activated calculator (Week 5 Task 2) in a container.
# Build context is the EE471-week5 submodule:
#   docker build -f Task-1-Docker/voice-calculator/Dockerfile -t voice-calculator EE471-week5

# No native libraries needed here: speech runs in the browser with the JavaScript SDK,
# the Python side only does math and hands out Azure tokens.
FROM python:3.12-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Same folder layout as the repository, because web_calculator.py imports
# ../EE471_MP1_Calculator/custom_classes.py relative to its own location
WORKDIR /app/Week-5-Task-2

COPY Week-5-Task-2/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY EE471_MP1_Calculator/ /app/EE471_MP1_Calculator/
COPY Week-5-Task-2/ .

RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "app:app"]
