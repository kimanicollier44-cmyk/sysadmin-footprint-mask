FROM python:3.12-slim
WORKDIR /app
COPY . /app
RUN chmod +x bin/sanitize-env bin/secure-exec
CMD ["python3", "main.py"]
