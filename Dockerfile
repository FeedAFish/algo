FROM python:3.12-slim

WORKDIR /Project

COPY requirement.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .