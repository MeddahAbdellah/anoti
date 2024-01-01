# Build stage
FROM python:3.8 AS builder
COPY . .
RUN pip install -r requirements.txt

# Final stage
FROM python:3.8-slim
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
COPY . .
WORKDIR /
EXPOSE 8080
ENTRYPOINT ["python"]
CMD ["-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
