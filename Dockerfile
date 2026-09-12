FROM python:3.13-slim

WORKDIR /app
COPY . /app

ENV PORT=10000
ENV MOTOJA_DB=/var/data/motoja.sqlite3

EXPOSE 10000
CMD ["python3", "server.py"]
