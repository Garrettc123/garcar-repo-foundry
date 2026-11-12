# Staging-only passive telemetry canary for Repo Foundry.
# This does not run repository generation, GitHub writes, auto-fixes or deployment workflows.
FROM python:3.12-alpine
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY mesh_heartbeat.py /app/mesh_heartbeat.py
USER 65532:65532
CMD ["sh", "-c", "while true; do python -u /app/mesh_heartbeat.py; sleep 300; done"]
