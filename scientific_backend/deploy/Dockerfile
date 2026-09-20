FROM python:3.13-slim
WORKDIR /app
COPY requirements.lock.txt .
RUN pip install --no-cache-dir -r requirements.lock.txt && useradd --uid 1000 --create-home scientist
COPY app app
COPY static static
COPY casepacks casepacks
COPY skills skills
RUN mkdir -p runtime && chown -R scientist:scientist /app/runtime
USER scientist
ENV ROSALIND_RUNTIME=/app/runtime
EXPOSE 8080
CMD ["python", "-m", "app", "serve", "--host", "0.0.0.0", "--port", "8080"]
