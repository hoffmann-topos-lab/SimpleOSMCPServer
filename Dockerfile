

FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && \
    apt-get install -y ca-certificates && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir "mcp[cli]"
COPY mcp_server.py .
COPY config.json .
RUN mkdir -p sandbox logs

ENV PYTHONUNBUFFERED=1
CMD ["python", "mcp_server.py"]
