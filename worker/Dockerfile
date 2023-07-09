FROM python:3.11-alpine
RUN apk add --update --no-cache supervisor
RUN mkdir /log
WORKDIR /worker
COPY . .
RUN pip install -r requirements.txt
ENTRYPOINT ["/usr/bin/supervisord", "-c", "/worker/supervisord.conf"]
