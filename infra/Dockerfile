FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/trace
COPY requirements.txt /tmp/backend-requirements.txt
COPY frontend/requirements.txt /tmp/frontend-requirements.txt
RUN python -m pip install -r /tmp/backend-requirements.txt -r /tmp/frontend-requirements.txt
RUN groupadd --gid 10001 trace && useradd --uid 10001 --gid trace --create-home trace

# Deliberate copies: no local environment, credentials or untracked uploads.
COPY app ./app
COPY frontend ./frontend
COPY fixtures ./fixtures
COPY samples ./samples
COPY eval ./eval
COPY scripts ./scripts
COPY infra/check_deployment.py ./infra/check_deployment.py
COPY .streamlit/config.toml ./.streamlit/config.toml

USER 10001:10001
