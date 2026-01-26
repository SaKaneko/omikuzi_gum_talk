FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ ./src/
ENV FLASK_APP=src.app.main
ENV FLASK_APP=app.main
# Ensure `src/` is on the import path so `import app...` works
ENV PYTHONPATH=/app/src
# Run as a module so package imports inside `app` work correctly

# Allow setting a build-time SECRET_KEY. Pass with `--build-arg SECRET_KEY=...`.
# Recommended: generate a strong random key at build time and pass it in:
#
# docker build \
#   --build-arg SECRET_KEY="$(python - <<'PY'\nimport secrets\nprint(secrets.token_urlsafe(48))\nPY)" \
#   -t your-image-name .
#
# Expose the build-arg as an image ENV so the app can read `os.environ['SECRET_KEY']`.
ARG SECRET_KEY
ENV SECRET_KEY=${SECRET_KEY}
