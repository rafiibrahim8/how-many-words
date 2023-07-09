FROM python:3.11-alpine
RUN apk add --update --no-cache supervisor
RUN mkdir /log
WORKDIR /server
COPY . .
RUN pip install -r requirements.txt
EXPOSE 65011
ENTRYPOINT ["/usr/bin/supervisord", "-c", "/server/supervisord.conf"]
