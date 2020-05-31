FROM python:3.7.7-alpine
WORKDIR /app
RUN apk add --no-cache gcc musl-dev linux-headers libffi-dev libressl-dev python3-dev
COPY ./src/requirements.txt requirements.txt
RUN pip install -r requirements.txt